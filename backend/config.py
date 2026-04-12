import os
from datetime import timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "a-very-long-secret-key-for-placement-portal-2026")
    # Always use backend/placement.db so cwd does not create duplicate empty DBs
    _SQLITE_PATH = os.path.join(BASE_DIR, "placement.db")
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + _SQLITE_PATH.replace("\\", "/")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "jwt-long-secret-key-placement-portal-2026")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    CACHE_TYPE = "RedisCache"
    CACHE_REDIS_URL = "redis://localhost:6379/0"
    CACHE_DEFAULT_TIMEOUT = 300
    CELERY_BROKER_URL = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND = "redis://localhost:6379/1"
    # MailHog: run ~/go/bin/MailHog then export USE_MAILHOG=1 (see mailhog.dev.env). UI: http://127.0.0.1:8025
    _use_mailhog = os.environ.get("USE_MAILHOG", "").lower() in ("1", "true", "yes")
    if _use_mailhog:
        MAIL_SERVER = os.environ.get("MAIL_SERVER", "127.0.0.1")
        MAIL_PORT = int(os.environ.get("MAIL_PORT", "1025"))
        MAIL_USE_TLS = False
        MAIL_USERNAME = ""
        MAIL_PASSWORD = ""
        MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "noreply@local.test")
    else:
        MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
        MAIL_PORT = int(os.environ.get("MAIL_PORT", "587"))
        MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() in ("1", "true", "yes")
        MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "")
        MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "")
        _mail_user = os.environ.get("MAIL_DEFAULT_SENDER", "") or MAIL_USERNAME
        MAIL_DEFAULT_SENDER = _mail_user or "noreply@local.test"
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB
