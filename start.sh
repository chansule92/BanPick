#!/bin/bash

# Render에서 제공하는 $PORT 환경 변수를 사용하거나, 기본값 8000을 사용합니다.
if [ -z "$PORT" ]; then
    PORT=8000
fi

# 마이그레이션 적용
python manage.py migrate --noinput

# Gunicorn 실행 (워커 수 설정은 성능에 중요합니다. 일반적인 권장사항: (2 * 코어 수) + 1)
# **주의:** myproject.wsgi는 여러분의 Django 프로젝트 이름으로 변경해야 합니다.
# 0.0.0.0에서 $PORT로 리스닝하여 Render의 요청을 받습니다.
exec gunicorn myproject.wsgi:application --bind 0.0.0.0:$PORT --workers 4
