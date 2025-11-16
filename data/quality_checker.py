"""
Data Quality Module

Purpose: Comprehensive data validation and reporting
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def missing_value_analysis(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyze missing values in the dataset.
    
    Args:
        df: Input DataFrame
    
    Returns:
        Dict with missing value statistics
    """
    missing_stats = {}
    total_rows = len(df)
    
    for col in df.columns:
        try:
            col_data = df[col]
            # Handle case where col might be a DataFrame (duplicate column names)
            if isinstance(col_data, pd.DataFrame):
                col_data = col_data.iloc[:, 0]  # Take first column if duplicate
            missing_count = col_data.isna().sum()
            # Ensure it's a scalar
            if isinstance(missing_count, pd.Series):
                missing_count = missing_count.iloc[0] if len(missing_count) > 0 else 0
            missing_count = int(missing_count) if pd.notna(missing_count) else 0
            missing_pct = (missing_count / total_rows) * 100 if total_rows > 0 else 0
            
            missing_stats[col] = {
                "missing_count": missing_count,
                "missing_percentage": round(missing_pct, 2),
                "non_missing_count": int(total_rows - missing_count)
            }
        except Exception as e:
            logger.warning(f"Error analyzing column {col}: {e}")
            missing_stats[col] = {
                "missing_count": 0,
                "missing_percentage": 0.0,
                "non_missing_count": total_rows
            }
    
    # Summary
    cols_with_missing = [col for col, stats in missing_stats.items() 
                        if stats["missing_count"] > 0]
    
    return {
        "columns_analyzed": len(df.columns),
        "columns_with_missing": len(cols_with_missing),
        "total_rows": total_rows,
        "per_column_stats": missing_stats,
        "columns_with_missing_list": cols_with_missing
    }


def outlier_detection(df: pd.DataFrame, method: str = "iqr") -> Dict[str, Any]:
    """
    Detect outliers using IQR method or z-scores.
    
    Args:
        df: Input DataFrame
        method: "iqr" or "zscore"
    
    Returns:
        Dict with outlier statistics
    """
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    outlier_stats = {}
    
    for col in numeric_cols:
        try:
            col_data = df[col]
            # Handle duplicate column names
            if isinstance(col_data, pd.DataFrame):
                col_data = col_data.iloc[:, 0]
            
            if col_data.isna().all():
                continue
            
            values = col_data.dropna()
            if len(values) == 0:
                continue
        except Exception as e:
            logger.warning(f"Error processing column {col} for outliers: {e}")
            continue
        
        if method == "iqr":
            Q1 = values.quantile(0.25)
            Q3 = values.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            col_data = df[col] if not isinstance(df[col], pd.DataFrame) else df[col].iloc[:, 0]
            outliers = df[(col_data < lower_bound) | (col_data > upper_bound)]
            outlier_count = len(outliers)
            
        elif method == "zscore":
            z_scores = np.abs((values - values.mean()) / values.std())
            outlier_mask = z_scores > 3
            outlier_count = outlier_mask.sum()
            outliers = df.loc[values.index[outlier_mask]]
        else:
            continue
        
        if outlier_count > 0:
            outlier_stats[col] = {
                "outlier_count": int(outlier_count),
                "outlier_percentage": round((outlier_count / len(df)) * 100, 2),
                "lower_bound": float(lower_bound) if method == "iqr" else None,
                "upper_bound": float(upper_bound) if method == "iqr" else None,
                "min_value": float(values.min()),
                "max_value": float(values.max()),
                "mean": float(values.mean()),
                "median": float(values.median())
            }
    
    return {
        "method": method,
        "columns_analyzed": len(numeric_cols),
        "columns_with_outliers": len(outlier_stats),
        "per_column_stats": outlier_stats
    }


