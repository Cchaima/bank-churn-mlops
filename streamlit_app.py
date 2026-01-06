import streamlit as st
import requests

# Configuration de la page
st.set_page_config(page_title="Bank Churn Predictor", page_icon="🏦")

st.title("🏦 Prédiction de Churn Bancaire")
st.markdown("Saisissez les informations du client pour évaluer le risque de départ.")

# URL de ton API Azure (remplace par ton lien si différent)
API_URL = "https://bankchurn.azurewebsites.net/predict"

# Formulaire de saisie
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
    # Préparation des données pour l'API
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
            response = requests.post(API_URL, json=payload)
            res = response.json()

        # Affichage du résultat
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