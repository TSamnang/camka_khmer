from front import front_bp
from flask import render_template, request, make_response, url_for, redirect, jsonify, session
import json
import random
from datetime import datetime
from bson import ObjectId
from products import get_product_by_id
from extension import mongo, csrf
from models.order import Order
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

        order_num = order.get('order_number', '')
        cust_name = order.get('customer_name', '')
        cust_phone = order.get('phone', '')
        cust_email = order.get('email', '')
        cust_addr = order.get('address', '')
        subtotal = float(order.get('subtotal', 0.0))
        delivery = float(order.get('delivery', 0.0))
        total = float(order.get('total', 0.0))

        message = f"🛒 <b>New Order Received!</b>\n\n"
        message += f"🔖 <b>Order ID:</b> #{order_num}\n"
        message += f"👤 <b>Name:</b> {cust_name}\n"
        message += f"📞 <b>Phone:</b> {cust_phone}\n"
        if cust_email:
            message += f"📧 <b>Email:</b> {cust_email}\n"
        message += f"📍 <b>Address:</b> {cust_addr}\n\n"

        message += f"🧾 <b>Items Ordered:</b>\n"
        message += "─" * 24 + "\n"
        for idx, item in enumerate(ordered_items, 1):
            qty = item.get('qty', item.get('quantity', 1))
            price = item.get('price', 0.0)
            line_tot = qty * price
            message += (
                f"{idx}. <b>{item.get('name', '')}</b>\n"
                f"   • Qty: {qty} × {item.get('unit', '')}\n"
                f"   • Price: ${price:.2f}  →  <b>${line_tot:.2f}</b>\n"
            )
        message += "─" * 24 + "\n"
        message += f"📦 <b>Subtotal:</b>  ${subtotal:.2f}\n"
        if delivery > 0:
            message += f"🚚 <b>Delivery:</b>  ${delivery:.2f}\n"
        else:
            message += f"🚚 <b>Delivery:</b>  FREE\n"
        message += f"💵 <b>Total:</b>  ${total:.2f}\n"
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

    customer = USER_CUSTOMER.find_by_id(session.get('customer_id'))

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
            'product_id': str(item['id']),
            'name':  product.get('name', ''),
            'image': product.get('image', ''),
            'unit':  product.get('unit', ''),
            'price': float(product.get('price', 0.0)),
            'qty':   int(item['qty']),
            'quantity': int(item['qty']),
            'line_total': round(float(product.get('price', 0.0)) * int(item['qty']), 2)
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
    inserted_id = Order.insert({
        'order_number': order_number,
        'customer_name': customer_name,
        'phone': phone,
        'email': email,
        'address': address,
        'customer_id': str(session.get('customer_id') or ''),
        'subtotal': subtotal,
        'delivery': delivery,
        'total': total,
        'payment_status': "Pending",
        'status': "Pending",
        'md5': md5,
        'qr_data': qr_raw,
        'qr_image': base64_uri,
        'items': ordered_items
    })

    new_order = Order.find_by_id(inserted_id)

    # Track order in session
    my_orders = session.get('my_order_ids', [])
    if inserted_id not in my_orders:
        my_orders.append(inserted_id)
    session['my_order_ids'] = my_orders

    # Send Telegram notification safely
    send_telegram_order_alert(new_order, ordered_items)

    if is_ajax:
        return jsonify({
            "success": True,
            "order_id": new_order['id'],
            "order_number": new_order.get('order_number'),
            "total": new_order.get('total'),
            "base64_uri": base64_uri,
            "md5": md5,
            "expires_seconds": 300
        })

    clean_cart = []
    for item in cart_list:
        product = get_product_by_id(item['id'])
        if product:
            clean_cart.append({
                'id': str(item['id']),
                'qty': int(item['qty']),
                'image': product.get('image', ''),
                'name': product.get('name', ''),
                'unit': product.get('unit', ''),
                'price': float(product.get('price', 0.0)),
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


@front_bp.get('/checkout/check-status/<order_id>')
def check_order_payment_status(order_id):
    order = Order.find_by_id(order_id)
    if not order:
        return jsonify({"status": "NOT_FOUND"}), 404

    current_pay_status = str(order.get('payment_status', 'Pending')).lower()
    if current_pay_status == 'paid':
        return jsonify({
            "status": "PAID",
            "order_id": order['id'],
            "order_number": order.get('order_number')
        })

    # If transaction has md5 and is still pending, attempt check with Bakong
    md5 = order.get('md5')
    if md5:
        try:
            khqr = KHQR(Config.BAKONG_TOKEN)
            res = khqr.check_payment(md5)
            status_str = res[0] if isinstance(res, tuple) else str(res)
            status_upper = status_str.upper()
            if status_upper == 'PAID':
                Order.update_payment_status(order_id, "Paid")
                return jsonify({
                    "status": "PAID",
                    "order_id": order['id'],
                    "order_number": order.get('order_number')
                })
            elif status_upper == 'SCANNED':
                return jsonify({
                    "status": "SCANNED",
                    "order_id": order['id'],
                    "order_number": order.get('order_number')
                })
        except Exception:
            pass

    return jsonify({
        "status": str(order.get('payment_status', 'PENDING')).upper(),
        "order_id": order['id'],
        "order_number": order.get('order_number')
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

    or_filters = []
    if order_ids:
        valid_oids = []
        for oid in order_ids:
            try:
                valid_oids.append(ObjectId(str(oid)))
            except Exception:
                pass
        if valid_oids:
            or_filters.append({"_id": {"$in": valid_oids}})
    if customer_id:
        or_filters.append({"customer_id": str(customer_id)})

    if or_filters:
        docs = list(mongo.db.orders.find({"$or": or_filters}).sort("created_at", -1))
        orders = [Order._wrap(d) for d in docs]
    else:
        orders = []

    highlight_id = request.args.get('order_id', '')

    return render_template(
        'front/my_orders.html',
        orders=orders,
        highlight_id=highlight_id,
        module=module
    )
