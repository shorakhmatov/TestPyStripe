"""
Django settings 
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-change-me')
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'payments',  
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'stripe_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'stripe_project.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


STRIPE_PUBLIC_KEY_USD = os.getenv('STRIPE_PUBLIC_KEY_USD')
STRIPE_SECRET_KEY_USD = os.getenv('STRIPE_SECRET_KEY_USD')
STRIPE_PUBLIC_KEY_EUR = os.getenv('STRIPE_PUBLIC_KEY_EUR')
STRIPE_SECRET_KEY_EUR = os.getenv('STRIPE_SECRET_KEY_EUR')

STRIPE_PUBLIC_KEYS = {
    'usd': STRIPE_PUBLIC_KEY_USD,
    'eur': STRIPE_PUBLIC_KEY_EUR or STRIPE_PUBLIC_KEY_USD,  
}

STRIPE_SECRET_KEYS = {
    'usd': STRIPE_SECRET_KEY_USD,
    'eur': STRIPE_SECRET_KEY_EUR or STRIPE_SECRET_KEY_USD,  
}

# Базовый ключ по умолчанию (USD)
STRIPE_PUBLIC_KEY = STRIPE_PUBLIC_KEY_USD
STRIPE_SECRET_KEY = STRIPE_SECRET_KEY_USD


# URL для перенаправления после входа
LOGIN_REDIRECT_URL = '/profile/'

# URL для перенаправления после выхода
LOGOUT_REDIRECT_URL = '/'

# URL страницы входа
LOGIN_URL = '/accounts/login/'

# Шаблоны для аутентификации
TEMPLATES[0]['DIRS'] = [BASE_DIR / 'templates']
