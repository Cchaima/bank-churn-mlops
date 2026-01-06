#!/bin/sh
# Lancer l'API en arrière-plan
uvicorn app.main:app --host 0.0.0.0 --port 8000 &

# Attendre que l'API soit prête
sleep 5

# Lancer l'interface Streamlit
streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0 --server.enableCORS false --server.enableXsrfProtection false