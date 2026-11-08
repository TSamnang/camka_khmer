from admin import admin_bp
from flask import render_template, request, redirect, url_for
from admin.auth import login_required
from extension import limiter, get_user_id
from werkzeug.security import generate_password_hash
from models.user_farmer import USER_FARMER
from models.user_customer import USER_CUSTOMER
from helper import save_profile_image, allowed


@admin_bp.get('/user/farmer')
@login_required
@limiter.limit("10 per minute", key_func=get_user_id)
def user_farmer_page():
    module = 'user_farmer'
    users = USER_FARMER.find_all()
    return render_template('admin/user/farmer.html', module=module, users=users)


@admin_bp.get('/user/customer')
@limiter.limit("10 per minute", key_func=get_user_id)
@login_required
def user_customer_page():
    module = 'user_customer'
    users = USER_CUSTOMER.find_all()
    return render_template('admin/user/customer.html', module=module, users=users)


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

    filename = save_profile_image(file) if file and file.filename else ''
    h_password = generate_password_hash(form.get('password') or '')

    USER_FARMER.insert({
        'profile': filename,
        'farmer_name': form.get('farmer_name', ''),
        'farm_name': form.get('farm_name', ''),
        'email': form.get('email', ''),
        'phoneNumber': form.get('phoneNumber', ''),
        'location': form.get('location', ''),
        'role': form.get('role', ''),
        'password': h_password,
    })

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
    form = request.form
    file = request.files.get("image")

    filename = save_profile_image(file) if file and file.filename else ''
    password = generate_password_hash(form.get('password') or '')

    USER_CUSTOMER.insert({
        'profile': filename,
        'customer_name': form.get('customer_name', ''),
        'customer_email': form.get('customer_email', ''),
        'phoneNumber': form.get('phoneNumber', ''),
        'location': form.get('location', ''),
        'role': form.get('role', 'Customer'),
        'status': form.get('status', 'Active'),
        'password': password,
    })

    return redirect(url_for('admin_bp.user_customer_page'))


@admin_bp.get('/user/edit-user/<user_id>')
@limiter.limit("10 per minute", key_func=get_user_id)
@login_required
def edit_user(user_id):
    module = 'user / edit / user'
    user = USER_FARMER.find_by_id(user_id)
    if not user:
        return redirect(url_for('admin_bp.user_farmer_page'))
    return render_template('admin/user/edit_farmer.html', module=module, user=user)


@admin_bp.post('/user/edit-user')
@login_required
def do_edit_user():
    form = request.form
    user_id = form.get('user_id')
    user = USER_FARMER.find_by_id(user_id)
    if not user:
        return redirect(url_for('admin_bp.user_farmer_page'))

    update_data = {
        'farmer_name': form.get('farmer_name', ''),
        'farm_name': form.get('farm_name', ''),
        'email': form.get('email', ''),
        'phoneNumber': form.get('phone', ''),
        'location': form.get('location', ''),
        'role': form.get('role', ''),
    }

    file = request.files.get("image")
    if file and file.filename and allowed(file.filename):
        filename = save_profile_image(file)
        if filename:
            update_data['profile'] = filename

    if form.get('password'):
        update_data['password'] = generate_password_hash(form.get('password'))

    USER_FARMER.update(user_id, update_data)
    return redirect(url_for('admin_bp.user_farmer_page'))


@admin_bp.get('/user/confirm-delete/<user_id>')
@limiter.limit("10 per minute", key_func=get_user_id)
@login_required
def confirm_delete(user_id):
    module = 'user / confirm delete'
    user = USER_FARMER.find_by_id(user_id)
    if not user:
        return redirect(url_for('admin_bp.user_farmer_page'))
    return render_template('admin/user/confirm_delete.html', module=module, user=user)


@admin_bp.post('/user/delete')
@login_required
def delete_user():
    form = request.form
    user_id = form.get('user_id')
    if user_id:
        USER_FARMER.delete(user_id)
    return redirect(url_for('admin_bp.user_farmer_page'))


@admin_bp.get('/user/edit-customer/<user_id>')
@limiter.limit("10 per minute", key_func=get_user_id)
@login_required
def edit_customer(user_id):
    module = 'user / edit / customer'
    user = USER_CUSTOMER.find_by_id(user_id)
    if not user:
        return redirect(url_for('admin_bp.user_customer_page'))
    return render_template('admin/user/edit_customer.html', module=module, user=user)


@admin_bp.post('/user/edit-customer')
@login_required
def do_edit_customer():
    form = request.form
    user_id = form.get('user_id')
    user = USER_CUSTOMER.find_by_id(user_id)
    if not user:
        return redirect(url_for('admin_bp.user_customer_page'))

    update_data = {
        'customer_name': form.get('customer_name', ''),
        'customer_email': form.get('customer_email', ''),
        'phoneNumber': form.get('phoneNumber', ''),
        'location': form.get('location', ''),
    }

    if form.get('role'):
        update_data['role'] = form.get('role')
    if form.get('status'):
        update_data['status'] = form.get('status')

    file = request.files.get("image")
    if file and file.filename and allowed(file.filename):
        filename = save_profile_image(file)
        if filename:
            update_data['profile'] = filename

    if form.get('password') and form.get('password').strip():
        update_data['password'] = generate_password_hash(form.get('password'))

    USER_CUSTOMER.update(user_id, update_data)
    return redirect(url_for('admin_bp.user_customer_page'))


@admin_bp.get('/user/confirm-delete-customer/<user_id>')
@limiter.limit("10 per minute", key_func=get_user_id)
@login_required
def confirm_delete_customer(user_id):
    module = 'user / confirm delete customer'
    user = USER_CUSTOMER.find_by_id(user_id)
    if not user:
        return redirect(url_for('admin_bp.user_customer_page'))
    return render_template('admin/user/confirm_delete_customer.html', module=module, user=user)


@admin_bp.post('/user/delete-customer')
@login_required
def delete_customer():
    form = request.form
    user_id = form.get('user_id')
    if user_id:
        USER_CUSTOMER.delete(user_id)
    return redirect(url_for('admin_bp.user_customer_page'))
