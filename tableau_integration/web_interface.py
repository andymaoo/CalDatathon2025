"""
Web Interface for Tableau Integration

Simple web interface that allows users to upload PDFs and automatically run the pipeline.
Outputs are saved to a location Tableau can connect to.
"""

import streamlit as st
import sys
from pathlib import Path
import subprocess
import shutil
import json
from datetime import datetime
import pandas as pd

# No direct imports needed - using subprocess

st.set_page_config(
    page_title="Education Policy Impact Pipeline",
    page_icon="📊",
    layout="wide"
)

# Configuration
TABLEAU_DIR = Path(__file__).parent.parent / "tableau" / "data_sources"
TABLEAU_DIR.mkdir(parents=True, exist_ok=True)

# Tableau Public dashboard URLs (set these after publishing to Tableau Public)
TABLEAU_DASHBOARDS = {
    "geographic": None,  # Set to: "https://public.tableau.com/views/GeographicImpact/Sheet1"
    "metrics": None,    # Set to: "https://public.tableau.com/views/AdvancedMetrics/Sheet1"
    "detail": None      # Set to: "https://public.tableau.com/views/CollegeDetail/Sheet1"
}


def run_pipeline(pdf_file, scenario_name):
    """Run the pipeline on uploaded PDF."""
    # Save uploaded file temporarily
    temp_dir = Path("tableau_integration/temp")
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    temp_pdf = temp_dir / pdf_file.name
    with open(temp_pdf, "wb") as f:
        f.write(pdf_file.getbuffer())
    
    try:
        # Run pipeline using the same Python interpreter (venv)
        cmd = [
            sys.executable, "pipeline/run_full_pipeline.py",
            "--bill", str(temp_pdf),
            "--scenario", scenario_name
        ]
        
        result = subprocess.run(
            cmd,
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            return False, result.stderr
        
        # Copy outputs to Tableau directory
        source_files = {
            "predictions": f"outputs/predictions/predicted_impact_{scenario_name}.csv",
            "equity": f"outputs/equity_analysis/equity_analysis_{scenario_name}.csv",
            "summary": f"outputs/summaries/summary_{scenario_name}.json"
        }
        
        target_files = {
            "predictions": TABLEAU_DIR / "current_predictions.csv",
            "equity": TABLEAU_DIR / "current_equity_analysis.csv",
            "summary": TABLEAU_DIR / "current_summary.json"
        }
        
        for key, source_path in source_files.items():
            source = Path(__file__).parent.parent / source_path
            target = target_files[key]
            
            if source.exists():
                shutil.copy2(source, target)
        
        # Create status file
        status = {
            "scenario": scenario_name,
            "pdf_name": pdf_file.name,
            "status": "success",
            "timestamp": datetime.now().isoformat()
        }
        
        with open(TABLEAU_DIR / "pipeline_status.json", "w") as f:
            json.dump(status, f, indent=2)
        
        return True, "Pipeline completed successfully!"
        
    except Exception as e:
        return False, str(e)
    finally:
        # Clean up temp file
        if temp_pdf.exists():
            temp_pdf.unlink()


def main():
    st.title("📊 Education Policy Impact ML Pipeline")
    st.markdown("Upload a bill PDF to automatically run impact predictions")
    
    # Sidebar
    with st.sidebar:
        st.header("Configuration")
        scenario_name = st.text_input(
            "Scenario Name",
            value=f"scenario_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            help="Name for this analysis scenario"
        )
        
        st.markdown("---")
        st.markdown("### Tableau Connection")
        st.info(f"Outputs saved to:\n`{TABLEAU_DIR}`")
        st.markdown("Connect Tableau to:\n- `current_predictions.csv`")
        
        st.markdown("---")
        st.markdown("### Tableau Public Embedding")
        if any(TABLEAU_DASHBOARDS.values()):
            st.success("✅ Dashboards configured")
            with st.expander("Configure Dashboard URLs"):
                geographic_url = st.text_input(
                    "Geographic Impact URL",
                    value=TABLEAU_DASHBOARDS.get("geographic") or "",
                    help="Paste Tableau Public URL for Geographic Impact dashboard"
                )
                metrics_url = st.text_input(
                    "Advanced Metrics URL",
                    value=TABLEAU_DASHBOARDS.get("metrics") or "",
                    help="Paste Tableau Public URL for Advanced Metrics dashboard"
                )
                detail_url = st.text_input(
                    "College Detail URL",
                    value=TABLEAU_DASHBOARDS.get("detail") or "",
                    help="Paste Tableau Public URL for College Detail dashboard"
                )
                if st.button("Update URLs"):
                    st.info("To persist URLs, update TABLEAU_DASHBOARDS in web_interface.py")
        else:
            st.info("💡 After publishing to Tableau Public, add URLs in code to enable embedding")
    
    # Main area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("Upload Bill PDF")
        uploaded_file = st.file_uploader(
            "Choose a PDF file",
            type=['pdf'],
            help="Upload an education policy bill PDF"
        )
        
        if uploaded_file is not None:
            st.success(f"File uploaded: {uploaded_file.name}")
            
            if st.button("🚀 Run Pipeline", type="primary", use_container_width=True):
                with st.spinner("Processing PDF and running pipeline..."):
                    success, message = run_pipeline(uploaded_file, scenario_name)
                    
                    if success:
                        st.success("✅ Pipeline completed successfully!")
                        st.balloons()
                        
                        # Show summary
                        summary_path = TABLEAU_DIR / "current_summary.json"
                        if summary_path.exists():
                            with open(summary_path) as f:
                                summary = json.load(f)
                            
                            st.markdown("### Results Summary")
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Colleges Affected", summary.get("total_colleges_affected", 0))
                            with col2:
                                st.metric("Students Impacted", f"{summary.get('total_students_impacted', 0):,}")
                            with col3:
                                st.metric("Avg Tuition Change", f"${summary.get('average_tuition_change_dollars', 0):,.0f}")
                            
                            if "plain_language_summary" in summary:
                                st.markdown("### Plain Language Summary")
                                st.info(summary["plain_language_summary"])
                            
                            # Display Tableau dashboards if URLs are configured
                            if any(TABLEAU_DASHBOARDS.values()):
                                st.markdown("---")
                                st.markdown("### 📊 Interactive Dashboards")
                                st.info("View detailed visualizations below. Dashboards update automatically when you refresh Tableau Public.")
                                
                                # Dashboard 1: Geographic Impact
                                if TABLEAU_DASHBOARDS.get("geographic"):
                                    st.subheader("🗺️ Geographic Impact Heatmap")
                                    st.components.v1.html(
                                        f'<iframe src="{TABLEAU_DASHBOARDS["geographic"]}" width="100%" height="800" frameborder="0"></iframe>',
                                        height=800,
                                        scrolling=True
                                    )
                                
                                # Dashboard 2: Advanced Metrics
                                if TABLEAU_DASHBOARDS.get("metrics"):
                                    st.subheader("📈 Advanced Metrics Dashboard")
                                    st.components.v1.html(
                                        f'<iframe src="{TABLEAU_DASHBOARDS["metrics"]}" width="100%" height="800" frameborder="0"></iframe>',
                                        height=800,
                                        scrolling=True
                                    )
                                
                                # Dashboard 3: College Detail
                                if TABLEAU_DASHBOARDS.get("detail"):
                                    st.subheader("🏫 College Detail View")
                                    st.components.v1.html(
                                        f'<iframe src="{TABLEAU_DASHBOARDS["detail"]}" width="100%" height="800" frameborder="0"></iframe>',
                                        height=800,
                                        scrolling=True
                                    )
                    else:
                        st.error(f"❌ Pipeline failed: {message}")
    
    with col2:
        st.header("Quick Stats")
        
        # Check if current predictions exist
        predictions_path = TABLEAU_DIR / "current_predictions.csv"
        if predictions_path.exists():
            df = pd.read_csv(predictions_path)
            
            st.metric("Total Colleges", len(df))
            st.metric("States Covered", df['state'].nunique() if 'state' in df.columns else 0)
            
            if 'equity_risk_class' in df.columns:
                st.markdown("### Equity Risk Breakdown")
                risk_counts = df['equity_risk_class'].value_counts()
                st.bar_chart(risk_counts)
        else:
            st.info("No predictions yet. Upload a PDF to get started!")
        
        # Show status
        status_path = TABLEAU_DIR / "pipeline_status.json"
        if status_path.exists():
            with open(status_path) as f:
                status = json.load(f)
            
            st.markdown("### Last Run")
            st.caption(f"PDF: {status.get('pdf_name', 'N/A')}")
            st.caption(f"Time: {status.get('timestamp', 'N/A')[:19]}")
            if status.get('status') == 'success':
                st.success("✓ Success")
            else:
                st.error("✗ Failed")
    
    # Instructions
    st.markdown("---")
    with st.expander("📖 How to Use"):
        st.markdown("""
        ### Step 1: Upload PDF
        - Drag and drop or click to upload a bill PDF
        - The PDF should contain education policy information
        
        ### Step 2: Run Pipeline
        - Click "Run Pipeline" button
        - Wait for processing to complete
        
        ### Step 3: Connect Tableau
        1. Open Tableau Desktop
        2. Connect → Text file
        3. Navigate to: `tableau/data_sources/current_predictions.csv`
        4. Start building visualizations!
        
        ### Output Files
        - `current_predictions.csv` - Main predictions (connect this in Tableau)
        - `current_equity_analysis.csv` - Equity breakdown
        - `current_summary.json` - Summary statistics
        """)


if __name__ == "__main__":
    main()

