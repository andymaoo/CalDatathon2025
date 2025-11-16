"""
Model Configuration

Hyperparameters and configuration for all ML models
"""

MODEL_CONFIGS = {
    "tuition": {
        "model_type": "xgb_regressor",
        "target": "tuition_change_pct",
        "hyperparameters": {
            "n_estimators": 200,
            "max_depth": 6,
            "learning_rate": 0.05,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "random_state": 42,
            "n_jobs": -1
        },
        "expected_r2": 0.75,
        "expected_mae": 2.0
    },
    "enrollment": {
        "model_type": "lgbm_regressor",
        "target": "enrollment_change_pct",
        "hyperparameters": {
            "n_estimators": 150,
            "max_depth": 5,
            "num_leaves": 31,
            "learning_rate": 0.05,
            "random_state": 42,
            "n_jobs": -1,
            "verbose": -1
        },
        "expected_r2": 0.70,
        "expected_mae": 3.0
    },
    "grad_rate": {
        "model_type": "rf_regressor",
        "target": "grad_rate_change",
        "hyperparameters": {
            "n_estimators": 200,
            "max_depth": 8,
            "min_samples_split": 5,
            "random_state": 42,
            "n_jobs": -1
        },
        "expected_r2": 0.60,
        "expected_mae": 1.0
    },
    "equity": {
        "model_type": "xgb_classifier",
        "target": "equity_risk_class",
        "hyperparameters": {
            "n_estimators": 150,
            "max_depth": 5,
            "learning_rate": 0.05,
            "objective": "multi:softmax",
            "num_class": 3,
            "random_state": 42,
            "n_jobs": -1
        },
        "expected_accuracy": 0.75,
        "class_labels": ["Low", "Medium", "High"]
    }
}

# Feature engineering configuration
FEATURE_CONFIG = {
    "interaction_features": [
        ("funding_change_pct", "pct_low_income"),
        ("baseline_tuition", "pct_minority"),
        ("min_wage_change", "childcare_subsidy"),
        ("enrollment", "pct_low_income")
    ],
    "binary_flags": {
        "high_risk_institution": {
            "condition": lambda df: (df.get("pct_low_income", 0) > 50) & (df.get("baseline_grad_rate", 100) < 50)
        },
        "minority_serving": {
            "condition": lambda df: df.get("pct_minority", 0) > 50
        },
        "small_enrollment": {
            "condition": lambda df: df.get("enrollment", 10000) < 2000
        }
    },
    "categorical_columns": ["state", "institution_type"],
    "numeric_columns": [
        "funding_change_pct",
        "min_wage_change",
        "childcare_subsidy",
        "tuition_cap_pct",
        "enrollment",
        "pct_low_income",
        "pct_minority",
        "baseline_tuition",
        "baseline_grad_rate"
    ]
}

# Training configuration
TRAINING_CONFIG = {
    "test_size": 0.2,
    "random_seed": 42,
    "cv_folds": 5,
    "stratify_by": ["state", "institution_type"]
}

