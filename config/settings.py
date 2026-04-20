from pathlib import Path
import os


BASE_DIR = Path(__file__).resolve().parent.parent


def env(name, default=None):
    return os.environ.get(name, default)


def env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


DJANGO_ENV = env("DJANGO_ENV", "development").lower()
ENV_SUFFIX = "PROD" if DJANGO_ENV in {"prod", "production"} else "DEV"


def env_for_environment(name, default=None):
    return env(f"{name}_{ENV_SUFFIX}", env(name, default))


SECRET_KEY = env("DJANGO_SECRET_KEY", "unsafe-development-key-change-me")
DEBUG = env_bool("DJANGO_DEBUG", True)
ALLOWED_HOSTS = [host.strip() for host in env("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if host.strip()]


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "storages",
    "accounts",
    "blog",
    "comments",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


if ENV_SUFFIX == "DEV":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / env("SQLITE_NAME_DEV", "db.sqlite3"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": env("DB_ENGINE_PROD", env("DB_ENGINE", "django.db.backends.postgresql")),
            "NAME": env_for_environment("DB_NAME", "django_blog"),
            "USER": env_for_environment("DB_USER", "django_blog"),
            "PASSWORD": env_for_environment("DB_PASSWORD", ""),
            "HOST": env_for_environment("DB_HOST", "localhost"),
            "PORT": env_for_environment("DB_PORT", "5432"),
        }
    }


AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = env("DJANGO_TIME_ZONE", "UTC")
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

USE_S3_STORAGE = env_bool("USE_S3_STORAGE", False)
if USE_S3_STORAGE:
    AWS_ACCESS_KEY_ID = env_for_environment("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = env_for_environment("AWS_SECRET_ACCESS_KEY")
    AWS_STORAGE_BUCKET_NAME = env_for_environment("AWS_STORAGE_BUCKET_NAME")
    AWS_S3_ENDPOINT_URL = env_for_environment("AWS_S3_ENDPOINT_URL")
    AWS_S3_REGION_NAME = env_for_environment("AWS_S3_REGION_NAME", "us-east-1")
    AWS_S3_CUSTOM_DOMAIN = env_for_environment("AWS_S3_CUSTOM_DOMAIN")
    AWS_S3_ADDRESSING_STYLE = env_for_environment("AWS_S3_ADDRESSING_STYLE", "path")
    AWS_LOCATION = env_for_environment("AWS_LOCATION", "media")
    AWS_DEFAULT_ACL = None
    AWS_QUERYSTRING_AUTH = env_bool(f"AWS_QUERYSTRING_AUTH_{ENV_SUFFIX}", env_bool("AWS_QUERYSTRING_AUTH", False))
    STORAGES = {
        "default": {"BACKEND": "storages.backends.s3boto3.S3Boto3Storage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

MAX_COVER_IMAGE_SIZE = int(env("MAX_COVER_IMAGE_SIZE", str(5 * 1024 * 1024)))
ALLOWED_COVER_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}

LOGIN_REDIRECT_URL = "blog:post_list"
LOGOUT_REDIRECT_URL = "blog:post_list"
