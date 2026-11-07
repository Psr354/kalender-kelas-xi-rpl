FROM python:3.12-slim

WORKDIR /app

COPY server/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY server/app.py app.py
COPY index.html index.html
COPY assets assets

ENV PSR354_DATABASE_PATH=/data/kalender.sqlite3
EXPOSE 5050

CMD ["gunicorn", "--bind", "0.0.0.0:5050", "--workers", "2", "app:app"]
