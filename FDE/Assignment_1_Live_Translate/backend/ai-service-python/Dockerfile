FROM python:3.11-slim

WORKDIR /app

# install deps first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# SQLite cache lives on a mounted volume so it survives restarts/deploys
ENV TRANSLATION_DB_PATH=/data/translations.db
ENV PORT=8080
EXPOSE 8080

# bind IPv6 (::) — Fly's private 6PN network (how the gateway reaches us) is
# IPv6-only; a dual-stack socket also serves IPv4. 0.0.0.0 alone is unreachable.
CMD ["sh", "-c", "uvicorn app:app --host :: --port ${PORT:-8080}"]
