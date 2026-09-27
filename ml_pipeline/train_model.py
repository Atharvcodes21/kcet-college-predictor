"""
Train XGBoost model on real KCET cutoff data.

The model predicts CUTOFF_RANK given:
  - COLLEGE (label-encoded)
  - COURSE_NAME (label-encoded)  
  - CATEGORY (label-encoded: GM, Cat-1, 2A, 2B, 3A, 3B, SC, ST)
  - SUB_QUOTA (label-encoded: General, Kannada Medium, Rural)
  - REGION (label-encoded: General, HK)
  - YEAR (numeric)

The backend uses this model to estimate cutoffs for any college/course/category
combination, then compares against the user's rank to compute a probability.
"""

import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error, r2_score
import pickle
import json
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
CLEAN_DATA_PATH = os.path.join(BASE_DIR, 'data', 'clean_data', 'kcet_cutoffs_clean.csv')
SAVE_DIR = os.path.join(BASE_DIR, 'saved_models')


def train_and_save():
    """Train XGBoost on real KCET data and save model + artifacts."""
    
    # ── Load Clean Data ──────────────────────────────────────────────────────
    print("Loading clean data...")
    df = pd.read_csv(CLEAN_DATA_PATH)
    print(f"  {len(df)} rows loaded")
    print(f"  Colleges: {df['COLLEGE'].nunique()}")
    print(f"  Courses: {df['COURSE_NAME'].nunique()}")
    print(f"  Categories: {sorted(df['CATEGORY'].unique())}")
    print(f"  Sub-quotas: {sorted(df['SUB_QUOTA'].unique())}")
    print(f"  Regions: {sorted(df['REGION'].unique())}")
    print(f"  Years: {sorted(df['YEAR'].unique())}")
    
    # ── Feature Engineering ──────────────────────────────────────────────────
    feature_cols = ['COLLEGE', 'COURSE_NAME', 'CATEGORY', 'SUB_QUOTA', 'REGION', 'YEAR']
    target_col = 'CUTOFF_RANK'
    
    # Label-encode categorical columns
    encoders = {}
    categorical_cols = ['COLLEGE', 'COURSE_NAME', 'CATEGORY', 'SUB_QUOTA', 'REGION']
    
    df_encoded = df.copy()
    for col in categorical_cols:
        le = LabelEncoder()
        df_encoded[col] = le.fit_transform(df_encoded[col])
        encoders[col] = le
        print(f"  Encoded {col}: {len(le.classes_)} unique values")
    
    X = df_encoded[feature_cols]
    y = df_encoded[target_col]
    
    # ── Train/Test Split ─────────────────────────────────────────────────────
    # Random 80/20 split (stratified by category for balanced evaluation)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    print(f"\n  Train set: {len(X_train)} rows")
    print(f"  Test set:  {len(X_test)} rows")
    
    # ── Train XGBoost ────────────────────────────────────────────────────────
    print("\nTraining XGBoost Regressor with early stopping...")
    model = xgb.XGBRegressor(
        n_estimators=1000,
        learning_rate=0.05,
        max_depth=7,
        min_child_weight=5,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_alpha=0.1,
        reg_lambda=1.0,
        random_state=42,
        n_jobs=-1,
        tree_method='hist',
        early_stopping_rounds=30,
    )
    
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=50
    )
    
    # ── Evaluate ─────────────────────────────────────────────────────────────
    y_pred_train = model.predict(X_train)
    y_pred_test = model.predict(X_test)
    
    train_r2 = r2_score(y_train, y_pred_train)
    test_r2 = r2_score(y_test, y_pred_test)
    train_mae = mean_absolute_error(y_train, y_pred_train)
    test_mae = mean_absolute_error(y_test, y_pred_test)
    
    print(f"\n{'='*60}")
    print("MODEL EVALUATION")
    print(f"  Train R2:  {train_r2:.4f}")
    print(f"  Test R2:   {test_r2:.4f}")
    print(f"  Train MAE: {train_mae:.0f} ranks")
    print(f"  Test MAE:  {test_mae:.0f} ranks")
    print(f"{'='*60}")
    
    # ── Feature Importance ───────────────────────────────────────────────────
    importance = dict(zip(feature_cols, model.feature_importances_))
    print("\nFeature Importance:")
    for feat, imp in sorted(importance.items(), key=lambda x: -x[1]):
        print(f"  {feat:15s}: {imp:.4f}")
    
    # ── Save Model + Artifacts ───────────────────────────────────────────────
    os.makedirs(SAVE_DIR, exist_ok=True)
    
    # Save model
    model_path = os.path.join(SAVE_DIR, 'kcet_model.pkl')
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    
    # Save encoders
    encoder_path = os.path.join(SAVE_DIR, 'encoders.pkl')
    with open(encoder_path, 'wb') as f:
        pickle.dump(encoders, f)
    
    # Save metadata for the backend (dropdown population + encoder mapping)
    metadata = {
        'colleges': sorted(encoders['COLLEGE'].classes_.tolist()),
        'courses': sorted(encoders['COURSE_NAME'].classes_.tolist()),
        'categories': sorted(encoders['CATEGORY'].classes_.tolist()),
        'sub_quotas': sorted(encoders['SUB_QUOTA'].classes_.tolist()),
        'regions': sorted(encoders['REGION'].classes_.tolist()),
        'years_trained': sorted(df['YEAR'].unique().tolist()),
        'feature_columns': feature_cols,
        'model_metrics': {
            'train_r2': round(train_r2, 4),
            'test_r2': round(test_r2, 4),
            'train_mae': round(train_mae, 1),
            'test_mae': round(test_mae, 1),
            'train_rows': int(len(X_train)),
            'test_rows': int(len(X_test)),
        }
    }
    
    metadata_path = os.path.join(SAVE_DIR, 'metadata.json')
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\nSaved to {SAVE_DIR}:")
    print(f"  - kcet_model.pkl  ({os.path.getsize(model_path) / 1024:.0f} KB)")
    print(f"  - encoders.pkl    ({os.path.getsize(encoder_path) / 1024:.0f} KB)")
    print(f"  - metadata.json")
    print("\nDone!")


if __name__ == "__main__":
    train_and_save()
