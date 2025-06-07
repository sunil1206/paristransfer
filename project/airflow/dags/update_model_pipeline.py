from sklearn.preprocessing import LabelEncoder
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import subprocess
import os
import joblib
import pandas as pd

def retrain_model():
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
    django.setup()
    from booking.models import TaxiData
    # Load data from DB
    data = list(TaxiData.objects.all().values())
    df = pd.DataFrame(data)
    # Drop non-feature columns
    df = df.drop(columns=["id", "created_at", "price"])  # price is the target
    # Identify categorical features
    categorical_features = ['trip_type', 'pickup_location', 'dropoff_location', 'transport_type']
    # Apply label encoding
    label_encoders = {}
    for feature in categorical_features:
        le = LabelEncoder()
        df[feature] = le.fit_transform(df[feature])
        label_encoders[feature] = le
        print(f"\nLabel encoding for {feature}:")
        for i, cls in enumerate(le.classes_):
            print(f"{cls} -> {i}")
    # Save encoders
    joblib.dump(label_encoders, os.path.join("booking/models", "label_encoders.joblib"))
    # Target
    target = pd.Series([d['price'] for d in data])
    # Train model
    from sklearn.ensemble import RandomForestRegressor
    model = RandomForestRegressor()
    model.fit(df, target)
    # Save model
    joblib.dump(model, os.path.join("booking/models", "price_model.joblib"))

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2023, 1, 1),
    'retries': 1,
}

with DAG('update_taxi_model',
         default_args=default_args,
         schedule_interval='@daily',  # or @hourly or cron
         catchup=False) as dag:

    load_task = PythonOperator(
        task_id='load_csv_to_db',
        python_callable=load_csv_to_db
    )

    train_task = PythonOperator(
        task_id='retrain_model',
        python_callable=retrain_model
    )

    load_task >> train_task
