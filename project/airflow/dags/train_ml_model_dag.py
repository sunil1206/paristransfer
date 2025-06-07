import os
import sys
import django
import pandas as pd
import joblib
import pickle
from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.compose import ColumnTransformer
from pathlib import Path
# ===== Django Setup =====
BASE_DIR = Path(__file__).resolve().parent.parent  # CHANGE THIS

sys.path.append(BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')  # CHANGE THIS
django.setup()

from booking.models import Booking  # CHANGE TO YOUR APP NAME

# ===== File Constants =====
DATA_FILE = '/booking/data/taxi_dataset.csv'
MODEL_FILE = '/booking/models/price_model.joblib'
ENCODER_FILE = '/tmp/label_encoders.pkl'

# ===== Utility: Encoding =====
def encode_categorical(df, categorical_cols):
    label_encoders = {}
    for col in categorical_cols:
        df[col] = df[col].astype(str)
        unique_vals = df[col].unique()
        mapping = {val: idx for idx, val in enumerate(unique_vals)}
        df[col] = df[col].map(mapping)
        label_encoders[col] = mapping
    return df, label_encoders

# ===== Task 1: Extract from PostgreSQL via Django ORM =====
def extract_data():
    queryset = Booking.objects.all().values(
        'pickup_location', 'dropoff_location', 'adults', 'children',
        'trip_type', 'transport_type', 'price'
    )
    df = pd.DataFrame(queryset)
    df.to_csv(DATA_FILE, index=False)
    print(f" Extracted {df.shape[0]} rows to {DATA_FILE}")

# ===== Task 2: Train ML model =====
def train_model():
    df = pd.read_csv(DATA_FILE)

    categorical_cols = ['pickup_location', 'dropoff_location', 'trip_type', 'transport_type']
    numeric_cols = ['adults', 'children']

    df, label_encoders = encode_categorical(df, categorical_cols)

    X = df[categorical_cols + numeric_cols]
    y = df['price']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    preprocessor = ColumnTransformer([
        ('num', StandardScaler(), numeric_cols),
        ('cat', 'passthrough', categorical_cols)
    ])

    pipeline = Pipeline([
        ('preprocessor', preprocessor),
        ('regressor', RandomForestRegressor(n_estimators=100, random_state=42))
    ])

    pipeline.fit(X_train, y_train)

    joblib.dump(pipeline, MODEL_FILE)
    with open(ENCODER_FILE, 'wb') as f:
        pickle.dump(label_encoders, f)

    print(f"✅ Model saved to {MODEL_FILE}, encoders to {ENCODER_FILE}")

# ===== Airflow DAG Definition =====
with DAG(
    dag_id='train_price_prediction_model',
    schedule_interval='@daily',
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['ml', 'django'],
    default_args={'owner': 'airflow'}
) as dag:

    extract_task = PythonOperator(
        task_id='extract_booking_data',
        python_callable=extract_data
    )

    train_task = PythonOperator(
        task_id='train_price_model',
        python_callable=train_model
    )

    extract_task >> train_task
