FROM python:3.11-slim

WORKDIR /usr/src/app

# 🚨 1. 모든 시스템 라이브러리를 한 번에 설치합니다. 🚨
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Gunicorn/Django 필요 (MySQLdb 우회용)
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    # Nginx 필요
    nginx \
    && rm -rf /var/lib/apt/lists/*

# 2. Python 의존성 설치
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 3. 코드 복사 및 Nginx 설정 파일 복사
COPY . .
COPY config/nginx.conf /etc/nginx/conf.d/default.conf

# 4. 정적 파일 수집 및 Nginx 경로 생성
# Nginx가 이 경로에서 정적 파일을 서빙합니다.
RUN mkdir -p /usr/src/app/static_root/
RUN python manage.py collectstatic --no-input

# 5. 포트 노출
EXPOSE 8080

# 🚨 6. CMD 변경: Nginx와 Gunicorn을 유니콘 소켓으로 연결하여 동시에 실행 🚨
# Nginx를 백그라운드에서 실행하고, Gunicorn을 소켓에 바인딩합니다.
CMD service nginx start && \
    gunicorn --bind unix:/tmp/gunicorn.sock config.wsgi:application --workers 1 --timeout 300 \
    --umask 007 --group 0
