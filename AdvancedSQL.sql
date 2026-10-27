DELIMITER $$

CREATE TRIGGER trg_region_demand_before_insert
BEFORE INSERT ON REGION_DETAILS
FOR EACH ROW
BEGIN
    IF NEW.Demand_MU IS NOT NULL THEN
        SET NEW.Demand_MU = NEW.Demand_MU * 0.024;
        
               IF NEW.Demand_MU > 100 THEN
            SET NEW.Demand_MU = NEW.Demand_MU - 15;
        END IF;
        
    END IF;
END$$

DELIMITER ;


DELIMITER $$

CREATE PROCEDURE sp_UpdateRegionGenerationFromProduction()
BEGIN
    
    UPDATE REGION_DETAILS AS rd
    JOIN (
               SELECT 
            p.State_Code,
            pl.Log_Date,
            SUM(pl.Todays_Actual_MU) AS Total_Actual_MU
        FROM 
            PRODUCTIONLOG AS pl
        JOIN 
            POWERPLANTS AS p ON pl.Plant_ID = p.Plant_ID
        WHERE
            p.State_Code IS NOT NULL
        GROUP BY 
            p.State_Code, pl.Log_Date
    ) AS daily_totals 
    ON 
        rd.State_Code = daily_totals.State_Code 
        AND rd.Report_Date = daily_totals.Log_Date

    -- Set the Generated_MU column to the calculated total
    SET 
        rd.Generated_MU = daily_totals.Total_Actual_MU;
END$$

DELIMITER ;




DELIMITER $$

CREATE PROCEDURE sp_UpdateRegionSurplusAndImports()
BEGIN
    UPDATE REGION_DETAILS
    SET 
        Surplus_MU = CASE 
                         WHEN Generated_MU > Demand_MU 
                             THEN (Generated_MU - Demand_MU) 
                         ELSE 0 
                     END,
        
        Imported_MU = CASE 
                          WHEN Demand_MU > Generated_MU 
                              THEN (Demand_MU - Generated_MU) 
                          ELSE 0 
                      END
    WHERE 
        Generated_MU IS NOT NULL 
        AND Demand_MU IS NOT NULL;
END$$

DELIMITER ;


DELIMITER $$

CREATE PROCEDURE sp_CalculatePlantEfficiency()
BEGIN
    UPDATE PRODUCTIONLOG
    SET 
        Efficiency_Percentage = (Todays_Actual_MU / Capable_Generation_MU) * 100
    WHERE 
        Capable_Generation_MU IS NOT NULL 
        AND Capable_Generation_MU > 0
        AND Todays_Actual_MU IS NOT NULL;
END$$

DELIMITER ;


CREATE PROCEDURE sp_InsertAllMissingActiveStatuses()
BEGIN
    
    INSERT INTO OPERATIONAL_STATUS (
        Plant_ID, 
        Unit_Number, 
        Status_Date, 
        Status, 
        Cap_Under_Outage_MW, 
        Expected_Sync_Date, 
        Remarks, 
        Outage_Date
    )
    -- Select all (Plant, Date) combinations...
    SELECT 
        p.Plant_ID,
        'Main' AS Unit_Number,     
        d.`Date` AS Status_Date,   
        'Active' AS Status,        
        0.00 AS Cap_Under_Outage_MW, 
        NULL AS Expected_Sync_Date,  
        NULL AS Remarks,             
        NULL AS Outage_Date          
    FROM 
        POWERPLANTS p
    CROSS JOIN 
        DATE_DIM d
    WHERE 
        -- ...for which NOT A SINGLE record exists in OPERATIONAL_STATUS
        -- for that Plant_ID and Date (regardless of Unit_Number)
        NOT EXISTS (
            SELECT 1 
            FROM OPERATIONAL_STATUS os
            WHERE os.Plant_ID = p.Plant_ID 
              AND os.Status_Date = d.`Date`
        );
END$$

DELIMITER ;

