from admin import admin_bp
from flask import render_template, request, redirect, url_for
from admin.auth import login_required
from extension import limiter, get_user_id, csrf
from models.order import Order


@admin_bp.get('/order')
@admin_bp.get('/sales/order')
@limiter.limit("20 per minute", key_func=get_user_id)
@login_required
def order_page():
    module = 'order'
    status_filter = request.args.get('status', 'all').strip().lower()

    orders = Order.find_all(status_filter=status_filter)

    total_count = Order.count()
    pending_count = Order.count(status_filter='pending')
    confirmed_count = Order.count(status_filter='confirmed')
    delivered_count = Order.count(status_filter='delivered')

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


@admin_bp.get('/order/<order_id>')
@admin_bp.get('/sales/order/<order_id>')
@admin_bp.get('/sales/order-details')
@limiter.limit("20 per minute", key_func=get_user_id)
@login_required
def order_detail_page(order_id=None):
    module = 'order / details'

    # Support legacy /sales/order-details?id=...
    if not order_id:
        order_id = request.args.get('id', '')

    if not order_id:
        # Fallback to the latest order if available
        first_order = Order.find_latest()
        if first_order:
            order_id = first_order['id']
        else:
            return redirect(url_for('admin_bp.order_page'))

    order = Order.find_by_id(order_id)
    if not order:
        return redirect(url_for('admin_bp.order_page'))

    return render_template(
        'admin/sales/order-detail.html',
        module=module,
        order=order
    )


@admin_bp.post('/order/<order_id>/confirm')
@admin_bp.post('/sales/order/<order_id>/confirm')
@csrf.exempt
@login_required
def confirm_order(order_id):
    """Admin endpoint to confirm a pending customer order."""
    Order.update_status(order_id, "Confirmed")
    return redirect(request.referrer or url_for('admin_bp.order_page'))


@admin_bp.post('/order/<order_id>/status')
@admin_bp.post('/sales/order/<order_id>/status')
@csrf.exempt
@login_required
def update_order_status(order_id):
    """Admin endpoint to update order status (Processing, Shipped, Delivered, Cancelled)."""
    new_status = request.form.get('status', '').strip().title()
    valid_statuses = {"Pending", "Confirmed", "Processing", "Shipped", "Delivered", "Cancelled"}
    if new_status in valid_statuses:
        Order.update_status(order_id, new_status)
    return redirect(request.referrer or url_for('admin_bp.order_detail_page', order_id=order_id))


@admin_bp.post('/order/<order_id>/delete')
@admin_bp.post('/sales/order/<order_id>/delete')
@csrf.exempt
@login_required
def delete_order(order_id):
    Order.delete(order_id)
    return redirect(url_for('admin_bp.order_page'))
