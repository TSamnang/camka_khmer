from admin import admin_bp
from flask import render_template
from admin.auth import login_required


@admin_bp.get('/pages/system/setting')
@login_required
def setting_page():
    module = 'setting'
    return render_template('admin/system/setting.html', module=module)

