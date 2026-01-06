#!/bin/sh
# Lancer FastAPI en arrière-plan
uvicorn app.main:app --host 0.0.0.0 --port 8000 &

# Lancer Streamlit au premier plan
streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0