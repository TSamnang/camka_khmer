from admin import admin_bp
from flask import render_template, request, redirect, url_for
from admin.auth import login_required
from sqlalchemy import text
from extension import db
from werkzeug.security import generate_password_hash
from models.user_farmer import USER_FARMER
from models.user_customer import USER_CUSTOMER
from helper import save_profile_image,allowed

from extension import limiter, get_user_id


@admin_bp.get('/user/farmer')
@login_required
@limiter.limit("10 per minute", key_func=get_user_id)
def user_farmer_page():
    module = 'user_farmer'
    sql = text("SELECT * FROM USER_FARMER")
    result = db.session.execute(sql)
    rows = [dict(row._mapping) for row in result]

    return render_template('admin/user/farmer.html', module=module, users= rows)


@admin_bp.get('/user/customer')
@limiter.limit("10 per minute", key_func=get_user_id)
@login_required
def user_customer_page():
    module = 'user_customer'
    sql = text("SELECT * FROM USER_CUSTOMER")
    result = db.session.execute(sql)
    rows = [dict(row._mapping) for row in result]
    return render_template('admin/user/customer.html', module=module, users= rows)


@admin_bp.get('/user/add-farmer')
@limiter.limit("10 per minute", key_func=get_user_id)
@login_required
def add_user_farmer():
    module = 'user / add / farmer'
    return render_template('admin/user/add_farmer.html', module=module)


@admin_bp.post('/user/add-farmer')
@login_required
def do_add_user_farmer():
    form = request.form
    file = request.files.get("image")

    filename = save_profile_image(file) if file and file.filename else None

    # Password hash
    h_password = generate_password_hash(
        form.get('password')
    )

    # Create farmer
    new_farmer = USER_FARMER(
        profile=filename if filename else '',
        farmer_name=form.get('farmer_name'),
        farm_name=form.get('farm_name'),
        email=form.get('email'),
        phoneNumber=form.get('phoneNumber'),
        location=form.get('location'),
        role=form.get('role'),
        password=h_password,
    )

    db.session.add(new_farmer)
    db.session.commit()

    return redirect(url_for('admin_bp.user_farmer_page'))


@admin_bp.get('/user/add-customer')
@limiter.limit("10 per minute", key_func=get_user_id)
@login_required
def add_user_customer():
    module = 'user / add / customer'
    return render_template('admin/user/add_customer.html', module=module)

@admin_bp.post('/user/add-customer')
@login_required
def do_add_user_customer():
    module = 'user / add / customer'
    form = request.form
    file = request.files.get("image")

    filename = save_profile_image(file) if file and file.filename else None

    password = generate_password_hash(form.get('password'))

    new_customer = USER_CUSTOMER(
        profile=filename if filename else '',
        customer_name=form.get('customer_name'),
        customer_email=form.get('customer_email'),
        phoneNumber=form.get('phoneNumber'),
        location=form.get('location'),
        role=form.get('role'),
        password=password,
        status=form.get('status'),
    )

    db.session.add(new_customer)
    db.session.commit()
    return redirect(url_for('admin_bp.user_customer_page'))


@admin_bp.get('/user/edit-user/<int:user_id>')
@limiter.limit("10 per minute", key_func=get_user_id)
@login_required
def edit_user(user_id):
    module = 'user / edit / user'
    sql = text("SELECT * FROM USER_FARMER WHERE id = :user_id")
    result = db.session.execute(sql, {"user_id": user_id}).fetchone()
    user = None
    if result:
        user = dict(result._mapping)
    else:
        return redirect(url_for('admin_bp.user_farmer_page'))
    return render_template('admin/user/edit_farmer.html', module=module, user=user)

@admin_bp.post('/user/edit-user')
@login_required
def do_edit_user():

    form = request.form
    user = USER_FARMER.query.get(form.get('user_id'))
    if not user:
        return redirect(url_for('admin_bp.user_farmer_page'))

    file = request.files.get("image")
    if file and file.filename and allowed(file.filename):
        filename = save_profile_image(file)
        if filename:
            user.profile = filename

    user.farmer_name = form.get('farmer_name')
    user.farm_name   = form.get('farm_name')
    user.email       = form.get('email')
    user.phoneNumber = form.get('phone')
    user.location    = form.get('location')
    user.role        = form.get('role')

    if form.get('password') is not None and form.get('password') != '':
        user.password = generate_password_hash(form.get('password'))

    db.session.commit()
    return redirect(url_for('admin_bp.user_farmer_page'))


@admin_bp.get('/user/confirm-delete/<int:user_id>')
@limiter.limit("10 per minute", key_func=get_user_id)
@login_required
def confirm_delete(user_id):
    module = 'user / confirm delete'
    sql = text("SELECT * FROM USER_FARMER WHERE id = :user_id")
    result = db.session.execute(sql, {"user_id": user_id}).fetchone()
    user = None
    if result:
        user = dict(result._mapping)
    else:
        return redirect(url_for('admin_bp.user_farmer_page'))
    return render_template('admin/user/confirm_delete.html', module=module, user=user)

@admin_bp.post('/user/delete')
@login_required
def delete_user():
    module = 'user / delete / user'
    form = request.form
    user_id = form.get('user_id')
    user = USER_FARMER.query.get(user_id)
    if not user:
        return redirect(url_for('admin_bp.user_farmer_page'))
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for('admin_bp.user_farmer_page'))