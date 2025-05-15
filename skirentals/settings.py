from pathlib import Path
import os

import dj_database_url

from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

GOOGLE_OAUTH_CLIENT_ID = os.environ.get('GOOGLE_OAUTH_CLIENT_ID')
if not GOOGLE_OAUTH_CLIENT_ID and "CI" not in os.environ:
    raise ValueError(
        'GOOGLE_OAUTH_CLIENT_ID is missing. '
        'Have you set it as an environment variable or in a .env file?'
    )

# sign in popup
SECURE_REFERRER_POLICY = 'no-referrer-when-downgrade'
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin-allow-popups"

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# File Upload settings
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Create a temp directory for file uploads
FILE_UPLOAD_TEMP_DIR = os.path.join(BASE_DIR, 'tmp')
os.makedirs(FILE_UPLOAD_TEMP_DIR, exist_ok=True)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    # Fallback to a default secret key for testing only
    SECRET_KEY = 'django-insecure-$eh8p018&m8)r0m$6obyl_v0^es%3oe70^d#awiu@zea=-&c)%'

# SECURITY WARNING: don't run with debug turned on in production!
IS_HEROKU_APP = "DYNO" in os.environ and "CI" not in os.environ
DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'

if IS_HEROKU_APP:

    SITE_ID = 2
    ALLOWED_HOSTS = ["*"]

    SECURE_SSL_REDIRECT = True
else:
    ALLOWED_HOSTS = ['127.0.0.1', 'localhost']
    SITE_ID = 1




# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    "whitenoise.runserver_nostatic",
    'equipment', # Add the equipment app to the list of installed apps
    'users',  # Add the users app to the list of installed apps

    #login packages
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',

    # S3 storage
    'storages',
]

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        }
    }
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'skirentals.middleware.AdminRedirectMiddleware',
    'skirentals.middleware.OAuthCancelledMiddleware',
    'skirentals.middleware.AccountCleanupMiddleware',
]

ROOT_URLCONF = 'skirentals.urls'

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

WSGI_APPLICATION = 'skirentals.wsgi.application'


# Database
if IS_HEROKU_APP:
    # In production on Heroku the database configuration is derived from the `DATABASE_URL`
    # environment variable by the dj-database-url package. `DATABASE_URL` will be set
    # automatically by Heroku when a database addon is attached to your Heroku app. See:
    # https://devcenter.heroku.com/articles/provisioning-heroku-postgres#application-config-vars
    # https://github.com/jazzband/dj-database-url
    DATABASES = {
        "default": dj_database_url.config(
            env="DATABASE_URL",
            conn_max_age=600,
            conn_health_checks=True,
            ssl_require=True,
        ),
    }
else:
    # When running locally in development or in CI, a sqlite database file will be used instead
    # to simplify initial setup. Longer term it's recommended to use Postgres locally too.
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'EST'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),  # Ensure this is correct
]

STATIC_URL = "/static/"

STORAGES = {
    # Enable WhiteNoise's GZip and Brotli compression of static assets:
    # https://whitenoise.readthedocs.io/en/latest/django.html#add-compression-and-caching-support
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Don't store the original (un-hashed filename) version of static files, to reduce slug size:
# https://whitenoise.readthedocs.io/en/latest/django.html#WHITENOISE_KEEP_ONLY_HASHED_FILES
WHITENOISE_KEEP_ONLY_HASHED_FILES = True

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
)

LOGIN_REDIRECT_URL = "dashboard_redirect"
LOGOUT_REDIRECT_URL = "/"

# Additional Allauth settings
ACCOUNT_EMAIL_REQUIRED = False
ACCOUNT_EMAIL_VERIFICATION = "none"
ACCOUNT_USERNAME_REQUIRED = True
SOCIALACCOUNT_AUTO_SIGNUP = False  # Require users to fill out the signup form
SOCIALACCOUNT_LOGIN_ON_GET = True  # Skip the intermediate "Do you want to sign in with Google?" page

# Email Configuration
# For development, emails will be printed to the console
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# In production, you would use something like this:
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = 'smtp.example.com'
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = 'your-email@example.com'
# EMAIL_HOST_PASSWORD = 'your-password'
# DEFAULT_FROM_EMAIL = 'SkiRentals <no-reply@skirentals.com>'

# AWS S3 Configuration
USE_S3 = os.environ.get('USE_S3', 'False') == 'True'

if USE_S3:
    # AWS Settings
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_OBJECT_OWNERSHIP = 'BucketOwnerPreferred'
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
    AWS_S3_OBJECT_PARAMETERS = {'CacheControl': 'max-age=86400'}

    # S3 Storage Settings
    STORAGES['default'] = {'BACKEND': 'storages.backends.s3boto3.S3Boto3Storage'}
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/'
else:
    # Local storage settings
    MEDIA_URL = '/media/'
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
    STORAGES['default'] = {'BACKEND': 'django.core.files.storage.FileSystemStorage'}