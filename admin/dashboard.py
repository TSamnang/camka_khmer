from admin import admin_bp
from flask import render_template
from admin.auth import login_required


@admin_bp.get('/dashboard')
@login_required
def dashboard_page():
    module = 'dashboard'
    return render_template('admin/dashboard/dashboard.html', module=module)

