"""
Custom Analysis Module

Purpose: Domain-specific metric calculations
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def calculate_affordability_stress_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate affordability stress score (composite of gap, wage, hours).
    
    Higher score = more financial stress
    
    Args:
        df: Input DataFrame with affordability metrics
    
    Returns:
        DataFrame with added 'affordability_stress_score' column
    """
    df = df.copy()
    
    # Normalize components (0-100 scale)
    stress_components = []
    
    # Component 1: Affordability gap (higher gap = more stress)
    gap_cols = [col for col in df.columns if "affordability_gap" in col or "gap" in col]
    if gap_cols:
        gap_col = gap_cols[0]
        if df[gap_col].max() > 0:
            gap_normalized = (df[gap_col] / df[gap_col].max()) * 100
        else:
            gap_normalized = pd.Series(0, index=df.index)
        stress_components.append(gap_normalized)
    
    # Component 2: Hours to cover gap (more hours = more stress)
    hours_cols = [col for col in df.columns if "hours" in col.lower() and "cover" in col.lower()]
    if hours_cols:
        hours_col = hours_cols[0]
        if df[hours_col].max() > 0:
            hours_normalized = (df[hours_col] / df[hours_col].max()) * 100
        else:
            hours_normalized = pd.Series(0, index=df.index)
        stress_components.append(hours_normalized)
    
    # Component 3: Low wage relative to cost (lower wage/cost ratio = more stress)
    wage_cols = [col for col in df.columns if "wage" in col.lower() or "min_wage" in col.lower()]
    cost_cols = [col for col in df.columns if "net_price" in col or "cost" in col.lower()]
    
    if wage_cols and cost_cols:
        wage_col = wage_cols[0]
        cost_col = cost_cols[0]
        wage_cost_ratio = df[wage_col] / (df[cost_col] + 1)  # +1 to avoid division by zero
        if wage_cost_ratio.max() > 0:
            # Invert: lower ratio = higher stress
            wage_stress = (1 - (wage_cost_ratio / wage_cost_ratio.max())) * 100
        else:
            wage_stress = pd.Series(50, index=df.index)  # Neutral if no data
        stress_components.append(wage_stress)
    
    # Combine components (weighted average)
    if stress_components:
        df["affordability_stress_score"] = pd.concat(stress_components, axis=1).mean(axis=1)
        df["affordability_stress_score"] = df["affordability_stress_score"].clip(0, 100)
    else:
        df["affordability_stress_score"] = 0
        logger.warning("No affordability components found. Setting stress score to 0.")
    
    return df


