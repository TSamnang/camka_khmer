from front import front_bp
from flask import render_template

@front_bp.get('/our-farm')
def our_farm_page():
    module = 'our_farm'
    return render_template('front/our_farm.html', module = module)

@front_bp.get('/apply-as-farmer')
def apply_farmer():
    module = 'our_farm'
    return render_template('front/apply_farmer.html', module = module)

