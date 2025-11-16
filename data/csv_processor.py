"""
CSV Aggregation & Cleaning Module

Purpose: Read, aggregate, clean, and validate multiple CSV sources
"""

import pandas as pd
import numpy as np
import os
from pathlib import Path
from typing import List, Dict, Optional, Union
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def read_and_merge_csvs(
    csv_paths: Dict[str, str],
    merge_keys: Dict[str, str],
    data_dir: str = "data/raw"
) -> pd.DataFrame:
    """
    Load multiple CSVs and merge on institution ID.
    
    Args:
        csv_paths: Dict mapping dataset names to CSV filenames
                   e.g., {"affordability": "affordability_gap.csv", "results": "college_results.csv"}
        merge_keys: Dict mapping dataset names to merge key column names
                   e.g., {"affordability": "institution_id", "results": "institution_id"}
        data_dir: Directory containing raw CSV files
    
    Returns:
        Merged DataFrame with all features
    """
    data_dir_path = Path(data_dir)
    dfs = {}
    
    for dataset_name, filename in csv_paths.items():
        filepath = data_dir_path / filename
        if not filepath.exists():
            logger.warning(f"File not found: {filepath}. Skipping {dataset_name} dataset.")
            continue
        
        try:
            df = pd.read_csv(filepath)
            merge_key = merge_keys.get(dataset_name)
            if merge_key and merge_key in df.columns:
                # Standardize merge key name
                df = df.rename(columns={merge_key: "institution_id"})
            elif "institution_id" not in df.columns:
                logger.warning(f"No merge key found in {dataset_name}. Attempting to infer...")
                # Try common ID column names
                for col in ["id", "unitid", "opeid", "college_id"]:
                    if col in df.columns:
                        df = df.rename(columns={col: "institution_id"})
                        break
            
            dfs[dataset_name] = df
            logger.info(f"Loaded {dataset_name}: {len(df)} rows, {len(df.columns)} columns")
        except Exception as e:
            logger.error(f"Error loading {filepath}: {e}")
            continue
    
    if not dfs:
        raise ValueError("No CSV files were successfully loaded.")
    
    # Start with the first dataset
    merged_df = dfs[list(dfs.keys())[0]].copy()
    
    # Merge remaining datasets
    for dataset_name, df in list(dfs.items())[1:]:
        if "institution_id" in df.columns and "institution_id" in merged_df.columns:
            merged_df = merged_df.merge(
                df,
                on="institution_id",
                how="outer",
                suffixes=("", f"_{dataset_name}")
            )
            logger.info(f"Merged {dataset_name}: {len(merged_df)} rows after merge")
        else:
            logger.warning(f"Cannot merge {dataset_name}: missing institution_id")
    
    return merged_df


def clean_data(df: pd.DataFrame, config: Optional[Dict] = None) -> pd.DataFrame:
    """
    Handle missing values, normalize column names, fix data types.
    
    Args:
        df: Input DataFrame
        config: Optional config dict with cleaning rules
    
    Returns:
        Cleaned DataFrame
    """
    df = df.copy()
    
    # Normalize column names: lowercase, replace spaces with underscores
    df.columns = df.columns.str.lower().str.replace(" ", "_").str.replace("-", "_")
    
    # Remove duplicate rows
    initial_rows = len(df)
    df = df.drop_duplicates()
    if len(df) < initial_rows:
        logger.info(f"Removed {initial_rows - len(df)} duplicate rows")
    
    # Handle missing values based on column type
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    categorical_cols = df.select_dtypes(include=["object", "category"]).columns
    
    # Fill numeric columns with median (or 0 for counts/percentages)
    for col in numeric_cols:
        if df[col].isna().sum() > 0:
            if "pct" in col or "rate" in col or "percent" in col:
                df[col] = df[col].fillna(0)
            else:
                df[col] = df[col].fillna(df[col].median())
    
    # Fill categorical columns with "Unknown"
    for col in categorical_cols:
        if df[col].isna().sum() > 0:
            df[col] = df[col].fillna("Unknown")
    
    # Fix data types
    # Ensure institution_id is string or int (not float)
    if "institution_id" in df.columns:
        df["institution_id"] = pd.to_numeric(df["institution_id"], errors="coerce").astype("Int64")
    
    # Convert percentage columns to 0-100 range if they're in 0-1 range
    pct_cols = [col for col in df.columns if "pct" in col or "rate" in col or "percent" in col]
    for col in pct_cols:
        if df[col].max() <= 1.0 and df[col].min() >= 0:
            df[col] = df[col] * 100
            logger.info(f"Converted {col} from 0-1 to 0-100 scale")
    
    # Ensure enrollment, tuition, etc. are numeric
    numeric_keywords = ["enrollment", "tuition", "price", "cost", "wage", "subsidy", "gap"]
    for col in df.columns:
        if any(keyword in col for keyword in numeric_keywords):
            df[col] = pd.to_numeric(df[col], errors="coerce")
    
    logger.info(f"Data cleaning complete. Final shape: {df.shape}")
    return df


