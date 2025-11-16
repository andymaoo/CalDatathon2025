"""
CSV Analysis Module

Purpose: Comprehensive CSV analysis toolkit
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from typing import Dict, List, Optional
import matplotlib.pyplot as plt
import seaborn as sns
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def analyze_csv(csv_path: str) -> Dict:
    """
    Load CSV and generate basic statistics.
    
    Args:
        csv_path: Path to CSV file
    
    Returns:
        Dict with basic statistics
    """
    df = pd.read_csv(csv_path)
    
    stats = {
        "file_path": csv_path,
        "shape": list(df.shape),
        "columns": list(df.columns),
        "memory_usage_mb": round(df.memory_usage(deep=True).sum() / 1024**2, 2),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()}
    }
    
    return stats


def statistical_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate statistical summary (mean, median, std, min, max, quartiles).
    
    Args:
        df: Input DataFrame
    
    Returns:
        Summary DataFrame
    """
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    if len(numeric_cols) == 0:
        logger.warning("No numeric columns found for statistical summary")
        return pd.DataFrame()
    
    summary = df[numeric_cols].describe().T
    summary["median"] = df[numeric_cols].median()
    summary["std"] = df[numeric_cols].std()
    
    return summary


def correlation_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate correlation matrix for numeric columns.
    
    Args:
        df: Input DataFrame
    
    Returns:
        Correlation matrix DataFrame
    """
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    if len(numeric_cols) < 2:
        logger.warning("Need at least 2 numeric columns for correlation analysis")
        return pd.DataFrame()
    
    corr_matrix = df[numeric_cols].corr()
    return corr_matrix


def distribution_plots(
    df: pd.DataFrame,
    output_dir: str,
    columns: Optional[List[str]] = None,
    max_plots: int = 10
):
    """
    Generate distribution plots (histograms, box plots).
    
    Args:
        df: Input DataFrame
        output_dir: Output directory for plots
        columns: Optional list of columns to plot
        max_plots: Maximum number of plots to generate
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    if columns:
        numeric_cols = [col for col in columns if col in numeric_cols]
    
    numeric_cols = numeric_cols[:max_plots]
    
    for col in numeric_cols:
        try:
            # Histogram
            plt.figure(figsize=(10, 6))
            df[col].hist(bins=30, edgecolor='black')
            plt.title(f"Distribution of {col}")
            plt.xlabel(col)
            plt.ylabel("Frequency")
            plt.tight_layout()
            plt.savefig(output_path / f"{col}_histogram.png", dpi=150, bbox_inches='tight')
            plt.close()
            
            # Box plot
            plt.figure(figsize=(8, 6))
            df[col].plot(kind='box')
            plt.title(f"Box Plot of {col}")
            plt.ylabel(col)
            plt.tight_layout()
            plt.savefig(output_path / f"{col}_boxplot.png", dpi=150, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Generated plots for {col}")
        except Exception as e:
            logger.warning(f"Error generating plots for {col}: {e}")


def aggregate_by_group(
    df: pd.DataFrame,
    group_cols: List[str],
    agg_functions: Optional[Dict[str, List[str]]] = None
) -> pd.DataFrame:
    """
    Group by columns and compute aggregated metrics.
    
    Args:
        df: Input DataFrame
        group_cols: Columns to group by
        agg_functions: Optional dict mapping columns to aggregation functions
    
    Returns:
        Aggregated DataFrame
    """
    # Filter to existing columns
    group_cols = [col for col in group_cols if col in df.columns]
    
    if not group_cols:
        logger.warning("No valid group columns found")
        return pd.DataFrame()
    
    if agg_functions is None:
        # Default: mean for numeric, count for all
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        numeric_cols = [col for col in numeric_cols if col not in group_cols]
        
        agg_functions = {
            col: ["mean", "count"] for col in numeric_cols[:10]  # Limit to first 10
        }
    
    aggregated = df.groupby(group_cols).agg(agg_functions).reset_index()
    
    # Flatten column names
    aggregated.columns = ["_".join(col).strip() if col[1] else col[0] 
                          for col in aggregated.columns.values]
    
    return aggregated


def compare_scenarios(scenario_csvs: List[str]) -> pd.DataFrame:
    """
    Compare multiple scenario outputs side-by-side.
    
    Args:
        scenario_csvs: List of CSV file paths
    
    Returns:
        Comparison DataFrame
    """
    comparisons = []
    
    for csv_path in scenario_csvs:
        df = pd.read_csv(csv_path)
        scenario_name = Path(csv_path).stem.replace("predicted_impact_", "")
        
        # Calculate summary stats
        summary = {
            "scenario": scenario_name,
            "colleges_count": len(df),
            "avg_tuition_change": df.get("tuition_change_dollars", pd.Series([0])).mean(),
            "total_students_affected": df.get("students_affected", pd.Series([0])).sum(),
            "high_risk_colleges": (df.get("equity_risk_class", pd.Series(["Low"])) == "High").sum() if "equity_risk_class" in df.columns else 0
        }
        
        comparisons.append(summary)
    
    comparison_df = pd.DataFrame(comparisons)
    return comparison_df


def analyze_scenario(
    csv_path: str,
    scenario_name: Optional[str] = None,
    output_dir: str = "outputs/analysis"
) -> Dict:
    """
    Complete analysis for a single scenario CSV.
    
    Args:
        csv_path: Path to CSV file
        scenario_name: Optional scenario name
        output_dir: Output directory
    
    Returns:
        Analysis results dict
    """
    if scenario_name is None:
        scenario_name = Path(csv_path).stem
    
    logger.info(f"Analyzing scenario: {scenario_name}")
    
    # Load data
    df = pd.read_csv(csv_path)
    
    # Statistical summary
    stats_summary = statistical_summary(df)
    
    # Correlation analysis
    corr_matrix = correlation_analysis(df)
    
    # Save statistics
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    stats_path = output_path / f"{scenario_name}_statistics.json"
    stats_dict = stats_summary.to_dict() if not stats_summary.empty else {}
    with open(stats_path, "w") as f:
        json.dump(stats_dict, f, indent=2, default=str)
    
    # Save correlation matrix
    if not corr_matrix.empty:
        corr_path = output_path / f"{scenario_name}_correlations.csv"
        corr_matrix.to_csv(corr_path)
    
    # Generate plots
    plots_dir = output_path / f"{scenario_name}_plots"
    distribution_plots(df, str(plots_dir), max_plots=5)
    
    # Aggregate by state/type if available
    aggregations = {}
    if "state" in df.columns:
        state_agg = aggregate_by_group(df, ["state"])
        aggregations["by_state"] = state_agg.to_dict("records")
    
    if "institution_type" in df.columns:
        type_agg = aggregate_by_group(df, ["institution_type"])
        aggregations["by_institution_type"] = type_agg.to_dict("records")
    
    results = {
        "scenario_name": scenario_name,
        "basic_stats": stats_dict,
        "aggregations": aggregations,
        "files_generated": {
            "statistics": str(stats_path),
            "correlations": str(corr_path) if not corr_matrix.empty else None,
            "plots_dir": str(plots_dir)
        }
    }
    
    logger.info(f"Analysis complete for {scenario_name}")
    return results


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        csv_path = sys.argv[1]
        results = analyze_scenario(csv_path)
        print(json.dumps(results, indent=2, default=str))

