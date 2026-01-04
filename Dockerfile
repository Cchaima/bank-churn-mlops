# 1. Utiliser une image Python officielle
FROM python:3.11-slim

# 2. Définir le répertoire de travail
WORKDIR /app

# 3. Copier le fichier des dépendances
COPY requirements.txt .

# 4. Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copier les dossiers nécessaires
COPY app/ ./app/
COPY model/ ./model/
COPY data/ ./data/

# 6. Exposer le port de l'API
EXPOSE 8000

# 7. Commande de lancement
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]