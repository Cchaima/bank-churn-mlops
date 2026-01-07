#!/bin/sh
# Lancer FastAPI en arrière-plan
uvicorn app.main:app --host 0.0.0.0 --port 8000 &

# Attendre 10 secondes que l'API soit prête
sleep 10

# Lancer Streamlit
streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0