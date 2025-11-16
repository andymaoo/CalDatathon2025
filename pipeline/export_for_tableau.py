"""
Export Layer for Tableau

Purpose: Generate clean, Tableau-ready CSV files and JSON summaries
"""

import pandas as pd
import json
from pathlib import Path
from typing import Dict, Optional
import logging
import shutil

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def export_predicted_impact(
    predictions_df: pd.DataFrame,
    scenario_name: str,
    output_dir: str = "outputs/predictions"
) -> str:
    """
    Export college-level predictions to CSV.
    
    Args:
        predictions_df: DataFrame with predictions
        scenario_name: Scenario identifier
        output_dir: Output directory
    
    Returns:
        Path to exported CSV
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Create a copy for export to avoid modifying original
    export_df = predictions_df.copy()
    
    # Map institution_name to name if needed (master dataset uses institution_name)
    if "institution_name" in export_df.columns and "name" not in export_df.columns:
        export_df["name"] = export_df["institution_name"]
    
    # Select key columns for Tableau
    key_columns = [
        "institution_id",
        "name",
        "state",
        "institution_type",
        "tuition_change_pct",
        "tuition_change_dollars",
        "enrollment_change_pct",
        "students_affected",
        "grad_rate_change",
        "equity_risk_class",
        "hours_to_cover_gap"
    ]
    
    # Add geographic columns if available
    geographic_cols = ["latitude", "longitude"]
    for col in geographic_cols:
        if col in export_df.columns and col not in key_columns:
            key_columns.append(col)
    
    # Add demographic columns if available
    # Try to find enrollment column (could be enrollment or total_enrollment)
    enrollment_col = None
    for col in ["enrollment", "total_enrollment", "total_enroll"]:
        if col in export_df.columns:
            enrollment_col = col
            break
    
    demographic_cols = ["pct_low_income", "pct_minority", "net_price", "grad_rate"]
    if enrollment_col:
        demographic_cols.append(enrollment_col)
    
    for col in demographic_cols:
        if col in export_df.columns and col not in key_columns:
            key_columns.append(col)
    
    # Filter to available columns
    export_columns = [col for col in key_columns if col in export_df.columns]
    
    # Create export DataFrame with selected columns
    export_df = export_df[export_columns].copy()
    
    # Fill missing values
    numeric_cols = export_df.select_dtypes(include=['number']).columns
    export_df[numeric_cols] = export_df[numeric_cols].fillna(0)
    
    categorical_cols = export_df.select_dtypes(include=['object']).columns
    export_df[categorical_cols] = export_df[categorical_cols].fillna("Unknown")
    
    # Ensure consistent types
    for col in export_df.columns:
        if export_df[col].dtype == 'object':
            # Remove any mixed types
            export_df[col] = export_df[col].astype(str)
    
    # Export to CSV
    filename = f"predicted_impact_{scenario_name}.csv"
    filepath = output_path / filename
    export_df.to_csv(filepath, index=False)
    
    logger.info(f"Exported predicted impact to {filepath}")
    logger.info(f"Shape: {export_df.shape}")
    
    return str(filepath)


def export_equity_analysis(
    predictions_df: pd.DataFrame,
    scenario_name: str,
    output_dir: str = "outputs/equity_analysis"
) -> str:
    """
    Export equity analysis grouped by risk class.
    
    Args:
        predictions_df: DataFrame with predictions
        scenario_name: Scenario identifier
        output_dir: Output directory
    
    Returns:
        Path to exported CSV
    """
    if "equity_risk_class" not in predictions_df.columns:
        logger.warning("No equity_risk_class column found. Skipping equity analysis export.")
        return ""
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Group by equity risk class
    equity_df = predictions_df.groupby("equity_risk_class").agg({
        "institution_id": "count",
        "tuition_change_dollars": ["mean", "sum"],
        "students_affected": "sum",
        "enrollment_change_pct": "mean",
        "grad_rate_change": "mean"
    }).reset_index()
    
    # Flatten column names
    equity_df.columns = ["equity_risk_class", "college_count", "avg_tuition_change", 
                         "total_tuition_impact", "total_students_affected", 
                         "avg_enrollment_change", "avg_grad_rate_change"]
    
    # Export to CSV
    filename = f"equity_analysis_{scenario_name}.csv"
    filepath = output_path / filename
    equity_df.to_csv(filepath, index=False)
    
    logger.info(f"Exported equity analysis to {filepath}")
    
    return str(filepath)


def export_summary_json(
    summary_dict: Dict,
    scenario_name: str,
    output_dir: str = "outputs/summaries"
) -> str:
    """
    Export summary statistics to JSON.
    
    Args:
        summary_dict: Summary statistics dict
        scenario_name: Scenario identifier
        output_dir: Output directory
    
    Returns:
        Path to exported JSON
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Add metadata
    summary_dict["scenario_name"] = scenario_name
    summary_dict["export_timestamp"] = pd.Timestamp.now().isoformat()
    
    # Export to JSON
    filename = f"summary_{scenario_name}.json"
    filepath = output_path / filename
    
    with open(filepath, "w") as f:
        json.dump(summary_dict, f, indent=2, default=str)
    
    logger.info(f"Exported summary to {filepath}")
    
    return str(filepath)


