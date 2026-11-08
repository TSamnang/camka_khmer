from front import front_bp
from flask import render_template
from models.product import Product
from models.category import Category


@front_bp.get('/')
def homepage():
    module = 'homepage'
    categories = Category.find_all()
    products = Product.find_all()
    return render_template('front/homepage.html', products=products, module=module, categories=categories)
