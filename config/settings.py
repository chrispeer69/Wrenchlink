import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env(name, default=None):
    value = os.getenv(name, default)
    return value.strip() if isinstance(value, str) else value


def env_bool(name, default=False):
    return str(env(name, str(default))).lower() in {"1", "true", "yes", "on"}


DEBUG = env_bool("DJANGO_DEBUG", False)
SECRET_KEY = env("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "local-development-only-change-me"
    else:
        raise ImproperlyConfigured("DJANGO_SECRET_KEY must be set when DJANGO_DEBUG=False.")

ALLOWED_HOSTS = [
    host.strip()
    for host in env("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]
if "healthcheck.railway.app" not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append("healthcheck.railway.app")
railway_domain = env("RAILWAY_PUBLIC_DOMAIN")
if railway_domain and railway_domain not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(railway_domain)

CSRF_TRUSTED_ORIGINS = [
    origin.strip().rstrip("/")
    for origin in env("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",")
    if origin.strip().startswith(("http://", "https://"))
]
if railway_domain:
    railway_origin = f"https://{railway_domain}"
    if railway_origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(railway_origin)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "accounts",
    "marketplace",
    "billing",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "marketplace.middleware.RequestSizeLimitMiddleware",
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
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "marketplace.context_processors.notification_counts",
            ],
        },
    },
]
WSGI_APPLICATION = "config.wsgi.application"

skip_database_config = env_bool("SKIP_DATABASE_CONFIG", False)
use_postgres = not skip_database_config and (
    env_bool("USE_POSTGRES", False)
    or bool(env("DATABASE_URL") or env("PGHOST") or env("DB_HOST"))
)
if use_postgres:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env("DB_NAME") or env("PGDATABASE"),
            "USER": env("DB_USER") or env("PGUSER"),
            "PASSWORD": env("DB_PASSWORD") or env("PGPASSWORD"),
            "HOST": env("DB_HOST") or env("PGHOST"),
            "PORT": env("DB_PORT") or env("PGPORT", "5432"),
            "CONN_MAX_AGE": 60,
            "OPTIONS": {"sslmode": env("DB_SSLMODE", "prefer")},
        }
    }
    missing = [
        key
        for key, value in DATABASES["default"].items()
        if key in {"NAME", "USER", "PASSWORD", "HOST"} and not value
    ]
    if missing:
        raise ImproperlyConfigured(
            "PostgreSQL is enabled but database variables are incomplete: "
            + ", ".join(missing)
        )
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_USER_MODEL = "accounts.User"
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = env("DJANGO_TIME_ZONE", "America/New_York")
USE_I18N = True
USE_TZ = True

STATIC_URL = "/assets/"
STATICFILES_DIRS = [BASE_DIR / "assets"]
STATIC_ROOT = BASE_DIR / "staticfiles"
default_storage = {"BACKEND": "django.core.files.storage.FileSystemStorage"}
if env("AWS_STORAGE_BUCKET_NAME"):
    default_storage = {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            "bucket_name": env("AWS_STORAGE_BUCKET_NAME"),
            "endpoint_url": env("AWS_S3_ENDPOINT_URL") or None,
            "access_key": env("AWS_ACCESS_KEY_ID"),
            "secret_key": env("AWS_SECRET_ACCESS_KEY"),
            "region_name": env("AWS_S3_REGION_NAME") or None,
            "default_acl": "private",
            "querystring_auth": True,
            "file_overwrite": False,
        },
    }

STORAGES = {
    "default": default_storage,
    "staticfiles": {
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage"
            if DEBUG
            else "whitenoise.storage.CompressedManifestStaticFilesStorage"
        )
    },
}
MEDIA_URL = "/private-media/"
railway_volume = env("RAILWAY_VOLUME_MOUNT_PATH")
default_media_root = Path(railway_volume) / "media" if railway_volume else BASE_DIR / "media"
MEDIA_ROOT = Path(env("MEDIA_ROOT", default_media_root))
DATA_UPLOAD_MAX_MEMORY_SIZE = 12 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
MAX_REQUEST_BODY_SIZE = 12 * 1024 * 1024

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "accounts:dashboard"
LOGOUT_REDIRECT_URL = "home"

EMAIL_BACKEND = env(
    "EMAIL_BACKEND",
    "django.core.mail.backends.smtp.EmailBackend"
    if env("EMAIL_HOST_USER")
    else "django.core.mail.backends.console.EmailBackend",
)
EMAIL_HOST = env("EMAIL_HOST") or "smtp.gmail.com"
EMAIL_PORT = int(env("EMAIL_PORT", "587"))
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = (
    env("DEFAULT_FROM_EMAIL") or EMAIL_HOST_USER or "noreply@wrenchlink.io"
)

ADMIN_URL = env("DJANGO_ADMIN_URL", "platform-control/").strip("/")
if not DEBUG and ADMIN_URL in {"admin", "platform-control", ""}:
    raise ImproperlyConfigured(
        "Set DJANGO_ADMIN_URL to a private, unguessable path in production."
    )

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", not DEBUG)
SECURE_REDIRECT_EXEMPT = [r"^health/$"]
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
X_FRAME_OPTIONS = "DENY"

STRIPE_SECRET_KEY = env("STRIPE_SECRET_KEY", "")
STRIPE_PUBLISHABLE_KEY = env("STRIPE_PUBLISHABLE_KEY", "")
STRIPE_WEBHOOK_SECRET = env("STRIPE_WEBHOOK_SECRET", "")
STRIPE_TECH_PRICE_ID = env("STRIPE_TECH_PRICE_ID", "")
STRIPE_STARTER_PRICE_ID = env("STRIPE_STARTER_PRICE_ID", "")
STRIPE_PRO_PRICE_ID = env("STRIPE_PRO_PRICE_ID", "")
