import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-trizen-photo-sharing-platform-secret-key-2026')
DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 't')
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,0.0.0.0').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'core',
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

ROOT_URLCONF = 'photo_sharing.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'core' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
            ],
        },
    },
]

WSGI_APPLICATION = 'photo_sharing.wsgi.application'

# Custom User Model
AUTH_USER_MODEL = 'core.User'

# Database Configuration
# Supports DATABASE_URL connection string (e.g., Supabase Postgres), individual DB env vars, or local SQLite fallback
DATABASE_URL = os.getenv('DATABASE_URL')
USE_POSTGRES = os.getenv('USE_POSTGRES', 'False').lower() in ('true', '1', 't')

if DATABASE_URL:
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            ssl_require=os.getenv('DB_SSL_REQUIRE', 'False').lower() in ('true', '1', 't'),
        )
    }
elif USE_POSTGRES:
    DATABASES = {
        'default': {
            'ENGINE': os.getenv('DB_ENGINE', 'django.db.backends.postgresql'),
            'NAME': os.getenv('DB_NAME', 'postgres'),
            'USER': os.getenv('DB_USER', 'postgres'),
            'PASSWORD': os.getenv('DB_PASSWORD', ''),
            'HOST': os.getenv('DB_HOST', 'localhost'),
            'PORT': os.getenv('DB_PORT', '5432'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }



AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media Storage Configuration
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Cloudflare R2 Object Storage Configuration
r2_bucket = os.getenv('R2_BUCKET_NAME') or os.getenv('AWS_STORAGE_BUCKET_NAME')
USE_R2_STORAGE = os.getenv('USE_R2_STORAGE', 'True' if r2_bucket else 'False').lower() in ('true', '1', 't')
if USE_R2_STORAGE:
    AWS_ACCESS_KEY_ID = os.getenv('R2_ACCESS_KEY_ID') or os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('R2_SECRET_ACCESS_KEY') or os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = r2_bucket

    
    r2_account_id = os.getenv('R2_ACCOUNT_ID')
    if r2_account_id:
        AWS_S3_ENDPOINT_URL = f"https://{r2_account_id}.r2.cloudflarestorage.com"
    else:
        AWS_S3_ENDPOINT_URL = os.getenv('R2_ENDPOINT_URL') or os.getenv('AWS_S3_ENDPOINT_URL')
        
    AWS_S3_REGION_NAME = os.getenv('R2_REGION_NAME', 'auto')
    AWS_DEFAULT_ACL = None
    AWS_QUERYSTRING_AUTH = True  # Enable presigned temporary URLs
    AWS_QUERYSTRING_EXPIRE = 900  # 15 minute temporary URL expiry
    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3.S3Storage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }

# Authentication URLs
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/login/'

# REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
