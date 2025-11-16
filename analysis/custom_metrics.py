"""
Custom Metric Analysis

Purpose: Domain-specific analysis functions
"""

import pandas as pd
import numpy as np
from typing import Dict, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def calculate_affordability_impact_score(df: pd.DataFrame) -> pd.Series:
    """
    Calculate affordability impact score (weighted composite).
    
    Args:
        df: Input DataFrame with impact predictions
    
    Returns:
        Series with affordability impact scores
    """
    score_components = []
    
    # Component 1: Tuition change (higher = worse)
    if "tuition_change_dollars" in df.columns:
        tuition_impact = df["tuition_change_dollars"].abs()
        if tuition_impact.max() > 0:
            tuition_normalized = (tuition_impact / tuition_impact.max()) * 100
        else:
            tuition_normalized = pd.Series(0, index=df.index)
        score_components.append(tuition_normalized)
    
    # Component 2: Hours to cover gap (more hours = worse)
    if "hours_to_cover_gap" in df.columns:
        hours_impact = df["hours_to_cover_gap"]
        if hours_impact.max() > 0:
            hours_normalized = (hours_impact / hours_impact.max()) * 100
        else:
            hours_normalized = pd.Series(0, index=df.index)
        score_components.append(hours_normalized)
    
    # Component 3: Enrollment drop (worse for students)
    if "enrollment_change_pct" in df.columns:
        enrollment_impact = df["enrollment_change_pct"].abs() * -1  # Negative change is bad
        if enrollment_impact.max() > 0:
            enrollment_normalized = (enrollment_impact / enrollment_impact.max()) * 100
        else:
            enrollment_normalized = pd.Series(0, index=df.index)
        score_components.append(enrollment_normalized)
    
    # Combine components
    if score_components:
        impact_score = pd.concat(score_components, axis=1).mean(axis=1)
    else:
        impact_score = pd.Series(0, index=df.index)
    
    return impact_score


def equity_gap_analysis(df: pd.DataFrame) -> Dict:
    """
    Compare impacts across demographics (equity gap analysis).
    
    Args:
        df: Input DataFrame
    
    Returns:
        Dict with equity gap metrics
    """
    results = {}
    
    # Compare by minority status
    if "pct_minority" in df.columns and "tuition_change_dollars" in df.columns:
        minority_serving = df[df["pct_minority"] > 50]
        non_minority_serving = df[df["pct_minority"] <= 50]
        
        if len(minority_serving) > 0 and len(non_minority_serving) > 0:
            results["minority_gap"] = {
                "minority_serving_avg_impact": float(minority_serving["tuition_change_dollars"].mean()),
                "non_minority_serving_avg_impact": float(non_minority_serving["tuition_change_dollars"].mean()),
                "gap": float(minority_serving["tuition_change_dollars"].mean() - 
                            non_minority_serving["tuition_change_dollars"].mean())
            }
    
    # Compare by low-income status
    if "pct_low_income" in df.columns and "tuition_change_dollars" in df.columns:
        low_income_serving = df[df["pct_low_income"] > 50]
        high_income_serving = df[df["pct_low_income"] <= 50]
        
        if len(low_income_serving) > 0 and len(high_income_serving) > 0:
            results["income_gap"] = {
                "low_income_serving_avg_impact": float(low_income_serving["tuition_change_dollars"].mean()),
                "high_income_serving_avg_impact": float(high_income_serving["tuition_change_dollars"].mean()),
                "gap": float(low_income_serving["tuition_change_dollars"].mean() - 
                            high_income_serving["tuition_change_dollars"].mean())
            }
    
    return results


