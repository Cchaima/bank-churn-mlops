from fastapi import FastAPI, HTTPException
import joblib
import pandas as pd
import os
import numpy as np
from app.models import CustomerFeatures
from app.drift_detection import detect_drift # Import de ton script

app = FastAPI(title="Bank Churn API")

# Chargement du modèle
model = joblib.load("model/churn_model.pkl")

@app.post("/predict")
def predict(features: CustomerFeatures):
    # 1. Conversion des données pour le modèle
    input_list = [
        features.CreditScore, features.Age, features.Tenure, features.Balance,
        features.NumOfProducts, features.HasCrCard, features.IsActiveMember,
        features.EstimatedSalary, features.Geography_Germany, features.Geography_Spain
    ]
    
    # 2. Prédiction
    proba = float(model.predict_proba([input_list])[0][1])
    risk = "High" if proba > 0.7 else "Medium" if proba > 0.3 else "Low"

    # 3. SAUVEGARDE pour le drift futur
    log_path = "data/production_data.csv"
    df_new = pd.DataFrame([input_list], columns=[
        'CreditScore', 'Age', 'Tenure', 'Balance', 'NumOfProducts', 
        'HasCrCard', 'IsActiveMember', 'EstimatedSalary', 
        'Geography_Germany', 'Geography_Spain'
    ])
    df_new.to_csv(log_path, mode='a', header=not os.path.exists(log_path), index=False)

    return {"churn_probability": proba, "risk_level": risk}

@app.get("/drift/check")
def check_drift(threshold: float = 0.05):
    # Appelle la fonction de ton fichier drift_detection.py
    return detect_drift("data/bank_churn.csv", "data/production_data.csv", threshold)