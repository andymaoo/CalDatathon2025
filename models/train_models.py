"""
Model Training Script

Purpose: Train 4 specialized ML models with evaluation and SHAP
"""

import pandas as pd
import numpy as np
from pathlib import Path
import joblib
import json
from sklearn.metrics import (
    r2_score, mean_absolute_error, mean_squared_error,
    accuracy_score, f1_score, classification_report, confusion_matrix
)
from sklearn.model_selection import cross_val_score
import xgboost as xgb
import lightgbm as lgb
from sklearn.ensemble import RandomForestRegressor
import shap
import matplotlib.pyplot as plt
import logging

from models.model_config import MODEL_CONFIGS, TRAINING_CONFIG
from models.feature_engineering import (
    prepare_features, split_data, save_preprocessing_artifacts
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def train_tuition_model(X_train, y_train, X_test, y_test, config):
    """Train XGBoost regressor for tuition change prediction."""
    logger.info("Training Tuition Change Model (XGBoost)...")
    
    model = xgb.XGBRegressor(**config["hyperparameters"])
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    
    logger.info(f"R² Score: {r2:.4f}")
    logger.info(f"MAE: {mae:.4f}%")
    logger.info(f"RMSE: {rmse:.4f}%")
    
    # Cross-validation
    cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring='r2')
    logger.info(f"CV R² (mean ± std): {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
    
    # SHAP values
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_test[:100])  # Sample for speed
    
    # Summary plot
    plt.figure(figsize=(10, 8))
    shap.summary_plot(shap_values, X_test[:100], show=False, plot_type="bar")
    plt.tight_layout()
    plt.savefig("outputs/visualizations/tuition_shap_summary.png", dpi=150, bbox_inches='tight')
    plt.close()
    logger.info("Saved SHAP summary plot")
    
    return model, {
        "r2": float(r2),
        "mae": float(mae),
        "rmse": float(rmse),
        "cv_r2_mean": float(cv_scores.mean()),
        "cv_r2_std": float(cv_scores.std())
    }


