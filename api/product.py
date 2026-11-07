from api import api_bp
from flask import request
from extension import db
from models.product import Product


@api_bp.get("/product")
def product():
    category = request.args.get('category')
    query = Product.query

    if category:
        cat_lower = category.strip().lower()
        query = query.filter(
            (db.func.lower(Product.category) == cat_lower) |
            (Product.category.ilike(f"%{cat_lower}%"))
        )

    products = query.order_by(Product.id.asc()).all()
    return [p.to_dict() for p in products]


@api_bp.get("/product/<int:product_id>")
def get_product(product_id):
    prod = db.session.get(Product, product_id)
    if not prod:
        return {"error": "Product not found"}, 404
    return prod.to_dict()
