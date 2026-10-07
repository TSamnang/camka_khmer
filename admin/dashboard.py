from admin import admin_bp
from flask import render_template, session
from admin.auth import login_required
from flask_limiter.util import get_remote_address

from extension import limiter


def get_user_id():
    user_id = session.get("id")
    return f"user_{user_id}" if user_id else get_remote_address()

@admin_bp.get('/dashboard')
@login_required
@limiter.limit("10 per minute", key_func=get_user_id)
def dashboard_page():
    module = 'dashboard'
    return render_template('admin/dashboard/dashboard.html', module=module)

