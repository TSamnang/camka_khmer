from admin import admin_bp
from flask import render_template, request, redirect, url_for, session
from extension import limiter
from werkzeug.security import check_password_hash
from functools import wraps
from models.user_farmer import USER_FARMER


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
    form = request.form
    username = (form.get('username') or '').strip()
    password = form.get('password') or ''

    user = USER_FARMER.find_by_name(username)

    if user and check_password_hash(user.get('password', ''), password):
        session.clear()
        session['is_login'] = True
        session['id'] = user.id
        session['profile'] = user.get('profile', '')
        session['farmer_name'] = user.get('farmer_name', '')
        session['farm_name'] = user.get('farm_name', '')
        session['email'] = user.get('email', '')
        session['phoneNumber'] = user.get('phoneNumber', '')
        session['location'] = user.get('location', '')
        session['role'] = user.get('role', '')
        return redirect(url_for('admin_bp.dashboard_page'))
    else:
        return redirect(url_for('admin_bp.admin_login'))


@admin_bp.get('/logout')
def admin_logout():
    session.clear()
    return redirect(url_for('admin_bp.admin_login'))
