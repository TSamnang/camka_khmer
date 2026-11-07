from datetime import date
from extension import db


class Product(db.Model):
    __tablename__ = 'product'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    farm = db.Column(db.String(120), nullable=True)
    farmer_id = db.Column(db.Integer, nullable=True)
    origin = db.Column(db.String(120), nullable=True)
    unit = db.Column(db.String(50), nullable=True, default="1 kg")
    price = db.Column(db.Float, nullable=False, default=0.0)
    stock = db.Column(db.Integer, nullable=False, default=0)
    badge = db.Column(db.String(50), nullable=True, default="Fresh")
    description = db.Column(db.Text, nullable=True)
    rating = db.Column(db.String(50), nullable=True, default="★★★★★")
    image = db.Column(db.String(255), nullable=True)
    posted = db.Column(db.String(20), nullable=True, default=lambda: date.today().strftime('%Y-%m-%d'))
    status = db.Column(db.String(50), nullable=False, default="Approved")

    @property
    def org_image(self):
        if not self.image:
            return "/static/images/bread.jpg"
        img = str(self.image)
        if "/static/uploads/thumb/" in img:
            return img.replace("/static/uploads/thumb/", "/static/uploads/org/")
        if "/uploads/thumb/" in img:
            return img.replace("/uploads/thumb/", "/uploads/org/")
        if "/thumb/" in img:
            return img.replace("/thumb/", "/org/")
        if not img.startswith("/") and not img.startswith("http"):
            return f"/static/uploads/org/{img}"
        return img

    @property
    def thumb_image(self):
        if not self.image:
            return "/static/images/bread.jpg"
        img = str(self.image)
        if "/static/uploads/org/" in img:
            return img.replace("/static/uploads/org/", "/static/uploads/thumb/")
        if "/uploads/org/" in img:
            return img.replace("/uploads/org/", "/uploads/thumb/")
        if "/org/" in img:
            return img.replace("/org/", "/thumb/")
        if not img.startswith("/") and not img.startswith("http"):
            return f"/static/uploads/thumb/{img}"
        return img

    def __getitem__(self, key):
        if key == "org_image":
            return self.org_image
        if key == "thumb_image":
            return self.thumb_image
        return getattr(self, key)

    def get(self, key, default=None):
        if key == "org_image":
            return self.org_image
        if key == "thumb_image":
            return self.thumb_image
        return getattr(self, key, default)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "origin": self.origin or "",
            "farm": self.farm or "",
            "unit": self.unit or "",
            "price": float(self.price) if self.price is not None else 0.0,
            "stock": self.stock or 0,
            "badge": self.badge or "",
            "description": self.description or "",
            "rating": self.rating or "★★★★★",
            "image": self.thumb_image,
            "org_image": self.org_image,
            "posted": self.posted or "",
            "status": self.status or "Approved"
        }

    def __repr__(self):
        return f"<Product id={self.id} name='{self.name}'>"


PRODUCT = Product
