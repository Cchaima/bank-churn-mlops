import streamlit as st
import requests
import pandas as pd

# Configuration de la page
st.set_page_config(page_title="Bank Churn MLOps", page_icon="🏦", layout="wide")

# ==========================================
# CONFIGURATION DES URLS
# ==========================================
# Sur Azure Container Apps (même conteneur), localhost:8000 est l'adresse de l'API FastAPI
BASE_URL = "http://localhost:8000"
API_URL = "https://bank-churn-app.grayplant-cb43b6b5.germanywestcentral.azurecontainerapps.io"

PREDICT_URL = f"{BASE_URL}/predict"
DRIFT_URL = f"{BASE_URL}/drift/check/"

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
            st.code(content[:1000]) 

# ==========================================
# PAGE 1 : PRÉDICTION
# ==========================================
if page == "🔮 Prédiction Individuelle":
    st.title("🏦 Prédiction de Churn Bancaire")
    st.markdown("Saisissez les informations du client pour évaluer son risque de départ.")
    
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
                show_debug_info(PREDICT_URL, response.status_code, response.text)

                if response.status_code == 200:
                    res = response.json()
                    st.divider()
                    prob = res["churn_probability"]
                    risk = res["risk_level"]
                    
                    # Affichage visuel du risque
                    color = "red" if risk == "Élevé" else "orange" if risk == "Moyen" else "green"
                    st.markdown(f"### Résultat : <span style='color:{color}'>{risk}</span>", unsafe_allow_html=True)
                    st.progress(prob)
                    st.write(f"Probabilité de départ : **{prob*100:.2f}%**")
                else:
                    st.error(f"L'API a répondu avec une erreur {response.status_code}")
        except Exception as e:
            st.error(f"Erreur de connexion à l'API : {e}")

# ==========================================
# PAGE 2 : MONITORING & DRIFT
# ==========================================
else:
    st.title("📊 Monitoring de la Dérive (Data Drift)")
    st.write("Cette page compare les données de production actuelles avec les données d'entraînement (référence).")
    
    threshold = st.slider("Seuil de sensibilité (p-value)", 0.01, 0.10, 0.05, help="Un p-value plus petit que ce seuil indique un drift statistique.")
        
    if st.button("🚀 Lancer l'analyse de Drift"):
        try:
            with st.spinner("Comparaison des distributions statistiques..."):
                # On envoie le seuil en paramètre à l'API
                response = requests.post(f"{DRIFT_URL}?threshold={threshold}")
                show_debug_info(DRIFT_URL, response.status_code, response.text)

                if response.status_code == 200:
                    results = response.json()
                    
                    # 1. Calcul des métriques globales
                    drift_data = results
                    total_features = len(drift_data)
                    drifted_features = sum(1 for f in drift_data.values() if f['drift_detected'])
                    
                    # 2. Affichage des indicateurs clés
                    st.success("Analyse terminée avec succès.")
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Variables analysées", total_features)
                    m2.metric("Variables avec Drift", drifted_features, delta=drifted_features, delta_color="inverse")
                    
                    status_text = "🚨 ALERTE : RÉENTRAÎNEMENT REQUIS" if drifted_features > 0 else "✅ MODÈLE STABLE"
                    m3.subheader(status_text)

                    # 3. Tableau détaillé des résultats
                    st.divider()
                    st.subheader("Détails par variable (Test Kolmogorov-Smirnov)")
                    
                    # Transformation du dictionnaire en DataFrame pour l'affichage
                    df_drift = pd.DataFrame.from_dict(drift_data, orient='index')
                    df_drift.index.name = "Caractéristique"
                    df_drift = df_drift.reset_index()
                    
                    # Mise en forme du tableau
                    def color_drift(val):
                        color = 'red' if val else 'green'
                        return f'color: {color}; font-weight: bold'

                    st.table(df_drift.style.applymap(color_drift, subset=['drift_detected']))
                    
                    if drifted_features > 0:
                        st.warning("⚠️ Certaines variables montrent une distribution différente du dataset d'origine. Les prédictions pourraient être moins fiables.")
                else:
                    st.error(f"Erreur API {response.status_code}. Vérifiez si l'API est lancée et le fichier production_data.csv existe.")
        except Exception as e:
            st.error(f"Impossible de joindre l'API : {e}")

    st.divider()
    with st.expander("ℹ️ Comprendre le Drift"):
        st.write("""
        Le **Data Drift** survient lorsque les données que le modèle reçoit en production 
        deviennent trop différentes de celles utilisées pendant l'entraînement. 
        
        Nous utilisons ici le test de **Kolmogorov-Smirnov** :
        - Si la **p-value** est inférieure au seuil choisi, nous rejetons l'hypothèse que les deux distributions sont identiques.
        - **Action suggérée :** Collecter plus de données récentes et ré-entraîner le modèle.
        """)
