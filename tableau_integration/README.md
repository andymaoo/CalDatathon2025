# Tableau Auto-Integration

Two methods to automatically run the pipeline when PDFs are uploaded and connect outputs to Tableau.

## Method 1: Folder Watcher (Recommended for Demo)

Automatically processes PDFs when dropped into a folder.

### Setup

1. **Install watchdog:**
   ```bash
   pip install watchdog
   ```

2. **Start the watcher:**
   ```bash
   python tableau_integration/tableau_auto_pipeline.py
   ```

3. **Drop PDFs in the watch folder:**
   - Default: `tableau_integration/upload/`
   - Just drag and drop your PDF file here
   - Pipeline runs automatically!

4. **Connect Tableau:**
   - Open Tableau Desktop
   - Connect → Text file
   - Navigate to: `tableau/data_sources/current_predictions.csv`
   - This file is automatically updated when new PDFs are processed

### How It Works

1. PDF dropped in `tableau_integration/upload/`
2. Watcher detects new PDF
3. Pipeline runs automatically
4. Outputs copied to `tableau/data_sources/` with fixed names:
   - `current_predictions.csv` (always the latest)
   - `current_equity_analysis.csv`
   - `current_summary.json`
5. Tableau can connect to these files (auto-refresh or manual refresh)

### Customize Watch Directory

```bash
python tableau_integration/tableau_auto_pipeline.py \
    --watch-dir path/to/your/folder \
    --tableau-dir path/to/tableau/data
```

---

## Method 2: Web Interface (User-Friendly)

Web-based interface for uploading PDFs and running the pipeline.

### Setup

1. **Install Streamlit:**
   ```bash
   pip install streamlit
   ```

2. **Run the web interface:**
   ```bash
   streamlit run tableau_integration/web_interface.py
   ```

3. **Open in browser:**
   - Interface opens at `http://localhost:8501`
   - Upload PDF through the web interface
   - Click "Run Pipeline"
   - Results appear in the interface

4. **Connect Tableau:**
   - Same as Method 1: Connect to `tableau/data_sources/current_predictions.csv`

### Features

- Drag-and-drop PDF upload
- Real-time processing status
- Results summary display
- Plain language summary
- Quick stats dashboard
- Automatic file copying to Tableau directory

---

## Tableau Connection

### Step 1: Connect to Fixed Output File

1. Open Tableau Desktop
2. **Connect → Text file**
3. Navigate to: `tableau/data_sources/current_predictions.csv`
4. Click **"Open"**

### Step 2: Set Up Auto-Refresh (Optional)

**Option A: Manual Refresh**
- Data → Refresh (or F5)
- Refresh whenever you process a new PDF

**Option B: Scheduled Refresh (Tableau Server)**
- If using Tableau Server/Online
- Set up scheduled refresh
- Or use web data connector

**Option C: Extract Refresh**
- Create data extract (.hyper file)
- Set up extract refresh schedule
- Extract updates automatically

### Step 3: Build Your Dashboard

The CSV has these columns ready for visualization:
- `institution_id`, `state`, `institution_type`
- `tuition_change_pct`, `tuition_change_dollars`
- `enrollment_change_pct`, `students_affected`
- `grad_rate_change`, `equity_risk_class`
- `hours_to_cover_gap`, `net_price`

---

## Workflow Examples

### Example 1: Quick Demo

1. Start watcher: `python tableau_integration/tableau_auto_pipeline.py`
2. Drop PDF in `tableau_integration/upload/`
3. Wait for processing (watch console)
4. Open Tableau → Connect to `current_predictions.csv`
5. Build visualization

### Example 2: Web Interface

1. Start web interface: `streamlit run tableau_integration/web_interface.py`
2. Open browser to `http://localhost:8501`
3. Upload PDF through interface
4. Click "Run Pipeline"
5. View results in web interface
6. Connect Tableau to `current_predictions.csv`

### Example 3: Multiple PDFs

1. Process multiple PDFs (each gets unique scenario name)
2. All outputs saved with timestamps
3. Latest always copied to `current_predictions.csv`
4. Tableau always shows most recent analysis

---

## File Structure

```
tableau_integration/
├── tableau_auto_pipeline.py    # Folder watcher script
├── web_interface.py             # Streamlit web interface
└── upload/                      # Drop PDFs here (watcher mode)

tableau/
└── data_sources/                # Tableau connects here
    ├── current_predictions.csv  # ← Connect Tableau to this
    ├── current_equity_analysis.csv
    ├── current_summary.json
    └── pipeline_status.json     # Status of last run
```

---

## Troubleshooting

### Issue: "Watcher not detecting files"
**Solution:**
- Make sure PDF is fully copied (not still copying)
- Check file permissions
- Try restarting the watcher

### Issue: "Tableau shows old data"
**Solution:**
- Refresh data source in Tableau (F5)
- Or reconnect to the CSV file
- Check `pipeline_status.json` for last run time

### Issue: "Web interface not starting"
**Solution:**
- Make sure Streamlit is installed: `pip install streamlit`
- Check port 8501 is available
- Try different port: `streamlit run web_interface.py --server.port 8502`

### Issue: "Pipeline fails in watcher"
**Solution:**
- Check console output for error messages
- Verify models are trained
- Check PDF file is valid (not corrupted)

---

## Advanced: Tableau Server Integration

For enterprise setups, you can publish the data source to Tableau Server:

```python
# After pipeline runs, publish to Tableau Server
import tableauserverclient as TSC

server = TSC.Server('https://your-server.com')
server.auth.sign_in(TSC.TableauAuth('username', 'password'))

datasource = TSC.DatasourceItem(project_id='project_id')
datasource = server.datasources.publish(
    datasource,
    'tableau/data_sources/current_predictions.csv',
    TSC.Server.PublishMode.Overwrite
)
```

---

## Quick Start Commands

### Method 1 (Folder Watcher):
```bash
# Terminal 1: Start watcher
python tableau_integration/tableau_auto_pipeline.py

# Terminal 2: Drop PDF in tableau_integration/upload/
# (or use file explorer)

# Tableau: Connect to tableau/data_sources/current_predictions.csv
```

### Method 2 (Web Interface):
```bash
# Start web interface
streamlit run tableau_integration/web_interface.py

# Open browser to http://localhost:8501
# Upload PDF and run pipeline

# Tableau: Connect to tableau/data_sources/current_predictions.csv
```

---

## Status File

The watcher creates `pipeline_status.json` with:
```json
{
  "scenario": "bill_20240101_120000",
  "pdf_name": "education_bill.pdf",
  "status": "success",
  "timestamp": "2024-01-01T12:00:00",
  "error": null
}
```

Tableau can read this file to show processing status or trigger refreshes.

