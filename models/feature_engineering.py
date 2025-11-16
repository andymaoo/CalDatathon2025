"""
Feature Engineering Module

Purpose: Create interaction features, encode categoricals, scale numeric features
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
import joblib
from pathlib import Path
from typing import Tuple, Dict, Optional
import logging
from model_config import FEATURE_CONFIG

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_interaction_features(df: pd.DataFrame, interaction_pairs: list) -> pd.DataFrame:
    """
    Create interaction features.
    
    Args:
        df: Input DataFrame
        interaction_pairs: List of (col1, col2) tuples
    
    Returns:
        DataFrame with interaction features added
    """
    df = df.copy()
    
    for col1, col2 in interaction_pairs:
        if col1 in df.columns and col2 in df.columns:
            interaction_name = f"{col1}_x_{col2}"
            df[interaction_name] = df[col1] * df[col2]
            logger.debug(f"Created interaction: {interaction_name}")
        else:
            logger.warning(f"Cannot create interaction {col1}_x_{col2}: missing columns")
    
    return df


def create_binary_flags(df: pd.DataFrame, flag_configs: Dict) -> pd.DataFrame:
    """
    Create binary risk flags.
    
    Args:
        df: Input DataFrame
        flag_configs: Dict mapping flag names to condition functions
    
    Returns:
        DataFrame with binary flags added
    """
    df = df.copy()
    
    for flag_name, config in flag_configs.items():
        condition_func = config["condition"]
        try:
            df[flag_name] = condition_func(df).astype(int)
            logger.debug(f"Created binary flag: {flag_name}")
        except Exception as e:
            logger.warning(f"Error creating flag {flag_name}: {e}")
            df[flag_name] = 0
    
    return df


def encode_categoricals(
    df: pd.DataFrame,
    categorical_cols: list,
    encoders: Optional[Dict] = None,
    fit: bool = True
) -> Tuple[pd.DataFrame, Dict]:
    """
    Label encode categorical columns.
    
    Args:
        df: Input DataFrame
        categorical_cols: List of categorical column names
        encoders: Optional pre-fitted encoders dict
        fit: Whether to fit new encoders
    
    Returns:
        Tuple of (encoded DataFrame, encoders dict)
    """
    df = df.copy()
    
    if encoders is None:
        encoders = {}
    
    for col in categorical_cols:
        if col not in df.columns:
            logger.warning(f"Column {col} not found. Skipping encoding.")
            continue
        
        if col not in encoders:
            encoders[col] = LabelEncoder()
        
        if fit:
            # Handle missing values
            df[col] = df[col].fillna("Unknown")
            encoders[col].fit(df[col])
        
        df[col + "_encoded"] = encoders[col].transform(df[col])
        logger.debug(f"Encoded {col} -> {col}_encoded")
    
    return df, encoders


def prepare_features(
    df: pd.DataFrame,
    config: Optional[Dict] = None,
    scaler: Optional[StandardScaler] = None,
    encoders: Optional[Dict] = None,
    fit: bool = True
) -> Tuple[pd.DataFrame, StandardScaler, Dict]:
    """
    Complete feature engineering pipeline.
    
    Args:
        df: Input DataFrame
        config: Feature configuration dict
        scaler: Optional pre-fitted scaler
        encoders: Optional pre-fitted encoders
        fit: Whether to fit scaler/encoders
    
    Returns:
        Tuple of (feature DataFrame, scaler, encoders)
    """
    if config is None:
        from model_config import FEATURE_CONFIG
        config = FEATURE_CONFIG
    
    df = df.copy()
    
    # Create interaction features
    if "interaction_features" in config:
        df = create_interaction_features(df, config["interaction_features"])
    
    # Create binary flags
    if "binary_flags" in config:
        df = create_binary_flags(df, config["binary_flags"])
    
    # Encode categoricals
    if "categorical_columns" in config:
        df, encoders = encode_categoricals(
            df,
            config["categorical_columns"],
            encoders=encoders,
            fit=fit
        )
    
    # Select feature columns
    feature_cols = []
    
    # Add numeric columns
    if "numeric_columns" in config:
        feature_cols.extend([col for col in config["numeric_columns"] if col in df.columns])
    
    # Add interaction features
    if "interaction_features" in config:
        for col1, col2 in config["interaction_features"]:
            interaction_name = f"{col1}_x_{col2}"
            if interaction_name in df.columns:
                feature_cols.append(interaction_name)
    
    # Add binary flags
    if "binary_flags" in config:
        feature_cols.extend(config["binary_flags"].keys())
    
    # Add encoded categoricals
    if "categorical_columns" in config:
        for col in config["categorical_columns"]:
            encoded_col = col + "_encoded"
            if encoded_col in df.columns:
                feature_cols.append(encoded_col)
    
    # Extract feature matrix
    X = df[feature_cols].copy()
    
    # Handle missing values
    X = X.fillna(0)
    
    # Scale numeric features
    if scaler is None:
        scaler = StandardScaler()
    
    if fit:
        X_scaled = pd.DataFrame(
            scaler.fit_transform(X),
            columns=X.columns,
            index=X.index
        )
    else:
        X_scaled = pd.DataFrame(
            scaler.transform(X),
            columns=X.columns,
            index=X.index
        )
    
    logger.info(f"Prepared {len(feature_cols)} features. Shape: {X_scaled.shape}")
    
    return X_scaled, scaler, encoders


def split_data(
    X: pd.DataFrame,
    y: pd.Series,
    test_size: float = 0.2,
    random_seed: int = 42,
    stratify: Optional[pd.Series] = None
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """
    Split data into train/test sets.
    
    Args:
        X: Feature matrix
        y: Target variable
        test_size: Proportion for test set
        random_seed: Random seed
        stratify: Optional stratification variable
    
    Returns:
        Tuple of (X_train, X_test, y_train, y_test)
    """
    if stratify is not None:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_seed, stratify=stratify
        )
    else:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_seed
        )
    
    logger.info(f"Train set: {len(X_train)} samples, Test set: {len(X_test)} samples")
    return X_train, X_test, y_train, y_test


def save_preprocessing_artifacts(
    scaler: StandardScaler,
    encoders: Dict,
    output_dir: str = "models/saved_models"
):
    """
    Save scaler and encoders for later use.
    
    Args:
        scaler: Fitted StandardScaler
        encoders: Dict of fitted LabelEncoders
        output_dir: Output directory
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Save scaler
    joblib.dump(scaler, output_path / "scaler.pkl")
    logger.info(f"Saved scaler to {output_path / 'scaler.pkl'}")
    
    # Save encoders
    for col_name, encoder in encoders.items():
        joblib.dump(encoder, output_path / f"{col_name}_encoder.pkl")
        logger.info(f"Saved {col_name} encoder")
    
    # Save all encoders together
    joblib.dump(encoders, output_path / "encoders.pkl")
    logger.info(f"Saved all encoders to {output_path / 'encoders.pkl'}")


def load_preprocessing_artifacts(
    output_dir: str = "models/saved_models"
) -> Tuple[StandardScaler, Dict]:
    """
    Load scaler and encoders.
    
    Args:
        output_dir: Directory containing saved artifacts
    
    Returns:
        Tuple of (scaler, encoders dict)
    """
    output_path = Path(output_dir)
    
    # Load scaler
    scaler = joblib.load(output_path / "scaler.pkl")
    
    # Load encoders
    encoders = joblib.load(output_path / "encoders.pkl")
    
    logger.info("Loaded preprocessing artifacts")
    return scaler, encoders

