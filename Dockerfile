# 사용할 Python 기본 이미지 선택 (경량 버전 권장)
FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /usr/src/app

# 시스템 라이브러리 업데이트 및 설치 (필요한 경우)
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     ... 필요한 라이브러리 ... \
#     && rm -rf /var/lib/apt/lists/*

# 파이썬 의존성 파일 복사 및 설치
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 파일 복사 (manage.py 및 모든 코드)
COPY . .

# Django 정적 파일 수집 (배포 전 필수)
RUN python manage.py collectstatic --no-input

# 환경 변수를 설정 (Gunicorn에서 사용할 포트를 명시)
ENV PORT 8000
# Render는 일반적으로 PORT 환경 변수를 통해 외부 포트를 연결하지만, 
# Dockerfile에서는 내부 컨테이너 포트를 명시적으로 설정할 수 있습니다.
# Render는 Dockerfile의 EXPOSE 포트를 감지하고 이를 웹 서비스의 대상으로 사용합니다.
EXPOSE 8000

# 컨테이너 시작 시 실행될 명령어 (Start Command 역할)
# Gunicorn을 실행할 때 컨테이너 내부의 포트(여기서는 8000)에 바인딩하도록 명시합니다.
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "config.wsgi:application"]
