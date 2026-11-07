from front import front_bp
from flask import render_template, request
from extension import db
from models.product import Product
from models.category import Category
from products import get_product_by_id


@front_bp.get('/product')
def product():
    module = 'product'
    active_category = request.args.get('category', '').strip()
    categories = Category.query.order_by(Category.id.asc()).all()
    products = Product.query.order_by(Product.id.asc()).all()
    return render_template(
        'front/product.html',
        products=products,
        module=module,
        categories=categories,
        active_category=active_category
    )


@front_bp.get('/product-detail/<int:product_id>')
def detail(product_id):
    qty = request.args.get('qty', 1, type=int)
    if qty < 1:
        qty = 1

    product = db.session.get(Product, product_id)
    if not product:
        product = get_product_by_id(product_id)

    cat_name = product.category if hasattr(product, 'category') else (product.get('category', '') if product else '')
    related_product = Product.query.filter(
        Product.category == cat_name,
        Product.id != product_id
    ).limit(4).all() if cat_name else []

    all_products = Product.query.all()

    return render_template('front/product-detail.html',
                           products=all_products,
                           product=product,
                           related_product=related_product,
                           qty=qty,
    )
