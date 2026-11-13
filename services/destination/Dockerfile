
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt gunicorn==23.0.0

COPY app.py .

EXPOSE 5002

CMD ["sh", "-c", "python -c 'from app import client, seed_destinations; client.admin.command(\"ping\"); seed_destinations()' && gunicorn --bind 0.0.0.0:5002 --workers 2 app:app"]
