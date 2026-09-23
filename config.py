from datetime import timedelta

class Config:

    SQLALCHEMY_DATABASE_URI = "sqlite:///mydb.sqlite3"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = "change-this"
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=1440)  # session TTL