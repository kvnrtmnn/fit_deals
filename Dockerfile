# Basis-Image: Python 3.9 (schlank)
FROM python:3.9-slim

# Arbeitsverzeichnis im Container
WORKDIR /app

# Abhängigkeiten kopieren und installieren
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Den Rest des Codes kopieren
COPY . .

# Port freigeben
EXPOSE 5000

# App starten
CMD ["python", "app.py"]
