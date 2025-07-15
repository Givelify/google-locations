# app/Dockerfile

FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /google-locations

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD tail -f /dev/null
    