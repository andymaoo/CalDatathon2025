"""
Data Quality Analysis for master_colleges.csv

Checks data types, missing values, and data quality issues.
"""

import pandas as pd
import numpy as np
from pathlib import Path

def analyze_data_quality(csv_path: str = "data/master_colleges.csv"):
    """Comprehensive data quality analysis."""
    
    print("=" * 80)
    print("DATA QUALITY ANALYSIS: master_colleges.csv")
    print("=" * 80)
    
    # Load data
    df = pd.read_csv(csv_path)
    
    print(f"\n[OVERVIEW] DATASET OVERVIEW")
    print(f"   Shape: {df.shape[0]:,} rows × {df.shape[1]} columns")
    print(f"   Memory usage: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
    
    # Data types
    print(f"\n[DATA TYPES]")
    dtype_counts = df.dtypes.value_counts()
    for dtype, count in dtype_counts.items():
        print(f"   {dtype}: {count} columns")
    
    # Missing values analysis
    print(f"\n[MISSING VALUES] MISSING VALUES ANALYSIS")
    missing = df.isnull().sum()
    missing_pct = (missing / len(df)) * 100
    
    # Columns with missing values
    cols_with_missing = missing[missing > 0].sort_values(ascending=False)
    
    if len(cols_with_missing) > 0:
        print(f"\n   Columns with missing values: {len(cols_with_missing)}")
        print(f"\n   Top 20 columns with most missing values:")
        print(f"   {'Column Name':<50} {'Missing':<12} {'Percentage':<12}")
        print(f"   {'-'*50} {'-'*12} {'-'*12}")
        for col, count in cols_with_missing.head(20).items():
            pct = missing_pct[col]
            print(f"   {col:<50} {count:<12,} {pct:>10.2f}%")
    else:
        print("   [OK] No missing values found!")
    
    # Data type issues
    print(f"\n[DATA TYPE ANALYSIS]")
    
    # Check for numeric columns that might be strings
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    object_cols = df.select_dtypes(include=['object']).columns
    
    print(f"   Numeric columns: {len(numeric_cols)}")
    print(f"   Object/string columns: {len(object_cols)}")
    
    # Check for columns that look numeric but are objects
    print(f"\n   Potential data type issues:")
    issues_found = False
    for col in object_cols:
        # Try to convert to numeric
        numeric_series = pd.to_numeric(df[col], errors='coerce')
        non_null_count = numeric_series.notna().sum()
        if non_null_count > len(df) * 0.5:  # More than 50% can be converted
            print(f"   [WARNING] '{col}' is object type but {non_null_count:,}/{len(df):,} values are numeric")
            issues_found = True
    
    if not issues_found:
        print("   [OK] No obvious data type issues found")
    
    # Check for duplicate rows
    print(f"\n[DUPLICATE ANALYSIS]")
    duplicate_rows = df.duplicated().sum()
    if duplicate_rows > 0:
        print(f"   [WARNING] Found {duplicate_rows:,} duplicate rows")
    else:
        print(f"   [OK] No duplicate rows found")
    
    # Check for duplicate institution IDs
    if 'institution_id' in df.columns or 'unit_id' in df.columns:
        id_col = 'institution_id' if 'institution_id' in df.columns else 'unit_id'
        duplicate_ids = df[id_col].duplicated().sum()
        if duplicate_ids > 0:
            print(f"   [WARNING] Found {duplicate_ids:,} duplicate {id_col} values")
        else:
            print(f"   [OK] All {id_col} values are unique")
    
    # Check for columns with all missing values
    print(f"\n[EMPTY COLUMNS]")
    empty_cols = df.columns[df.isnull().all()].tolist()
    if empty_cols:
        print(f"   [WARNING] Found {len(empty_cols)} completely empty columns:")
        for col in empty_cols:
            print(f"      - {col}")
    else:
        print("   [OK] No completely empty columns")
    
    # Summary statistics for numeric columns
    print(f"\n[NUMERIC COLUMNS] NUMERIC COLUMNS SUMMARY")
    if len(numeric_cols) > 0:
        print(f"   Analyzing {len(numeric_cols)} numeric columns...")
        # Show columns with high missing rates
        numeric_missing = missing[numeric_cols]
        high_missing_numeric = numeric_missing[(numeric_missing / len(df)) > 0.5].sort_values(ascending=False)
        if len(high_missing_numeric) > 0:
            print(f"\n   Numeric columns with >50% missing values:")
            for col, count in high_missing_numeric.head(10).items():
                pct = (count / len(df)) * 100
                print(f"      - {col}: {count:,} missing ({pct:.1f}%)")
    
    # Key columns check
    print(f"\n[KEY COLUMNS] KEY COLUMNS CHECK")
    key_cols = ['institution_id', 'unit_id', 'institution_name', 'state', 'state_abbreviation']
    found_key_cols = [col for col in key_cols if col in df.columns]
    print(f"   Key columns found: {found_key_cols}")
    for col in found_key_cols:
        missing_count = df[col].isnull().sum()
        if missing_count > 0:
            print(f"   [WARNING] '{col}' has {missing_count:,} missing values")
        else:
            print(f"   [OK] '{col}' has no missing values")
    
    # Overall quality score
    print(f"\n[QUALITY SCORE] OVERALL QUALITY SCORE")
    total_cells = df.shape[0] * df.shape[1]
    missing_cells = df.isnull().sum().sum()
    completeness = (1 - missing_cells / total_cells) * 100
    
    print(f"   Data completeness: {completeness:.2f}%")
    print(f"   Missing cells: {missing_cells:,} / {total_cells:,}")
    
    # Quality rating
    if completeness >= 95:
        quality_rating = "Excellent"
    elif completeness >= 85:
        quality_rating = "Good"
    elif completeness >= 70:
        quality_rating = "Fair"
    else:
        quality_rating = "Poor"
    
    print(f"   Quality rating: {quality_rating}")
    
    print("\n" + "=" * 80)
    print("Analysis complete!")
    print("=" * 80)
    
    return {
        'shape': df.shape,
        'missing_summary': cols_with_missing.to_dict() if len(cols_with_missing) > 0 else {},
        'completeness': completeness,
        'quality_rating': quality_rating,
        'duplicate_rows': duplicate_rows,
        'empty_columns': empty_cols
    }


def analyze_duplicate_unit_ids(csv_path: str = "data/master_colleges.csv"):
    """
    Analyze duplicate unit_ids to determine if they are:
    1. True duplicate rows (same data)
    2. Same institution with different reports/data
    """
    
    print("=" * 80)
    print("DUPLICATE UNIT_ID ANALYSIS")
    print("=" * 80)
    
    # Load data
    df = pd.read_csv(csv_path)
    
    # Check if unit_id exists
    if 'unit_id' not in df.columns:
        print("[ERROR] 'unit_id' column not found in dataset")
        return
    
    # Find duplicate unit_ids
    duplicate_ids = df[df.duplicated(subset=['unit_id'], keep=False)].sort_values('unit_id')
    unique_unit_ids_with_duplicates = duplicate_ids['unit_id'].unique()
    
    print(f"\n[SUMMARY]")
    print(f"   Total rows: {len(df):,}")
    print(f"   Unique unit_ids: {df['unit_id'].nunique():,}")
    print(f"   unit_ids with duplicates: {len(unique_unit_ids_with_duplicates):,}")
    print(f"   Total rows with duplicate unit_ids: {len(duplicate_ids):,}")
    
    if len(unique_unit_ids_with_duplicates) == 0:
        print("\n[OK] No duplicate unit_ids found!")
        return
    
    # Analyze each duplicate unit_id
    print(f"\n[ANALYSIS] Analyzing duplicate unit_ids...")
    
    true_duplicates = 0
    different_records = 0
    sample_duplicates = []
    
    # Sample analysis - check first 10 duplicate unit_ids in detail
    sample_size = min(10, len(unique_unit_ids_with_duplicates))
    
    for unit_id in unique_unit_ids_with_duplicates[:sample_size]:
        rows = df[df['unit_id'] == unit_id].copy()
        
        if len(rows) > 1:
            # Check if rows are identical (excluding unit_id itself)
            other_cols = [col for col in df.columns if col != 'unit_id']
            
            # Compare rows pairwise
            is_identical = True
            differences = []
            
            for i in range(len(rows)):
                for j in range(i + 1, len(rows)):
                    row1 = rows.iloc[i][other_cols]
                    row2 = rows.iloc[j][other_cols]
                    
                    # Check for differences
                    diff_cols = row1[row1 != row2].index.tolist()
                    if diff_cols:
                        is_identical = False
                        differences.append({
                            'row_pair': (i, j),
                            'different_columns': diff_cols,
                            'num_differences': len(diff_cols)
                        })
            
            if is_identical:
                true_duplicates += 1
                sample_duplicates.append({
                    'unit_id': unit_id,
                    'type': 'true_duplicate',
                    'num_rows': len(rows),
                    'differences': None
                })
            else:
                different_records += 1
                sample_duplicates.append({
                    'unit_id': unit_id,
                    'type': 'different_records',
                    'num_rows': len(rows),
                    'differences': differences[0] if differences else None
                })
    
    # Full analysis - count all duplicates
    print(f"\n[DETAILED ANALYSIS] Sample of {sample_size} duplicate unit_ids:")
    print(f"\n   {'Unit ID':<15} {'Rows':<8} {'Type':<20} {'Details'}")
    print(f"   {'-'*15} {'-'*8} {'-'*20} {'-'*40}")
    
    for sample in sample_duplicates:
        details = ""
        if sample['type'] == 'true_duplicate':
            details = f"Identical rows (true duplicate)"
        elif sample['differences']:
            diff_info = sample['differences']
            details = f"{diff_info['num_differences']} different columns"
            if diff_info['num_differences'] <= 5:
                details += f": {', '.join(diff_info['different_columns'][:5])}"
        
        print(f"   {sample['unit_id']:<15} {sample['num_rows']:<8} {sample['type']:<20} {details}")
    
    # Full dataset analysis
    print(f"\n[FULL DATASET ANALYSIS]")
    
    # Count how many unit_ids have truly identical rows vs different data
    all_true_duplicates = 0
    all_different_records = 0
    
    for unit_id in unique_unit_ids_with_duplicates:
        rows = df[df['unit_id'] == unit_id]
        if len(rows) > 1:
            # Check if all rows are identical (excluding unit_id)
            other_cols = [col for col in df.columns if col != 'unit_id']
            first_row = rows.iloc[0][other_cols]
            
            all_identical = True
            for idx in range(1, len(rows)):
                if not rows.iloc[idx][other_cols].equals(first_row):
                    all_identical = False
                    break
            
            if all_identical:
                all_true_duplicates += 1
            else:
                all_different_records += 1
    
    print(f"   unit_ids with identical rows (true duplicates): {all_true_duplicates:,}")
    print(f"   unit_ids with different data (different reports): {all_different_records:,}")
    
    # Show example of what differs
    print(f"\n[EXAMPLE DIFFERENCES]")
    example_found = False
    for unit_id in unique_unit_ids_with_duplicates[:5]:
        rows = df[df['unit_id'] == unit_id]
        if len(rows) > 1:
            other_cols = [col for col in df.columns if col != 'unit_id']
            first_row = rows.iloc[0]
            second_row = rows.iloc[1]
            
            diff_cols = []
            for col in other_cols:
                if pd.isna(first_row[col]) and pd.isna(second_row[col]):
                    continue
                if first_row[col] != second_row[col]:
                    diff_cols.append(col)
            
            if diff_cols:
                example_found = True
                print(f"\n   Example: unit_id = {unit_id} ({len(rows)} rows)")
                print(f"   Columns that differ: {len(diff_cols)}")
                print(f"   Sample differences:")
                for col in diff_cols[:5]:
                    val1 = first_row[col]
                    val2 = second_row[col]
                    print(f"      - {col}:")
                    print(f"          Row 1: {val1}")
                    print(f"          Row 2: {val2}")
                if len(diff_cols) > 5:
                    print(f"      ... and {len(diff_cols) - 5} more columns")
                break
    
    if not example_found:
        print("   All sampled duplicates appear to be true duplicates (identical rows)")
    
    # Distribution of duplicate counts
    print(f"\n[DUPLICATE DISTRIBUTION]")
    duplicate_counts = df['unit_id'].value_counts()
    duplicate_counts = duplicate_counts[duplicate_counts > 1]
    
    if len(duplicate_counts) > 0:
        print(f"   Distribution of duplicate counts:")
        count_dist = duplicate_counts.value_counts().sort_index()
        for count, num_ids in count_dist.items():
            print(f"      {count} rows per unit_id: {num_ids:,} unit_ids")
    
    # Recommendations
    print(f"\n[RECOMMENDATIONS]")
    if all_true_duplicates > all_different_records:
        print(f"   [WARNING] Most duplicates are true duplicates (identical rows)")
        print(f"   Recommendation: Remove duplicate rows to avoid data leakage")
    elif all_different_records > all_true_duplicates:
        print(f"   [INFO] Most duplicates are different records for same institution")
        print(f"   Recommendation: This is likely intentional (e.g., different years, categories)")
        print(f"   Consider: Add a year/category column or aggregate appropriately")
    else:
        print(f"   [INFO] Mixed: Some true duplicates, some different records")
        print(f"   Recommendation: Review data source to understand why duplicates exist")
    
    print("\n" + "=" * 80)
    print("Duplicate unit_id analysis complete!")
    print("=" * 80)
    
    return {
        'total_duplicate_unit_ids': len(unique_unit_ids_with_duplicates),
        'true_duplicates': all_true_duplicates,
        'different_records': all_different_records,
        'sample_analysis': sample_duplicates
    }


if __name__ == "__main__":
    analyze_data_quality()
    print("\n")
    analyze_duplicate_unit_ids()
