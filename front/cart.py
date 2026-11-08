from front import front_bp
from flask import render_template, request, redirect, url_for, make_response
from products import get_product_by_id, increase_cart_item, decrease_cart_item
import json


@front_bp.context_processor
def navbar():
    cart_list = request.cookies.get('cart_list')
    cart_list = json.loads(cart_list) if cart_list else []
    return dict(cart_list=cart_list)


@front_bp.get('/cart/add')
def cart_add():
    product_id = request.args.get('product_id')
    qty = int(request.args.get('qty', 1))
    if qty < 1:
        qty = 1

    cart_list = request.cookies.get('cart_list')
    cart_list = json.loads(cart_list) if cart_list else []

    if product_id:
        product_id = str(product_id).strip()
        duplicate_product_ids = [str(item['id']) for item in cart_list]
        if product_id in duplicate_product_ids:
            for item in cart_list:
                if str(item['id']) == product_id:
                    item['qty'] = int(item.get('qty', 1)) + qty
        else:
            cart_list.append({'id': product_id, 'qty': qty})

    slim_cart = [{'id': str(item['id']), 'qty': int(item['qty'])} for item in cart_list]

    response = make_response(redirect(url_for('front_bp.cart')))
    response.set_cookie('cart_list', json.dumps(slim_cart))
    return response


@front_bp.get('/cart/increase')
def cart_increase_route():
    product_id = request.args.get('product_id')
    if not product_id:
        return redirect(url_for('front_bp.cart'))
    cart_list = request.cookies.get('cart_list')
    cart_list = json.loads(cart_list) if cart_list else []
    cart_list = increase_cart_item(cart_list, str(product_id).strip())

    slim_cart = [{'id': str(i['id']), 'qty': int(i['qty'])} for i in cart_list]
    response = make_response(redirect(url_for('front_bp.cart')))
    response.set_cookie('cart_list', json.dumps(slim_cart))
    return response


@front_bp.get('/cart/decrease')
def cart_decrease_route():
    product_id = request.args.get('product_id')
    if not product_id:
        return redirect(url_for('front_bp.cart'))
    cart_list = request.cookies.get('cart_list')
    cart_list = json.loads(cart_list) if cart_list else []
    cart_list = decrease_cart_item(cart_list, str(product_id).strip())

    slim_cart = [{'id': str(i['id']), 'qty': int(i['qty'])} for i in cart_list]
    response = make_response(redirect(url_for('front_bp.cart')))
    response.set_cookie('cart_list', json.dumps(slim_cart))
    return response


@front_bp.get('/cart/clear')
def delete_all_items():
    response = make_response(redirect(url_for('front_bp.cart')))
    response.set_cookie('cart_list', '', expires=0)
    return response


@front_bp.get('/cart/remove')
def delete_single_item():
    product_id = str(request.args.get('product_id') or '').strip()
    cart_list = json.loads(request.cookies.get('cart_list', '[]'))
    new_cart = []
    for item in cart_list:
        if str(item.get('id', '')) != product_id:
            new_cart.append(item)
    cart_list = new_cart

    response = make_response(redirect(url_for('front_bp.cart')))
    response.set_cookie('cart_list', json.dumps(cart_list))
    return response


@front_bp.get('/cart')
def cart():
    cart_list = request.cookies.get('cart_list')
    cart_list = json.loads(cart_list) if cart_list else []

    clean_cart = []
    for item in cart_list:
        product = get_product_by_id(item['id'])
        if product is None:
            continue
        clean_cart.append({
            'id':    str(item['id']),
            'qty':   int(item['qty']),
            'image': product.get('image', ''),
            'name':  product.get('name', ''),
            'unit':  product.get('unit', ''),
            'price': float(product.get('price', 0.0)),
        })

    DELIVERY_FEE = 0.00
    FREE_DELIVERY = 25.00

    subtotal = sum(item['qty'] * item['price'] for item in clean_cart)
    delivery = 0.00 if subtotal >= FREE_DELIVERY else DELIVERY_FEE
    total    = subtotal + delivery

    return render_template(
        'front/cart.html',
        cart_list=clean_cart,
        subtotal=subtotal,
        delivery=delivery,
        total=total
    )
