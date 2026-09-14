from pathlib import Path
import os

from dotenv import load_dotenv


# ============================================================
# BASE DIRECTORY
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent


# ============================================================
# ENVIRONMENT VARIABLES
# ============================================================

load_dotenv(BASE_DIR / ".env")


# ============================================================
# SECURITY
# ============================================================

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-change-this-in-production",
)

DEBUG = os.environ.get(
    "DEBUG",
    "False",
).lower() in ("1", "true", "yes", "on")


# ============================================================
# ALLOWED HOSTS
# ============================================================

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "testserver",
    "curex-diagnostic-center.vercel.app",
    ".vercel.app",
]

extra_allowed_hosts = os.environ.get(
    "DJANGO_ALLOWED_HOSTS",
    "",
).split(",")

for host in extra_allowed_hosts:
    host = host.strip()

    if host and host not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(host)


# ============================================================
# APPLICATIONS#
INSTALLED_APPS = [
    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third-party
    "storages",

    # Project apps
    "accounts",
    "customers",
    "dashboard",
    "inventory",
    "orders",
    "results",
    "sales",
    "sitecontent",
    "whatsapp_bot",
]



# ============================================================
# MIDDLEWARE
# ============================================================

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",

    # WhiteNoise serves Django static files
    "whitenoise.middleware.WhiteNoiseMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# ============================================================
# URLS / WSGI
# ============================================================

ROOT_URLCONF = "salesplatform.urls"

WSGI_APPLICATION = "salesplatform.wsgi.application"


# ============================================================
# TEMPLATES
# ============================================================

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "templates",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


# ============================================================
# DATABASE
# ============================================================
#
# Vercel / production:
#   DATABASE_URL should contain your Supabase PostgreSQL URL.
#
# Local:
#   If DATABASE_URL is not available, SQLite is used.
#
# ============================================================

DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()

if DATABASE_URL:
    import dj_database_url

    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
            ssl_require=True,
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


# ============================================================
# PASSWORD VALIDATION
# ============================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "MinimumLengthValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "CommonPasswordValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "NumericPasswordValidator"
        ),
    },
]


# ============================================================
# INTERNATIONALIZATION
# ============================================================

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Africa/Lagos"

USE_I18N = True

USE_TZ = True


# ============================================================
# STATIC FILES
# ============================================================
#
# IMPORTANT:
# STATIC_URL MUST be defined.
#
# Django templates use:
# {% load static %}
# {% static "..." %}
#
# ============================================================

STATIC_URL = "/static/"

STATICFILES_DIRS = [
    BASE_DIR / "static",
]

STATIC_ROOT = BASE_DIR / "staticfiles"


# ============================================================
# MEDIA FILES
# ============================================================
#
# Local development can use:
#     media/
#
# Production on Vercel MUST use Supabase S3.
#
# ============================================================

MEDIA_URL = "/media/"

MEDIA_ROOT = BASE_DIR / "media"


# ============================================================
# SUPABASE S3 STORAGE
# ============================================================

USE_S3 = os.environ.get(
    "USE_S3",
    "False",
).lower() in ("1", "true", "yes", "on")


# Vercel should ALWAYS use S3.
if os.environ.get(
    "VERCEL",
    "",
).lower() in ("1", "true", "yes", "on"):
    USE_S3 = True


# ============================================================
# DJANGO STORAGE CONFIGURATION
# ============================================================

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },

    "staticfiles": {
        "BACKEND": (
            "whitenoise.storage.CompressedManifestStaticFilesStorage"
            if not DEBUG
            else "django.contrib.staticfiles.storage.StaticFilesStorage"
        ),
    },
}


# ============================================================
# SUPABASE S3
# ============================================================

