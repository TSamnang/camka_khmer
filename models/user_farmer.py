from extension import db

class USER_FARMER(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    profile = db.Column(db.String(120), nullable=False)
    farmer_name = db.Column(db.String(80), nullable=False)
    farm_name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    phoneNumber = db.Column(db.String(120), nullable=False, unique=True)
    location = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(120), nullable=False)
    password = db.Column(db.String(255), nullable=False)