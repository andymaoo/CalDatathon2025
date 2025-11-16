"""
Export Layer for Tableau

Purpose: Generate clean, Tableau-ready CSV files and JSON summaries
"""

import pandas as pd
import json
from pathlib import Path
from typing import Dict, Optional
import logging

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
    
    # Add demographic columns if available
    # Try to find enrollment column (could be enrollment or total_enrollment)
    enrollment_col = None
    for col in ["enrollment", "total_enrollment", "total_enroll"]:
        if col in predictions_df.columns:
            enrollment_col = col
            break
    
    demographic_cols = ["pct_low_income", "pct_minority", "net_price", "grad_rate"]
    if enrollment_col:
        demographic_cols.append(enrollment_col)
    
    for col in demographic_cols:
        if col in predictions_df.columns and col not in key_columns:
            key_columns.append(col)
    
    # Filter to available columns
    export_columns = [col for col in key_columns if col in predictions_df.columns]
    
    # Create export DataFrame
    export_df = predictions_df[export_columns].copy()
    
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

