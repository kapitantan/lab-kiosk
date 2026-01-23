FROM python:3.11-slim

WORKDIR /app

# PostgreSQL接続用ライブラリ(psycopg2)のビルドに必要なものをインストール
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# コードはdocker-composeでマウントするので、ここではコピーしない