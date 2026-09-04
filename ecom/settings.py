import os
from pathlib import Path

from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

import pymysql     # This should be installed dependency on namecheap's ssh terminal
pymysql.install_as_MySQLdb()

DEBUG = os.getenv("DEBUG", "False").strip().lower() in {"1", "true", "yes", "on"}

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "django-insecure-local-development-only-change-me"
    else:
        raise ImproperlyConfigured("DJANGO_SECRET_KEY must be set when DEBUG=False.")

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv(
        "ALLOWED_HOSTS",
        "127.0.0.1,localhost,awakeningsaints.org,www.awakeningsaints.org,.vercel.app",
    ).split(",")
    if host.strip()
]


INSTALLED_APPS = [
    "jazzmin",
    "django_ckeditor_5",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "ecomapp.apps.EcomappConfig",
    "useraccounts.apps.UseraccountsConfig",
    "basketapp.apps.BasketappConfig",
]

AUTHENTICATION_BACKENDS = [
    "useraccounts.auth_backends.EmailAuthBackend",  # <-- use your correct path
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

# Optional: custom CSS for CKEditor styling in admin
CKEDITOR_5_CUSTOM_CSS = "css/ckeditor_custom.css"

CKEDITOR_5_CONFIGS = {
    "default": {
        "toolbar": [
            {
                "name": "styles",
                "items": [
                    "heading",
                    "bold",
                    "italic",
                    "underline",
                    "strikethrough",
                    "link",
                    "blockquote",
                    "code",
                    "codeBlock",
                ],
            },
            {
                "name": "lists",
                "items": [
                    "bulletedList",
                    "numberedList",
                    "todoList",
                ],
            },
            {
                "name": "alignment",
                "items": [
                    "alignment:left",
                    "alignment:center",
                    "alignment:right",
                    "alignment:justify",
                ],
            },
            {
                "name": "insert",
                "items": [
                    "imageUpload",
                    "mediaEmbed",
                    "insertTable",
                    "horizontalLine",
                ],
            },
            {
                "name": "undo",
                "items": ["undo", "redo"],
            },
        ],
        "blockToolbar": ["paragraph", "heading1", "heading2", "heading3", "heading4"],
        # Image toolbar when image is selected
        "image": {
            "toolbar": [
                "imageTextAlternative",  # Alt text
                "imageStyle:200px",  # Full width
                "imageStyle:side",  # Side aligned
                "imageStyle:alignLeft",
                "imageStyle:alignRight",
                "imageStyle:alignCenter",
                "imageRemove",  # Delete/remove image
            ]
        },
        # Table toolbar
        "table": {
            "contentToolbar": [
                "tableColumn",
                "tableRow",
                "mergeTableCells",
                "tableProperties",
                "tableCellProperties",
            ]
        },
        # Alignment options
        "alignment": {"options": ["left", "center", "right", "justify"]},
        # Editor dimensions
        "height": 400,
        "width": "100%",
        "placeholder": "Write text here...",
    },
}

ROOT_URLCONF = "ecom.urls"

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
                # addintional context processors
                "ecomapp.context_processors.categories",
                "basketapp.context_processors.cart",
            ],
        },
    },
]

WSGI_APPLICATION = "ecom.wsgi.application"


DATABASE_ENGINE = os.getenv("DATABASE_ENGINE", "mysql").strip().lower()

if DATABASE_ENGINE == "sqlite":
    sqlite_database_path = Path(os.getenv("SQLITE_DATABASE_PATH", "db.sqlite3"))
    if not sqlite_database_path.is_absolute():
        sqlite_database_path = BASE_DIR / sqlite_database_path

    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": sqlite_database_path,
        }
    }
elif DATABASE_ENGINE == "mysql":
    required_db_settings = {
        "DB_NAME": os.getenv("DB_NAME"),
        "DB_USER": os.getenv("DB_USER"),
        "DB_PASSWORD": os.getenv("DB_PASSWORD"),
    }
    missing_db_settings = [key for key, value in required_db_settings.items() if not value]
    if missing_db_settings:
        raise ImproperlyConfigured(
            "Missing MySQL environment settings: " + ", ".join(missing_db_settings)
        )

    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": required_db_settings["DB_NAME"],
            "USER": required_db_settings["DB_USER"],
            "PASSWORD": required_db_settings["DB_PASSWORD"],
            "HOST": os.getenv("DB_HOST", "localhost"),
            "PORT": os.getenv("DB_PORT", "3306"),
        }
    }
else:
    raise ImproperlyConfigured(
        "DATABASE_ENGINE must be either 'sqlite' for local development or 'mysql' for deployment."
    )


AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# STATIC_URL = 'static/'
# STATICFILES_DIRS = [ BASE_DIR / 'static' ]

# MEDIA_URL = '/media/'
# MEDIA_ROOT = os.path.join(BASE_DIR, 'media/')

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

# Vercel automatically uploads collectstatic output to its CDN.  Treat the
# repository's existing media library as a prefixed static source on Vercel so
# covers, sermons and previously uploaded files are served by the CDN instead of
# being copied into the Python function bundle.
IS_VERCEL = bool(os.getenv("VERCEL"))
if IS_VERCEL:
    STATICFILES_DIRS = [
        BASE_DIR / "static",
        ("media", BASE_DIR / "media"),
    ]
    MEDIA_URL = f"{STATIC_URL}media/"
else:
    STATICFILES_DIRS = [BASE_DIR / "static"]
    MEDIA_URL = "/media/"

MEDIA_ROOT = os.path.join(BASE_DIR, "media")


######## These tell django about the custom user modal we created ########
AUTH_USER_MODEL = "useraccounts.UserBase"


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG


# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# =========================
# PAYMENT GATEWAY SETTINGS
# =========================

LIVEPAY_PUBLIC_KEY = os.getenv("LIVEPAY_PUBLIC_KEY")
LIVEPAY_SECRET_KEY = os.getenv("LIVEPAY_SECRET_KEY")
LIVEPAY_BASE_URL = os.getenv("LIVEPAY_BASE_URL", "https://livepay.me/api")
LIVEPAY_ACCOUNT_NUMBER = os.getenv("LIVEPAY_ACCOUNT_NUMBER")

LIVEPAY_WEBHOOK_SECRET = os.getenv("LIVEPAY_WEBHOOK_SECRET")

# LOGIN_URL = "login"
# LOGIN_REDIRECT_URL = "/"
# LOGOUT_REDIRECT_URL = "/"

# Secure Downloads
# DOWNLOAD_LINK_EXPIRY_MINUTES = 30

DEFAULT_CURRENCY = "USD"


EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.getenv("EMAIL_HOST", "awakeningsaints.org")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "465"))
EMAIL_USE_SSL = os.getenv("EMAIL_USE_SSL", "True").strip().lower() in {"1", "true", "yes", "on"}
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "info@awakeningsaints.org")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", EMAIL_HOST_USER)


CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CSRF_TRUSTED_ORIGINS",
        "https://awakeningsaints.org,https://www.awakeningsaints.org,https://*.vercel.app",
    ).split(",")
    if origin.strip()
]
