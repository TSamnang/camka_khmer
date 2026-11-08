from api import api_bp
from flask import request, jsonify
from models.product import Product


@api_bp.get("/product")
def product():
    category = request.args.get('category')
    if category:
        products = Product.find_by_category(category)
    else:
        products = Product.find_all()
    return jsonify([p.to_dict() for p in products])


@api_bp.get("/product/<product_id>")
def get_product(product_id):
    prod = Product.find_by_id(product_id)
    if not prod:
        return {"error": "Product not found"}, 404
    return prod.to_dict()
