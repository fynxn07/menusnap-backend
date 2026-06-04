FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*



COPY MenuSnap_Django/requirements.txt .
COPY MenuSnap_Django/requirements-dev.txt .

RUN python -m pip install --upgrade pip \
    && pip install -r requirements.txt \
    && pip install -r requirements-dev.txt


COPY . .

WORKDIR /app/MenuSnap_Django


ENV PYTHONPATH=/app

RUN python manage.py collectstatic --noinput

RUN python manage.py migrate --noinput

CMD ["gunicorn", "MenuSnap.asgi:application", "-k", "uvicorn.workers.UvicornWorker", "--workers", "1", "--bind", "0.0.0.0:8000"]
