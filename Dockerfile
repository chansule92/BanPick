# ------------------------------------
# 1단계: 빌드 스테이지 (Build Stage) - WhiteNoise를 사용하여 정적 파일 수집
# ------------------------------------
FROM python:3.11-slim AS builder

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

WORKDIR /usr/src/app

# requirements.txt에 gunicorn, django, **whitenoise** 가 포함되어 있어야 합니다.
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt --no-cache-dir

COPY . .

# 정적 파일 수집
RUN python manage.py collectstatic --noinput

# ------------------------------------
# 2단계: 최종 서비스 스테이지 (Final Service Stage)
# ------------------------------------
FROM python:3.11-slim

ENV PYTHONUNBUFFERED 1

WORKDIR /usr/src/app

# 1단계에서 설치된 종속성과 코드를 복사합니다.
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/src/app /usr/src/app

# Render는 환경 변수 $PORT를 사용합니다.
# 이 포트를 Gunicorn이 리스닝하도록 설정합니다.
ARG PORT=8000
ENV PORT=${PORT}
EXPOSE ${PORT}

# start.sh 파일 복사 및 실행 권한 부여
COPY start.sh /start.sh
RUN chmod +x /start.sh

# 컨테이너 시작 명령
CMD ["/start.sh"]
