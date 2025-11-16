# Tableau Integration Guide

## Current Integration Approach

The pipeline outputs **CSV files** that Tableau can directly connect to. This is the simplest and most reliable integration method.

---

## Method 1: Direct CSV Connection (Recommended)

### Step-by-Step Integration

#### 1. Run Your Pipeline
```bash
python pipeline/run_full_pipeline.py \
    --bill bills/sample_bills/sb-743_0.pdf \
    --scenario my_analysis
```

This creates:
- `outputs/predictions/predicted_impact_my_analysis.csv`
- `outputs/equity_analysis/equity_analysis_my_analysis.csv`
- `outputs/summaries/summary_my_analysis.json`

#### 2. Connect Tableau to CSV

**In Tableau Desktop:**
1. Open Tableau Desktop
2. Click **"Connect to Data"** → **"Text file"**
3. Navigate to: `outputs/predictions/predicted_impact_my_analysis.csv`
4. Click **"Open"**
5. Click **"Sheet 1"** to start visualizing

#### 3. Verify Data Connection

You should see these columns:
- `institution_id` - Unique college identifier
- `state` - State name (for geographic mapping)
- `institution_type` - Public Four-Year, Public Two-Year, etc.
- `tuition_change_pct` - Percentage change in tuition
- `tuition_change_dollars` - Dollar impact (use for color/size)
- `enrollment_change_pct` - Enrollment change percentage
- `students_affected` - Number of students impacted
- `grad_rate_change` - Graduation rate change
- `equity_risk_class` - Low/Medium/High (use for color)
- `hours_to_cover_gap` - Hours of work needed
- `net_price` - Current net price

---

## Method 2: Tableau Data Extract (.hyper) - Advanced

For better performance with large datasets, you can create Tableau data extracts.

### Option A: Manual Extract Creation

1. **Connect to CSV** (as in Method 1)
2. **Create Extract:**
   - Data → Extract Data
   - Choose extract location
   - Click **"Extract"**
3. **Use Extract:**
   - Tableau will use the `.hyper` file instead of CSV
   - Faster performance for large datasets
   - Can schedule refreshes

### Option B: Automated Extract (Python Script)

Create a script to generate extracts programmatically:

```python
# scripts/create_tableau_extract.py
from tableauhyperapi import HyperProcess, Connection, TableDefinition, SqlType, \
    TableName, CreateMode, Telemetry, Inserter
import pandas as pd
from pathlib import Path

def create_hyper_extract(csv_path, hyper_path):
    """Convert CSV to Tableau .hyper extract."""
    # Read CSV
    df = pd.read_csv(csv_path)
    
    # Create hyper extract
    with HyperProcess(telemetry=Telemetry.SEND_USAGE_DATA_TO_TABLEAU) as hyper:
        with Connection(hyper.endpoint, hyper_path, CreateMode.CREATE_AND_REPLACE) as connection:
            # Define table schema
            table_definition = TableDefinition(
                table_name=TableName("Extract", "Predictions"),
                columns=[
                    TableDefinition.Column("institution_id", SqlType.big_int()),
                    TableDefinition.Column("state", SqlType.text()),
                    TableDefinition.Column("institution_type", SqlType.text()),
                    TableDefinition.Column("tuition_change_dollars", SqlType.double()),
                    # Add all columns...
                ]
            )
            
            # Create table and insert data
            connection.catalog.create_table(table_definition)
            with Inserter(connection, table_definition) as inserter:
                for _, row in df.iterrows():
                    inserter.add_row(row.values)
                inserter.execute()
    
    print(f"Created Tableau extract: {hyper_path}")

if __name__ == "__main__":
    csv_path = "outputs/predictions/predicted_impact_test.csv"
    hyper_path = "tableau/extracts/predictions_test.hyper"
    create_hyper_extract(csv_path, hyper_path)
```

**Note:** Requires `tableauhyperapi` package:
```bash
pip install tableauhyperapi
```

---

## Method 3: Tableau Server/Online API (Enterprise)

For automated publishing to Tableau Server/Online:

### Setup

1. **Install Tableau Server Client:**
   ```bash
   pip install tableauserverclient
   ```

2. **Create Publishing Script:**
   ```python
   # scripts/publish_to_tableau.py
   import tableauserverclient as TSC
   from pathlib import Path
   
   def publish_to_tableau(csv_path, server_url, site_name, username, password):
       """Publish CSV as data source to Tableau Server."""
       
       # Authenticate
       tableau_auth = TSC.TableauAuth(username, password, site_name)
       server = TSC.Server(server_url, use_server_version=True)
       
       with server.auth.sign_in(tableau_auth):
           # Create data source
           datasource = TSC.DatasourceItem(project_id="your_project_id")
           datasource = server.datasources.publish(
               datasource,
               csv_path,
               TSC.Server.PublishMode.Overwrite
           )
           
           print(f"Published datasource: {datasource.id}")
   
   if __name__ == "__main__":
       publish_to_tableau(
           csv_path="outputs/predictions/predicted_impact_test.csv",
           server_url="https://your-tableau-server.com",
           site_name="your_site",
           username="your_username",
           password="your_password"
       )
   ```

