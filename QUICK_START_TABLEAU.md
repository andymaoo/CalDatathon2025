# Quick Start: Tableau Auto-Integration

## Two Ways to Automatically Run Pipeline with Tableau

### Method 1: Folder Watcher (Easiest for Demo)

**How it works:** Drop PDFs in a folder, pipeline runs automatically, Tableau connects to fixed output file.

#### Setup:

1. **Install dependencies:**
   ```bash
   pip install watchdog
   ```

2. **Start the watcher:**
   ```bash
   # Windows
   tableau_integration\start_auto_pipeline.bat
   
   # Or directly:
   python tableau_integration/tableau_auto_pipeline.py
   ```

3. **Drop a PDF:**
   - Drag and drop your PDF into: `tableau_integration/upload/`
   - The pipeline runs automatically!
   - Watch the console for progress

4. **Connect Tableau:**
   - Open Tableau Desktop
   - Connect → Text file
   - Navigate to: `tableau/data_sources/current_predictions.csv`
   - This file is automatically updated with the latest results

#### That's it! 
- Every time you drop a new PDF, it processes automatically
- Tableau always shows the latest results in `current_predictions.csv`

---

### Method 2: Web Interface (Most User-Friendly)

**How it works:** Web interface where you upload PDFs, see results, and Tableau connects to the same output file.

#### Setup:

1. **Install Streamlit:**
   ```bash
   pip install streamlit
   ```

2. **Start the web interface:**
   ```bash
   # Windows
   tableau_integration\start_web_interface.bat
   
   # Or directly:
   streamlit run tableau_integration/web_interface.py
   ```

3. **Use the interface:**
   - Browser opens at `http://localhost:8501`
   - Upload PDF through the web interface
   - Click "Run Pipeline"
   - See results summary in the browser

4. **Connect Tableau:**
   - Same as Method 1: Connect to `tableau/data_sources/current_predictions.csv`

---

## Complete Workflow Example

### Using Folder Watcher:

```bash
# Terminal 1: Start watcher
python tableau_integration/tableau_auto_pipeline.py

# File Explorer: Drag PDF to tableau_integration/upload/
# (or copy/paste the PDF file)

# Tableau Desktop:
# 1. Connect → Text file
# 2. Select: tableau/data_sources/current_predictions.csv
# 3. Build your dashboard
# 4. Refresh (F5) when you process a new PDF
```

### Using Web Interface:

```bash
# Terminal: Start web interface
streamlit run tableau_integration/web_interface.py

# Browser:
# 1. Go to http://localhost:8501
# 2. Upload PDF
# 3. Click "Run Pipeline"
# 4. View results

# Tableau Desktop:
# 1. Connect → Text file
# 2. Select: tableau/data_sources/current_predictions.csv
# 3. Build your dashboard
```

---

## Key Features

✅ **Automatic Processing:** PDFs are processed as soon as they're uploaded  
✅ **Fixed Output Location:** Tableau always connects to the same file  
✅ **Latest Results:** New PDFs automatically update the output  
✅ **Status Tracking:** Check `pipeline_status.json` for last run info  
✅ **Multiple Outputs:** Predictions, equity analysis, and summary all available  

---

## File Locations

**Upload PDFs here:**
- `tableau_integration/upload/` (for folder watcher)

**Tableau connects here:**
- `tableau/data_sources/current_predictions.csv` ← **Main file for Tableau**
- `tableau/data_sources/current_equity_analysis.csv`
- `tableau/data_sources/current_summary.json`
- `tableau/data_sources/pipeline_status.json` (status info)

---

## Troubleshooting

**Watcher not detecting files?**
- Make sure PDF is fully copied (wait a second after dropping)
- Check the console for error messages
- Try restarting the watcher

**Tableau shows old data?**
- Press F5 in Tableau to refresh
- Or reconnect to the CSV file
- Check `pipeline_status.json` for last run timestamp

**Web interface not starting?**
- Install Streamlit: `pip install streamlit`
- Check if port 8501 is available
- Try: `streamlit run tableau_integration/web_interface.py --server.port 8502`

---

## Next Steps

1. **Choose your method** (folder watcher or web interface)
2. **Start the service** (run the script)
3. **Upload a PDF** (drop in folder or use web interface)
4. **Connect Tableau** to `tableau/data_sources/current_predictions.csv`
5. **Build your dashboard!**

For detailed instructions, see `tableau_integration/README.md`.

