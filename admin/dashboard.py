from admin import admin_bp
from flask import render_template
from admin.auth import login_required
from extension import db, limiter, get_user_id
from models.user_farmer import USER_FARMER
from models.user_customer import USER_CUSTOMER
from models.product import Product
from models.order import Order


@admin_bp.get('/dashboard')
@login_required
@limiter.limit("10 per minute", key_func=get_user_id)
def dashboard_page():
    module = 'dashboard'
    farmer_count = USER_FARMER.query.count()
    customer_count = USER_CUSTOMER.query.count()
    pending_count = Product.query.filter(db.func.lower(Product.status) == 'pending').count()
    recent_products = Product.query.order_by(Product.id.desc()).limit(5).all()

    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    total_revenue = db.session.query(db.func.sum(Order.total)).filter(db.func.lower(Order.payment_status) == 'paid').scalar() or 0.0

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