def aggregate_metrics(
    df: pd.DataFrame,
    group_cols: Optional[List[str]] = None,
    agg_functions: Optional[Dict[str, List[str]]] = None
) -> pd.DataFrame:
    """
    Compute summary statistics per college, state, institution type.
    
    Args:
        df: Input DataFrame
        group_cols: Columns to group by (e.g., ["state", "institution_type"])
        agg_functions: Dict mapping column names to aggregation functions
    
    Returns:
        Aggregated DataFrame
    """
    if group_cols is None:
        group_cols = ["state", "institution_type"]
    
    # Filter to existing columns
    group_cols = [col for col in group_cols if col in df.columns]
    
    if not group_cols:
        logger.warning("No valid group columns found. Returning original DataFrame.")
        return df
    
    if agg_functions is None:
        # Default aggregations
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        agg_functions = {
            col: ["mean", "median", "std", "min", "max", "count"]
            for col in numeric_cols
            if col not in group_cols
        }
    
    # Aggregate
    aggregated = df.groupby(group_cols).agg(agg_functions).reset_index()
    
    # Flatten column names
    aggregated.columns = ["_".join(col).strip() if col[1] else col[0] 
                          for col in aggregated.columns.values]
    
    logger.info(f"Aggregated data: {len(aggregated)} groups from {len(df)} rows")
    return aggregated


def build_master_colleges(
    csv_paths: Optional[Dict[str, str]] = None,
    merge_keys: Optional[Dict[str, str]] = None,
    output_path: str = "data/master_colleges.csv",
    data_dir: str = "data/raw"
) -> pd.DataFrame:
    """
    Main function to build master colleges dataset.
    
    Args:
        csv_paths: Dict mapping dataset names to CSV filenames
        merge_keys: Dict mapping dataset names to merge key column names
        output_path: Output path for master dataset
        data_dir: Directory containing raw CSV files
    
    Returns:
        Master colleges DataFrame
    """
    if csv_paths is None:
        # Default CSV paths
        csv_paths = {
            "affordability": "affordability_gap.csv",
            "results": "college_results.csv"
        }
    
    if merge_keys is None:
        merge_keys = {
            "affordability": "institution_id",
            "results": "institution_id"
        }
    
    # Read and merge CSVs
    logger.info("Reading and merging CSV files...")
    merged_df = read_and_merge_csvs(csv_paths, merge_keys, data_dir)
    
    # Clean data
    logger.info("Cleaning data...")
    cleaned_df = clean_data(merged_df)
    
    # Save master dataset
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    cleaned_df.to_csv(output_path, index=False)
    logger.info(f"Master colleges dataset saved to {output_path}")
    
    return cleaned_df


if __name__ == "__main__":
    # Example usage
    master_df = build_master_colleges()
    print(f"Master dataset shape: {master_df.shape}")
    print(f"Columns: {list(master_df.columns)}")

