import os
import dj_database_url
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent 

DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL'),
        conn_max_age=600 
    )
}

SECRET_KEY = 'django-insecure-n@5*w)f0u*o#^i47f(6&ec%8clz#*j@inf5kb4kn0ngchwft43'
