from front import front_bp
from flask import render_template, request
from products import products, get_product_by_id, get_product_by_category



@front_bp.get('/product')
def product():
    module = 'product'
    return render_template('front/product.html', products = products, module = module)


@front_bp.get('/product-detail/<int:product_id>')
def detail(product_id):
    qty = request.args.get('qty', 1, type=int)
    if qty < 1:
        qty = 1

    product = get_product_by_id(product_id)
    related_product = get_product_by_category(product['category'])
    return render_template('front/product-detail.html',
                           products=products,
                           product=product,
                           related_product=related_product,
                           qty=qty,
    )