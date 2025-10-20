FROM python:3.11-slim

WORKDIR /usr/src/app

RUN apt-get update && apt-get install -y --no-install-recommends \
    # 1. 컴파일러
    gcc \
    # 2. MySQL 클라이언트 개발 라이브러리 (필수)
    default-libmysqlclient-dev \
    # 3. pkg-config (로그에서 누락되었다고 알림)
    pkg-config \
    # 4. 기타 도구 (선택적)
    && rm -rf /var/lib/apt/lists/*


COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --no-input

ENV PORT 8080
EXPOSE 8080
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "config.wsgi:application", "--timeout", "600"]
