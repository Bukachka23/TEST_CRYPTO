FROM python:3.12.3-slim as base

RUN apt-get -y update && apt-get -y upgrade && apt-get install -y --no-install-recommends ffmpeg libpq-dev libgmp-dev build-essential supervisor && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
ENV PYTHONPATH "${PYTHONPATH}:/app"

COPY wallet_service ./wallet_service
COPY user_verification_service ./user_verification_service

EXPOSE 8001

CMD ["uvicorn", "wallet_service.main:app", "--host", "0.0.0.0", "--port", "8001"] 