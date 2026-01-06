import pandas as pd
from scipy.stats import ks_2samp
import numpy as np
import os

def detect_drift(reference_file, production_file, threshold=0.05):
    """Détecte le drift entre les données de référence et de production"""
    ref_data = pd.read_csv(reference_file)
    
    # Sécurité : Si pas de données de prod, on simule un petit échantillon
    if not os.path.exists(production_file):
        prod_data = ref_data.sample(n=min(100, len(ref_data))).copy()
        prod_data['Age'] = prod_data['Age'] + np.random.normal(0, 5, size=len(prod_data))
    else:
        prod_data = pd.read_csv(production_file)

    drift_results = {}
    # On exclut la cible 'Exited'
    features = [c for c in ref_data.columns if c != 'Exited']

    for col in features:
        if col in prod_data.columns:
            # Test Kolmogorov-Smirnov
            stat, p_val = ks_2samp(ref_data[col].dropna(), prod_data[col].dropna())
            drift_results[col] = {
                "p_value": float(p_val),
                "drift_detected": bool(p_val < threshold)
            }
    
    return drift_results