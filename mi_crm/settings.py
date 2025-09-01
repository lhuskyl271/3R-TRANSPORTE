# settings.py

import os
from pathlib import Path
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-default-key-for-local-development')

# SECURITY WARNING: don't run with debug turned on in production!
# El modo DEBUG se activará solo si la variable de entorno DEBUG no está establecida como 'False'
DEBUG = os.environ.get('DEBUG', 'True') != 'False'

ALLOWED_HOSTS = os.environ.get(
    'DJANGO_ALLOWED_HOSTS',
    'threer-transporte.onrender.com,localhost,127.0.0.1'
).split(',')


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'ventas.apps.VentasConfig',
    'storages',  # Para gestionar archivos con S3
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # Importante: Whitenoise para archivos estáticos
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'mi_crm.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

WSGI_APPLICATION = 'mi_crm.wsgi.application'


# --- ✅ CONFIGURACIÓN DE BASE DE DATOS MODIFICADA ---
# Detecta si estás en Render (usando DATABASE_URL) o en tu máquina local.

if 'DATABASE_URL' in os.environ:
    # Configuración para Producción (Render)
    DATABASES = {
        'default': dj_database_url.config(
            conn_max_age=600,
            ssl_require=True
        )
    }
else:
    # Configuración para Desarrollo Local (tu computadora)
    # Usa un archivo de base de datos simple llamado db.sqlite3
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'es-es'
TIME_ZONE = 'America/Mexico_City'
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images) & Media Files (User Uploads)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_BUCKET_NAME')
AWS_S3_REGION_NAME = os.environ.get('AWS_REGION')
AWS_LOCATION = 'media'  # Carpeta dentro de tu bucket para archivos subidos por usuarios
AWS_S3_SIGNATURE_VERSION = 's3v4'
AWS_S3_ADDRESSING_STYLE = 'virtual'

# Configuración condicional para S3 (producción) o local
if AWS_STORAGE_BUCKET_NAME:
    # --- Configuración para S3 (Producción) ---
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com'
    STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/static/'
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/{AWS_LOCATION}/'
    
    # Almacenamiento para archivos estáticos y de medios en S3
    STATICFILES_STORAGE = 'storages.backends.s3boto3.S3StaticStorage'
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    
    # El STATIC_ROOT es donde `collectstatic` pondrá los archivos antes de subirlos a S3.
    # No se usa para servir archivos directamente en producción con S3.
    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles_build')
    
else:
    # --- Configuración para Desarrollo Local ---
    STATIC_URL = '/static/'
    MEDIA_URL = '/media/'
    
    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles') # Para collectstatic local
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')      # Donde se guardan los archivos subidos
    
    # Directorios donde Django buscará archivos estáticos adicionales
    STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
    
    # Whitenoise es una excelente opción para servir estáticos en desarrollo y algunas producciones simples
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
    DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'


# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# URLs de autenticación
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login'

# Para seguridad en producción con HTTPS
CSRF_TRUSTED_ORIGINS = [
    'https://threer-transporte.onrender.com',
]