if USE_S3:

    AWS_ACCESS_KEY_ID = os.environ.get(
        "AWS_ACCESS_KEY_ID",
        "",
    )

    AWS_SECRET_ACCESS_KEY = os.environ.get(
        "AWS_SECRET_ACCESS_KEY",
        "",
    )

    AWS_STORAGE_BUCKET_NAME = os.environ.get(
        "AWS_STORAGE_BUCKET_NAME",
        "curexdiagnostic",
    )

    AWS_S3_REGION_NAME = os.environ.get(
        "AWS_S3_REGION_NAME",
        "eu-central-1",
    )

    AWS_S3_ENDPOINT_URL = os.environ.get(
        "AWS_S3_ENDPOINT_URL",
        "https://elcdmtupofucgjzabuxc.storage.supabase.co/storage/v1/s3",
    )

    AWS_S3_ADDRESSING_STYLE = os.environ.get(
        "AWS_S3_ADDRESSING_STYLE",
        "path",
    )

    AWS_S3_SIGNATURE_VERSION = "s3v4"

    AWS_DEFAULT_ACL = None

    AWS_S3_FILE_OVERWRITE = False

    AWS_QUERYSTRING_AUTH = True

    AWS_QUERYSTRING_EXPIRE = 3600

    # All uploaded media files go to Supabase S3.
    STORAGES["default"] = {
        "BACKEND": "storages.backends.s3.S3Storage",
    }


# ============================================================
# DEFAULT PRIMARY KEY
# ============================================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ============================================================
# AUTHENTICATION
# ============================================================

LOGIN_URL = "/accounts/login/"

LOGIN_REDIRECT_URL = "/dashboard/"

LOGOUT_REDIRECT_URL = "/accounts/login/"


# ============================================================
# CSRF
# ============================================================

CSRF_TRUSTED_ORIGINS = [
    "https://curex-diagnostic-center.vercel.app",
    "https://*.vercel.app",
]


extra_csrf_origins = os.environ.get(
    "DJANGO_CSRF_TRUSTED_ORIGINS",
    "",
).split(",")

for origin in extra_csrf_origins:
    origin = origin.strip()

    if origin and origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(origin)


# ============================================================
# VERCEL / HTTPS
# ============================================================

SECURE_PROXY_SSL_HEADER = (
    "HTTP_X_FORWARDED_PROTO",
    "https",
)


# ============================================================
# SECURITY SETTINGS
# ============================================================

if not DEBUG:

    SECURE_SSL_REDIRECT = True

    SESSION_COOKIE_SECURE = True

    CSRF_COOKIE_SECURE = True

    SECURE_HSTS_SECONDS = 31536000

    SECURE_HSTS_INCLUDE_SUBDOMAINS = True

    SECURE_HSTS_PRELOAD = True


# ============================================================
# WHITE NOISE
# ============================================================

STATICFILES_STORAGE = (
    "whitenoise.storage.CompressedManifestStaticFilesStorage"
)


# ============================================================
# SESSION / CSRF
# ============================================================

SESSION_COOKIE_HTTPONLY = True

CSRF_COOKIE_HTTPONLY = False


# ============================================================
# FILE UPLOAD LIMITS
# ============================================================

DATA_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024

FILE_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024


# ============================================================
# EMAIL
# ============================================================

EMAIL_BACKEND = os.environ.get(
    "EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend",
)

EMAIL_HOST = os.environ.get(
    "EMAIL_HOST",
    "",
)

EMAIL_PORT = int(
    os.environ.get(
        "EMAIL_PORT",
        "587",
    )
)

EMAIL_USE_TLS = os.environ.get(
    "EMAIL_USE_TLS",
    "True",
).lower() in ("1", "true", "yes", "on")

EMAIL_HOST_USER = os.environ.get(
    "EMAIL_HOST_USER",
    "",
)

EMAIL_HOST_PASSWORD = os.environ.get(
    "EMAIL_HOST_PASSWORD",
    "",
)

DEFAULT_FROM_EMAIL = os.environ.get(
    "DEFAULT_FROM_EMAIL",
    "Curex Diagnostic Center <noreply@curexdiagnostic.com>",
)


# ============================================================
# WHATSAPP BOT
# ============================================================

WHATSAPP_ACCESS_TOKEN = os.environ.get(
    "WHATSAPP_ACCESS_TOKEN",
    "",
)

WHATSAPP_PHONE_NUMBER_ID = os.environ.get(
    "WHATSAPP_PHONE_NUMBER_ID",
    "",
)

WHATSAPP_VERIFY_TOKEN = os.environ.get(
    "WHATSAPP_VERIFY_TOKEN",
    "",
)


# ============================================================
# LOGGING
# ============================================================

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,

    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },

    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },

    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}