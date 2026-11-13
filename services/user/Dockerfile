
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt gunicorn==23.0.0

COPY app.py .

EXPOSE 5001

CMD ["sh", "-c", "python -c 'from app import create_users_table; create_users_table()' && gunicorn --bind 0.0.0.0:5001 --workers 2 app:app"]
