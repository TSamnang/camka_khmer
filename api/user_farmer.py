from api import api_bp
from sqlalchemy import text
from extension import db

@api_bp.get('/user/farmer')
def user_farmer():
    sql = text("SELECT * FROM USER_FARMER")
    result = db.session.execute(sql)
    rows = [dict(row._mapping) for row in result]

    return rows