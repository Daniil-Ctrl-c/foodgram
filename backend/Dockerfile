FROM python:3.9-slim

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    build-essential \
    zlib1g-dev \
    libjpeg-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip wheel && pip install --no-cache-dir -r requirements.txt

COPY . .

COPY ./data /app/data

RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "foodgram.wsgi:application", "--bind", "0.0.0.0:8000"]
