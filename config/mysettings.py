# 현재 데이터베이스의 값을 입력한다.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'loldb',
        'USER': 'root',
        'PASSWORD': 'glemfk12',
        'HOST': 'localhost',
        'PORT': 3306
    }
}

# settings.py에 있던 시크릿 키를 아래 ''안에 입력한다.
SECRET_KEY = 'django-insecure-n@5*w)f0u*o#^i47f(6&ec%8clz#*j@inf5kb4kn0ngchwft43'
