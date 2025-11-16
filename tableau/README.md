# Tableau Integration Guide

This directory contains all files needed for Tableau visualization integration.

## Directory Structure

```
tableau/
├── data_sources/          # Auto-updated CSV files (DO NOT EDIT MANUALLY)
│   ├── current_predictions.csv
│   ├── current_equity_analysis.csv
│   └── current_summary.json
└── dashboards/            # Your Tableau workbooks (build these)
    ├── geographic_impact.twbx
    ├── advanced_metrics.twbx
    └── college_detail.twbx
```

## Quick Start

### Step 1: Run the Pipeline

The pipeline automatically generates and updates CSV files in `data_sources/`:

```bash
python pipeline/run_full_pipeline.py --bill bills/sample_bills/your_bill.pdf --scenario demo
```

This creates:
- `current_predictions.csv` - Main predictions with all columns (name, latitude, longitude, etc.)
- `current_equity_analysis.csv` - Equity breakdown by risk class
- `current_summary.json` - Summary statistics and plain language summary

### Step 2: Build Dashboards in Tableau Desktop

1. **Open Tableau Desktop**
2. **Connect to Data:**
   - Connect → Text File
   - Navigate to: `tableau/data_sources/current_predictions.csv`
   - Click "Open"

3. **Build Your Dashboards:**
   - See detailed instructions below for each dashboard
   - Save workbooks to `tableau/dashboards/`

4. **Refresh Data:**
   - After running pipeline with new data
   - In Tableau: Data → Refresh All Extracts (or press F5)
   - Dashboards update automatically

## Dashboard Building Guide

### Dashboard 1: Geographic Impact Heatmap

**Purpose:** Show policy impact by state on a map

**Steps:**
1. Connect to `current_predictions.csv`
2. Create a **Filled Map** visualization:
   - Drag `State` to "Marks" → Geographic Role → State
   - Drag `tuition_change_dollars` to Color
   - Change aggregation to Average
   - Format color: Diverging color scheme (red for negative, green for positive)
3. Add **KPI Cards** at top:
   - Total Colleges: COUNT(`institution_id`)
   - Total Students: SUM(`students_affected`)
   - Avg Tuition Change: AVG(`tuition_change_dollars`)
4. Add **Filters:**
   - `institution_type` (dropdown)
   - `equity_risk_class` (dropdown)
5. Add **Tooltip:**
   - State name
   - Number of colleges affected
   - Average tuition change
6. Save as: `tableau/dashboards/geographic_impact.twbx`

### Dashboard 2: Advanced Metrics Dashboard

**Purpose:** Show detailed metrics, equity analysis, and demographic breakdowns

**Steps:**
1. Connect to `current_predictions.csv`
2. Create **KPI Cards** (top row):
   - Total Colleges: COUNT(`institution_id`)
   - Total Students: SUM(`students_affected`)
   - Avg Tuition Change: AVG(`tuition_change_dollars`)
   - High-Risk Colleges: COUNT where `equity_risk_class` = "High"
3. Create **Scatter Plot:**
   - X-axis: `pct_low_income` (or `net_price` if demographics not available)
   - Y-axis: `tuition_change_dollars`
   - Color: `equity_risk_class`
   - Size: `students_affected`
   - Tooltip: College name, demographics, impact metrics
4. Create **Bar Charts:**
   - Chart 1: Impact by Low-Income %
     - X: `pct_low_income` (create bins: 0-25%, 25-50%, 50-75%, 75-100%)
     - Y: AVG(`tuition_change_dollars`)
   - Chart 2: Impact by Minority %
     - X: `pct_minority` (create bins: 0-25%, 25-50%, 50-75%, 75-100%)
     - Y: AVG(`tuition_change_dollars`)
5. Create **Table:**
   - Top 10 Most Affected Colleges
   - Columns: `name`, `state`, `tuition_change_dollars`, `students_affected`, `equity_risk_class`
   - Sort by: `tuition_change_dollars` (descending)
6. Add **Filters:** State, Institution Type, Equity Risk Class
7. Save as: `tableau/dashboards/advanced_metrics.twbx`

### Dashboard 3: College Detail View

**Purpose:** Show detailed impact for a single selected college

**Steps:**
1. Connect to `current_predictions.csv`
2. Create **Parameter:**
   - Name: "Selected College"
   - Data type: String
   - Allowable values: List → All values from `name` column
3. Create **KPI Cards:**
   - Tuition Change ($): `tuition_change_dollars` (filtered by parameter)
   - Students Affected: `students_affected` (filtered by parameter)
   - Hours to Cover Gap: `hours_to_cover_gap` (filtered by parameter)
   - Enrollment Change (%): `enrollment_change_pct` (filtered by parameter)
