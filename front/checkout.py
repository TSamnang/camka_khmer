from front import front_bp
from flask import render_template, request, make_response, url_for, redirect, jsonify, session
import json
import random
from datetime import datetime
from products import get_product_by_id
from extension import db, csrf
from models.order import Order, OrderItem
from models.user_customer import USER_CUSTOMER
from bakong_khqr import KHQR
from config import Config


DELIVERY_FEE = 0.00
FREE_DELIVERY = 25.00


def generate_order_number():
    date_str = datetime.utcnow().strftime('%Y%m%d')
    rand_str = f"{random.randint(1000, 9999)}"
    return f"ORD-{date_str}-{rand_str}"


def build_khqr_data(amount, bill_number, phone_number=None):

    try:
        #Token from .env
        khqr = KHQR(Config.BAKONG_TOKEN)

        qr_string = khqr.create_qr(
            account_id=Config.BAKONG_ACCOUNT_ID,
            merchant_name=Config.BAKONG_MERCHANT_NAME,
            merchant_city=Config.BAKONG_MERCHANT_CITY,
            amount=round(float(amount), 2),
            currency="USD",
            store_label=Config.BAKONG_STORE_LABEL,
            phone_number=phone_number or Config.BAKONG_PHONE_NUMBER,
            bill_number=bill_number or "TRX012345",
            terminal_label=Config.BAKONG_TERMINAL_LABEL,
            static=False,
            expiration=1
        )

        base64_uri = khqr.qr_image(qr_string, format="base64_uri")
        md5 = getattr(qr_string, 'md5', None)
        if not md5:
            try:
                md5 = khqr.generate_md5(str(qr_string))
            except Exception:
                md5 = ""
        return str(qr_string), str(base64_uri), str(md5)
    except Exception as e:
        print(f"KHQR generation warning: {e}")
        return "", "", ""


def send_telegram_order_alert(order, ordered_items):
    """Safely send order summary to Telegram notification channel using .env credentials."""
    try:
        import requests
        bot_token = Config.TELEGRAM_ORDER_BOT_TOKEN
        chat_id = Config.TELEGRAM_ORDER_CHAT_ID

        if not bot_token or not chat_id:
            return

        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

        message = f"🛒 <b>New Order Received!</b>\n\n"
        message += f"🔖 <b>Order ID:</b> #{order.order_number}\n"
        message += f"👤 <b>Name:</b> {order.customer_name}\n"
        message += f"📞 <b>Phone:</b> {order.phone}\n"
        if order.email:
            message += f"📧 <b>Email:</b> {order.email}\n"
        message += f"📍 <b>Address:</b> {order.address}\n\n"

        message += f"🧾 <b>Items Ordered:</b>\n"
        message += "─" * 24 + "\n"
        for idx, item in enumerate(ordered_items, 1):
            line_tot = item['qty'] * item['price']
            message += (
                f"{idx}. <b>{item['name']}</b>\n"
                f"   • Qty: {item['qty']} × {item.get('unit', '')}\n"
                f"   • Price: ${item['price']:.2f}  →  <b>${line_tot:.2f}</b>\n"
            )
        message += "─" * 24 + "\n"
        message += f"📦 <b>Subtotal:</b>  ${order.subtotal:.2f}\n"
        if order.delivery > 0:
            message += f"🚚 <b>Delivery:</b>  ${order.delivery:.2f}\n"
        else:
            message += f"🚚 <b>Delivery:</b>  FREE\n"
        message += f"💵 <b>Total:</b>  ${order.total:.2f}\n"
        message += f"💳 <b>Payment:</b>  Pending (KHQR)"

        payload = {
            "text": message,
            "parse_mode": "HTML",
            "chat_id": chat_id,
            "disable_web_page_preview": False,
            "disable_notification": False
        }
        headers = {
            "accept": "application/json",
            "content-type": "application/json"
        }
        requests.post(url, json=payload, headers=headers, timeout=5)
    except Exception as err:
        print(f"Telegram notification skipped/failed: {err}")