def export_for_tableau(
    predictions_df: pd.DataFrame,
    summary_dict: Dict,
    scenario_name: str,
    output_base_dir: str = "outputs"
) -> Dict[str, str]:
    """
    Main export function - exports all Tableau-ready files.
    
    Args:
        predictions_df: DataFrame with predictions
        summary_dict: Summary statistics dict
        scenario_name: Scenario identifier
        output_base_dir: Base output directory
    
    Returns:
        Dict mapping file types to file paths
    """
    logger.info(f"Exporting scenario '{scenario_name}' for Tableau...")
    
    exported_files = {}
    
    # Export predicted impact CSV
    impact_csv = export_predicted_impact(
        predictions_df,
        scenario_name,
        output_dir=f"{output_base_dir}/predictions"
    )
    exported_files["predicted_impact"] = impact_csv
    
    # Export equity analysis CSV
    equity_csv = export_equity_analysis(
        predictions_df,
        scenario_name,
        output_dir=f"{output_base_dir}/equity_analysis"
    )
    if equity_csv:
        exported_files["equity_analysis"] = equity_csv
    
    # Export summary JSON
    summary_json = export_summary_json(
        summary_dict,
        scenario_name,
        output_dir=f"{output_base_dir}/summaries"
    )
    exported_files["summary"] = summary_json
    
    logger.info(f"Export complete. Files exported: {list(exported_files.keys())}")
    
    # Copy files to fixed Tableau location for easy connection
    tableau_data_dir = Path("tableau/data_sources")
    tableau_data_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy predicted impact CSV to fixed location
    if "predicted_impact" in exported_files and Path(exported_files["predicted_impact"]).exists():
        tableau_predictions = tableau_data_dir / "current_predictions.csv"
        shutil.copy2(exported_files["predicted_impact"], tableau_predictions)
        logger.info(f"Copied predictions to {tableau_predictions}")
    
    # Copy equity analysis CSV to fixed location
    if "equity_analysis" in exported_files and exported_files["equity_analysis"] and Path(exported_files["equity_analysis"]).exists():
        tableau_equity = tableau_data_dir / "current_equity_analysis.csv"
        shutil.copy2(exported_files["equity_analysis"], tableau_equity)
        logger.info(f"Copied equity analysis to {tableau_equity}")
    
    # Copy summary JSON to fixed location
    if "summary" in exported_files and Path(exported_files["summary"]).exists():
        tableau_summary = tableau_data_dir / "current_summary.json"
        shutil.copy2(exported_files["summary"], tableau_summary)
        logger.info(f"Copied summary to {tableau_summary}")
    
    return exported_files


if __name__ == "__main__":
    # Example usage
    import sys
    if len(sys.argv) > 2:
        csv_path = sys.argv[1]
        scenario_name = sys.argv[2]
        
        df = pd.read_csv(csv_path)
        summary = {
            "total_colleges_affected": len(df),
            "total_students_impacted": int(df.get("students_affected", 0).sum()) if "students_affected" in df.columns else 0
        }
        
        exported = export_for_tableau(df, summary, scenario_name)
        print(f"Exported files: {exported}")