DELIMITER $$
CREATE PROCEDURE sp_GenerateDailyEnergyReport(IN report_date DATE)
BEGIN
SELECT
rd.State_Code,
rd.Report_Date,
COALESCE(rd.Generated_MU, 0) AS total_generated_mu,
COALESCE(rd.Demand_MU, 0) AS total_demand_mu,
COALESCE(rd.Surplus_MU, 0) AS total_surplus_mu,
COALESCE(rd.Imported_MU, 0) AS total_imported_mu
FROM REGION_DETAILS rd
WHERE rd.Report_Date = report_date
ORDER BY rd.State_Code;
END$$
DELIMITER ;

DELIMITER $$
CREATE PROCEDURE sp_IdentifyUnderperformingPlants(IN threshold_efficiency DECIMAL(5,2), IN days_to_check INT)
BEGIN
    SELECT
        p.Plant_ID,
        p.Plant_Name,
        s.State_Name,
        ROUND(AVG(pl.Efficiency_Percentage), 2) AS avg_efficiency
    FROM POWERPLANTS p
    LEFT JOIN PRODUCTIONLOG pl ON p.Plant_ID = pl.Plant_ID
    LEFT JOIN STATE s ON p.State_Code = s.State_Code
    WHERE pl.Log_Date >= DATE_SUB(CURDATE(), INTERVAL days_to_check DAY)
    GROUP BY p.Plant_ID, p.Plant_Name, s.State_Name
    HAVING AVG(pl.Efficiency_Percentage) < threshold_efficiency
    ORDER BY avg_efficiency ASC;
END$$
DELIMITER ;



DELIMITER $$
CREATE PROCEDURE sp_CalculateRegionalMetrics(IN start_date DATE, IN end_date DATE)
BEGIN
    -- Aggregate production data by state first
    WITH StateProduction AS (
        SELECT 
            p.State_Code,
            COUNT(DISTINCT p.Plant_ID) AS Total_Plants,
            COALESCE(SUM(pl.Todays_Actual_MU), 0) AS Total_Generated_MU
        FROM POWERPLANTS p
        LEFT JOIN PRODUCTIONLOG pl ON p.Plant_ID = pl.Plant_ID 
            AND pl.Log_Date BETWEEN start_date AND end_date
        GROUP BY p.State_Code
    ),
    StateDemand AS (
        SELECT 
            State_Code,
            COALESCE(SUM(Demand_MU), 0) AS Total_Demand_MU
        FROM REGION_DETAILS
        WHERE Report_Date BETWEEN start_date AND end_date
        GROUP BY State_Code
    )
    SELECT
        s.Region,
        COALESCE(SUM(sp.Total_Plants), 0) AS Total_Plants,
        COALESCE(SUM(sp.Total_Generated_MU), 0) AS Total_Generated_MU,
        COALESCE(SUM(sd.Total_Demand_MU), 0) AS Total_Demand_MU,
        CASE 
            WHEN SUM(sd.Total_Demand_MU) > 0 THEN
                ROUND((SUM(sp.Total_Generated_MU) / SUM(sd.Total_Demand_MU)) * 100, 2)
            ELSE 0
        END AS Supply_Percentage
    FROM STATE s
    LEFT JOIN StateProduction sp ON s.State_Code = sp.State_Code
    LEFT JOIN StateDemand sd ON s.State_Code = sd.State_Code
    GROUP BY s.Region
    ORDER BY Total_Generated_MU DESC;
END$$
DELIMITER ;



Get main dashboard KPIs and metrics

