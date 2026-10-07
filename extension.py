from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
from flask import session
from flask_cors import CORS

db = SQLAlchemy()
migrate = Migrate()


def get_user_id():
    user_id = session.get("id")
    return f"user_{user_id}" if user_id else get_remote_address()

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["10000 per day", "1000 per minute"]
)

csrf = CSRFProtect()

core = CORS()

