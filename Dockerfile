FROM python:3.11-slim

WORKDIR /usr/src/app

# 🚨 1. 모든 시스템 라이브러리를 한 번에 설치합니다. 🚨
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    nginx \
    # 🚨 NGINX 기본 설정 파일 삭제: Welcome to Nginx! 페이지를 띄우는 설정입니다.
    # 이 파일을 삭제해야 사용자 설정이 적용됩니다.
    && rm -f /etc/nginx/sites-enabled/default \
    && rm -rf /var/lib/apt/lists/*

# 2. Python 의존성 설치
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 3. 코드 복사 및 Nginx 설정 파일 복사
COPY . .
# 사용자님의 nginx.conf 파일을 NGINX가 읽는 정확한 위치에 복사합니다.
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 4. 정적 파일 수집 및 Nginx 경로 생성
# 🚨 정적 파일 경로 통일: static_root 대신 static 사용
RUN mkdir -p /usr/src/app/static/
# collectstatic이 파일을 /usr/src/app/static 에 저장합니다.
RUN python manage.py collectstatic --no-input

# 5. 포트 노출
EXPOSE 8080

# 🚨 6. CMD: Nginx와 Gunicorn을 유니콘 소켓으로 연결하여 동시에 실행 🚨
# 권한 안정화를 위해 --group www-data 사용
CMD service nginx start && \
    gunicorn --bind unix:/tmp/gunicorn.sock config.wsgi:application --workers 1 --timeout 300 --umask 007 --group www-data
