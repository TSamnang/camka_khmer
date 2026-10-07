from admin import admin_bp
from flask import render_template
from admin.auth import login_required
from extension import limiter, get_user_id

@admin_bp.get('/catalog/category')
@limiter.limit("10 per minute", key_func=get_user_id)
@login_required
def category_page():
    module = 'category'
    return render_template('admin/catalog/category.html', module=module)

@admin_bp.get('/catalog/product')
@limiter.limit("10 per minute", key_func=get_user_id)
@login_required
def product_page():
    module = 'product'
    return render_template('admin/catalog/product.html', module=module)

@admin_bp.get('/product/add')
@limiter.limit("10 per minute", key_func=get_user_id)
@login_required
def add_product():
    module = 'product / add'
    return render_template('admin/catalog/add_product.html', module=module)
