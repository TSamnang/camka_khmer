from datetime import date
from admin import admin_bp
from flask import render_template, request, redirect, url_for
from admin.auth import login_required
from extension import db, limiter, get_user_id
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
    categories = Category.query.order_by(Category.id.asc()).all()
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

    filename = save_profile_image(file) if file and file.filename else None

    new_cat = Category(
        name=form.get('name', '').strip(),
        description=form.get('description', '').strip(),
        image=filename if filename else ''
    )

    db.session.add(new_cat)
    db.session.commit()

    return redirect(url_for('admin_bp.category_page'))


@admin_bp.get('/catalog/edit-category/<int:category_id>')
@limiter.limit("10 per minute", key_func=get_user_id)
@login_required
def edit_category(category_id):
    module = 'category / edit'
    category = db.session.get(Category, category_id)
    if not category:
        return redirect(url_for('admin_bp.category_page'))
    return render_template('admin/catalog/edit_category.html', module=module, category=category)


@admin_bp.post('/catalog/edit-category')
@login_required
def do_edit_category():
    form = request.form
    category_id = form.get('category_id')
    category = db.session.get(Category, int(category_id)) if category_id else None
    if not category:
        return redirect(url_for('admin_bp.category_page'))

    file = request.files.get("image")
    if file and file.filename and allowed(file.filename):
        filename = save_profile_image(file)
        if filename:
            category.image = filename

    category.name = form.get('name', '').strip()
    category.description = form.get('description', '').strip()

    db.session.commit()
    return redirect(url_for('admin_bp.category_page'))


@admin_bp.get('/catalog/confirm-delete-category/<int:category_id>')
@limiter.limit("10 per minute", key_func=get_user_id)
@login_required
def confirm_delete_category(category_id):
    module = 'category / confirm delete'
    category = db.session.get(Category, category_id)
    if not category:
        return redirect(url_for('admin_bp.category_page'))
    return render_template('admin/catalog/confirm_delete.html', module=module, category=category)


@admin_bp.post('/catalog/delete-category')
@login_required
def delete_category():
    form = request.form
    category_id = form.get('category_id')
    category = db.session.get(Category, int(category_id)) if category_id else None
    if category:
        db.session.delete(category)
        db.session.commit()
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

    query = Product.query
    if status_filter in ['pending', 'approved', 'rejected']:
        query = query.filter(db.func.lower(Product.status) == status_filter)

    products = query.order_by(Product.id.desc()).all()
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
    categories = Category.query.order_by(Category.name.asc()).all()
    farmers = USER_FARMER.query.all()
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
    file = request.files.get("photo") or request.files.get("image")

    # Image handling
    image_path = "/static/images/bread.jpg"
    if file and file.filename and allowed(file.filename):
        filename = save_profile_image(file)
        if filename:
            image_path = url_for('static', filename='uploads/thumb/' + filename)

    category_name = form.get('category', '').strip()
    category_id = form.get('category_id')
    cat_id = None
    if category_id:
        try:
            cat_id = int(category_id)
        except (ValueError, TypeError):
            pass
    if not cat_id and category_name:
        cat_obj = Category.query.filter(Category.name.ilike(category_name)).first()
        if cat_obj:
            cat_id = cat_obj.id

    price = 0.0
    try:
        price = float(form.get('price', 0.0))
    except (ValueError, TypeError):
        price = 0.0

    stock = 0
    try:
        stock = int(form.get('stock', 0))
    except (ValueError, TypeError):
        stock = 0

    farm_val = form.get('farm') or form.get('farmer') or ''
    origin_val = form.get('origin', '').strip() or 'Cambodia'
    badge_val = form.get('badge', 'Fresh').strip() or 'Fresh'
    status_val = form.get('status', 'Approved').strip() or 'Approved'

    new_prod = Product(
        name=form.get('name', '').strip(),
        category=category_name,
        category_id=cat_id,
        farm=farm_val,
        origin=origin_val,
        unit=form.get('unit', '1 kg').strip(),
        price=price,
        stock=stock,
        badge=badge_val,
        description=form.get('description', '').strip(),
        rating=form.get('rating', '★★★★★').strip() or '★★★★★',
        image=image_path,
        posted=form.get('posted') or date.today().strftime('%Y-%m-%d'),
        status=status_val
    )

    db.session.add(new_prod)
    db.session.commit()

    return redirect(url_for('admin_bp.product_page'))


@admin_bp.get('/product/edit/<int:product_id>')
@limiter.limit("10 per minute", key_func=get_user_id)
@login_required
def edit_product(product_id):
    module = 'product / edit'
    product = db.session.get(Product, product_id)
    if not product:
        return redirect(url_for('admin_bp.product_page'))

    categories = Category.query.order_by(Category.name.asc()).all()
    farmers = USER_FARMER.query.all()
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
    product = db.session.get(Product, int(product_id)) if product_id else None
    if not product:
        return redirect(url_for('admin_bp.product_page'))

    file = request.files.get("photo") or request.files.get("image")
    if file and file.filename and allowed(file.filename):
        filename = save_profile_image(file)
        if filename:
            product.image = url_for('static', filename='uploads/thumb/' + filename)

    product.name = form.get('name', '').strip()
    category_name = form.get('category', '').strip()
    product.category = category_name

    cat_obj = Category.query.filter(Category.name.ilike(category_name)).first()
    if cat_obj:
        product.category_id = cat_obj.id

    product.farm = form.get('farm') or form.get('farmer') or ''
    product.origin = form.get('origin', '').strip()
    product.unit = form.get('unit', '').strip()

    try:
        product.price = float(form.get('price', product.price))
    except (ValueError, TypeError):
        pass

    try:
        product.stock = int(form.get('stock', product.stock))
    except (ValueError, TypeError):
        pass

    product.badge = form.get('badge', '').strip() or 'Fresh'
    product.description = form.get('description', '').strip()
    product.rating = form.get('rating', '').strip() or '★★★★★'
    product.status = form.get('status', product.status).strip()

    db.session.commit()
    return redirect(url_for('admin_bp.product_page'))


@admin_bp.get('/product/confirm-delete/<int:product_id>')
@limiter.limit("10 per minute", key_func=get_user_id)
@login_required
def confirm_delete_product(product_id):
    module = 'product / confirm delete'
    product = db.session.get(Product, product_id)
    if not product:
        return redirect(url_for('admin_bp.product_page'))
    return render_template('admin/catalog/confirm_delete_product.html', module=module, product=product)


@admin_bp.post('/product/delete')
@login_required
def delete_product():
    form = request.form
    product_id = form.get('product_id')
    product = db.session.get(Product, int(product_id)) if product_id else None
    if product:
        db.session.delete(product)
        db.session.commit()
    return redirect(url_for('admin_bp.product_page'))
