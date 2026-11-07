from extension import db


class Category(db.Model):
    __tablename__ = 'category'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    image = db.Column(db.String(255), nullable=True)
    _product_count = db.Column('product_count', db.Integer, default=0, nullable=True)

    @property
    def product_count(self):
        try:
            from models.product import Product
            cat_name = (self.name or '').strip().lower()
            count = Product.query.filter(
                (Product.category_id == self.id) |
                (db.func.lower(Product.category) == cat_name) |
                (Product.category.ilike(f"%{cat_name}%"))
            ).count()
            return count
        except Exception:
            return self._product_count or 0

    @property
    def org_image(self):
        if not self.image:
            return "/static/images/vegetable.jpg"
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
            return "/static/images/vegetable.jpg"
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

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description or '',
            'product_count': self.product_count,
            'image': self.thumb_image,
            'org_image': self.org_image
        }

    def __repr__(self):
        return f"<Category id={self.id} name='{self.name}'>"


CATEGORY = Category
