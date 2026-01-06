import streamlit as st
import requests
import pandas as pd

# Configuration de la page
st.set_page_config(page_title="Bank Churn MLOps", page_icon="🏦", layout="wide")

# URLs de ton API Azure
BASE_URL = "https://bankchurn.azurewebsites.net"
PREDICT_URL = f"{BASE_URL}/predict"
DRIFT_URL = f"{BASE_URL}/drift/check"

# Barre latérale pour la navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Aller vers", ["🔮 Prédiction Individuelle", "📊 Monitoring & Drift"])

# ==========================================
# PAGE 1 : PRÉDICTION
# ==========================================
if page == "🔮 Prédiction Individuelle":
    st.title("🏦 Prédiction de Churn Bancaire")
    st.markdown("Saisissez les informations du client pour évaluer le risque de départ.")

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
            "CreditScore": credit_score,
            "Age": age,
            "Tenure": tenure,
            "Balance": balance,
            "NumOfProducts": num_products,
            "HasCrCard": 1 if has_card == "Oui" else 0,
            "IsActiveMember": 1 if is_active == "Oui" else 0,
            "EstimatedSalary": salary,
            "Geography_Germany": 1 if geography == "Allemagne" else 0,
            "Geography_Spain": 1 if geography == "Espagne" else 0
        }

        try:
            with st.spinner("Analyse en cours..."):
                response = requests.post(PREDICT_URL, json=payload)
                res = response.json()

            st.divider()
            prob = res["churn_probability"]
            risk = res["risk_level"]

            st.subheader(f"Résultat : Risque {risk}")
            st.progress(prob)
            st.write(f"Probabilité de départ : **{prob*100:.2f}%**")
            
            if risk == "High":
                st.error("⚠️ Attention : Ce client présente un risque élevé de départ.")
            elif risk == "Medium":
                st.warning("⚖️ Risque modéré : Une action commerciale est conseillée.")
            else:
                st.success("✅ Client fidèle : Le risque de churn est faible.")

        except Exception as e:
            st.error(f"Erreur de connexion à l'API : {e}")

# ==========================================
# PAGE 2 : MONITORING
# ==========================================
else:
    st.title("📊 Monitoring du Modèle & Drift")
    st.markdown("""
    Cette page permet de comparer les données de production actuelles avec les données d'entraînement 
    pour détecter si le comportement des clients a changé (**Data Drift**).
    """)

    col1, col2 = st.columns(2)
    
    with col1:
        st.info("L'analyse compare `bank_churn.csv` (Référence) avec `production_data.csv`.")
        threshold = st.slider("Seuil de sensibilité (p-value)", 0.01, 0.10, 0.05)
        
    if st.button("🚀 Lancer l'analyse de Drift"):
        try:
            with st.spinner("Calcul du drift en cours..."):
                # On envoie le threshold en paramètre query
                response = requests.post(f"{DRIFT_URL}?threshold={threshold}")
                data = response.json()

            if response.status_code == 200:
                st.success("Analyse de drift terminée avec succès !")
                
                # Affichage des métriques
                m1, m2, m3 = st.columns(3)
                m1.metric("Variables Analysées", data["features_analyzed"])
                
                drifted = data["features_drifted"]
                m2.metric("Variables avec Drift", drifted, delta=drifted, delta_color="inverse" if drifted > 0 else "normal")
                
                status = "🚨 Alerte" if drifted > 0 else "✅ OK"
                m3.metric("Statut Santé", status)

                if drifted > 0:
                    st.warning(f"Il y a une dérive sur {drifted} variable(s). Un réentraînement du modèle est conseillé.")
                else:
                    st.success("Aucune dérive significative détectée. Le modèle est stable.")
            else:
                st.error(f"Erreur lors de l'analyse : {data.get('detail', 'Inconnue')}")

        except Exception as e:
            st.error(f"Impossible de joindre l'API de monitoring : {e}")

    st.divider()
    st.subheader("💡 Aide au monitoring")
    st.write("""
    - **Si le drift est élevé :** Les données clients actuelles ne ressemblent plus aux données passées.
    - **Action :** Collecter de nouvelles données étiquetées et réentraîner le modèle.
    """)