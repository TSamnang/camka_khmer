from api import api_bp
from flask import request, jsonify
from datetime import datetime
import random
from extension import db
from models.order import Order, OrderItem
from models.product import Product
from bakong_khqr import KHQR
from config import Config


DELIVERY_FEE = 2.00
FREE_DELIVERY = 25.00


def generate_api_order_number():
    date_str = datetime.utcnow().strftime('%Y%m%d')
    rand_str = f"{random.randint(1000, 9999)}"
    return f"ORD-{date_str}-{rand_str}"


@api_bp.get("/order")
def get_orders():
    """Retrieve list of orders with optional filters."""
    status = request.args.get('status')
    payment_status = request.args.get('payment_status')
    phone = request.args.get('phone')
    order_number = request.args.get('order_number')
    limit = request.args.get('limit', 50, type=int)

    query = Order.query

    if status:
        query = query.filter(db.func.lower(Order.status) == status.strip().lower())
    if payment_status:
        query = query.filter(db.func.lower(Order.payment_status) == payment_status.strip().lower())
    if phone:
        query = query.filter(Order.phone.ilike(f"%{phone.strip()}%"))
    if order_number:
        query = query.filter(Order.order_number.ilike(f"%{order_number.strip()}%"))

    orders = query.order_by(Order.created_at.desc()).limit(limit).all()
    return jsonify([o.to_dict() for o in orders])


@api_bp.get("/order/<int:order_id>")
def get_order(order_id):
    """Retrieve details for a specific order by ID."""
    order = db.session.get(Order, order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404
    return jsonify(order.to_dict())


@api_bp.post("/order")
def create_order():
    """Create a new order via API."""
    data = request.get_json(silent=True) or request.form
    if not data:
        return jsonify({"error": "Missing JSON payload or form data"}), 400

    firstname = data.get('firstname', '').strip()
    lastname = data.get('lastname', '').strip()
    customer_name = f"{firstname} {lastname}".strip() or data.get('customer_name', '').strip()
    phone = data.get('phone', '').strip()
    email = data.get('email', '').strip()
    address = data.get('address', '').strip()
    items_data = data.get('items', [])

    if not phone or not address:
        return jsonify({"error": "Phone and address are required"}), 400

    if not items_data:
        return jsonify({"error": "Order must include at least one item"}), 400

    ordered_items = []
    subtotal = 0.0

    for item in items_data:
        p_id = item.get('product_id') or item.get('id')
        qty = int(item.get('quantity', item.get('qty', 1)))
        if qty < 1:
            qty = 1

        product = db.session.get(Product, p_id) if p_id else None
        if not product:
            continue

        price = float(product.price)
        line_tot = round(price * qty, 2)
        subtotal += line_tot

        ordered_items.append({
            'product_id': product.id,
            'name': product.name,
            'image': product.image,
            'unit': product.unit or '1 unit',
            'price': price,
            'quantity': qty,
            'line_total': line_tot
        })

    if not ordered_items:
        return jsonify({"error": "None of the specified products could be found"}), 400

    delivery = 0.00 if subtotal >= FREE_DELIVERY else DELIVERY_FEE
    total = round(subtotal + delivery, 2)
    order_number = generate_api_order_number()

    # Generate KHQR
    qr_raw, base64_uri, md5 = "", "", ""
    try:
        khqr = KHQR(Config.BAKONG_TOKEN)
        qr_string = khqr.create_qr(
            account_id=Config.BAKONG_ACCOUNT_ID,
            merchant_name=Config.BAKONG_MERCHANT_NAME,
            merchant_city=Config.BAKONG_MERCHANT_CITY,
            amount=round(float(total), 2),
            currency="USD",
            store_label=Config.BAKONG_STORE_LABEL,
            phone_number=phone or Config.BAKONG_PHONE_NUMBER,
            bill_number=order_number,
            terminal_label=Config.BAKONG_TERMINAL_LABEL,
            static=False,
            expiration=1
        )
        base64_uri = khqr.qr_image(qr_string, format="base64_uri")
        md5 = getattr(qr_string, 'md5', None) or khqr.generate_md5(str(qr_string))
        qr_raw = str(qr_string)
    except Exception as e:
        print(f"API KHQR generation error: {e}")

    new_order = Order(
        order_number=order_number,
        customer_name=customer_name or "API Customer",
        phone=phone,
        email=email,
        address=address,
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

    for item in ordered_items:
        db.session.add(OrderItem(
            order_id=new_order.id,
            product_id=item['product_id'],
            product_name=item['name'],
            product_image=item['image'],
            unit=item['unit'],
            price=item['price'],
            quantity=item['quantity'],
            line_total=item['line_total']
        ))

    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Order created successfully",
        "order": new_order.to_dict()
    }), 201


@api_bp.patch("/order/<int:order_id>/confirm")
def api_confirm_order(order_id):
    """Confirm a pending order."""
    order = db.session.get(Order, order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404

    order.status = "Confirmed"
    db.session.commit()
    return jsonify({
        "success": True,
        "message": f"Order #{order.order_number} confirmed successfully",
        "order": order.to_dict()
    })


@api_bp.patch("/order/<int:order_id>/status")
def api_update_order_status(order_id):
    """Update order status or payment status."""
    order = db.session.get(Order, order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404

    data = request.get_json(silent=True) or request.form
    if not data:
        return jsonify({"error": "No data provided"}), 400

    if 'status' in data:
        valid_statuses = {"pending", "confirmed", "processing", "shipped", "delivered", "cancelled"}
        req_status = str(data['status']).strip().lower()
        if req_status in valid_statuses:
            order.status = req_status.title()

    if 'payment_status' in data:
        valid_payments = {"pending", "paid", "expired", "failed"}
        req_pay = str(data['payment_status']).strip().lower()
        if req_pay in valid_payments:
            order.payment_status = req_pay.title()

    db.session.commit()
    return jsonify({
        "success": True,
        "message": "Status updated successfully",
        "order": order.to_dict()
    })


@api_bp.delete("/order/<int:order_id>")
def api_delete_order(order_id):
    """Delete an order by ID."""
    order = db.session.get(Order, order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404

    db.session.delete(order)
    db.session.commit()
    return jsonify({"success": True, "message": f"Order #{order_id} deleted successfully"})

