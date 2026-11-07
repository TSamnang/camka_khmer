from api import api_bp
from extension import db
from models.category import Category


@api_bp.get("/category")
def category():
    categories = Category.query.order_by(Category.id.asc()).all()
    return [c.to_dict() for c in categories]


@api_bp.get("/category/<int:category_id>")
def get_category(category_id):
    cat = db.session.get(Category, category_id)
    if not cat:
        return {"error": "Category not found"}, 404
    return cat.to_dict()

