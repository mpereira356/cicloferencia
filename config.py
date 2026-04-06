import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class Config:
    APP_NAME = "Cicloferência Bikes"
    APP_SLUG = "cicloferencia-bikes"
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-insecure-key-change-me")
    _database_url = os.getenv("DATABASE_URL", "").strip()
    if _database_url.startswith("sqlite:///") and not _database_url.startswith("sqlite:////"):
        sqlite_relative_path = _database_url.replace("sqlite:///", "", 1)
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{(BASE_DIR / sqlite_relative_path).resolve()}"
    elif _database_url:
        SQLALCHEMY_DATABASE_URI = _database_url
    else:
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{(BASE_DIR / 'instance' / 'cicloferencia.db').resolve()}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH_MB", 4)) * 1024 * 1024
    UPLOAD_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
    UPLOAD_FOLDER = BASE_DIR / "app" / "static" / "uploads"
    WTF_CSRF_TIME_LIMIT = None
    REMEMBER_COOKIE_HTTPONLY = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("FLASK_ENV") == "production"
    REMEMBER_COOKIE_SECURE = os.getenv("FLASK_ENV") == "production"
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 6
    RATELIMIT_STORAGE_URI = "memory://"
    RATELIMIT_HEADERS_ENABLED = True
    CONTACT_WHATSAPP = os.getenv("CONTACT_WHATSAPP", "5511914528745")
    SITE_URL = os.getenv("SITE_URL", "http://127.0.0.1:5000")
    SECURITY_CSP = (
        "default-src 'self'; "
        "img-src 'self' data: https://maps.gstatic.com https://*.googleapis.com https://*.ggpht.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "script-src 'self' 'unsafe-inline'; "
        "frame-src https://www.google.com;"
    )


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
