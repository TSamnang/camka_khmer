from datetime import date
from admin import admin_bp
from flask import render_template, request, redirect, url_for
from admin.auth import login_required
from extension import limiter, get_user_id
from models.category import Category
from models.product import Product
from models.user_farmer import USER_FARMER
from helper import save_profile_image, allowed


# ==============================================================================
# CATEGORY MANAGEMENT
# ==============================================================================

@admin_bp.get('/catalog/category')
@limiter.limit("10 per minute", key_func=get_user_id)
@login_required
def category_page():
    module = 'category'
    categories = Category.find_all()
    return render_template('admin/catalog/category.html', module=module, categories=categories)


@admin_bp.get('/catalog/add-category')
@limiter.limit("10 per minute", key_func=get_user_id)
@login_required
def add_category():
    module = 'category / add'
    return render_template('admin/catalog/add_category.html', module=module)


@admin_bp.post('/catalog/add-category')
@login_required
def do_add_category():
    form = request.form
    file = request.files.get("image")

    filename = save_profile_image(file) if file and file.filename else ''

    Category.insert({
        'name': form.get('name', '').strip(),
        'description': form.get('description', '').strip(),
        'image': filename
    })

    return redirect(url_for('admin_bp.category_page'))


@admin_bp.get('/catalog/edit-category/<category_id>')
@limiter.limit("10 per minute", key_func=get_user_id)
@login_required
def edit_category(category_id):
    module = 'category / edit'
    category = Category.find_by_id(category_id)
    if not category:
        return redirect(url_for('admin_bp.category_page'))
    return render_template('admin/catalog/edit_category.html', module=module, category=category)


@admin_bp.post('/catalog/edit-category')
@login_required
def do_edit_category():
    form = request.form
    category_id = form.get('category_id')
    category = Category.find_by_id(category_id)
    if not category:
        return redirect(url_for('admin_bp.category_page'))

    update_data = {
        'name': form.get('name', '').strip(),
        'description': form.get('description', '').strip(),
    }

    file = request.files.get("image")
    if file and file.filename and allowed(file.filename):
        filename = save_profile_image(file)
        if filename:
            update_data['image'] = filename

    Category.update(category_id, update_data)
    return redirect(url_for('admin_bp.category_page'))


@admin_bp.get('/catalog/confirm-delete-category/<category_id>')
@limiter.limit("10 per minute", key_func=get_user_id)
@login_required
def confirm_delete_category(category_id):
    module = 'category / confirm delete'
    category = Category.find_by_id(category_id)
    if not category:
        return redirect(url_for('admin_bp.category_page'))
    return render_template('admin/catalog/confirm_delete.html', module=module, category=category)


@admin_bp.post('/catalog/delete-category')
@login_required
def delete_category():
    form = request.form
    category_id = form.get('category_id')
    if category_id:
        Category.delete(category_id)
    return redirect(url_for('admin_bp.category_page'))


# ==============================================================================
# PRODUCT MANAGEMENT
# ==============================================================================

@admin_bp.get('/catalog/product')
@limiter.limit("10 per minute", key_func=get_user_id)
@login_required
def product_page():
    module = 'product'
    status_filter = request.args.get('status', 'all').strip().lower()
    products = Product.find_all(status_filter=status_filter)
    return render_template(
        'admin/catalog/product.html',
        module=module,
        products=products,
        current_status=status_filter
    )


@admin_bp.get('/product/add')
@limiter.limit("10 per minute", key_func=get_user_id)
@login_required
def add_product():
    module = 'product / add'
    categories = Category.find_all()
    farmers = USER_FARMER.find_all()
    return render_template(
        'admin/catalog/add_product.html',
        module=module,
        categories=categories,
        farmers=farmers
    )


@admin_bp.post('/product/add')
@login_required
def do_add_product():
    form = request.form
    file = request.files.get("image")

    filename = save_profile_image(file) if file and file.filename else ''

    Product.insert({
        'name': form.get('name', '').strip(),
        'category': form.get('category', '').strip(),
        'category_id': form.get('category_id', '').strip(),
        'farm': form.get('farm', '').strip(),
        'farmer_id': form.get('farmer_id', '').strip(),
        'origin': form.get('origin', '').strip(),
        'unit': form.get('unit', '1 kg').strip(),
        'price': float(form.get('price', 0) or 0),
        'stock': int(form.get('stock', 0) or 0),
        'badge': form.get('badge', 'Fresh').strip(),
        'description': form.get('description', '').strip(),
        'rating': form.get('rating', '★★★★★').strip(),
        'image': filename,
        'status': form.get('status', 'Approved').strip(),
        'posted': date.today().strftime('%Y-%m-%d'),
    })

    return redirect(url_for('admin_bp.product_page'))


@admin_bp.get('/product/edit/<product_id>')
@limiter.limit("10 per minute", key_func=get_user_id)
@login_required
def edit_product(product_id):
    module = 'product / edit'
    product = Product.find_by_id(product_id)
    if not product:
        return redirect(url_for('admin_bp.product_page'))
    categories = Category.find_all()
    farmers = USER_FARMER.find_all()
    return render_template(
        'admin/catalog/edit_product.html',
        module=module,
        product=product,
        categories=categories,
        farmers=farmers
    )


@admin_bp.post('/product/edit')
@login_required
def do_edit_product():
    form = request.form
    product_id = form.get('product_id')
    product = Product.find_by_id(product_id)
    if not product:
        return redirect(url_for('admin_bp.product_page'))

    update_data = {
        'name': form.get('name', '').strip(),
        'category': form.get('category', '').strip(),
        'category_id': form.get('category_id', '').strip(),
        'farm': form.get('farm', '').strip(),
        'farmer_id': form.get('farmer_id', '').strip(),
        'origin': form.get('origin', '').strip(),
        'unit': form.get('unit', '1 kg').strip(),
        'price': float(form.get('price', 0) or 0),
        'stock': int(form.get('stock', 0) or 0),
        'badge': form.get('badge', 'Fresh').strip(),
        'description': form.get('description', '').strip(),
        'rating': form.get('rating', '★★★★★').strip(),
        'status': form.get('status', 'Approved').strip(),
    }

    file = request.files.get("image")
    if file and file.filename and allowed(file.filename):
        filename = save_profile_image(file)
        if filename:
            update_data['image'] = filename

    Product.update(product_id, update_data)
    return redirect(url_for('admin_bp.product_page'))


@admin_bp.get('/product/confirm-delete/<product_id>')
@limiter.limit("10 per minute", key_func=get_user_id)
@login_required
def confirm_delete_product(product_id):
    module = 'product / confirm delete'
    product = Product.find_by_id(product_id)
    if not product:
        return redirect(url_for('admin_bp.product_page'))
    return render_template('admin/catalog/confirm_delete_product.html', module=module, product=product)


@admin_bp.post('/product/delete')
@login_required
def delete_product():
    form = request.form
    product_id = form.get('product_id')
    if product_id:
        Product.delete(product_id)
    return redirect(url_for('admin_bp.product_page'))


@admin_bp.post('/product/approve/<product_id>')
@login_required
def approve_product(product_id):
    Product.update(product_id, {'status': 'Approved'})
    return redirect(url_for('admin_bp.product_page'))


@admin_bp.post('/product/reject/<product_id>')
@login_required
def reject_product(product_id):
    Product.update(product_id, {'status': 'Rejected'})
    return redirect(url_for('admin_bp.product_page'))
