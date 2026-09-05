import os
from pathlib import Path

from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

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
    # Unfold must be before Django's admin app so it can supply the admin theme.
    "unfold",
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

# A focused admin workspace for the book library. The dashboard data is supplied
# at request time so every administrator sees current download activity.
UNFOLD = {
    "SITE_TITLE": "Awakening Saints Admin",
    "SITE_HEADER": "Awakening Saints",
    "SITE_SUBHEADER": "Digital Library",
    "SITE_SYMBOL": "auto_stories",
    "SITE_URL": "/",
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": True,
    "DASHBOARD_CALLBACK": "ecomapp.admin_dashboard.dashboard_callback",
    "COLORS": {
        "primary": {
            "50": "#f0f9ff",
            "100": "#e0f2fe",
            "200": "#bae6fd",
            "300": "#7dd3fc",
            "400": "#38bdf8",
            "500": "#0ea5e9",
            "600": "#0284c7",
            "700": "#0369a1",
            "800": "#075985",
            "900": "#0c4a6e",
            "950": "#082f49",
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": True,
        "navigation": [
            {
                "title": "Library",
                "items": [
                    {
                        "title": "Books",
                        "icon": "menu_book",
                        "link": "/admin/ecomapp/product/",
                    },
                    {
                        "title": "Download activity",
                        "icon": "download",
                        "link": "/admin/ecomapp/freebookdownload/",
                        "badge": "ecomapp.admin_dashboard.downloads_today_badge",
                        "badge_variant": "info",
                    },
                    {
                        "title": "Categories",
                        "icon": "category",
                        "link": "/admin/ecomapp/category/",
                    },
                    {
                        "title": "Book previews",
                        "icon": "preview",
                        "link": "/admin/ecomapp/bookpreview/",
                    },
                    {
                        "title": "Reader reviews",
                        "icon": "rate_review",
                        "link": "/admin/ecomapp/bookreview/",
                    },
                ],
            },
            {
                "title": "Communication",
                "items": [
                    {
                        "title": "Email subscribers",
                        "icon": "mark_email_read",
                        "link": "/admin/ecomapp/emailsubscriber/",
                    },
                    {
                        "title": "Subscriber messages",
                        "icon": "campaign",
                        "link": "/admin/ecomapp/subscribermessage/",
                    },
                ],
            },
            {
                "title": "Legacy commerce",
                "items": [
                    {
                        "title": "Book orders",
                        "icon": "receipt_long",
                        "link": "/admin/ecomapp/bookorder/",
                    },
                    {
                        "title": "Payment logs",
                        "icon": "payments",
                        "link": "/admin/ecomapp/paymentlog/",
                    },
                ],
            },
        ],
    },
}

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

DATABASE_URL = (
    os.getenv("DATABASE_URL")
    or os.getenv("POSTGRES_URL")
    or os.getenv("POSTGRES_PRISMA_URL")
)
MYSQL_ENVIRONMENT = {
    "DB_NAME": os.getenv("DB_NAME"),
    "DB_USER": os.getenv("DB_USER"),
    "DB_PASSWORD": os.getenv("DB_PASSWORD"),
}
MYSQL_SETTINGS = {
    "NAME": MYSQL_ENVIRONMENT["DB_NAME"],
    "USER": MYSQL_ENVIRONMENT["DB_USER"],
    "PASSWORD": MYSQL_ENVIRONMENT["DB_PASSWORD"],
}

if DATABASE_URL:
    import dj_database_url

    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=0,
        )
    }
elif all(MYSQL_SETTINGS.values()):
    # Namecheap's Python environment normally has PyMySQL available instead of
    # mysqlclient. Register it before Django loads its MySQL backend.
    import pymysql

    pymysql.install_as_MySQLdb()
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            **MYSQL_SETTINGS,
            "HOST": os.getenv("DB_HOST", "localhost"),
            "PORT": os.getenv("DB_PORT", "3306"),
            "OPTIONS": {"charset": "utf8mb4"},
        }
    }
elif any(MYSQL_ENVIRONMENT.values()):
    missing_settings = [
        name
        for name, value in MYSQL_ENVIRONMENT.items()
        if not value
    ]
    raise ImproperlyConfigured(
        "Incomplete MySQL configuration. Set DB_NAME, DB_USER and DB_PASSWORD. "
        f"Missing: {', '.join(missing_settings)}."
    )
elif DEBUG:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    raise ImproperlyConfigured(
        "Database configuration is missing. Set DATABASE_URL for PostgreSQL or "
        "DB_NAME, DB_USER and DB_PASSWORD for MySQL."
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

# Vercel uploads ``collectstatic`` output to its CDN. Treat the repository's
# existing media library as a prefixed static source there, but keep MEDIA_URL
# outside STATIC_URL: Django 6 rejects nested media/static URLs.
IS_VERCEL = bool(os.getenv("VERCEL"))
if IS_VERCEL:
    STATICFILES_DIRS = [
        BASE_DIR / "static",
        ("media", BASE_DIR / "media"),
    ]
else:
    STATICFILES_DIRS = [BASE_DIR / "static"]

# On Vercel, vercel.json rewrites /media/* to the collected /static/media/*
# assets. Keeping this distinct from STATIC_URL is required by Django 6.
MEDIA_URL = "/media/"

MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# Vercel Functions cannot persist uploads under /var/task. Existing repository
# media remains available through the /media/ -> /static/media/ rewrite, while
# all new FileField/ImageField uploads are stored in Vercel Blob.
if IS_VERCEL:
    STORAGES = {
        "default": {"BACKEND": "ecom.storage.VercelBlobStorage"},
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        },
    }



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
