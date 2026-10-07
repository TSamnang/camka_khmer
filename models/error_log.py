from datetime import datetime
from extension import db


class ErrorLog(db.Model):
    __tablename__ = 'error_log'

    id = db.Column(db.Integer, primary_key=True)
    status_code = db.Column(db.Integer, nullable=True)
    endpoint = db.Column(db.String(255), nullable=True)
    method = db.Column(db.String(10), nullable=True)
    user_name = db.Column(db.String(100), nullable=True)
    client_ip = db.Column(db.String(100), nullable=True)
    threat_level = db.Column(db.String(100), nullable=True)
    error_type = db.Column(db.String(150), nullable=True)
    error_detail = db.Column(db.Text, nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    telegram_sent = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'status_code': self.status_code,
            'endpoint': self.endpoint,
            'method': self.method,
            'user_name': self.user_name,
            'client_ip': self.client_ip,
            'threat_level': self.threat_level,
            'error_type': self.error_type,
            'error_detail': self.error_detail,
            'user_agent': self.user_agent,
            'telegram_sent': self.telegram_sent,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

    def __repr__(self):
        return f"<ErrorLog id={self.id} status={self.status_code} endpoint='{self.endpoint}' user='{self.user_name}'>"


# Alias for uppercase naming convention
ERROR_LOG = ErrorLog
