from admin import admin_bp
from flask import render_template, session
from admin.auth import login_required
from extension import limiter, get_user_id


@admin_bp.get('/dashboard')
@login_required
@limiter.limit("10 per minute", key_func=get_user_id)
def dashboard_page():
    module = 'dashboard'
    return render_template('admin/dashboard/dashboard.html', module=module)

