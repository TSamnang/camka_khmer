from front import front_bp
from flask import render_template


@front_bp.get('/about')
def about():
    module = 'about'
    return render_template('front/about.html', module = module)