FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY scripts ./scripts
RUN chmod +x /app/scripts/entrypoint.sh

EXPOSE 8000
CMD ["sh", "/app/scripts/entrypoint.sh"]
