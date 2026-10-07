from admin import admin_bp
from flask import render_template
from admin.auth import login_required
from extension import limiter, get_user_id


@admin_bp.get('/pages/system/setting')
@limiter.limit("10 per minute", key_func=get_user_id)
@login_required
def setting_page():
    module = 'setting'
    return render_template('admin/system/setting.html', module=module)