def train_enrollment_model(X_train, y_train, X_test, y_test, config):
    """Train LightGBM regressor for enrollment change prediction."""
    logger.info("Training Enrollment Change Model (LightGBM)...")
    
    model = lgb.LGBMRegressor(**config["hyperparameters"])
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    
    logger.info(f"R² Score: {r2:.4f}")
    logger.info(f"MAE: {mae:.4f}%")
    logger.info(f"RMSE: {rmse:.4f}%")
    
    # Cross-validation
    cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring='r2')
    logger.info(f"CV R² (mean ± std): {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
    
    return model, {
        "r2": float(r2),
        "mae": float(mae),
        "rmse": float(rmse),
        "cv_r2_mean": float(cv_scores.mean()),
        "cv_r2_std": float(cv_scores.std())
    }


def train_grad_rate_model(X_train, y_train, X_test, y_test, config):
    """Train Random Forest regressor for graduation rate change prediction."""
    logger.info("Training Graduation Rate Model (Random Forest)...")
    
    model = RandomForestRegressor(**config["hyperparameters"])
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    
    logger.info(f"R² Score: {r2:.4f}")
    logger.info(f"MAE: {mae:.4f}%")
    logger.info(f"RMSE: {rmse:.4f}%")
    
    # Cross-validation
    cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring='r2')
    logger.info(f"CV R² (mean ± std): {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
    
    return model, {
        "r2": float(r2),
        "mae": float(mae),
        "rmse": float(rmse),
        "cv_r2_mean": float(cv_scores.mean()),
        "cv_r2_std": float(cv_scores.std())
    }


def train_equity_model(X_train, y_train, X_test, y_test, config):
    """Train XGBoost classifier for equity risk classification."""
    logger.info("Training Equity Risk Model (XGBoost Classifier)...")
    
    model = xgb.XGBClassifier(**config["hyperparameters"])
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, average='weighted')
    
    logger.info(f"Accuracy: {accuracy:.4f}")
    logger.info(f"F1 Score (weighted): {f1:.4f}")
    
    # Classification report - handle cases where not all classes are present
    unique_labels = sorted(list(set(y_test) | set(y_pred)))
    available_labels = [config["class_labels"][i] for i in unique_labels if i < len(config["class_labels"])]
    report = classification_report(y_test, y_pred, labels=unique_labels, target_names=available_labels, output_dict=True, zero_division=0)
    logger.info("\nClassification Report:")
    logger.info(classification_report(y_test, y_pred, labels=unique_labels, target_names=available_labels, zero_division=0))
    
    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred)
    logger.info(f"\nConfusion Matrix:\n{cm}")
    
    # Cross-validation
    cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring='accuracy')
    logger.info(f"CV Accuracy (mean ± std): {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
    
    return model, {
        "accuracy": float(accuracy),
        "f1_weighted": float(f1),
        "classification_report": report,
        "confusion_matrix": cm.tolist(),
        "cv_accuracy_mean": float(cv_scores.mean()),
        "cv_accuracy_std": float(cv_scores.std())
    }


def main(
    training_data_path: str = "outputs/training_data.csv",
    output_dir: str = "models/saved_models"
):
    """
    Main training function.
    
    Args:
        training_data_path: Path to training data CSV
        output_dir: Directory to save models
    """
    # Load training data
    logger.info(f"Loading training data from {training_data_path}...")
    df = pd.read_csv(training_data_path)
    logger.info(f"Loaded {len(df)} training samples")
    
    # Prepare features
    logger.info("Preparing features...")
    X, scaler, encoders = prepare_features(df, fit=True)
    
    # Save preprocessing artifacts
    save_preprocessing_artifacts(scaler, encoders, output_dir)
    
    # Train each model
    models = {}
    metrics = {}
    
    for model_name, config in MODEL_CONFIGS.items():
        target = config["target"]
        
        if target not in df.columns:
            logger.warning(f"Target {target} not found. Skipping {model_name} model.")
            continue
        
        y = df[target]
        
        # For classification, encode labels
        if config["model_type"] == "xgb_classifier":
            from sklearn.preprocessing import LabelEncoder
            label_encoder = LabelEncoder()
            y_encoded = label_encoder.fit_transform(y)
            joblib.dump(label_encoder, Path(output_dir) / f"{model_name}_label_encoder.pkl")
        else:
            y_encoded = y
        
        # Split data
        stratify = None
        if TRAINING_CONFIG.get("stratify_by") and model_name == "equity":
            # Create stratification variable for equity model
            stratify = y_encoded
        
        X_train, X_test, y_train, y_test = split_data(
            X, y_encoded,
            test_size=TRAINING_CONFIG["test_size"],
            random_seed=TRAINING_CONFIG["random_seed"],
            stratify=stratify
        )
        
        # Train model
        if model_name == "tuition":
            model, model_metrics = train_tuition_model(X_train, y_train, X_test, y_test, config)
        elif model_name == "enrollment":
            model, model_metrics = train_enrollment_model(X_train, y_train, X_test, y_test, config)
        elif model_name == "grad_rate":
            model, model_metrics = train_grad_rate_model(X_train, y_train, X_test, y_test, config)
        elif model_name == "equity":
            model, model_metrics = train_equity_model(X_train, y_train, X_test, y_test, config)
        else:
            continue
        
        # Save model
        model_path = Path(output_dir) / f"{model_name}_model.pkl"
        joblib.dump(model, model_path)
        logger.info(f"Saved {model_name} model to {model_path}")
        
        models[model_name] = model
        metrics[model_name] = model_metrics
    
    # Save metadata
    metadata = {
        "models_trained": list(models.keys()),
        "metrics": metrics,
        "training_config": TRAINING_CONFIG,
        "feature_count": X.shape[1]
    }
    
    metadata_path = Path(output_dir) / "model_metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2, default=str)
    logger.info(f"Saved model metadata to {metadata_path}")
    
    logger.info("\n" + "="*50)
    logger.info("Model Training Complete!")
    logger.info("="*50)
    for model_name, model_metrics in metrics.items():
        logger.info(f"\n{model_name.upper()} Model:")
        for metric, value in model_metrics.items():
            if isinstance(value, (int, float)):
                logger.info(f"  {metric}: {value:.4f}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Train ML models")
    parser.add_argument("--training-data", default="outputs/training_data.csv",
                       help="Path to training data CSV")
    parser.add_argument("--output-dir", default="models/saved_models",
                       help="Output directory for models")
    
    args = parser.parse_args()
    
    # Create output directories
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    Path("outputs/visualizations").mkdir(parents=True, exist_ok=True)
    
    main(
        training_data_path=args.training_data,
        output_dir=args.output_dir
    )

