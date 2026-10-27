"""
Generate User Requirement Specification PDF for Indian Energy Monitoring System
"""
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib import colors
from datetime import datetime

def create_urs_pdf():
    filename = "User_Requirement_Specification.pdf"
    doc = SimpleDocTemplate(filename, pagesize=letter,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=18)
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1e40af'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading1_style = ParagraphStyle(
        'CustomHeading1',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#1e40af'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    heading2_style = ParagraphStyle(
        'CustomHeading2',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#2563eb'),
        spaceAfter=10,
        spaceBefore=10,
        fontName='Helvetica-Bold'
    )
    
    heading3_style = ParagraphStyle(
        'CustomHeading3',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=colors.HexColor('#3b82f6'),
        spaceAfter=8,
        spaceBefore=8,
        fontName='Helvetica-Bold'
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=10,
        alignment=TA_JUSTIFY,
        spaceAfter=6
    )
    
    bullet_style = ParagraphStyle(
        'CustomBullet',
        parent=styles['BodyText'],
        fontSize=10,
        leftIndent=20,
        spaceAfter=4
    )
    
    # Title Page
    elements.append(Spacer(1, 2*inch))
    elements.append(Paragraph("USER REQUIREMENT SPECIFICATION", title_style))
    elements.append(Spacer(1, 0.3*inch))
    elements.append(Paragraph("Indian Energy Monitoring System", heading1_style))
    elements.append(Spacer(1, 0.5*inch))
    elements.append(Paragraph(f"Document Date: {datetime.now().strftime('%B %d, %Y')}", body_style))
    elements.append(Spacer(1, 0.2*inch))
    elements.append(Paragraph("Version 1.0", body_style))
    elements.append(PageBreak())
    
    # Abstract
    elements.append(Paragraph("ABSTRACT", heading1_style))
    abstract_text = """
    The Indian Energy Monitoring System is a comprehensive web-based platform designed to track, analyze, 
    and visualize India's energy generation landscape in real-time. The system aggregates live data from 
    meritindia.in, capturing daily generation statistics from renewable and conventional power plants across 
    multiple states and regions. Built with a React-based frontend and Flask backend architecture, the platform 
    provides stakeholders with interactive dashboards, analytical insights, and automated alert mechanisms for 
    monitoring energy production patterns. The system maintains a structured database of power plants, companies, 
    and regional metrics, enabling comparative analysis of energy mix, generation trends, and capacity utilization. 
    By processing daily XLS and PDF reports through automated web scraping, the platform transforms raw energy data 
    into actionable intelligence, supporting decision-making for energy policy, grid management, and renewable energy 
    transition planning. The application serves as a centralized monitoring tool for understanding India's dynamic 
    energy ecosystem and facilitating data-driven insights into the nation's power generation infrastructure.
    """
    elements.append(Paragraph(abstract_text, body_style))
    elements.append(Spacer(1, 0.3*inch))
    
    # 1. System Overview
    elements.append(Paragraph("1. SYSTEM OVERVIEW", heading1_style))
    elements.append(Paragraph(
        "A comprehensive real-time energy monitoring platform that tracks, analyzes, and visualizes India's "
        "power generation infrastructure by aggregating data from meritindia.in, providing stakeholders with "
        "actionable insights for energy management and policy planning.",
        body_style
    ))
    elements.append(Spacer(1, 0.2*inch))
    
    # 2. Functional Requirements
    elements.append(Paragraph("2. FUNCTIONAL REQUIREMENTS", heading1_style))
    
    # 2.1 Data Acquisition
    elements.append(Paragraph("2.1 Data Acquisition & Processing", heading2_style))
    data_acq_points = [
        "<b>Real-time Data Scraping:</b> Automated web scraping from meritindia.in to fetch daily power generation reports",
        "<b>Multi-format Support:</b> Process XLS (plant generation) and PDF (renewable energy) reports",
        "<b>Scheduled Updates:</b> Daily synchronization of power plant generation data from GitHub repository",
        "<b>Data Parsing Pipeline:</b> Sequential execution of integrated_web_scrapping.py, parseall1.py, parseall2.py, and parseall3.py"
    ]
    for point in data_acq_points:
        elements.append(Paragraph(f"• {point}", bullet_style))
    elements.append(Spacer(1, 0.15*inch))
    
    # 2.2 Dashboard & Visualization
    elements.append(Paragraph("2.2 Dashboard & Visualization", heading2_style))
    elements.append(Paragraph("<b>Main Dashboard KPIs:</b>", heading3_style))
    dashboard_kpis = [
        "Total number of power plants",
        "Today's generation (MU - Million Units)",
        "Today's demand (MU)",
        "Average efficiency percentage",
        "Total operational capacity (MW - Megawatts)",
        "Plants under outage count",
        "Critical coal stock alerts",
        "Date-based filtering capability"
    ]
    for kpi in dashboard_kpis:
        elements.append(Paragraph(f"• {kpi}", bullet_style))
    elements.append(Spacer(1, 0.1*inch))
    
    elements.append(Paragraph("<b>Interactive Charts:</b>", heading3_style))
    chart_types = [
        "Energy mix pie chart (renewable vs non-renewable)",
        "Regional performance bar charts",
        "Trend line charts for historical analysis",
        "Map visualization for geographical distribution",
        "Top performing plants comparison"
    ]
    for chart in chart_types:
        elements.append(Paragraph(f"• {chart}", bullet_style))
    elements.append(Spacer(1, 0.15*inch))
    
    # 2.3 Plant Management
    elements.append(Paragraph("2.3 Plant Management", heading2_style))
    elements.append(Paragraph("<b>Plant Listing:</b>", heading3_style))
    plant_list_features = [
        "Paginated view (20 plants per page)",
        "Search functionality by plant name/ID",
        "Filter by state, sector (State/Private/Central), energy type",
        "Display basic plant information"
    ]
    for feature in plant_list_features:
        elements.append(Paragraph(f"• {feature}", bullet_style))
    elements.append(Spacer(1, 0.1*inch))
    
    elements.append(Paragraph("<b>Detailed Plant View:</b>", heading3_style))
    plant_detail_features = [
        "Comprehensive plant information (name, location, sector, energy type)",
        "Production history with efficiency metrics",
        "Operational capacity and capability",
        "Coal stock levels (for thermal plants)",
        "Operational status by unit",
        "Outage information with expected sync dates",
        "Date-based historical data viewing"
    ]
    for feature in plant_detail_features:
        elements.append(Paragraph(f"• {feature}", bullet_style))
    elements.append(Spacer(1, 0.15*inch))
    
    elements.append(PageBreak())
    
    # 2.4 Analytics & Insights
    elements.append(Paragraph("2.4 Analytics & Insights", heading2_style))
    elements.append(Paragraph("<b>Regional Performance Analysis:</b>", heading3_style))
    regional_features = [
        "Region-wise total plants count",
        "Generated energy (MU)",
        "Demand (MU)",
        "Surplus/deficit calculation",
        "Supply percentage metrics",
        "Energy status classification"
    ]
    for feature in regional_features:
        elements.append(Paragraph(f"• {feature}", bullet_style))
    elements.append(Spacer(1, 0.1*inch))
    
    elements.append(Paragraph("<b>Efficiency Comparison:</b>", heading3_style))
    efficiency_features = [
        "Plant-wise average efficiency ranking",
        "Top 20 performing plants",
        "Efficiency percentage over time"
    ]
    for feature in efficiency_features:
        elements.append(Paragraph(f"• {feature}", bullet_style))
    elements.append(Spacer(1, 0.1*inch))
    
    elements.append(Paragraph("<b>Renewable Energy Mix:</b>", heading3_style))
    renewable_features = [
        "State-wise renewable vs non-renewable breakdown",
        "Renewable percentage calculation",
        "Production values in MU",
        "Last 30-day aggregated data"
    ]
    for feature in renewable_features:
        elements.append(Paragraph(f"• {feature}", bullet_style))
    elements.append(Spacer(1, 0.15*inch))
    
    # 2.5 Alert System
    elements.append(Paragraph("2.5 Alert System", heading2_style))
    elements.append(Paragraph("<b>Real-time Monitoring Alerts:</b>", heading3_style))
    alert_types = [
        "<b>Low Efficiency Alerts:</b> Plants with &lt;60% average efficiency (3-day window)",
        "<b>Critical Coal Stock:</b> Thermal plants with &lt;7 days coal stock (WARNING: 4-7 days, CRITICAL: &lt;4 days)",
        "<b>Plant Outage Alerts:</b> Units under outage status (CRITICAL: ≥500 MW, WARNING: &lt;500 MW)"
    ]
    for alert in alert_types:
        elements.append(Paragraph(f"• {alert}", bullet_style))
    elements.append(Spacer(1, 0.1*inch))
    
    elements.append(Paragraph("<b>Alert Dashboard:</b>", heading3_style))
    alert_dashboard = [
        "Total alerts count",
        "Critical vs warning categorization",
        "Detailed alert information with plant name, state, and values",
        "Coal stock table with operational capacity"
    ]
    for item in alert_dashboard:
        elements.append(Paragraph(f"• {item}", bullet_style))
    elements.append(Spacer(1, 0.15*inch))
    
    # 2.6 Regional Management
    elements.append(Paragraph("2.6 Regional/State Management", heading2_style))
    regional_mgmt = [
        "Plant count per state",
        "Generated energy",
        "Demand",
        "Energy status (surplus/deficit)",
        "Date-based filtering",
        "Regional grouping (Northern, Southern, Eastern, Western, North-Eastern)"
    ]
    for item in regional_mgmt:
        elements.append(Paragraph(f"• {item}", bullet_style))
    elements.append(Spacer(1, 0.15*inch))
    
    # 2.7 Database Administration
    elements.append(Paragraph("2.7 Database Administration", heading2_style))
    admin_features = [
        "<b>Daily Report Generation:</b> Generate comprehensive daily energy reports by date with state-wise aggregated metrics",
        "<b>Underperforming Plant Identification:</b> Configurable efficiency threshold and time window",
        "<b>Data Pipeline Trigger:</b> Manual trigger for complete ETL process with error handling"
    ]
    for feature in admin_features:
        elements.append(Paragraph(f"• {feature}", bullet_style))
    elements.append(Spacer(1, 0.2*inch))
    
    elements.append(PageBreak())
    
    # 3. Data Model
    elements.append(Paragraph("3. DATA MODEL", heading1_style))
    elements.append(Paragraph("3.1 Core Entities", heading2_style))
    
    entities = [
        "<b>POWERPLANTS:</b> Plant_ID, Plant_Name, State_Code, Sector_ID, Type_ID",
        "<b>STATE:</b> State_Code, State_Name, Region, Population",
        "<b>SECTOR:</b> Sector_ID, Sector_Name (State/Private/Central)",
        "<b>ENERGYTYPE:</b> Type_ID, Type_Name (Thermal, Hydro, Wind, Solar, Biomass, etc.), Description",
        "<b>PRODUCTIONLOG:</b> Plant_ID, Log_Date, Efficiency_Percentage, Todays_Actual_MU, Capable_Generation_MU, Operational_Capacity_MW, Coal_Stock_Days",
        "<b>OPERATIONAL_STATUS:</b> Plant_ID, Unit_Number, Status_Date, Cap_Under_Outage_MW, Status, Outage_Date, Expected_Sync_Date, Remarks",
        "<b>REGION_DETAILS:</b> State_Code, Report_Date, Generated_MU, Imported_MU, Surplus_MU, Demand_MU, Monitored_Capacity_MW, Grid_Frequency_HZ",
        "<b>DATE_DIM:</b> Date, Day, Month, Year"
    ]
    for entity in entities:
        elements.append(Paragraph(f"• {entity}", bullet_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # 4. Technical Architecture
    elements.append(Paragraph("4. TECHNICAL ARCHITECTURE", heading1_style))
    
    elements.append(Paragraph("4.1 Backend (Python/Flask)", heading2_style))
    backend_specs = [
        "<b>Framework:</b> Flask 3.0.0",
        "<b>Database:</b> MySQL with SQLAlchemy ORM",
        "<b>API Architecture:</b> RESTful APIs with Blueprint modularization",
        "<b>Routes:</b> /api/dashboard/*, /api/plants/*, /api/alerts/*, /api/analytics/*, /api/regions/*, /api/db-admin/*, /api/health"
    ]
    for spec in backend_specs:
        elements.append(Paragraph(f"• {spec}", bullet_style))
    elements.append(Spacer(1, 0.15*inch))
    
    elements.append(Paragraph("4.2 Frontend (React)", heading2_style))
    frontend_specs = [
        "<b>Framework:</b> React 18.3.1",
        "<b>Routing:</b> React Router DOM 7.9.5",
        "<b>Charts:</b> Recharts 3.3.0",
        "<b>HTTP Client:</b> Axios 1.13.2",
        "<b>UI Components:</b> Reusable Card components, Loading spinners, Alert banners, Data tables with pagination, Interactive charts, Navbar and Sidebar navigation"
    ]
    for spec in frontend_specs:
        elements.append(Paragraph(f"• {spec}", bullet_style))
    elements.append(Spacer(1, 0.15*inch))
    
    elements.append(Paragraph("4.3 Data Processing", heading2_style))
    data_processing = [
        "<b>Web Scraping:</b> Requests, PDFPlumber, Pandas",
        "<b>Data Sources:</b> GitHub repository for daily XLS reports, meritindia.in for renewable PDF reports",
        "<b>File Formats:</b> XLS, PDF, CSV",
        "<b>Output Folders:</b> Daily_Plant_Generation_XLS_Reports/, Daily_Renewable_PDF_Reports/, Processed_Renewable_XLSX_reports/"
    ]
    for item in data_processing:
        elements.append(Paragraph(f"• {item}", bullet_style))
    elements.append(Spacer(1, 0.2*inch))
    
    elements.append(PageBreak())
    
    # 5. User Interfaces
    elements.append(Paragraph("5. USER INTERFACES", heading1_style))
    
    elements.append(Paragraph("5.1 Pages", heading2_style))
    pages = [
        "<b>Dashboard</b> - Main overview with KPIs and charts",
        "<b>Plants</b> - Searchable, filterable plant listing",
        "<b>PlantDetails</b> - Detailed single plant view",
        "<b>Analytics</b> - Regional performance and renewable mix analysis",
        "<b>Alerts</b> - System alerts and critical warnings",
        "<b>Regions</b> - State-wise energy statistics",
        "<b>Companies</b> - Company/sector information",
        "<b>Admin</b> - Database administration tools"
    ]
    for page in pages:
        elements.append(Paragraph(f"• {page}", bullet_style))
    elements.append(Spacer(1, 0.15*inch))
    
    elements.append(Paragraph("5.2 Navigation", heading2_style))
    navigation = [
        "Fixed sidebar with page links",
        "Top navbar with branding",
        "Responsive design for desktop/tablet"
    ]
    for item in navigation:
        elements.append(Paragraph(f"• {item}", bullet_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # 6. Non-Functional Requirements
    elements.append(Paragraph("6. NON-FUNCTIONAL REQUIREMENTS", heading1_style))
    
    nfr_categories = [
        ("6.1 Performance", [
            "API response time <2 seconds for dashboard queries",
            "Support for pagination to handle large datasets",
            "Efficient database queries with proper indexing"
        ]),
        ("6.2 Reliability", [
            "Error handling for failed web scraping",
            "Graceful degradation when data is unavailable",
            "Retry mechanisms for API failures",
            "Data validation at input level"
        ]),
        ("6.3 Usability", [
            "Intuitive dashboard with visual KPIs",
            "Date picker for historical data viewing",
            "Search and filter capabilities",
            "Loading indicators during data fetch",
            "Error messages with retry options"
        ]),
        ("6.4 Maintainability", [
            "Modular code structure",
            "Separation of concerns (routes, services, models)",
            "Reusable React components",
            "Environment-based configuration",
            "Comprehensive error logging"
        ]),
        ("6.5 Security", [
            "CORS configuration for API access",
            "SQL injection prevention via parameterized queries",
            "Input validation and sanitization"
        ])
    ]
    
    for category, items in nfr_categories:
        elements.append(Paragraph(category, heading2_style))
        for item in items:
            elements.append(Paragraph(f"• {item}", bullet_style))
        elements.append(Spacer(1, 0.1*inch))
    
    elements.append(Spacer(1, 0.1*inch))
    
    # 7. System Constraints
    elements.append(Paragraph("7. SYSTEM CONSTRAINTS", heading1_style))
    constraints = [
        "MySQL database required",
        "Daily data updates from meritindia.in",
        "Internet connectivity for web scraping",
        "Storage for XLS/PDF report archives",
        "Python 3.x runtime environment",
        "Node.js for frontend development"
    ]
    for constraint in constraints:
        elements.append(Paragraph(f"• {constraint}", bullet_style))
    
    # Build PDF
    doc.build(elements)
    print(f"✅ PDF generated successfully: {filename}")
    return filename

if __name__ == "__main__":
    try:
        pdf_file = create_urs_pdf()
        print(f"\n📄 User Requirement Specification PDF has been created!")
        print(f"📁 Location: {pdf_file}")
    except Exception as e:
        print(f"❌ Error generating PDF: {e}")
        print("Make sure reportlab is installed: pip install reportlab")
