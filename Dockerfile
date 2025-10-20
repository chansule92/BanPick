FROM python:3.11-slim


WORKDIR /usr/src/app


RUN apt-get update && apt-get install -y --no-install-recommends \
    default-libmysqlclient-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt


COPY . .


RUN python manage.py collectstatic --no-input


ENV PORT 8000
EXPOSE 8000


CMD ["gunicorn", "--bind", "0.0.0.0:8000", "config.wsgi:application"]
