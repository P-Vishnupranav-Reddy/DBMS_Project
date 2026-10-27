import os
import sys
import argparse
import datetime
import decimal
import traceback

from pymongo import MongoClient
import mysql.connector

# --- Configuration from env ---
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/IndianEnergy-Company")
MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DB = os.getenv("MYSQL_DB", "IndianEnergyDB")

TARGET_TABLE = os.getenv("TARGET_TABLE", "REGION_DETAILS")
TARGET_DATE_COL = os.getenv("TARGET_DATE_COL", "Report_Date")
TARGET_STATE_COL = os.getenv("TARGET_STATE_COL", "State_Code")
TARGET_DEMAND_COL = os.getenv("TARGET_DEMAND_COL", "Demand_MU")

DATE_DIM_TABLE = os.getenv("DATE_DIM_TABLE", "DATE_DIM")
DATE_DIM_DATE_COL = os.getenv("DATE_DIM_DATE_COL", "Date")

MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "companies")

# --- Helpers ---
def get_mongo_client():
    return MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)

def get_mysql_conn():
    return mysql.connector.connect(
        host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER, password=MYSQL_PASSWORD, database=MYSQL_DB,
        autocommit=False
    )

def parse_date(v):
    if v is None: 
        return None
    if isinstance(v, (datetime.date, datetime.datetime)):
        return v.date() if isinstance(v, datetime.datetime) else v
    v = str(v).strip()
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.datetime.strptime(v, fmt).date()
        except Exception:
            pass
    # try ISO parse
    try:
        return datetime.date.fromisoformat(v)
    except Exception:
        return None

# Core apply: add demand_mu to REGION_DETAILS.Demand_MU for row (state_code, report_date)
def apply_doc(conn, mongo_coll, doc, dry_run=False, insert_if_missing=False):
    """
    Returns dict: {"ok": True} or {"ok": False, "reason": "...", "error": ...}
    """
    try:
        company_id = int(doc.get("id"))
    except Exception:
        return {"ok": False, "reason": "invalid_id"}

    demand_date = parse_date(doc.get("demand_date"))
    state_code = doc.get("state_code")
    demand_mu = doc.get("demand_MU")

    if demand_date is None or not state_code or demand_mu is None:
        return {"ok": False, "reason": "missing_fields"}

    demand_val = decimal.Decimal(str(demand_mu))

    cur = conn.cursor()
    try:
        # Begin transaction
        conn.start_transaction()

        # Ensure DATE_DIM entry exists if requested
        if insert_if_missing:
            cur.execute(f"SELECT {DATE_DIM_DATE_COL} FROM {DATE_DIM_TABLE} WHERE {DATE_DIM_DATE_COL} = %s FOR UPDATE", (demand_date,))
            if cur.fetchone() is None:
                # try inserting a minimal DATE_DIM row
                try:
                    cur.execute(f"INSERT INTO {DATE_DIM_TABLE} ({DATE_DIM_DATE_COL}) VALUES (%s)", (demand_date,))
                except Exception as e:
                    # cannot insert date_dim; bail out
                    conn.rollback()
                    return {"ok": False, "reason": "cannot_insert_date_dim", "error": str(e)}
        else:
            # Optionally check presence (but don't error here; we'll fail later on missing fk or missing row)
            pass

        # Lock the target REGION_DETAILS row
        cur.execute(
            f"SELECT {TARGET_DEMAND_COL} FROM {TARGET_TABLE} WHERE {TARGET_STATE_COL} = %s AND {TARGET_DATE_COL} = %s FOR UPDATE",
            (state_code, demand_date)
        )
        row = cur.fetchone()
        if row:
            current = decimal.Decimal(str(row[0] or 0))
            new_val = current + demand_val
            if not dry_run:
                cur.execute(
                    f"UPDATE {TARGET_TABLE} SET {TARGET_DEMAND_COL} = %s WHERE {TARGET_STATE_COL} = %s AND {TARGET_DATE_COL} = %s",
                    (str(new_val), state_code, demand_date)
                )
        else:
            # No existing fact row
            if insert_if_missing:
                # Attempt insert of minimal row (State_Code, Report_Date, Demand_MU)
                try:
                    if not dry_run:
                        cur.execute(
                            f"INSERT INTO {TARGET_TABLE} ({TARGET_STATE_COL}, {TARGET_DATE_COL}, {TARGET_DEMAND_COL}) VALUES (%s, %s, %s)",
                            (state_code, demand_date, str(demand_val))
                        )
                except Exception as e:
                    conn.rollback()
                    return {"ok": False, "reason": "insert_target_failed", "error": str(e)}
            else:
                conn.rollback()
                return {"ok": False, "reason": "no_target_row"}

        # Commit MySQL
        if not dry_run:
            conn.commit()
            # mark mongo doc as synced
            mongo_coll.update_one({"id": company_id}, {"$set": {"synced": True, "applied_at": datetime.datetime.utcnow()}})
        else:
            # dry run: rollback the transaction and don't update mongo
            conn.rollback()

        return {"ok": True}
    except Exception as e:
        try: conn.rollback()
        except: pass
        return {"ok": False, "reason": "mysql_error", "error": str(e), "trace": traceback.format_exc()}
    finally:
        try: cur.close()
        except: pass

