#!/bin/bash
# Linux/Mac script to start the auto-pipeline watcher

echo "Starting Tableau Auto-Pipeline Watcher..."
echo ""
echo "Drop PDF files in: tableau_integration/upload/"
echo "Outputs will be saved to: tableau/data_sources/"
echo ""
echo "Press Ctrl+C to stop"
echo ""

python tableau_integration/tableau_auto_pipeline.py

