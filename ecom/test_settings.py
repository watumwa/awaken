import os

from .settings import *


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.getenv("AWAKE_TEST_DATABASE", BASE_DIR / "test.sqlite3"),
    }
}

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
