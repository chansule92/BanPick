FROM python:3.11-slim

WORKDIR /usr/src/app

ENV PYTHONUNBUFFERED 1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        pkg-config \
        default-libmysqlclient-dev \
        libpq-dev \
        build-essential \
        postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "your_project_name.wsgi:application"]