SELECT COUNT(DISTINCT Plant_ID) FROM POWERPLANTS;
SELECT Log_Date FROM PRODUCTIONLOG GROUP BY Log_Date HAVING COUNT(DISTINCT Plant_ID) = :total ORDER BY Log_Date DESC LIMIT 1;
SELECT MAX(d.`Date`) FROM DATE_DIM d WHERE EXISTS (SELECT 1 FROM PRODUCTIONLOG pl WHERE pl.Log_Date = d.`Date;

SELECT COALESCE(SUM(Todays_Actual_MU), 0) FROM PRODUCTIONLOG WHERE Log_Date = :log_date;
SELECT ROUND(AVG(Efficiency_Percentage), 2) FROM PRODUCTIONLOG WHERE Log_Date = :log_date;
SELECT COUNT(DISTINCT Plant_ID) FROM OPERATIONAL_STATUS WHERE Status_Date = :status_date AND Status = 'Under Outage;

Get energy type distribution for last 30 days

SELECT COUNT(DISTINCT Plant_ID) FROM POWERPLANTS;
SELECT Log_Date FROM PRODUCTIONLOG GROUP BY Log_Date HAVING COUNT(DISTINCT Plant_ID) = :total ORDER BY Log_Date DESC LIMIT 1;
SELECT MAX(d.`Date`) FROM DATE_DIM d WHERE EXISTS (SELECT 1 FROM PRODUCTIONLOG pl WHERE pl.Log_Date = d.`Date;

SELECT 
COALESCE(et.Type_Name, 'Unknown') as type_name,
COUNT(DISTINCT p.Plant_ID) as plant_count,
COALESCE(SUM(pl.Todays_Actual_MU), 0) as total_generation_mu,
COALESCE(ROUND(AVG(pl.Efficiency_Percentage), 2), 0) as avg_efficiency
FROM ENERGYTYPE et
LEFT JOIN POWERPLANTS p ON et.Type_ID = p.Type_ID
LEFT JOIN PRODUCTIONLOG pl ON p.Plant_ID = pl.Plant_ID 
AND pl.Log_Date = :log_date
WHERE et.Type_ID IS NOT NULL
GROUP BY et.Type_Name
HAVING SUM(pl.Todays_Actual_MU) > 0
ORDER BY total_generation_mu DESC;

Get top performing plants

SELECT 
    p.Plant_ID,
    p.Plant_Name,
    s.State_Name,
    et.Type_Name,
    COALESCE(ROUND(pl.Efficiency_Percentage, 2), 0) AS efficiency,
    COALESCE(ROUND(pl.Todays_Actual_MU, 2), 0) AS todays_generation_mu
FROM POWERPLANTS p
LEFT JOIN STATE s 
    ON p.State_Code = s.State_Code
LEFT JOIN ENERGYTYPE et 
    ON p.Type_ID = et.Type_ID
LEFT JOIN PRODUCTIONLOG pl 
    ON p.Plant_ID = pl.Plant_ID 
   AND pl.Log_Date = :log_date
ORDER BY efficiency DESC
LIMIT 10;



Get all power plants
Get comprehensive plant details

SELECT 
    p.Plant_ID,
    p.Plant_Name,
    s.State_Name,
    s.Region,
    sec.Sector_Name,
    et.Type_Name,
    et.Description,

    (SELECT AVG(Efficiency_Percentage)
     FROM PRODUCTIONLOG
     WHERE Plant_ID = p.Plant_ID 
       AND Log_Date = :selected_date) AS Avg_Efficiency,

    (SELECT SUM(Todays_Actual_MU)
     FROM PRODUCTIONLOG
     WHERE Plant_ID = p.Plant_ID 
       AND Log_Date = :selected_date) AS Total_Generation_MU,

    (SELECT AVG(Operational_Capacity_MW)
     FROM PRODUCTIONLOG
     WHERE Plant_ID = p.Plant_ID 
       AND Log_Date = :selected_date) AS Avg_Capacity_MW,

    (SELECT MAX(Log_Date)
     FROM PRODUCTIONLOG
     WHERE Plant_ID = p.Plant_ID) AS Last_Log_Date,

    (SELECT Status
     FROM OPERATIONAL_STATUS
     WHERE Plant_ID = p.Plant_ID
       AND Status_Date = :selected_date
     LIMIT 1) AS Current_Status,

    (SELECT Remarks
     FROM OPERATIONAL_STATUS
     WHERE Plant_ID = p.Plant_ID
       AND Status_Date = :selected_date
     LIMIT 1) AS Status_Remarks,

    (SELECT Outage_Date
     FROM OPERATIONAL_STATUS
     WHERE Plant_ID = p.Plant_ID
       AND Status_Date = :selected_date
     LIMIT 1) AS Outage_Date

FROM POWERPLANTS p
INNER JOIN STATE s 
    ON p.State_Code = s.State_Code
INNER JOIN SECTOR sec 
    ON p.Sector_ID = sec.Sector_ID
INNER JOIN ENERGYTYPE et 
    ON p.Type_ID = et.Type_ID
WHERE p.Plant_ID = :plant_id;


Get production history for a plant

SELECT 
    Log_Date,
    Efficiency_Percentage,
    Todays_Actual_MU,
    Capable_Generation_MU,
    Operational_Capacity_MW,
    Coal_Stock_Days
FROM PRODUCTIONLOG
WHERE Plant_ID = :plant_id
  AND Log_Date >= DATE_SUB(CURDATE(), INTERVAL :days DAY)
ORDER BY Log_Date DESC;



Get list of states for filtering

SELECT DISTINCT s.State_Code, s.State_Name
            FROM STATE s
            INNER JOIN POWERPLANTS p ON s.State_Code = p.State_Code
            ORDER BY s.State_Name;


Get list of sectors for filtering

SELECT DISTINCT sec.Sector_ID, sec.Sector_Name
            FROM SECTOR sec
            INNER JOIN POWERPLANTS p ON sec.Sector_ID = p.Sector_ID
            ORDER BY sec.Sector_Name;

Get list of energy types for filtering

SELECT DISTINCT et.Type_ID, et.Type_Name
            FROM ENERGYTYPE et
            INNER JOIN POWERPLANTS p ON et.Type_ID = p.Type_ID
            ORDER BY et.Type_Name;

Get all regions with energy statistics

SELECT 
    rd.State_Code,
    s.State_Name,
    s.Region,
    (SELECT COUNT(DISTINCT Plant_ID) 
     FROM POWERPLANTS 
     WHERE State_Code = rd.State_Code) AS Plant_Count,
     
    COALESCE(rd.Generated_MU, 0) AS Generated_MU,
    COALESCE(rd.Demand_MU, 0) AS Demand_MU,

    CASE 
        WHEN COALESCE(rd.Generated_MU, 0) >= COALESCE(rd.Demand_MU, 0) 
            THEN 'Surplus'
        ELSE 'Deficit'
    END AS Energy_Status

FROM REGION_DETAILS rd
INNER JOIN STATE s 
    ON rd.State_Code = s.State_Code

WHERE rd.Report_Date = :selected_date
ORDER BY s.Region, s.State_Name;

Get energy mix distribution for a specific state

SELECT 
    et.Type_Name,
    COALESCE(SUM(pl.Todays_Actual_MU), 0) AS Total_Generated_MU
FROM POWERPLANTS p
INNER JOIN ENERGYTYPE et 
    ON p.Type_ID = et.Type_ID
LEFT JOIN PRODUCTIONLOG pl 
    ON p.Plant_ID = pl.Plant_ID 
   AND pl.Log_Date = :selected_date
WHERE p.State_Code = :state_code
GROUP BY et.Type_Name
HAVING Total_Generated_MU > 0
ORDER BY Total_Generated_MU DESC;


Get all system alerts

SELECT 
    'Low Efficiency' AS Alert_Type,
    p.Plant_Name,
    s.State_Name,
    ROUND(AVG(pl.Efficiency_Percentage), 2) AS Value,
    'WARNING' AS Severity,
    MAX(pl.Log_Date) AS Last_Occurrence
FROM POWERPLANTS p
INNER JOIN PRODUCTIONLOG pl 
    ON p.Plant_ID = pl.Plant_ID
INNER JOIN STATE s 
    ON p.State_Code = s.State_Code
WHERE pl.Log_Date >= DATE_SUB(CURDATE(), INTERVAL 3 DAY)
GROUP BY 
    p.Plant_ID, 
    p.Plant_Name, 
    s.State_Name
HAVING AVG(pl.Efficiency_Percentage) < 60

UNION ALL

SELECT 
    'Critical Coal Stock' AS Alert_Type,
    p.Plant_Name,
    s.State_Name,
    pl.Coal_Stock_Days AS Value,
    CASE 
        WHEN pl.Coal_Stock_Days < 4 THEN 'CRITICAL'
        ELSE 'WARNING'
    END AS Severity,
    pl.Log_Date AS Last_Occurrence
FROM POWERPLANTS p
INNER JOIN PRODUCTIONLOG pl 
    ON p.Plant_ID = pl.Plant_ID
INNER JOIN STATE s 
    ON p.State_Code = s.State_Code
INNER JOIN ENERGYTYPE et 
    ON p.Type_ID = et.Type_ID
WHERE pl.Log_Date = (
        SELECT MAX(Log_Date) 
        FROM PRODUCTIONLOG 
        WHERE Plant_ID = p.Plant_ID
      )
  AND et.Type_Name IN ('THERMAL', 'THER (CGT)')
  AND pl.Coal_Stock_Days < 7

UNION ALL

SELECT 
    'Plant Outage' AS Alert_Type,
    p.Plant_Name,
    s.State_Name,
    os.Cap_Under_Outage_MW AS Value,
    CASE 
        WHEN os.Cap_Under_Outage_MW >= 500 THEN 'CRITICAL'
        ELSE 'WARNING'
    END AS Severity,
    os.Status_Date AS Last_Occurrence
FROM POWERPLANTS p
INNER JOIN OPERATIONAL_STATUS os 
    ON p.Plant_ID = os.Plant_ID
INNER JOIN STATE s 
    ON p.State_Code = s.State_Code
WHERE os.Status = 'Under Outage'
  AND os.Status_Date >= DATE_SUB(CURDATE(), INTERVAL 1 DAY)

ORDER BY 
    Severity DESC, 
    Last_Occurrence DESC;


Get plants with critical coal stock


SELECT 
    p.Plant_ID,
    p.Plant_Name,
    s.State_Name,
    sec.Sector_Name,
    pl.Log_Date,
    pl.Coal_Stock_Days,
    pl.Operational_Capacity_MW,
    CASE 
        WHEN pl.Coal_Stock_Days < 4 THEN 'CRITICAL'
        WHEN pl.Coal_Stock_Days < 7 THEN 'WARNING'
        ELSE 'ADEQUATE'
    END AS Stock_Status
FROM POWERPLANTS p
INNER JOIN PRODUCTIONLOG pl 
    ON p.Plant_ID = pl.Plant_ID
INNER JOIN STATE s 
    ON p.State_Code = s.State_Code
INNER JOIN SECTOR sec 
    ON p.Sector_ID = sec.Sector_ID
INNER JOIN ENERGYTYPE et 
    ON p.Type_ID = et.Type_ID
WHERE et.Type_Name IN ('THERMAL', 'THER (CGT)')
  AND pl.Coal_Stock_Days IS NOT NULL
  AND pl.Log_Date = (
        SELECT MAX(Log_Date) 
        FROM PRODUCTIONLOG 
        WHERE Plant_ID = p.Plant_ID
      )
  AND pl.Coal_Stock_Days < 7
ORDER BY 
    pl.Coal_Stock_Days ASC, 
    pl.Operational_Capacity_MW DESC;


Get renewable vs non-renewable energy mix by state

WITH EnergyMix AS (
    SELECT 
        s.State_Name,
        s.Region,
        CASE 
            WHEN et.Type_Name IN ('HYDRO', 'WIND', 'SOLAR', 'BIOMASS') 
                THEN 'Renewable'
            ELSE 'Non-Renewable'
        END AS Energy_Category,
        SUM(pl.Todays_Actual_MU) AS Total_Production_MU
    FROM POWERPLANTS p
    INNER JOIN PRODUCTIONLOG pl 
        ON p.Plant_ID = pl.Plant_ID
    INNER JOIN STATE s 
        ON p.State_Code = s.State_Code
    INNER JOIN ENERGYTYPE et 
        ON p.Type_ID = et.Type_ID
    GROUP BY 
        s.State_Name, 
        s.Region, 
        Energy_Category
)

SELECT 
    State_Name,
    Region,
    SUM(CASE WHEN Energy_Category = 'Renewable' THEN Total_Production_MU ELSE 0 END) AS Renewable_MU,
    SUM(CASE WHEN Energy_Category = 'Non-Renewable' THEN Total_Production_MU ELSE 0 END) AS Non_Renewable_MU,
    SUM(Total_Production_MU) AS Total_MU,
    ROUND(
        (
            SUM(CASE WHEN Energy_Category = 'Renewable' THEN Total_Production_MU ELSE 0 END) 
            / NULLIF(SUM(Total_Production_MU), 0)
        ) * 100, 
        2
    ) AS Renewable_Percentage
FROM EnergyMix
GROUP BY 
    State_Name, 
    Region
ORDER BY 
    Renewable_Percentage DESC;




