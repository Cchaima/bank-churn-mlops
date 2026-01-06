FROM python:3.11-slim

WORKDIR /app

# 1. Installer les bibliothèques
COPY requirements.txt .
# Remplace ton ancienne ligne 7 par celle-ci :
RUN pip install --no-cache-dir --default-timeout=1000 -r requirements.txt

# 2. Copier tes dossiers et fichiers
COPY app/ ./app/
COPY model/ ./model/
COPY data/ ./data/
COPY streamlit_app.py .
COPY start.sh .

# 3. Rendre le script exécutable
RUN chmod +x start.sh

# 4. Dire à Azure quel port utiliser
EXPOSE 8501

# 5. Lancer la "recette" au démarrage
CMD ["./start.sh"]