---

## Method 4: Live Connection with Database (Advanced)

If you want real-time updates, connect Tableau to a database:

### Setup PostgreSQL/MySQL

1. **Create database table:**
   ```sql
   CREATE TABLE predictions (
       institution_id BIGINT,
       state VARCHAR(50),
       institution_type VARCHAR(50),
       tuition_change_dollars DECIMAL(10,2),
       -- ... other columns
   );
   ```

2. **Export from pipeline to database:**
   ```python
   # Add to pipeline/export_for_tableau.py
   import sqlalchemy
   
   def export_to_database(df, connection_string):
       """Export predictions to database."""
       engine = sqlalchemy.create_engine(connection_string)
       df.to_sql('predictions', engine, if_exists='replace', index=False)
   ```

3. **Connect Tableau to database:**
   - Data → Connect → PostgreSQL/MySQL
   - Enter connection details
   - Select `predictions` table

---

## Recommended Workflow

### For Development/Demo:

**Use Method 1 (Direct CSV):**
- Simplest setup
- No additional infrastructure
- Easy to share workbooks
- Works with Tableau Desktop and Tableau Public

### For Production:

**Use Method 2 (Data Extracts):**
- Better performance
- Can schedule refreshes
- Smaller file sizes
- Still easy to share

### For Enterprise:

**Use Method 3 (Tableau Server):**
- Centralized data sources
- Automated publishing
- Version control
- Access management

---

## Enhancing Pipeline Output for Tableau

### Add Calculated Fields to CSV

Modify `pipeline/export_for_tableau.py` to include pre-calculated fields:

```python
# Add to export_predicted_impact function
def export_predicted_impact(...):
    # ... existing code ...
    
    # Add Tableau-friendly calculated fields
    export_df["impact_severity"] = pd.cut(
        export_df["tuition_change_dollars"],
        bins=[-float('inf'), -1000, 0, 1000, float('inf')],
        labels=["Severe Negative", "Moderate Negative", "Positive", "Severe Positive"]
    )
    
    export_df["risk_color"] = export_df["equity_risk_class"].map({
        "High": "#FF0000",
        "Medium": "#FFA500",
        "Low": "#00FF00"
    })
    
    export_df["formatted_tuition_change"] = export_df["tuition_change_dollars"].apply(
        lambda x: f"${x:,.0f}"
    )
    
    # ... rest of export code ...
```

### Add Geographic Data

If you want better mapping, add latitude/longitude:

```python
# Add state coordinates for better mapping
state_coords = {
    "Alabama": (32.806671, -86.791130),
    "Alaska": (61.370716, -152.404419),
    # ... etc
}

export_df["state_lat"] = export_df["state"].map(lambda x: state_coords.get(x, (0, 0))[0])
export_df["state_lon"] = export_df["state"].map(lambda x: state_coords.get(x, (0, 0))[1])
```

---

## Automated Integration Script

Create a script that runs pipeline and prepares Tableau files:

```python
# scripts/run_and_prepare_tableau.py
import subprocess
import sys
from pathlib import Path

def run_pipeline_and_prepare_tableau(bill_path, scenario_name):
    """Run pipeline and prepare files for Tableau."""
    
    # 1. Run pipeline
    print(f"Running pipeline for {scenario_name}...")
    subprocess.run([
        "python", "pipeline/run_full_pipeline.py",
        "--bill", bill_path,
        "--scenario", scenario_name,
        "--run-analysis"
    ], check=True)
    
    # 2. Verify outputs
    csv_path = f"outputs/predictions/predicted_impact_{scenario_name}.csv"
    if not Path(csv_path).exists():
        raise FileNotFoundError(f"Output file not found: {csv_path}")
    
    # 3. Copy to Tableau folder (optional)
    tableau_dir = Path("tableau/data_sources")
    tableau_dir.mkdir(parents=True, exist_ok=True)
    
    import shutil
    shutil.copy(csv_path, tableau_dir / f"predictions_{scenario_name}.csv")
    
    print(f"\n✓ Pipeline complete!")
    print(f"✓ CSV ready for Tableau: {tableau_dir / f'predictions_{scenario_name}.csv'}")
    print(f"\nTo connect in Tableau:")
    print(f"  1. Open Tableau Desktop")
    print(f"  2. Connect → Text file")
    print(f"  3. Select: {tableau_dir / f'predictions_{scenario_name}.csv'}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python run_and_prepare_tableau.py <bill_path> <scenario_name>")
        sys.exit(1)
    
    run_pipeline_and_prepare_tableau(sys.argv[1], sys.argv[2])
```

---

## Tableau Dashboard Templates

