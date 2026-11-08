from front import front_bp
from flask import render_template, request
from models.product import Product
from models.category import Category
from products import get_product_by_id


@front_bp.get('/product')
def product():
    module = 'product'
    active_category = request.args.get('category', '').strip()
    categories = Category.find_all()

    if active_category:
        products = Product.find_by_category(active_category)
    else:
        products = Product.find_all()

    return render_template(
        'front/product.html',
        products=products,
        module=module,
        categories=categories,
        active_category=active_category
    )


@front_bp.get('/product-detail/<product_id>')
def detail(product_id):
    qty = request.args.get('qty', 1, type=int)
    if qty < 1:
        qty = 1

    product = Product.find_by_id(product_id)
    if not product:
        product = get_product_by_id(product_id)

    cat_name = product.get('category', '') if product else ''
    if cat_name:
        related_candidates = Product.find_by_category(cat_name)
        related_product = [p for p in related_candidates if str(p.get('id', '')) != str(product_id)][:4]
    else:
        related_product = []

    all_products = Product.find_all()

    return render_template(
        'front/product-detail.html',
        products=all_products,
        product=product,
        related_product=related_product,
        qty=qty,
    )
