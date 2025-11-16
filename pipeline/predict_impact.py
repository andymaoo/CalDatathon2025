"""
Impact Prediction Pipeline

Purpose: Predict impacts for each college using trained ML models
"""

import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from typing import Dict, List, Optional
import logging
import os

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, will use system env vars

from models.feature_engineering import prepare_features, load_preprocessing_artifacts
from pipeline.extract_bill import process_bill

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def filter_affected_colleges(
    master_df: pd.DataFrame,
    bill_params: Dict,
    affected_states: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Filter colleges affected by the bill.
    
    Args:
        master_df: Master colleges DataFrame
        bill_params: Extracted bill parameters
        affected_states: Optional list of affected states
    
    Returns:
        Filtered DataFrame
    """
    df = master_df.copy()
    
    # Filter by institution type
    affected_types = bill_params.get("affected_types", [])
    if affected_types:
        if "institution_type" in df.columns:
            df = df[df["institution_type"].isin(affected_types)]
        logger.info(f"Filtered to {len(df)} colleges by institution type: {affected_types}")
    
    # Filter by state if specified
    if affected_states and "state" in df.columns:
        df = df[df["state"].isin(affected_states)]
        logger.info(f"Filtered to {len(df)} colleges by state: {affected_states}")
    
    return df


def build_prediction_features(
    colleges_df: pd.DataFrame,
    bill_params: Dict,
    scaler,
    encoders: Dict
) -> pd.DataFrame:
    """
    Build feature matrix for prediction.
    
    Args:
        colleges_df: Filtered colleges DataFrame
        bill_params: Bill parameters
        scaler: Fitted scaler
        encoders: Fitted encoders
    
    Returns:
        Feature matrix
    """
    # Create a copy for feature engineering
    df = colleges_df.copy()
    
    # Add bill parameters to each college
    df["funding_change_pct"] = bill_params.get("funding_change_pct", 0)
    df["min_wage_change"] = bill_params.get("min_wage_change", 0)
    df["childcare_subsidy"] = bill_params.get("childcare_subsidy", 0)
    df["tuition_cap_pct"] = bill_params.get("tuition_cap_pct", 0)
    
    # Ensure required columns exist with defaults
    required_cols = {
        "enrollment": 5000,
        "pct_low_income": 30,
        "pct_minority": 25,
        "baseline_tuition": "net_price",
        "baseline_grad_rate": "grad_rate"
    }
    
    for col, default in required_cols.items():
        if col not in df.columns:
            if isinstance(default, str):
                # Try alternative column name
                if default in df.columns:
                    df[col] = df[default]
                else:
                    df[col] = 0
            else:
                df[col] = default
    
    # Rename columns if needed
    if "baseline_tuition" not in df.columns and "net_price" in df.columns:
        df["baseline_tuition"] = df["net_price"]
    if "baseline_grad_rate" not in df.columns and "grad_rate" in df.columns:
        df["baseline_grad_rate"] = df["grad_rate"]
    
    # Prepare features (same as training)
    from models.feature_engineering import prepare_features
    X, _, _ = prepare_features(df, scaler=scaler, encoders=encoders, fit=False)
    
    return X


def run_predictions(
    colleges_df: pd.DataFrame,
    feature_matrix: pd.DataFrame,
    models_dir: str = "models/saved_models"
) -> pd.DataFrame:
    """
    Run predictions through all 4 models.
    
    Args:
        colleges_df: Colleges DataFrame (for adding predictions)
        feature_matrix: Feature matrix X
        models_dir: Directory containing trained models
    
    Returns:
        DataFrame with predictions added
    """
    models_path = Path(models_dir)
    results_df = colleges_df.copy()
    
    # Load models
    models = {}
    model_names = ["tuition", "enrollment", "grad_rate", "equity"]
    
    for model_name in model_names:
        model_path = models_path / f"{model_name}_model.pkl"
        if model_path.exists():
            models[model_name] = joblib.load(model_path)
            logger.info(f"Loaded {model_name} model")
        else:
            logger.warning(f"Model not found: {model_path}")
    
    # Predict tuition change
    if "tuition" in models:
        results_df["tuition_change_pct"] = models["tuition"].predict(feature_matrix)
        logger.info("Predicted tuition changes")
    
    # Predict enrollment change
    if "enrollment" in models:
        results_df["enrollment_change_pct"] = models["enrollment"].predict(feature_matrix)
        logger.info("Predicted enrollment changes")
    
    # Predict grad rate change
    if "grad_rate" in models:
        results_df["grad_rate_change"] = models["grad_rate"].predict(feature_matrix)
        logger.info("Predicted graduation rate changes")
    
    # Predict equity risk
    if "equity" in models:
        # Load label encoder if needed
        label_encoder_path = models_path / "equity_label_encoder.pkl"
        if label_encoder_path.exists():
            label_encoder = joblib.load(label_encoder_path)
            equity_predictions = models["equity"].predict(feature_matrix)
            results_df["equity_risk_class"] = label_encoder.inverse_transform(equity_predictions)
        else:
            equity_predictions = models["equity"].predict(feature_matrix)
            results_df["equity_risk_class"] = equity_predictions
        logger.info("Predicted equity risk classes")
    
    return results_df


def calculate_derived_metrics(results_df: pd.DataFrame, bill_params: Dict) -> pd.DataFrame:
    """
    Calculate derived metrics (dollars, students affected, hours to cover gap).
    
    Args:
        results_df: DataFrame with predictions
        bill_params: Bill parameters
    
    Returns:
        DataFrame with derived metrics
    """
    df = results_df.copy()
    
    # Tuition change in dollars
    if "baseline_tuition" in df.columns and "tuition_change_pct" in df.columns:
        df["tuition_change_dollars"] = (df["baseline_tuition"] * df["tuition_change_pct"]) / 100
    elif "net_price" in df.columns and "tuition_change_pct" in df.columns:
        df["tuition_change_dollars"] = (df["net_price"] * df["tuition_change_pct"]) / 100
    else:
        df["tuition_change_dollars"] = 0
    
    # Students affected
    if "enrollment" in df.columns and "enrollment_change_pct" in df.columns:
        df["students_affected"] = (df["enrollment"] * abs(df["enrollment_change_pct"])) / 100
    else:
        df["students_affected"] = 0
    
    # Hours to cover gap
    # Get state minimum wage (default to $15 if not available)
    min_wage = bill_params.get("min_wage_change", 0)
    if min_wage == 0:
        # Try to get from state data or use default
        min_wage = 15.0  # Default minimum wage
    
    if "affordability_gap" in df.columns:
        df["hours_to_cover_gap"] = (df["affordability_gap"] + df.get("tuition_change_dollars", 0)) / max(min_wage, 1)
    elif "tuition_change_dollars" in df.columns:
        df["hours_to_cover_gap"] = df["tuition_change_dollars"] / max(min_wage, 1)
    else:
        df["hours_to_cover_gap"] = 0
    
    return df


def aggregate_impact_summary(results_df: pd.DataFrame) -> Dict:
    """
    Generate summary statistics and top-N lists.
    
    Args:
        results_df: DataFrame with predictions
    
    Returns:
        Summary dict
    """
    summary = {
        "total_colleges_affected": len(results_df),
        "total_students_impacted": int(results_df.get("students_affected", 0).sum()) if "students_affected" in results_df.columns else 0,
        "average_tuition_change_pct": float(results_df.get("tuition_change_pct", 0).mean()) if "tuition_change_pct" in results_df.columns else 0,
        "average_tuition_change_dollars": float(results_df.get("tuition_change_dollars", 0).mean()) if "tuition_change_dollars" in results_df.columns else 0,
        "average_enrollment_change_pct": float(results_df.get("enrollment_change_pct", 0).mean()) if "enrollment_change_pct" in results_df.columns else 0,
        "average_grad_rate_change": float(results_df.get("grad_rate_change", 0).mean()) if "grad_rate_change" in results_df.columns else 0,
    }
    
    # Equity risk breakdown
    if "equity_risk_class" in results_df.columns:
        equity_counts = results_df["equity_risk_class"].value_counts().to_dict()
        summary["equity_risk_breakdown"] = equity_counts
        summary["high_risk_colleges"] = equity_counts.get("High", 0)
    else:
        summary["equity_risk_breakdown"] = {}
        summary["high_risk_colleges"] = 0
    
    # Demographic breakdowns
    if "pct_minority" in results_df.columns:
        minority_serving = (results_df["pct_minority"] > 50).sum()
        summary["minority_serving_institutions_affected"] = int(minority_serving)
    
    if "pct_low_income" in results_df.columns:
        low_income_serving = (results_df["pct_low_income"] > 50).sum()
        summary["low_income_serving_institutions_affected"] = int(low_income_serving)
    
    # Top 10 most-affected colleges
    if "tuition_change_dollars" in results_df.columns:
        top_affected = results_df.nlargest(10, "tuition_change_dollars")[
            ["institution_id", "name" if "name" in results_df.columns else results_df.columns[0], "tuition_change_dollars"]
        ].to_dict("records")
        summary["top_10_most_affected"] = top_affected
    
    return summary


def generate_plain_language_summary(
    bill_text_sample: str,
    summary_stats: Dict,
    api_key: Optional[str] = None
) -> str:
    """
    Generate voter-friendly explanation using LLM.
    
    Args:
        bill_text_sample: Sample bill text
        summary_stats: Aggregate summary statistics
        api_key: Anthropic API key
    
    Returns:
        Plain language summary string
    """
    if api_key is None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not api_key:
        logger.warning("Anthropic API key not found. Using template summary.")
        return f"This bill affects {summary_stats.get('total_colleges_affected', 0)} colleges and {summary_stats.get('total_students_impacted', 0):,} students."
    
    try:
        import os
        from anthropic import Anthropic
        
        client = Anthropic(api_key=api_key)
        
        prompt = f"""Write a 2-sentence plain language summary (8th-grade reading level) explaining how this education bill affects college students.

Focus on:
- Personal impact (dollar amounts, not percentages)
- Concrete numbers (how many students, how much money)
- Simple language (no jargon like "appropriations" - say "money" instead)

Bill context: {bill_text_sample[:500]}

Impact statistics:
- Colleges affected: {summary_stats.get('total_colleges_affected', 0)}
- Students impacted: {summary_stats.get('total_students_impacted', 0):,}
- Average tuition change: ${summary_stats.get('average_tuition_change_dollars', 0):,.0f}
- High-risk colleges: {summary_stats.get('high_risk_colleges', 0)}

Write exactly 2 sentences, under 50 words total, focusing on what this means for a first-generation college student:"""

        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )
        
        summary = response.content[0].text.strip()
        logger.info("Generated plain language summary")
        return summary
        
    except Exception as e:
        logger.error(f"LLM summary generation failed: {e}")
        return f"This bill affects {summary_stats.get('total_colleges_affected', 0)} colleges and {summary_stats.get('total_students_impacted', 0):,} students."


def predict_bill_impact(
    bill_pdf_path: str,
    master_colleges_path: str = "data/master_colleges.csv",
    models_dir: str = "models/saved_models",
    affected_states: Optional[List[str]] = None,
    use_box: bool = False,
    box_folder_id: Optional[str] = None
) -> Tuple[pd.DataFrame, Dict]:
    """
    Main function to predict bill impact.
    
    Args:
        bill_pdf_path: Path to bill PDF (or filename if using Box)
        master_colleges_path: Path to master colleges CSV
        models_dir: Directory containing trained models
        affected_states: Optional list of affected states
        use_box: Whether to download bill from Box
        box_folder_id: Box folder ID if using Box
    
    Returns:
        Tuple of (predictions DataFrame, summary dict)
    """
    # Load master colleges
    logger.info(f"Loading master colleges from {master_colleges_path}...")
    master_df = pd.read_csv(master_colleges_path)
    
    # Process bill (download from Box if needed)
    if use_box and box_folder_id:
        from pipeline.box_client import initialize_box_client
        box_client = initialize_box_client()
        if box_client.is_available():
            local_pdf_path = f"bills/temp_{Path(bill_pdf_path).name}"
            if box_client.download_bill_from_box(box_folder_id, bill_pdf_path, local_pdf_path):
                bill_pdf_path = local_pdf_path
    
    # Extract bill parameters
    logger.info("Extracting bill parameters...")
    bill_params = process_bill(bill_pdf_path)
    
    # Filter affected colleges
    logger.info("Filtering affected colleges...")
    affected_colleges = filter_affected_colleges(master_df, bill_params, affected_states)
    
    if len(affected_colleges) == 0:
        logger.warning("No colleges match the bill criteria")
        return pd.DataFrame(), {}
    
    # Load preprocessing artifacts
    logger.info("Loading preprocessing artifacts...")
    scaler, encoders = load_preprocessing_artifacts(models_dir)
    
    # Build features
    logger.info("Building prediction features...")
    feature_matrix = build_prediction_features(affected_colleges, bill_params, scaler, encoders)
    
    # Run predictions
    logger.info("Running predictions...")
    results_df = run_predictions(affected_colleges, feature_matrix, models_dir)
    
    # Calculate derived metrics
    logger.info("Calculating derived metrics...")
    results_df = calculate_derived_metrics(results_df, bill_params)
    
    # Generate summary
    logger.info("Generating impact summary...")
    summary = aggregate_impact_summary(results_df)
    
    # Generate plain language summary
    bill_text = bill_params.get("bill_text_sample", "")
    summary["plain_language_summary"] = generate_plain_language_summary(bill_text, summary)
    
    logger.info("Impact prediction complete!")
    return results_df, summary


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        bill_path = sys.argv[1]
        results, summary = predict_bill_impact(bill_path)
        print(f"\nSummary:")
        print(f"Colleges affected: {summary.get('total_colleges_affected', 0)}")
        print(f"Students impacted: {summary.get('total_students_impacted', 0):,}")
        print(f"\nPlain language summary:")
        print(summary.get('plain_language_summary', ''))

