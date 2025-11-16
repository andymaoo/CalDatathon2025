"""Quick verification script to check Tableau setup."""
import json
from pathlib import Path

print("=" * 60)
print("Tableau Integration Setup Verification")
print("=" * 60)

# Check files
data_dir = Path("data_sources")
files = {
    "current_predictions.csv": "Main predictions data",
    "current_equity_analysis.csv": "Equity analysis breakdown",
    "current_summary.json": "Summary statistics"
}

print("\nFiles Status:")
all_exist = True
for filename, description in files.items():
    filepath = data_dir / filename
    exists = filepath.exists()
    status = "OK" if exists else "MISSING"
    print(f"  {status} {filename} - {description}")
    if not exists:
        all_exist = False

# Check CSV columns
if (data_dir / "current_predictions.csv").exists():
    import pandas as pd
    df = pd.read_csv(data_dir / "current_predictions.csv", nrows=1)
    print("\nCSV Columns Check:")
    required = ['name', 'latitude', 'longitude', 'state', 'tuition_change_dollars', 
                'students_affected', 'equity_risk_class', 'institution_id']
    missing = [c for c in required if c not in df.columns]
    if missing:
        print(f"  MISSING columns: {missing}")
    else:
        print(f"  OK - All required columns present ({len(df.columns)} total columns)")

# Check summary
if (data_dir / "current_summary.json").exists():
    with open(data_dir / "current_summary.json") as f:
        summary = json.load(f)
    print("\nSummary Statistics:")
    print(f"  Colleges affected: {summary.get('total_colleges_affected', 0):,}")
    print(f"  Students impacted: {summary.get('total_students_impacted', 0):,}")
    print(f"  Avg tuition change: ${summary.get('average_tuition_change_dollars', 0):,.0f}")

# Check dashboards directory
dashboards_dir = Path("dashboards")
print("\nDashboards Directory:")
if dashboards_dir.exists():
    twbx_files = list(dashboards_dir.glob("*.twbx"))
    if twbx_files:
        print(f"  OK - Found {len(twbx_files)} dashboard(s):")
        for f in twbx_files:
            print(f"     - {f.name}")
    else:
        print("  WARNING - No .twbx files found (dashboards not built yet)")
        print("     See README.md for building instructions")
else:
    print("  WARNING - Dashboards directory not found")

print("\n" + "=" * 60)
if all_exist:
    print("OK - Setup complete! Ready to build Tableau dashboards.")
    print("   See tableau/README.md for dashboard building instructions.")
else:
    print("WARNING - Some files are missing. Run the pipeline first:")
    print("   python pipeline/run_full_pipeline.py --bill <pdf> --scenario <name>")
print("=" * 60)