def rollback_doc(conn, mongo_coll, company_id, dry_run=False):
    """
    Subtract the original demand value and unset synced flag.
    """
    doc = mongo_coll.find_one({"id": company_id})
    if not doc:
        return {"ok": False, "reason": "mongo_doc_not_found"}
    if not doc.get("synced"):
        return {"ok": False, "reason": "not_marked_synced"}

    demand_date = parse_date(doc.get("demand_date"))
    state_code = doc.get("state_code")
    demand_mu = doc.get("demand_MU")
    if demand_date is None or not state_code or demand_mu is None:
        return {"ok": False, "reason": "missing_fields_in_doc"}

    demand_val = decimal.Decimal(str(demand_mu))
    cur = conn.cursor()
    try:
        conn.start_transaction()
        cur.execute(
            f"SELECT {TARGET_DEMAND_COL} FROM {TARGET_TABLE} WHERE {TARGET_STATE_COL} = %s AND {TARGET_DATE_COL} = %s FOR UPDATE",
            (state_code, demand_date)
        )
        row = cur.fetchone()
        if not row:
            conn.rollback()
            return {"ok": False, "reason": "target_row_missing"}
        current = decimal.Decimal(str(row[0] or 0))
        new_val = current - demand_val
        if new_val < 0:
            new_val = decimal.Decimal("0")
        if not dry_run:
            cur.execute(
                f"UPDATE {TARGET_TABLE} SET {TARGET_DEMAND_COL} = %s WHERE {TARGET_STATE_COL} = %s AND {TARGET_DATE_COL} = %s",
                (str(new_val), state_code, demand_date)
            )
            conn.commit()
            # unset synced and set rolled_back_at
            mongo_coll.update_one({"id": company_id}, {"$set": {"synced": False, "rolled_back_at": datetime.datetime.utcnow()}})
        else:
            conn.rollback()
        return {"ok": True}
    except Exception as e:
        try: conn.rollback()
        except: pass
        return {"ok": False, "reason": "mysql_error", "error": str(e), "trace": traceback.format_exc()}
    finally:
        try: cur.close()
        except: pass

def main():
    parser = argparse.ArgumentParser(description="Sync Mongo companies -> MySQL REGION_DETAILS.Demand_MU")
    grp = parser.add_mutually_exclusive_group(required=True)
    grp.add_argument("--apply", action="store_true", help="Apply unapplied companies")
    grp.add_argument("--rollback", type=int, help="Rollback company by numeric id")
    parser.add_argument("--dry-run", action="store_true", help="Do not commit changes")
    parser.add_argument("--insert-if-missing", action="store_true", help="Insert DATE_DIM and REGION_DETAILS rows if missing")
    args = parser.parse_args()

    # Connect to Mongo
    try:
        mongo = get_mongo_client()
        mdb = mongo.get_default_database()
        coll = mdb[MONGO_COLLECTION]
    except Exception as e:
        print("Mongo connection failed:", e); sys.exit(1)

    # Connect to MySQL
    try:
        conn = get_mysql_conn()
    except Exception as e:
        print("MySQL connection failed:", e); sys.exit(1)

    try:
        if args.apply:
            cursor = coll.find({"$or":[{"synced": {"$exists": False}}, {"synced": False}]})
            applied = 0
            skipped = 0
            for doc in cursor:
                result = apply_doc(conn, coll, doc, dry_run=args.dry_run, insert_if_missing=args.insert_if_missing)
                if result.get("ok"):
                    applied += 1
                    print(f"Applied id={doc.get('id')}")
                else:
                    skipped += 1
                    print(f"Skipped id={doc.get('id')} reason={result.get('reason')}", result.get("error", ""))
            print(f"Done: applied={applied}, skipped={skipped}")
        else:
            cid = int(args.rollback)
            result = rollback_doc(conn, coll, cid, dry_run=args.dry_run)
            if result.get("ok"):
                print(f"Rolled back id={cid}")
            else:
                print("Rollback failed:", result)
    finally:
        try: conn.close()
        except: pass
        try: mongo.close()
        except: pass

if __name__ == "__main__":
    main()