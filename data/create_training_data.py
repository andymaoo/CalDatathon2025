"""
Synthetic Training Data Generator

Purpose: Generate 1000+ realistic training scenarios using Monte Carlo + economic theory
"""

import pandas as pd
import numpy as np
from pathlib import Path
import os
from typing import Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_synthetic_scenarios(
    master_colleges_df: pd.DataFrame,
    n_scenarios: int = 1000,
    random_seed: int = 42
) -> pd.DataFrame:
    """
    Generate synthetic training scenarios.
    
    Args:
        master_colleges_df: Master colleges dataset
        n_scenarios: Number of scenarios to generate
        random_seed: Random seed for reproducibility
    
    Returns:
        DataFrame with synthetic training data
    """
    np.random.seed(random_seed)
    
    scenarios = []
    
    # Sample colleges (with replacement to get n_scenarios)
    college_indices = np.random.choice(len(master_colleges_df), size=n_scenarios, replace=True)
    
    for i, college_idx in enumerate(college_indices):
        college = master_colleges_df.iloc[college_idx].copy()
        
        # Sample policy parameters from distributions
        funding_change_pct = np.random.uniform(-20, 10)  # More cuts than increases
        min_wage_change = np.random.uniform(-2, 5)  # Wage changes in dollars
        childcare_subsidy = np.random.uniform(0, 5000)  # Subsidy amount
        tuition_cap_pct = np.random.uniform(-10, 20)  # Tuition cap changes
        
        # Get college attributes
        baseline_tuition = college.get("net_price", college.get("tuition", 10000))
        if pd.isna(baseline_tuition) or baseline_tuition <= 0:
            baseline_tuition = 10000  # Default
        
        # Try multiple column names for enrollment
        enrollment = college.get("enrollment") or college.get("total_enrollment") or college.get("total_enroll")
        if pd.isna(enrollment) or enrollment <= 0:
            enrollment = 5000  # Default
        
        pct_low_income = college.get("pct_low_income", college.get("pell_pct", 30))
        if pd.isna(pct_low_income):
            pct_low_income = 30  # Default
        
        pct_minority = college.get("pct_minority", 25)
        if pd.isna(pct_minority):
            pct_minority = 25  # Default
        
        baseline_grad_rate = college.get("grad_rate", college.get("graduation_rate", 60))
        if pd.isna(baseline_grad_rate):
            baseline_grad_rate = 60  # Default
        
        institution_type = college.get("institution_type", "public")
        state = college.get("state", "CA")
        
        # Calculate outcomes using economic elasticities
        
        # 1. Tuition Change
        # Public colleges: 60% dependent on state funding
        # Private colleges: 20% dependent
        if institution_type.lower() in ["public", "community"]:
            funding_dependency = 0.6
        else:
            funding_dependency = 0.2
        
        # Base tuition change from funding
        tuition_change_from_funding = funding_change_pct * funding_dependency
        
        # Add effect of tuition cap
        if tuition_cap_pct != 0:
            # Cap limits the change
            if tuition_change_from_funding > tuition_cap_pct:
                tuition_change_pct = tuition_cap_pct
            else:
                tuition_change_pct = tuition_change_from_funding
        else:
            tuition_change_pct = tuition_change_from_funding
        
        # Add noise
        tuition_change_pct += np.random.normal(0, 1.5)  # σ = 1.5%
        
        # 2. Enrollment Change
        # Every $1000 tuition increase → 2-5% enrollment drop for low-income students
        tuition_change_dollars = (baseline_tuition * tuition_change_pct) / 100
        enrollment_elasticity = np.random.uniform(0.02, 0.05)  # Per $1000
        enrollment_change_pct = -(tuition_change_dollars / 1000) * enrollment_elasticity * 100
        
        # Min wage increase helps (reduces enrollment drop)
        if min_wage_change > 0:
            enrollment_boost = min_wage_change * 0.5  # Each $1 wage increase = 0.5% enrollment boost
            enrollment_change_pct += enrollment_boost
        
        # Childcare subsidy helps (especially for student-parents)
        if childcare_subsidy > 0:
            enrollment_boost = (childcare_subsidy / 1000) * 0.3  # Each $1000 = 0.3% boost
            enrollment_change_pct += enrollment_boost
        
        # Add noise
        enrollment_change_pct += np.random.normal(0, 2.0)  # σ = 2%
        
        # 3. Graduation Rate Change
        # Financial stress → 1-3% graduation rate decline
        affordability_stress = abs(tuition_change_dollars) / baseline_tuition if baseline_tuition > 0 else 0
        grad_rate_change = -affordability_stress * np.random.uniform(1, 3)
        
        # Min wage and childcare help (reduce stress)
        if min_wage_change > 0:
            grad_rate_change += min_wage_change * 0.1  # Each $1 = 0.1% boost
        if childcare_subsidy > 0:
            grad_rate_change += (childcare_subsidy / 1000) * 0.05  # Each $1000 = 0.05% boost
        
        # Add noise
        grad_rate_change += np.random.normal(0, 1.0)  # σ = 1%
        
        # 4. Equity Risk Score
        # Composite based on demographics + affordability stress
        demographic_risk = (pct_low_income / 100) * 40 + (pct_minority / 100) * 30
        financial_stress_risk = min(abs(tuition_change_dollars) / 2000, 1) * 30  # Max $2000 impact = 30 points
        
        equity_risk_score = demographic_risk + financial_stress_risk
        equity_risk_score = min(100, max(0, equity_risk_score))  # Clip to 0-100
        
        # Classify equity risk
        if equity_risk_score <= 33:
            equity_risk_class = "Low"
        elif equity_risk_score <= 66:
            equity_risk_class = "Medium"
        else:
            equity_risk_class = "High"
        
        # Create scenario row
        scenario = {
            # Features (inputs)
            "funding_change_pct": funding_change_pct,
            "min_wage_change": min_wage_change,
            "childcare_subsidy": childcare_subsidy,
            "tuition_cap_pct": tuition_cap_pct,
            "state": state,
            "institution_type": institution_type,
            "enrollment": enrollment,
            "pct_low_income": pct_low_income,
            "pct_minority": pct_minority,
            "baseline_tuition": baseline_tuition,
            "baseline_grad_rate": baseline_grad_rate,
            
            # Targets (outputs)
            "tuition_change_pct": tuition_change_pct,
            "enrollment_change_pct": enrollment_change_pct,
            "grad_rate_change": grad_rate_change,
            "equity_risk_score": equity_risk_score,
            "equity_risk_class": equity_risk_class
        }
        
        scenarios.append(scenario)
        
        if (i + 1) % 100 == 0:
            logger.info(f"Generated {i + 1}/{n_scenarios} scenarios...")
    
    training_df = pd.DataFrame(scenarios)
    logger.info(f"Generated {len(training_df)} synthetic training scenarios")
    
    return training_df