def state_vulnerability_ranking(df: pd.DataFrame) -> pd.DataFrame:
    """
    Rank states by vulnerability (which states hit hardest).
    
    Args:
        df: Input DataFrame
    
    Returns:
        DataFrame with state rankings
    """
    if "state" not in df.columns:
        logger.warning("No 'state' column found")
        return pd.DataFrame()
    
    # Aggregate by state
    state_agg = df.groupby("state").agg({
        "tuition_change_dollars": "mean",
        "students_affected": "sum",
        "institution_id": "count"
    }).reset_index()
    
    state_agg.columns = ["state", "avg_tuition_impact", "total_students_affected", "college_count"]
    
    # Calculate vulnerability score (weighted)
    if state_agg["avg_tuition_impact"].max() > 0:
        state_agg["vulnerability_score"] = (
            (state_agg["avg_tuition_impact"] / state_agg["avg_tuition_impact"].max()) * 50 +
            (state_agg["total_students_affected"] / state_agg["total_students_affected"].max()) * 50
        )
    else:
        state_agg["vulnerability_score"] = 0
    
    # Rank by vulnerability
    state_agg = state_agg.sort_values("vulnerability_score", ascending=False)
    state_agg["rank"] = range(1, len(state_agg) + 1)
    
    return state_agg


def institution_resilience_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """
    Analyze which institutions can absorb shocks (resilience analysis).
    
    Args:
        df: Input DataFrame
    
    Returns:
        DataFrame with resilience scores
    """
    resilience_components = []
    
    # Component 1: Large enrollment (more resilient)
    # Try to find enrollment column (could be enrollment or total_enrollment)
    enrollment_col = None
    for col in ["enrollment", "total_enrollment", "total_enroll"]:
        if col in df.columns:
            enrollment_col = col
            break
    
    if enrollment_col:
        if df[enrollment_col].max() > 0:
            enrollment_resilience = (df[enrollment_col] / df[enrollment_col].max()) * 100
        else:
            enrollment_resilience = pd.Series(50, index=df.index)
        resilience_components.append(enrollment_resilience)
    
    # Component 2: Low impact (more resilient)
    if "tuition_change_dollars" in df.columns:
        impact = df["tuition_change_dollars"].abs()
        if impact.max() > 0:
            impact_resilience = (1 - (impact / impact.max())) * 100
        else:
            impact_resilience = pd.Series(100, index=df.index)
        resilience_components.append(impact_resilience)
    
    # Component 3: Institution type (private typically more resilient)
    if "institution_type" in df.columns:
        type_scores = {
            "private": 80,
            "public": 60,
            "community": 40
        }
        type_resilience = df["institution_type"].map(type_scores).fillna(50)
        resilience_components.append(type_resilience)
    
    # Combine components
    if resilience_components:
        df["resilience_score"] = pd.concat(resilience_components, axis=1).mean(axis=1)
    else:
        df["resilience_score"] = 50
    
    # Rank by resilience
    df = df.sort_values("resilience_score", ascending=False)
    df["resilience_rank"] = range(1, len(df) + 1)
    
    return df[["institution_id", "name", "resilience_score", "resilience_rank"]].head(20)


def calculate_custom_metrics(df: pd.DataFrame, output_path: str = None) -> Dict:
    """
    Calculate all custom metrics for a scenario.
    
    Args:
        df: Input DataFrame
        output_path: Optional path to save results
    
    Returns:
        Dict with all custom metrics
    """
    logger.info("Calculating custom metrics...")
    
    results = {}
    
    # Affordability impact score
    df["affordability_impact_score"] = calculate_affordability_impact_score(df)
    results["affordability_impact"] = {
        "mean": float(df["affordability_impact_score"].mean()),
        "median": float(df["affordability_impact_score"].median()),
        "max": float(df["affordability_impact_score"].max())
    }
    
    # Equity gap analysis
    results["equity_gaps"] = equity_gap_analysis(df)
    
    # State vulnerability ranking
    state_ranking = state_vulnerability_ranking(df)
    if not state_ranking.empty:
        results["state_vulnerability"] = state_ranking.to_dict("records")
    
    # Institution resilience
    resilience_df = institution_resilience_analysis(df)
    if not resilience_df.empty:
        results["most_resilient_institutions"] = resilience_df.to_dict("records")
    
    # Save if output path provided
    if output_path:
        import json
        from pathlib import Path
        output_path_obj = Path(output_path)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(results, f, indent=2, default=str)
        logger.info(f"Custom metrics saved to {output_path}")
    
    return results


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        csv_path = sys.argv[1]
        df = pd.read_csv(csv_path)
        metrics = calculate_custom_metrics(df, f"outputs/analysis/{Path(csv_path).stem}_custom_metrics.json")
        print(f"Calculated custom metrics for {len(df)} colleges")

