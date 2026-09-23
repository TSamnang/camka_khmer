from front import front_bp
from flask import render_template
from flask import request, redirect, url_for


@front_bp.get('/login')
def login():
    return render_template('front/login.html')


@front_bp.post('/login')
def login_post():
    email = request.form.get('email')
    password = request.form.get('password')
    # TODO: add real credential validation here
    # For now, redirect to homepage on submit
    return redirect(url_for('front_bp.homepage'))


@front_bp.get('/register')
def register():
    return render_template('front/register.html')