def duplicate_detection(df: pd.DataFrame, key_columns: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Detect duplicate rows and duplicate key values.
    
    Args:
        df: Input DataFrame
        key_columns: Columns that should be unique (e.g., institution_id)
    
    Returns:
        Dict with duplicate statistics
    """
    results = {
        "duplicate_rows": int(df.duplicated().sum()),
        "duplicate_percentage": round((df.duplicated().sum() / len(df)) * 100, 2) if len(df) > 0 else 0
    }
    
    if key_columns:
        key_duplicates = {}
        for col in key_columns:
            if col in df.columns:
                dup_count = df[col].duplicated().sum()
                key_duplicates[col] = {
                    "duplicate_count": int(dup_count),
                    "duplicate_percentage": round((dup_count / len(df)) * 100, 2) if len(df) > 0 else 0,
                    "unique_count": int(df[col].nunique())
                }
        results["key_column_duplicates"] = key_duplicates
    
    return results


def data_type_validation(df: pd.DataFrame, expected_types: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Validate data types and ranges.
    
    Args:
        df: Input DataFrame
        expected_types: Dict mapping column names to expected types
    
    Returns:
        Dict with validation results
    """
    validation_results = {}
    
    # Check numeric ranges
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    for col in numeric_cols:
        issues = []
        
        # Check for percentage columns (should be 0-100)
        if "pct" in col or "rate" in col or "percent" in col:
            if df[col].min() < 0 or df[col].max() > 100:
                issues.append(f"Percentage out of range: min={df[col].min()}, max={df[col].max()}")
        
        # Check for enrollment (should be positive)
        if "enrollment" in col:
            if (df[col] < 0).any():
                issues.append(f"Negative enrollment values found: {((df[col] < 0).sum())} rows")
        
        # Check for tuition/price (should be non-negative)
        if any(keyword in col for keyword in ["tuition", "price", "cost"]):
            if (df[col] < 0).any():
                issues.append(f"Negative values found: {((df[col] < 0).sum())} rows")
        
        if issues:
            validation_results[col] = {
                "status": "issues_found",
                "issues": issues
            }
        else:
            validation_results[col] = {
                "status": "valid"
            }
    
    # Check expected types
    if expected_types:
        type_issues = {}
        for col, expected_type in expected_types.items():
            if col in df.columns:
                actual_type = str(df[col].dtype)
                if expected_type not in actual_type:
                    type_issues[col] = {
                        "expected": expected_type,
                        "actual": actual_type
                    }
        if type_issues:
            validation_results["type_mismatches"] = type_issues
    
    return {
        "columns_validated": len(numeric_cols),
        "columns_with_issues": len([r for r in validation_results.values() if r.get("status") == "issues_found"]),
        "validation_results": validation_results
    }


def cross_column_consistency(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Check cross-column consistency (e.g., enrollment > 0, grad_rate 0-100).
    
    Args:
        df: Input DataFrame
    
    Returns:
        Dict with consistency check results
    """
    consistency_issues = []
    
    # Check: enrollment should be positive
    if "enrollment" in df.columns:
        negative_enrollment = (df["enrollment"] < 0).sum()
        if negative_enrollment > 0:
            consistency_issues.append({
                "check": "enrollment_positive",
                "issue": f"{negative_enrollment} rows with negative enrollment",
                "severity": "high"
            })
    
    # Check: grad_rate should be 0-100
    grad_rate_cols = [col for col in df.columns if "grad_rate" in col or "graduation_rate" in col]
    for col in grad_rate_cols:
        out_of_range = ((df[col] < 0) | (df[col] > 100)).sum()
        if out_of_range > 0:
            consistency_issues.append({
                "check": f"{col}_range",
                "issue": f"{out_of_range} rows with grad_rate outside 0-100",
                "severity": "medium"
            })
    
    # Check: tuition should be less than total cost
    if "tuition" in df.columns and "total_cost" in df.columns:
        tuition_exceeds_cost = (df["tuition"] > df["total_cost"]).sum()
        if tuition_exceeds_cost > 0:
            consistency_issues.append({
                "check": "tuition_vs_total_cost",
                "issue": f"{tuition_exceeds_cost} rows where tuition > total_cost",
                "severity": "medium"
            })
    
    return {
        "consistency_checks_performed": len(consistency_issues) + 3,
        "issues_found": len(consistency_issues),
        "issues": consistency_issues
    }


def quality_checks(df: pd.DataFrame, output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Run comprehensive quality checks and generate report.
    
    Args:
        df: Input DataFrame
        output_path: Optional path to save JSON report
    
    Returns:
        Complete quality report dict
    """
    logger.info("Running data quality checks...")
    
    report = {
        "dataset_info": {
            "shape": list(df.shape),
            "columns": list(df.columns),
            "memory_usage_mb": round(df.memory_usage(deep=True).sum() / 1024**2, 2)
        },
        "missing_values": missing_value_analysis(df),
        "outliers": outlier_detection(df, method="iqr"),
        "duplicates": duplicate_detection(df, key_columns=["institution_id"] if "institution_id" in df.columns else None),
        "data_types": data_type_validation(df),
        "consistency": cross_column_consistency(df)
    }
    
    # Overall quality score (0-100)
    quality_score = 100
    if report["missing_values"]["columns_with_missing"] > 0:
        quality_score -= min(30, report["missing_values"]["columns_with_missing"] * 2)
    if report["outliers"]["columns_with_outliers"] > 0:
        quality_score -= min(20, report["outliers"]["columns_with_outliers"] * 2)
    if report["duplicates"]["duplicate_rows"] > 0:
        quality_score -= min(20, report["duplicates"]["duplicate_rows"])
    if report["consistency"]["issues_found"] > 0:
        quality_score -= min(30, report["consistency"]["issues_found"] * 5)
    
    report["overall_quality_score"] = max(0, quality_score)
    
    # Save report
    if output_path:
        output_path_obj = Path(output_path)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2, default=str)
        logger.info(f"Quality report saved to {output_path}")
    
    logger.info(f"Quality checks complete. Overall score: {report['overall_quality_score']}/100")
    return report


if __name__ == "__main__":
    # Example usage
    import sys
    if len(sys.argv) > 1:
        csv_path = sys.argv[1]
        df = pd.read_csv(csv_path)
        report = quality_checks(df, f"outputs/data_quality_report.json")
        print(f"Quality Score: {report['overall_quality_score']}/100")

