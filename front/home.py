from front import front_bp
from flask import render_template
from products import products

@front_bp.get('/')
def homepage():
    module = 'homepage'
    return render_template('front/homepage.html', products = products, module = module)
