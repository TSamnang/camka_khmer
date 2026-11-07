from front import front_bp
from flask import render_template
from models.product import Product
from models.category import Category

@front_bp.get('/')
def homepage():
    module = 'homepage'
    categories = Category.query.order_by(Category.id.asc()).all()
    products = Product.query.order_by(Product.id.asc()).all()
    return render_template('front/homepage.html', products=products, module=module, categories=categories)
