# 사용할 Python 기본 이미지 선택 (경량 버전 권장)
FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /usr/src/app

# 🚨🚨🚨 이 섹션을 반드시 수정하세요 🚨🚨🚨
# 시스템 라이브러리 업데이트 및 MySQLdb 설치를 위한 패키지 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    # 1. 컴파일러
    gcc \
    # 2. MySQL 클라이언트 개발 라이브러리 (필수)
    default-libmysqlclient-dev \
    # 3. pkg-config (로그에서 누락되었다고 알림)
    pkg-config \
    # 4. 기타 도구 (선택적)
    && rm -rf /var/lib/apt/lists/*

# 파이썬 의존성 파일 복사 및 설치
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
# ... (이후 collectstatic 및 CMD는 그대로 둡니다)


COPY . .


RUN python manage.py collectstatic --no-input


ENV PORT 8000
EXPOSE 8000


CMD ["gunicorn", "--bind", "0.0.0.0:8000", "config.wsgi:application"]
