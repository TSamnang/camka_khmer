from api import api_bp
from flask import jsonify
from models.category import Category


@api_bp.get("/category")
def category():
    categories = Category.find_all()
    return jsonify([Category.to_dict_from_doc(c) for c in categories])


@api_bp.get("/category/<category_id>")
def get_category(category_id):
    cat = Category.find_by_id(category_id)
    if not cat:
        return {"error": "Category not found"}, 404
    return jsonify(Category.to_dict_from_doc(cat))
