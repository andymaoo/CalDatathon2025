@echo off
REM Windows batch script to start the web interface

echo Starting Tableau Web Interface...
echo.
echo Opening browser at http://localhost:8501
echo.

streamlit run tableau_integration/web_interface.py

pause

