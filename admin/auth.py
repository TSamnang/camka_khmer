from admin import admin_bp
from flask import render_template, request, redirect, url_for, session
from sqlalchemy import text
from extension import db, limiter
from werkzeug.security import check_password_hash
from functools import wraps


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("is_login"):
            return redirect(url_for("admin_bp.admin_login", next=request.path))
        return view(*args, **kwargs)

    return wrapped

@admin_bp.get('/login')
@limiter.limit("10 per minute")
def admin_login():
    module = 'login'
    session.clear()
    return render_template('admin/system/login.html', module=module)


@admin_bp.post('/login')
@limiter.limit("5 per minute")
def admin_do_login():
    module = 'login'
    form = request.form
    username = form.get('username').strip()
    password = form.get('password')

    sql = text("SELECT * FROM USER_FARMER WHERE farmer_name = :farmer_name")
    user = db.session.execute(sql, {"farmer_name": username}).fetchone()

    if user:
        # check password
        if check_password_hash(user.password, password):
            session.clear()
            session['is_login'] = True
            session['id'] = user.id
            session['profile'] = user.profile
            session['farmer_name'] = user.farmer_name
            session['farm_name'] = user.farm_name
            session['email'] = user.email
            session['phoneNumber'] = user.phoneNumber
            session['location'] = user.location
            session['role'] = user.role
            return redirect(url_for('admin_bp.dashboard_page'))
        else:
            return redirect(url_for('admin_bp.admin_login'))
    else:
        return redirect(url_for('admin_bp.admin_login'))


@admin_bp.get('/logout')
def admin_logout():
    session.clear()
    return redirect(url_for('admin_bp.admin_login'))