@front_bp.get('/checkout')
def checkout():
    # Require customer account to access checkout
    if not session.get('customer_id') or not session.get('is_customer_login'):
        return redirect(url_for('front_bp.login', next=url_for('front_bp.checkout'), msg='need_account'))

    customer = db.session.get(USER_CUSTOMER, session.get('customer_id'))

    cart_list = request.cookies.get('cart_list')
    cart_list = json.loads(cart_list) if cart_list else []

    clean_cart = []
    for item in cart_list:
        product = get_product_by_id(item['id'])
        if product is None:
            continue
        clean_cart.append({
            'id':    item['id'],
            'qty':   item['qty'],
            'image': product['image'],
            'name':  product['name'],
            'unit':  product['unit'],
            'price': product['price'],
            'origin': product.get('origin', ''),
        })

    subtotal = sum(item['qty'] * item['price'] for item in clean_cart)
    delivery = 0.00 if (subtotal >= FREE_DELIVERY or subtotal == 0) else DELIVERY_FEE
    total = subtotal + delivery

    return render_template(
        'front/checkout.html',
        cart_list=clean_cart,
        subtotal=subtotal,
        total=total,
        delivery=delivery,
        module='checkout',
        customer=customer
    )


@front_bp.post('/checkout')
@csrf.exempt
def checkout_post():
    is_ajax = (
        request.headers.get('X-Requested-With') == 'XMLHttpRequest' or
        request.is_json or
        'application/json' in request.headers.get('Accept', '') or
        request.args.get('format') == 'json'
    )

    # Require customer account to place order
    if not session.get('customer_id') or not session.get('is_customer_login'):
        if is_ajax:
            return jsonify({
                "success": False,
                "require_account": True,
                "error": "You must have an account and be logged in to buy products.",
                "login_url": url_for('front_bp.login', next=url_for('front_bp.checkout'), msg='need_account')
            }), 401
        return redirect(url_for('front_bp.login', next=url_for('front_bp.checkout'), msg='need_account'))

    customer = db.session.get(USER_CUSTOMER, session.get('customer_id'))

    cart_list = request.cookies.get('cart_list')
    cart_list = json.loads(cart_list) if cart_list else []

    if not cart_list:
        if is_ajax:
            return jsonify({"success": False, "error": "Your cart is empty."}), 400
        return redirect(url_for('front_bp.cart'))

    # Read customer info from form or JSON
    if request.is_json:
        data = request.get_json()
        firstname = data.get('firstname', '').strip()
        lastname = data.get('lastname', '').strip()
        phone = data.get('phone', '').strip()
        email = data.get('email', '').strip()
        address = data.get('address', '').strip()
    else:
        firstname = request.form.get('firstname', '').strip()
        lastname = request.form.get('lastname', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        address = request.form.get('address', '').strip()

    customer_name = f"{firstname} {lastname}".strip() or "Valued Customer"

    ordered_items = []
    for item in cart_list:
        product = get_product_by_id(item['id'])
        if product is None:
            continue
        ordered_items.append({
            'product_id': item['id'],
            'name':  product['name'],
            'image': product['image'],
            'unit':  product.get('unit', ''),
            'price': float(product['price']),
            'qty':   int(item['qty']),
        })

    if not ordered_items:
        if is_ajax:
            return jsonify({"success": False, "error": "Products in cart are no longer available."}), 400
        return redirect(url_for('front_bp.cart'))

    subtotal = sum(i['qty'] * i['price'] for i in ordered_items)
    delivery = 0.00 if subtotal >= FREE_DELIVERY else DELIVERY_FEE
    total = round(subtotal + delivery, 2)

    order_number = generate_order_number()

    # Generate KHQR code and Base64 Data URI
    qr_raw, base64_uri, md5 = build_khqr_data(total, order_number, phone)

    # Save Order in Database
    new_order = Order(
        order_number=order_number,
        customer_name=customer_name,
        phone=phone,
        email=email,
        address=address,
        customer_id=session.get('customer_id'),
        subtotal=subtotal,
        delivery=delivery,
        total=total,
        payment_status="Pending",
        status="Pending",
        md5=md5,
        qr_data=qr_raw,
        qr_image=base64_uri
    )
    db.session.add(new_order)
    db.session.flush()

    # Add Order Items
    for item in ordered_items:
        order_item = OrderItem(
            order_id=new_order.id,
            product_id=item['product_id'],
            product_name=item['name'],
            product_image=item['image'],
            unit=item['unit'],
            price=item['price'],
            quantity=item['qty'],
            line_total=round(item['price'] * item['qty'], 2)
        )
        db.session.add(order_item)

    db.session.commit()

    # Track order in session
    my_orders = session.get('my_order_ids', [])
    if new_order.id not in my_orders:
        my_orders.append(new_order.id)
    session['my_order_ids'] = my_orders

    # Send Telegram notification safely
    send_telegram_order_alert(new_order, ordered_items)

    if is_ajax:
        return jsonify({
            "success": True,
            "order_id": new_order.id,
            "order_number": new_order.order_number,
            "total": new_order.total,
            "base64_uri": base64_uri,
            "md5": md5,
            "expires_seconds": 300
        })

    # Non-AJAX fallback: render checkout page with popup modal trigger
    clean_cart = []
    for item in cart_list:
        product = get_product_by_id(item['id'])
        if product:
            clean_cart.append({
                'id': item['id'],
                'qty': item['qty'],
                'image': product['image'],
                'name': product['name'],
                'unit': product['unit'],
                'price': product['price'],
            })

    return render_template(
        'front/checkout.html',
        cart_list=clean_cart,
        subtotal=subtotal,
        total=total,
        delivery=delivery,
        module='checkout',
        modal_order=new_order,
        modal_base64_uri=base64_uri
    )


@front_bp.get('/checkout/check-status/<int:order_id>')
def check_order_payment_status(order_id):
    order = db.session.get(Order, order_id)
    if not order:
        return jsonify({"status": "NOT_FOUND"}), 404

    if order.payment_status.lower() == 'paid':
        return jsonify({
            "status": "PAID",
            "order_id": order.id,
            "order_number": order.order_number
        })

    # If transaction has md5 and is still pending, attempt check with Bakong
    if order.md5:
        try:
            khqr = KHQR(Config.BAKONG_TOKEN)
            res = khqr.check_payment(order.md5)
            status_str = res[0] if isinstance(res, tuple) else str(res)
            status_upper = status_str.upper()
            if status_upper == 'PAID':
                order.payment_status = "Paid"
                db.session.commit()
                return jsonify({
                    "status": "PAID",
                    "order_id": order.id,
                    "order_number": order.order_number
                })
            elif status_upper == 'SCANNED':
                return jsonify({
                    "status": "SCANNED",
                    "order_id": order.id,
                    "order_number": order.order_number
                })
        except Exception:
            pass

    return jsonify({
        "status": order.payment_status.upper(),
        "order_id": order.id,
        "order_number": order.order_number
    })


@front_bp.post('/checkout/clear-cart')
@csrf.exempt
def clear_cart_endpoint():
    resp = make_response(jsonify({"success": True}))
    resp.set_cookie('cart_list', '', expires=0)
    return resp


@front_bp.get('/my-orders')
def my_orders():
    module = 'my_orders'
    order_ids = session.get('my_order_ids', [])
    customer_id = session.get('customer_id') or session.get('user_id')

    orders = []
    if order_ids or customer_id:
        query = Order.query
        filters = []
        if order_ids:
            filters.append(Order.id.in_(order_ids))
        if customer_id:
            filters.append(Order.customer_id == customer_id)
        orders = query.filter(db.or_(*filters)).order_by(Order.created_at.desc()).all()

    highlight_id = request.args.get('order_id', type=int)

    return render_template(
        'front/my_orders.html',
        orders=orders,
        highlight_id=highlight_id,
        module=module
    )
