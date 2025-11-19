import os
import dj_database_url
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent 

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql', 
        'NAME': 'banpick_postgresql',   
        'USER': 'banpick_postgresql_user',  
        'PASSWORD': 'WL9YPmomzpLbwuvgP8lbs9imR55Zb6q2', 
        # (Render 내부 네트워크 통신용 주소)
        'HOST': 'postgresql://banpick_postgresql_user:WL9YPmomzpLbwuvgP8lbs9imR55Zb6q2@dpg-d4emop0gjchc73fka7gg-a/banpick_postgresql', 
        'PORT': '5432',  
    }
}
SECRET_KEY = 'django-insecure-n@5*w)f0u*o#^i47f(6&ec%8clz#*j@inf5kb4kn0ngchwft43'