### Template 1: Impact Map Dashboard

**Structure:**
```
Dashboard: "Education Policy Impact Analysis"

┌─────────────────────────────────────────┐
│ Filters: [State] [Institution Type]     │
├─────────────────────────────────────────┤
│ ┌─────────────────┐ ┌────────────────┐│
│ │ Geographic Map  │ │ Top 10 Colleges ││
│ │ (State-level)   │ │ (Bar Chart)    ││
│ └─────────────────┘ └────────────────┘│
│ ┌─────────────────────────────────────┐│
│ │ Equity Scorecard (Scatter Plot)     ││
│ └─────────────────────────────────────┘│
│ ┌──────────┐ ┌──────────┐ ┌──────────┐│
│ │ Total    │ │ Avg      │ │ High Risk││
│ │ Colleges │ │ Impact $ │ │ Count    ││
│ └──────────┘ └──────────┘ └──────────┘│
└─────────────────────────────────────────┘
```

**Key Visualizations:**
1. **Filled Map:** States colored by average `tuition_change_dollars`
2. **Bar Chart:** Top 10 colleges by `tuition_change_dollars`
3. **Scatter Plot:** X=`tuition_change_dollars`, Y=`students_affected`, Color=`equity_risk_class`
4. **KPI Cards:** Aggregated metrics

### Template 2: College Detail Dashboard

**Structure:**
```
Dashboard: "College Impact Details"

┌─────────────────────────────────────────┐
│ Parameter: [Select College]              │
├─────────────────────────────────────────┤
│ ┌──────────┐ ┌──────────┐ ┌──────────┐│
│ │ Tuition  │ │ Students │ │ Hours to ││
│ │ Change $ │ │ Affected │ │ Cover    ││
│ └──────────┘ └──────────┘ └──────────┘│
│ ┌─────────────────────────────────────┐│
│ │ Impact Metrics (Bar Chart)          ││
│ └─────────────────────────────────────┘│
│ ┌─────────────────────────────────────┐│
│ │ Plain Language Summary (Text)        ││
│ └─────────────────────────────────────┘│
└─────────────────────────────────────────┘
```

---

## Best Practices

### 1. Data Refresh Strategy

**Option A: Manual Refresh**
- Run pipeline when new bill arrives
- Reconnect Tableau to updated CSV
- Refresh data source in Tableau

**Option B: Scheduled Refresh**
- Set up cron job / scheduled task to run pipeline
- Use Tableau Server/Online for automatic refresh
- Or use data extracts with scheduled updates

### 2. File Organization

```
tableau/
├── data_sources/          # CSV files for Tableau
│   ├── predictions_test.csv
│   └── predictions_funding_cut.csv
├── extracts/              # .hyper files (optional)
│   └── predictions_test.hyper
└── dashboards/            # .twbx workbook files
    ├── impact_map.twbx
    └── equity_scorecard.twbx
```

### 3. Naming Conventions

- **CSV files:** `predictions_<scenario>_<date>.csv`
- **Workbooks:** `<dashboard_name>_<version>.twbx`
- **Data sources:** Descriptive names matching scenarios

### 4. Performance Optimization

- **Use data extracts** for datasets > 1M rows
- **Aggregate data** at state level for overview dashboards
- **Filter early** - add filters before detailed views
- **Limit marks** - use sampling for very large datasets

---

## Quick Start Checklist

- [ ] Run pipeline to generate CSV outputs
- [ ] Open Tableau Desktop
- [ ] Connect to `outputs/predictions/predicted_impact_<scenario>.csv`
- [ ] Verify all columns are loaded correctly
- [ ] Set `State` as geographic field
- [ ] Create first visualization (map or bar chart)
- [ ] Add filters for interactivity
- [ ] Build dashboard with multiple views
- [ ] Save workbook to `tableau/dashboards/`
- [ ] (Optional) Publish to Tableau Server/Public

---

## Troubleshooting

### Issue: "State not recognized as geographic"
**Solution:** Right-click `State` column → Geographic Role → State

### Issue: "CSV file too large"
**Solution:** 
- Use data extract instead
- Filter data before connecting
- Aggregate at state level

### Issue: "Missing columns in Tableau"
**Solution:** 
- Check CSV file has headers
- Verify column names don't have special characters
- Re-export from pipeline if needed

### Issue: "Performance is slow"
**Solution:**
- Create data extract (.hyper file)
- Filter data before loading
- Use aggregated views for overview

---

## Next Steps

1. **Start Simple:** Connect to CSV and create basic visualizations
2. **Build Dashboards:** Create the 3 recommended dashboard templates
3. **Optimize:** Create data extracts for better performance
4. **Automate:** Set up scripts for automated pipeline → Tableau workflow
5. **Publish:** Share dashboards via Tableau Server/Public

For detailed visualization instructions, see `TABLEAU_CONNECTION_GUIDE.md`.