def calculate_equity_risk_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate equity risk indicators (demographics + financial stress).
    
    Args:
        df: Input DataFrame
    
    Returns:
        DataFrame with added equity risk columns
    """
    df = df.copy()
    
    # Binary flags
    # High low-income percentage
    low_income_cols = [col for col in df.columns if "low_income" in col or "pell" in col.lower()]
    if low_income_cols:
        low_income_col = low_income_cols[0]
        df["high_low_income"] = (df[low_income_col] > 50).astype(int)
    else:
        df["high_low_income"] = 0
    
    # High minority percentage
    minority_cols = [col for col in df.columns if "minority" in col or "pct_minority" in col]
    if minority_cols:
        minority_col = minority_cols[0]
        df["high_minority"] = (df[minority_col] > 50).astype(int)
    else:
        df["high_minority"] = 0
    
    # Low graduation rate
    grad_rate_cols = [col for col in df.columns if "grad_rate" in col or "graduation_rate" in col]
    if grad_rate_cols:
        grad_rate_col = grad_rate_cols[0]
        df["low_grad_rate"] = (df[grad_rate_col] < 50).astype(int)
    else:
        df["low_grad_rate"] = 0
    
    # High affordability stress
    if "affordability_stress_score" in df.columns:
        df["high_stress"] = (df["affordability_stress_score"] > 70).astype(int)
    else:
        df["high_stress"] = 0
    
    # Composite equity risk score (0-100)
    risk_factors = ["high_low_income", "high_minority", "low_grad_rate", "high_stress"]
    df["equity_risk_score"] = df[risk_factors].sum(axis=1) * 25  # Each factor = 25 points
    
    # Equity risk class
    df["equity_risk_class"] = pd.cut(
        df["equity_risk_score"],
        bins=[-1, 33, 66, 100],
        labels=["Low", "Medium", "High"]
    )
    
    return df


def calculate_institutional_resilience_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate institutional resilience score (enrollment size, endowment, funding dependency).
    
    Higher score = more resilient to shocks
    
    Args:
        df: Input DataFrame
    
    Returns:
        DataFrame with added 'resilience_score' column
    """
    df = df.copy()
    
    resilience_components = []
    
    # Component 1: Enrollment size (larger = more resilient)
    enrollment_cols = [col for col in df.columns if "enrollment" in col.lower()]
    if enrollment_cols:
        enrollment_col = enrollment_cols[0]
        if df[enrollment_col].max() > 0:
            enrollment_normalized = (df[enrollment_col] / df[enrollment_col].max()) * 100
        else:
            enrollment_normalized = pd.Series(50, index=df.index)
        resilience_components.append(enrollment_normalized)
    
    # Component 2: Institution type (private typically more resilient due to diverse funding)
    if "institution_type" in df.columns:
        type_scores = {
            "private": 80,
            "public": 60,
            "community": 40,
            "unknown": 50
        }
        type_resilience = df["institution_type"].map(type_scores).fillna(50)
        resilience_components.append(type_resilience)
    
    # Component 3: Low funding dependency (if we have funding data)
    funding_cols = [col for col in df.columns if "funding" in col.lower() and "dependency" in col.lower()]
    if funding_cols:
        funding_col = funding_cols[0]
        # Lower dependency = higher resilience
        if df[funding_col].max() > 0:
            funding_resilience = (1 - (df[funding_col] / df[funding_col].max())) * 100
        else:
            funding_resilience = pd.Series(50, index=df.index)
        resilience_components.append(funding_resilience)
    
    # Combine components
    if resilience_components:
        df["resilience_score"] = pd.concat(resilience_components, axis=1).mean(axis=1)
        df["resilience_score"] = df["resilience_score"].clip(0, 100)
    else:
        df["resilience_score"] = 50  # Neutral if no data
        logger.warning("No resilience components found. Setting resilience score to 50.")
    
    return df


def calculate_state_level_aggregations(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate state-level aggregations (average impacts, total students affected).
    
    Args:
        df: Input DataFrame with college-level data
    
    Returns:
        DataFrame with state-level aggregations
    """
    if "state" not in df.columns:
        logger.warning("No 'state' column found. Cannot aggregate by state.")
        return pd.DataFrame()
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    numeric_cols = [col for col in numeric_cols if col != "institution_id"]
    
    agg_dict = {}
    for col in numeric_cols:
        if "enrollment" in col.lower() or "students" in col.lower():
            agg_dict[col] = "sum"  # Sum for counts
        else:
            agg_dict[col] = "mean"  # Average for rates/percentages
    
    state_agg = df.groupby("state").agg(agg_dict).reset_index()
    
    # Add count of institutions per state
    state_agg["institution_count"] = df.groupby("state").size().values
    
    return state_agg


def enhance_master_colleges(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply all custom analysis functions to enhance master colleges dataset.
    
    Args:
        df: Input master colleges DataFrame
    
    Returns:
        Enhanced DataFrame with all derived features
    """
    logger.info("Calculating custom metrics...")
    
    # Calculate all custom metrics
    df = calculate_affordability_stress_score(df)
    df = calculate_equity_risk_indicators(df)
    df = calculate_institutional_resilience_score(df)
    
    logger.info("Custom analysis complete. Added derived features.")
    return df


if __name__ == "__main__":
    # Example usage
    import sys
    if len(sys.argv) > 1:
        csv_path = sys.argv[1]
        df = pd.read_csv(csv_path)
        enhanced_df = enhance_master_colleges(df)
        output_path = csv_path.replace(".csv", "_enhanced.csv")
        enhanced_df.to_csv(output_path, index=False)
        print(f"Enhanced dataset saved to {output_path}")
        print(f"New columns: {[col for col in enhanced_df.columns if col not in df.columns]}")

