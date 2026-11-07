from admin import admin_bp
from flask import render_template, request, redirect, url_for, flash
from admin.auth import login_required
from extension import db, limiter, get_user_id, csrf
from models.order import Order


@admin_bp.get('/order')
@admin_bp.get('/sales/order')
@limiter.limit("20 per minute", key_func=get_user_id)
@login_required
def order_page():
    module = 'order'
    status_filter = request.args.get('status', 'all').strip().lower()

    query = Order.query
    if status_filter and status_filter != 'all':
        query = query.filter(db.func.lower(Order.status) == status_filter)

    orders = query.order_by(Order.created_at.desc()).all()

    total_count = Order.query.count()
    pending_count = Order.query.filter(db.func.lower(Order.status) == 'pending').count()
    confirmed_count = Order.query.filter(db.func.lower(Order.status) == 'confirmed').count()
    delivered_count = Order.query.filter(db.func.lower(Order.status) == 'delivered').count()

    return render_template(
        'admin/sales/order.html',
        module=module,
        orders=orders,
        current_status=status_filter,
        total_count=total_count,
        pending_count=pending_count,
        confirmed_count=confirmed_count,
        delivered_count=delivered_count
    )


@admin_bp.get('/order/<int:order_id>')
@admin_bp.get('/sales/order/<int:order_id>')
@admin_bp.get('/sales/order-details')
@limiter.limit("20 per minute", key_func=get_user_id)
@login_required
def order_detail_page(order_id=None):
    module = 'order / details'

    # Support legacy /sales/order-details?id=...
    if not order_id:
        order_id = request.args.get('id', type=int)

    if not order_id:
        # Fallback to the latest order if available
        first_order = Order.query.order_by(Order.id.desc()).first()
        if first_order:
            order_id = first_order.id
        else:
            return redirect(url_for('admin_bp.order_page'))

    order = db.session.get(Order, order_id)
    if not order:
        return redirect(url_for('admin_bp.order_page'))

    return render_template(
        'admin/sales/order-detail.html',
        module=module,
        order=order
    )


@admin_bp.post('/order/<int:order_id>/confirm')
@admin_bp.post('/sales/order/<int:order_id>/confirm')
@csrf.exempt
@login_required
def confirm_order(order_id):
    """Admin endpoint to confirm a pending customer order."""
    order = db.session.get(Order, order_id)
    if order:
        order.status = "Confirmed"
        db.session.commit()
    return redirect(request.referrer or url_for('admin_bp.order_page'))


@admin_bp.post('/order/<int:order_id>/status')
@admin_bp.post('/sales/order/<int:order_id>/status')
@csrf.exempt
@login_required
def update_order_status(order_id):
    """Admin endpoint to update order status (Processing, Shipped, Delivered, Cancelled)."""
    order = db.session.get(Order, order_id)
    if order:
        new_status = request.form.get('status', '').strip().title()
        valid_statuses = {"Pending", "Confirmed", "Processing", "Shipped", "Delivered", "Cancelled"}
        if new_status in valid_statuses:
            order.status = new_status
            db.session.commit()
    return redirect(request.referrer or url_for('admin_bp.order_detail_page', order_id=order_id))


@admin_bp.post('/order/<int:order_id>/delete')
@admin_bp.post('/sales/order/<int:order_id>/delete')
@csrf.exempt
@login_required
def delete_order(order_id):
    order = db.session.get(Order, order_id)
    if order:
        db.session.delete(order)
        db.session.commit()
    return redirect(url_for('admin_bp.order_page'))
