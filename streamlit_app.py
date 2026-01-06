import streamlit as st
import requests
import pandas as pd

# Configuration de la page
st.set_page_config(page_title="Bank Churn MLOps", page_icon="🏦", layout="wide")

# URLs de ton API Azure

# Cela fonctionne sur ton PC, dans Docker et sur Azure sans aucune modification !
BASE_URL = "http://localhost:8000"

PREDICT_URL = f"{BASE_URL}/predict"
DRIFT_URL = f"{BASE_URL}/drift/check"

# Barre latérale pour la navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Aller vers", ["🔮 Prédiction Individuelle", "📊 Monitoring & Drift"])

# --- CONSOLE DE DÉBOGAGE ---
st.sidebar.divider()
debug_mode = st.sidebar.checkbox("🛠️ Activer le mode Debug")

def show_debug_info(url, status_code, content):
    """Affiche une console de debug si l'option est cochée"""
    if debug_mode:
        with st.expander("🔍 Console de Débogage (Réponse API)", expanded=True):
            st.write(f"**URL appelée :** `{url}`")
            st.write(f"**Status Code :** `{status_code}`")
            st.write("**Contenu brut reçu :**")
            st.code(content[:1000]) # On affiche les 1000 premiers caractères

# ==========================================
# PAGE 1 : PRÉDICTION
# ==========================================
if page == "🔮 Prédiction Individuelle":
    st.title("🏦 Prédiction de Churn Bancaire")
    
    with st.form("customer_form"):
        col1, col2 = st.columns(2)
        with col1:
            credit_score = st.number_input("Score de Crédit", 300, 850, 600)
            age = st.number_input("Âge", 18, 100, 40)
            tenure = st.slider("Ancienneté (années)", 0, 10, 5)
            balance = st.number_input("Solde du compte (€)", 0.0, 250000.0, 50000.0)
            num_products = st.selectbox("Nombre de produits", [1, 2, 3, 4])
        with col2:
            has_card = st.radio("Possède une carte ?", ["Oui", "Non"])
            is_active = st.radio("Membre actif ?", ["Oui", "Non"])
            salary = st.number_input("Salaire estimé (€)", 0.0, 200000.0, 50000.0)
            geography = st.selectbox("Pays", ["France", "Allemagne", "Espagne"])
        submit = st.form_submit_button("Analyser le risque")

    if submit:
        payload = {
            "CreditScore": credit_score, "Age": age, "Tenure": tenure, "Balance": balance,
            "NumOfProducts": num_products, "HasCrCard": 1 if has_card == "Oui" else 0,
            "IsActiveMember": 1 if is_active == "Oui" else 0, "EstimatedSalary": salary,
            "Geography_Germany": 1 if geography == "Allemagne" else 0,
            "Geography_Spain": 1 if geography == "Espagne" else 0
        }

        try:
            with st.spinner("Analyse en cours..."):
                response = requests.post(PREDICT_URL, json=payload)
                
                # Debugging
                show_debug_info(PREDICT_URL, response.status_code, response.text)

                if response.status_code == 200:
                    res = response.json()
                    st.divider()
                    prob = res["churn_probability"]
                    risk = res["risk_level"]
                    st.subheader(f"Résultat : Risque {risk}")
                    st.progress(prob)
                    st.write(f"Probabilité : **{prob*100:.2f}%**")
                else:
                    st.error(f"L'API a répondu avec une erreur {response.status_code}")
        except Exception as e:
            st.error(f"Erreur fatale : {e}")

# ==========================================
# PAGE 2 : MONITORING
# ==========================================
else:
    st.title("📊 Monitoring & Drift")
    threshold = st.slider("Seuil de sensibilité (p-value)", 0.01, 0.10, 0.05)
        
    if st.button("🚀 Lancer l'analyse de Drift"):
        try:
            with st.spinner("Calcul en cours..."):
                response = requests.post(f"{DRIFT_URL}?threshold={threshold}")
                
                # Debugging
                show_debug_info(DRIFT_URL, response.status_code, response.text)

                if response.status_code == 200:
                    data = response.json()
                    st.success("Analyse terminée.")
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Variables", data["features_analyzed"])
                    m2.metric("Driftées", data["features_drifted"])
                    m3.metric("Santé", "🚨 Alerte" if data["features_drifted"] > 0 else "✅ OK")
                else:
                    st.error(f"Erreur API {response.status_code}. Vérifiez la console de debug.")
        except Exception as e:
            st.error(f"Impossible de joindre l'API : {e}")