from admin import admin_bp
from flask import render_template
from admin.auth import login_required
from extension import limiter, get_user_id
from models.user_farmer import USER_FARMER
from models.user_customer import USER_CUSTOMER
from models.product import Product
from models.order import Order


@admin_bp.get('/dashboard')
@login_required
@limiter.limit("10 per minute", key_func=get_user_id)
def dashboard_page():
    module = 'dashboard'
    farmer_count = USER_FARMER.count()
    customer_count = USER_CUSTOMER.count()
    pending_count = Product.count(status_filter='pending')
    recent_products = Product.find_all()[:5]
    recent_orders = Order.find_all(limit=5)
    total_revenue = Order.total_revenue()

    return render_template(
        'admin/dashboard/dashboard.html',
        module=module,
        farmer_count=farmer_count,
        customer_count=customer_count,
        pending_count=pending_count,
        recent_products=recent_products,
        recent_orders=recent_orders,
        total_revenue=total_revenue
    )
