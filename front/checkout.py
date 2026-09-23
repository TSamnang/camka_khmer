from front import front_bp
from flask import render_template, request, make_response, url_for, redirect
import json
from products import get_product_by_id


@front_bp.get('/checkout')
def checkout():

    cart_list = request.cookies.get('cart_list')
    cart_list = json.loads(cart_list) if cart_list else []

    # Map slim cookie data to full product info for display
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
            'origin': product['origin'],
        })

        # calculate price — must be OUTSIDE the loop so it runs even for empty carts
        DELIVERY_FEE = 2.00
        FREE_DELIVERY = 25.00

        subtotal = sum(item['qty'] * item['price'] for item in clean_cart)
        delivery = 0.00 if subtotal >= FREE_DELIVERY else DELIVERY_FEE
        total = subtotal + delivery

    return render_template('front/checkout.html',
                           cart_list = clean_cart,
                           subtotal=subtotal,
                           total=total,
                           delivery=delivery,)

@front_bp.post('/checkout')
def checkout_post():
    import requests

    cart_list = request.cookies.get('cart_list')
    cart_list = json.loads(cart_list) if cart_list else []

    form = request.form
    firstname = form['firstname']
    lastname = form['lastname']
    phone = form['phone']
    email = form['email']
    address = form['address']

    DELIVERY_FEE = 2.00
    FREE_DELIVERY = 25.00

    ordered_items = []
    for item in cart_list:
        product = get_product_by_id(item['id'])
        if product is None:
            continue
        ordered_items.append({
            'name':  product['name'],
            'unit':  product['unit'],
            'price': product['price'],
            'qty':   item['qty'],
        })

    subtotal = sum(i['qty'] * i['price'] for i in ordered_items)
    delivery = 0.00 if subtotal >= FREE_DELIVERY else DELIVERY_FEE
    total    = subtotal + delivery

    # send notification to telegram
    bot_token = "8667483588:AAHSOOvhPmY02B6s4nHWZM1cuL8U1sDN9sw"
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    message  = f"🛒 <b>New Order Received!</b>\n\n"
    message += f"👤 <b>Name:</b> {firstname} {lastname}\n"
    message += f"📞 <b>Phone:</b> {phone}\n"
    message += f"📧 <b>Email:</b> {email}\n"
    message += f"📍 <b>Address:</b> {address}\n\n"

    message += f"🧾 <b>Items Ordered:</b>\n"
    message += "─" * 24 + "\n"
    idx = 1
    for item in ordered_items:
        line_total = item['qty'] * item['price']
        message += (
            f"{idx}. <b>{item['name']}</b>\n"
            f"   • Qty: {item['qty']} × {item['unit']}\n"
            f"   • Price: ${item['price']:.2f}  →  <b>${line_total:.2f}</b>\n"
        )
        idx += 1
    message += "─" * 24 + "\n"
    message += f"📦 <b>Subtotal:</b>  ${subtotal:.2f}\n"
    if delivery > 0:
        message += f"🚚 <b>Delivery:</b>  ${delivery:.2f}\n"
    else:
        message += f"🚚 <b>Delivery:</b>  FREE\n"
    message += f"💵 <b>Total:</b>  ${total:.2f}"

    payload = {
        "text": message,
        "parse_mode": "HTML",
        "chat_id": "@comkakhmer",
        "disable_web_page_preview": False,
        "disable_notification": False,
        "reply_to_message_id": None
    }
    headers = {
        "accept": "application/json",
        "User-Agent": "Telegram Bot SDK - (https://github.com/irazasyed/telegram-bot-sdk)",
        "content-type": "application/json"
    }

    requests.post(url, json=payload, headers=headers)

    # Clear the cart and redirect to homepage after successful order
    res = make_response(redirect(url_for('front_bp.homepage')))
    res.set_cookie('cart_list', '', expires=0)
    return res

