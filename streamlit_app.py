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
    st.write("Cette page compare les données de production actuelles avec les données d'entraînement.")

    # 1. Configuration du seuil
    threshold = st.slider(
        "Seuil de sensibilité (p-value)", 
        0.01, 0.10, 0.05, 
        help="Un p-value plus petit que ce seuil indique un drift statistique."
    )

    if st.button("🚀 Lancer l'analyse de Drift"):
        try:
            with st.spinner("Analyse statistique en cours sur Azure..."):
                # Nettoyage de l'URL pour éviter les doubles slashes ou slashes finaux
                url_clean = DRIFT_URL.rstrip('/')
                
                # Utilisation de 'params' pour passer le threshold proprement
                response = requests.post(url_clean, params={"threshold": threshold}, timeout=30)

            # Vérification du statut HTTP
            if response.status_code == 200:
                results = response.json()

                # SÉCURITÉ : On vérifie que 'results' est bien un dictionnaire
                if isinstance(results, dict) and len(results) > 0:
                    st.success("✅ Analyse terminée avec succès.")
                    
                    # 1. Calcul des métriques
                    total_features = len(results)
                    # On utilise .get() pour éviter les erreurs de clés manquantes
                    drifted_features = sum(1 for f in results.values() if isinstance(f, dict) and f.get('drift_detected', False))
                    
                    # 2. Affichage des indicateurs
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Variables analysées", total_features)
                    m2.metric("Variables avec Drift", drifted_features, delta=drifted_features, delta_color="inverse")
                    
                    if drifted_features > 0:
                        m3.error("🚨 RÉENTRAÎNEMENT REQUIS")
                    else:
                        m3.success("✅ MODÈLE STABLE")

                    # 3. Tableau détaillé
                    st.divider()
                    st.subheader("Détails par variable (Test Kolmogorov-Smirnov)")
                    
                    df_drift = pd.DataFrame.from_dict(results, orient='index')
                    df_drift.index.name = "Caractéristique"
                    df_drift = df_drift.reset_index()
                    
                    # Style conditionnel
                    def color_drift(val):
                        return 'color: #ff4b4b; font-weight: bold' if val else 'color: #09ab3b'

                    st.table(df_drift.style.applymap(color_drift, subset=['drift_detected']))
                    
                    if drifted_features > 0:
                        st.warning("⚠️ Dérive détectée : les distributions de production divergent des données historiques.")
                else:
                    st.error("L'API a renvoyé un format de données vide ou invalide.")
            
            elif response.status_code == 405:
                st.error("Erreur 405 : La méthode POST n'est pas autorisée sur cet URL. Vérifiez la config de l'API.")
            else:
                st.error(f"Erreur API {response.status_code} : {response.text}")

        except Exception as e:
            st.error(f"Erreur de connexion : {e}")

    st.divider()
    with st.expander("ℹ️ Comprendre le Drift"):
        st.write("""
        Le **Data Drift** survient lorsque les données reçues en production deviennent trop différentes de celles de l'entraînement. 
        
        **Méthode :** Test de Kolmogorov-Smirnov.
        - **p-value < seuil :** On rejette l'idée que les données sont identiques (Drift détecté).
        - **Action :** Si le drift est élevé, une mise à jour du modèle est nécessaire.
        """)
