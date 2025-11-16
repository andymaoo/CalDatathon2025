"""
Tableau Auto-Pipeline Integration

Automated script that watches for PDF uploads and runs pipeline automatically.
Outputs are saved to a fixed location that Tableau can connect to.
"""

import os
import sys
import time
import shutil
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess
import logging
from datetime import datetime
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.run_full_pipeline import main as run_pipeline_main
import argparse

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PDFHandler(FileSystemEventHandler):
    """Handler for PDF file events."""
    
    def __init__(self, watch_dir, output_dir, tableau_dir):
        self.watch_dir = Path(watch_dir)
        self.output_dir = Path(output_dir)
        self.tableau_dir = Path(tableau_dir)
        self.processing = set()  # Track files being processed
        
        # Create directories
        self.tableau_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Watching directory: {self.watch_dir}")
        logger.info(f"Tableau output directory: {self.tableau_dir}")
    
    def on_created(self, event):
        """Called when a file is created in the watch directory."""
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        
        # Only process PDF files
        if file_path.suffix.lower() != '.pdf':
            return
        
        # Avoid processing the same file twice
        if file_path in self.processing:
            return
        
        # Wait a moment for file to be fully written
        time.sleep(1)
        
        if not file_path.exists():
            return
        
        logger.info(f"New PDF detected: {file_path.name}")
        self.process_pdf(file_path)
    
    def process_pdf(self, pdf_path):
        """Process a PDF file through the pipeline."""
        self.processing.add(pdf_path)
        
        try:
            # Generate scenario name from filename and timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            scenario_name = f"{pdf_path.stem}_{timestamp}"
            
            logger.info(f"Processing PDF: {pdf_path.name}")
            logger.info(f"Scenario name: {scenario_name}")
            
            # Run the pipeline
            logger.info("Running pipeline...")
            
            # Build command arguments
            cmd_args = [
                "python", "pipeline/run_full_pipeline.py",
                "--bill", str(pdf_path),
                "--scenario", scenario_name
            ]
            
            # Run pipeline
            result = subprocess.run(
                cmd_args,
                cwd=Path(__file__).parent.parent,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"Pipeline failed: {result.stderr}")
                return
            
            logger.info("Pipeline completed successfully")
            
            # Copy outputs to Tableau directory with fixed names
            self.copy_to_tableau(scenario_name)
            
            # Create status file for Tableau to check
            self.create_status_file(scenario_name, pdf_path.name, "success")
            
            logger.info(f"✓ Outputs ready in Tableau directory: {self.tableau_dir}")
            
        except Exception as e:
            logger.error(f"Error processing PDF: {e}", exc_info=True)
            self.create_status_file(scenario_name, pdf_path.name, "error", str(e))
        finally:
            self.processing.discard(pdf_path)
    
    def copy_to_tableau(self, scenario_name):
        """Copy output files to Tableau directory with fixed names."""
        source_files = {
            "predictions": f"outputs/predictions/predicted_impact_{scenario_name}.csv",
            "equity": f"outputs/equity_analysis/equity_analysis_{scenario_name}.csv",
            "summary": f"outputs/summaries/summary_{scenario_name}.json"
        }
        
        target_files = {
            "predictions": self.tableau_dir / "current_predictions.csv",
            "equity": self.tableau_dir / "current_equity_analysis.csv",
            "summary": self.tableau_dir / "current_summary.json"
        }
        
        for key, source_path in source_files.items():
            source = Path(__file__).parent.parent / source_path
            target = target_files[key]
            
            if source.exists():
                shutil.copy2(source, target)
                logger.info(f"Copied {key} to {target}")
            else:
                logger.warning(f"Source file not found: {source}")
    
    def create_status_file(self, scenario_name, pdf_name, status, error_msg=None):
        """Create a status file for Tableau to check."""
        status_data = {
            "scenario": scenario_name,
            "pdf_name": pdf_name,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "error": error_msg
        }
        
        status_file = self.tableau_dir / "pipeline_status.json"
        with open(status_file, "w") as f:
            json.dump(status_data, f, indent=2)
        
        logger.info(f"Status file updated: {status}")


def start_watcher(watch_dir="tableau_integration/upload", tableau_dir="tableau/data_sources"):
    """Start watching for PDF files."""
    watch_path = Path(__file__).parent.parent / watch_dir
    tableau_path = Path(__file__).parent.parent / tableau_dir
    
    # Create watch directory if it doesn't exist
    watch_path.mkdir(parents=True, exist_ok=True)
    
    event_handler = PDFHandler(watch_path, "outputs", tableau_path)
    observer = Observer()
    observer.schedule(event_handler, str(watch_path), recursive=False)
    observer.start()
    
    logger.info("="*60)
    logger.info("Tableau Auto-Pipeline Watcher Started")
    logger.info("="*60)
    logger.info(f"Watching directory: {watch_path}")
    logger.info(f"Drop PDF files here to automatically process them")
    logger.info(f"Outputs will be saved to: {tableau_path}")
    logger.info("Press Ctrl+C to stop")
    logger.info("="*60)
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("\nStopping watcher...")
        observer.stop()
    
    observer.join()
    logger.info("Watcher stopped")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tableau Auto-Pipeline Watcher")
    parser.add_argument(
        "--watch-dir",
        default="tableau_integration/upload",
        help="Directory to watch for PDF files"
    )
    parser.add_argument(
        "--tableau-dir",
        default="tableau/data_sources",
        help="Directory for Tableau data sources"
    )
    
    args = parser.parse_args()
    start_watcher(args.watch_dir, args.tableau_dir)

