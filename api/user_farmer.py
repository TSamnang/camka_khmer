from api import api_bp
from flask import jsonify
from models.user_farmer import USER_FARMER


@api_bp.get('/user/farmer')
def user_farmer():
    farmers = USER_FARMER.find_all()
    sanitized = []
    for f in farmers:
        d = dict(f)
        d.pop('password', None)
        d.pop('_id', None)
        sanitized.append(d)
    return jsonify(sanitized)
