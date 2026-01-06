FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# On copie les dossiers
COPY app/ ./app/
COPY model/ ./model/
COPY data/ ./data/

# --- AJOUT ICI ---
COPY streamlit_app.py . 
# -----------------

COPY start.sh .
RUN chmod +x start.sh

# Azure va écouter sur le port exposé ici
EXPOSE 8501

CMD ["./start.sh"]