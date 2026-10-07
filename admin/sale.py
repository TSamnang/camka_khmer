from admin import admin_bp
from flask import render_template
from admin.auth import login_required
from extension import limiter, get_user_id


@admin_bp.get('/sales/order')
@limiter.limit("10 per minute", key_func=get_user_id)
@login_required
def order_page():
    module = 'order'
    return render_template('admin/sales/order.html', module=module)

@admin_bp.get('/sales/order-details')
@limiter.limit("10 per minute", key_func=get_user_id)
@login_required
def order_detail_page():
    module = 'order / order-details'
    return render_template('admin/sales/order-detail.html', module=module)
