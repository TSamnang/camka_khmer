import os
import secrets
from datetime import timedelta
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).resolve().parent / '.env'
    load_dotenv(dotenv_path=env_path)
except Exception:
    # Graceful standard-library fallback if python-dotenv isn't loaded
    env_path = Path(__file__).resolve().parent / '.env'
    if env_path.is_file():
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, val = line.split('=', 1)
                    os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))


class Config:
    # Flask Security: load from .env, or generate random temporary key in RAM
    SECRET_KEY = os.getenv("SECRET_KEY") or secrets.token_hex(32)
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    FLASK_DEBUG = os.getenv("FLASK_DEBUG", "0").lower() in ("1", "true")

    # Database Configuration: SQLite default locally, PostgreSQL/MySQL in production
    _db_url = os.getenv("DATABASE_URL", "sqlite:///mydb.sqlite3")
    if _db_url.startswith("postgres://"):
        _db_url = _db_url.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = _db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Session & Cookie Security
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=1440)  # 24 hours
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "False").lower() in ("true", "1")

    # CORS Configuration
    CORS_ORIGINS = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:3200").split(",")
        if origin.strip()
    ]

    # Telegram Alert Bot (Rate Limit 429, Internal Error 500)
    # Stored strictly in .env — NO tokens hardcoded here!
    TELEGRAM_DEV_BOT_TOKEN = os.getenv("TELEGRAM_DEV_BOT_TOKEN")
    TELEGRAM_DEV_CHAT_ID = os.getenv("TELEGRAM_DEV_CHAT_ID")

    # Telegram Order Notification Bot (Customer Orders)
    # Stored strictly in .env — NO tokens hardcoded here!
    TELEGRAM_ORDER_BOT_TOKEN = os.getenv("TELEGRAM_ORDER_BOT_TOKEN")
    TELEGRAM_ORDER_CHAT_ID = os.getenv("TELEGRAM_ORDER_CHAT_ID")

    # Bakong KHQR Credentials
    # Stored strictly in .env — NO tokens or credentials hardcoded here!
    BAKONG_TOKEN = os.getenv("BAKONG_TOKEN")
    BAKONG_ACCOUNT_ID = os.getenv("BAKONG_ACCOUNT_ID")
    BAKONG_MERCHANT_NAME = os.getenv("BAKONG_MERCHANT_NAME", "CamkaKhmer")
    BAKONG_MERCHANT_CITY = os.getenv("BAKONG_MERCHANT_CITY", "Phnom Penh")
    BAKONG_PHONE_NUMBER = os.getenv("BAKONG_PHONE_NUMBER")
    BAKONG_STORE_LABEL = os.getenv("BAKONG_STORE_LABEL", "Cashier-01")
    BAKONG_TERMINAL_LABEL = os.getenv("BAKONG_TERMINAL_LABEL", "POS-01")