def main(
    master_colleges_path: str = "data/master_colleges.csv",
    output_path: str = "outputs/training_data.csv",
    n_scenarios: int = 1000,
    random_seed: int = 42
):
    """
    Main function to generate training data.
    
    Args:
        master_colleges_path: Path to master colleges CSV
        output_path: Output path for training data
        n_scenarios: Number of scenarios to generate
        random_seed: Random seed
    """
    # Load master colleges
    if not Path(master_colleges_path).exists():
        logger.error(f"Master colleges file not found: {master_colleges_path}")
        logger.info("Please run data/build_master_colleges.py first")
        return
    
    logger.info(f"Loading master colleges from {master_colleges_path}...")
    master_df = pd.read_csv(master_colleges_path)
    logger.info(f"Loaded {len(master_df)} colleges")
    
    # Generate synthetic scenarios
    logger.info(f"Generating {n_scenarios} synthetic training scenarios...")
    training_df = generate_synthetic_scenarios(master_df, n_scenarios, random_seed)
    
    # Save training data
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    training_df.to_csv(output_path, index=False)
    logger.info(f"Training data saved to {output_path}")
    
    # Print summary statistics
    logger.info("\nTraining Data Summary:")
    logger.info(f"Total scenarios: {len(training_df)}")
    logger.info(f"\nTarget Variable Statistics:")
    logger.info(f"Tuition Change: mean={training_df['tuition_change_pct'].mean():.2f}%, std={training_df['tuition_change_pct'].std():.2f}%")
    logger.info(f"Enrollment Change: mean={training_df['enrollment_change_pct'].mean():.2f}%, std={training_df['enrollment_change_pct'].std():.2f}%")
    logger.info(f"Grad Rate Change: mean={training_df['grad_rate_change'].mean():.2f}%, std={training_df['grad_rate_change'].std():.2f}%")
    logger.info(f"\nEquity Risk Distribution:")
    logger.info(training_df['equity_risk_class'].value_counts().to_string())


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate synthetic training data")
    parser.add_argument("--master-colleges", default="data/master_colleges.csv",
                       help="Path to master colleges CSV")
    parser.add_argument("--output", default="outputs/training_data.csv",
                       help="Output path for training data")
    parser.add_argument("--n-scenarios", type=int, default=1000,
                       help="Number of scenarios to generate")
    parser.add_argument("--seed", type=int, default=42,
                       help="Random seed")
    
    args = parser.parse_args()
    main(
        master_colleges_path=args.master_colleges,
        output_path=args.output,
        n_scenarios=args.n_scenarios,
        random_seed=args.seed
    )