4. Add **Text Summary:**
   - Create calculated field or use summary from JSON
   - Display plain language impact description
5. Create **Before/After Comparison:**
   - Bar chart showing:
     - Baseline Net Price: `net_price - tuition_change_dollars`
     - Predicted Net Price: `net_price`
     - Baseline Grad Rate: `grad_rate - grad_rate_change`
     - Predicted Grad Rate: `grad_rate`
6. Create **Demographics Breakdown:**
   - Pie chart or bar chart:
     - Low-income percentage
     - Minority percentage
     - Institution type
7. Save as: `tableau/dashboards/college_detail.twbx`

## Available Columns in CSV

The `current_predictions.csv` includes:

**Identifiers:**
- `institution_id` - Unique college ID
- `name` - College name
- `state` - State name
- `institution_type` - Type (Public Four-Year, Community College, etc.)

**Geographic:**
- `latitude` - Latitude coordinate
- `longitude` - Longitude coordinate

**Predictions:**
- `tuition_change_pct` - Percentage change in tuition
- `tuition_change_dollars` - Dollar change in tuition
- `enrollment_change_pct` - Percentage change in enrollment
- `students_affected` - Number of students affected
- `grad_rate_change` - Change in graduation rate
- `equity_risk_class` - Risk level (Low/Medium/High)
- `hours_to_cover_gap` - Hours needed to cover affordability gap

**Demographics (if available):**
- `pct_low_income` - Percentage of low-income students
- `pct_minority` - Percentage of minority students
- `total_enrollment` - Total enrollment
- `net_price` - Net price
- `grad_rate` - Graduation rate

## Testing Your Dashboards

1. **Run pipeline with test data:**
   ```bash
   python pipeline/run_full_pipeline.py --bill bills/sample_bills/sb-743_0.pdf --scenario test
   ```

2. **Open Tableau Desktop:**
   - Open your dashboard workbook
   - Refresh data source (F5 or Data → Refresh)

3. **Verify:**
   - Map displays correctly (if using geographic dashboard)
   - All visualizations show data
   - Filters work
   - Tooltips display correct information

4. **Test with new data:**
   - Run pipeline with different bill
   - Refresh Tableau
   - Verify dashboards update

## Publishing to Tableau Public (Optional)

To embed dashboards in the Streamlit frontend:

1. **Publish to Tableau Public:**
   - In Tableau Desktop: Server → Tableau Public → Save to Tableau Public
   - Or: File → Save to Tableau Public
   - Sign in with free Tableau Public account
   - Publish all 3 dashboards

2. **Get Embed URLs:**
   - Go to your Tableau Public profile
   - Click on each dashboard
   - Click "Share" button
   - Copy the embed URL (format: `https://public.tableau.com/views/DashboardName/Sheet1`)

3. **Add URLs to Streamlit:**
   - Edit `tableau_integration/web_interface.py`
   - Update `TABLEAU_DASHBOARDS` dictionary with your URLs:
     ```python
     TABLEAU_DASHBOARDS = {
         "geographic": "https://public.tableau.com/views/YourDashboard/Sheet1",
         "metrics": "https://public.tableau.com/views/YourDashboard/Sheet1",
         "detail": "https://public.tableau.com/views/YourDashboard/Sheet1"
     }
     ```

4. **View in Streamlit:**
   - Run: `streamlit run tableau_integration/web_interface.py`
   - Upload PDF and run pipeline
   - Dashboards will appear embedded below the results

## Troubleshooting

**Problem: Dashboard shows no data**
- Check that `current_predictions.csv` exists in `data_sources/`
- Verify CSV has data (open in Excel/text editor)
- Refresh data source in Tableau (F5)

**Problem: Missing columns**
- Run pipeline again to regenerate CSV
- Check that pipeline completed successfully
- Verify `pipeline/export_for_tableau.py` includes all columns

**Problem: Map not displaying**
- Verify `state` column has valid state names
- Check that `latitude` and `longitude` columns exist
- Try using geographic role: Right-click `state` → Geographic Role → State

**Problem: Embedding not working**
- Verify Tableau Public URLs are correct
- Check that dashboards are published and public
- Ensure URLs are in correct format (no extra parameters)

## Next Steps

1. ✅ Build all 3 dashboards
2. ✅ Test with sample data
3. ✅ Publish to Tableau Public (optional)
4. ✅ Add URLs to Streamlit (optional)
5. ✅ Demo your complete workflow!

