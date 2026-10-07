from flask import Flask, render_template, request, jsonify, session
import json
from config import Config
from extension import db, migrate, limiter, csrf, core
from front import front_bp
from admin import admin_bp
from api import api_bp


app = Flask(__name__)
app.config.from_object(Config)


db.init_app(app)
migrate.init_app(app, db)
limiter.init_app(app)
csrf.init_app(app)
core.init_app(app, resources={
    r"/api/*": {"origins": "http://localhost:4200"}
})


# Context processor to ensure cart_list is always available
@app.context_processor
def inject_cart_defaults():
    try:
        cart_cookie = request.cookies.get('cart_list')
        cart_list = json.loads(cart_cookie) if cart_cookie else []
    except Exception:
        cart_list = []
    return dict(cart_list=cart_list)


#load model
import models

app.register_blueprint(front_bp, url_prefix="/")

app.register_blueprint(admin_bp, url_prefix="/admin")

app.register_blueprint(api_bp, url_prefix="/api")




def get_current_user_name():
    try:
        if session:
            for key in ("farmer_name", "user_name", "username", "customer_name", "email"):
                val = session.get(key)
                if val:
                    return str(val)
    except Exception:
        pass

    try:
        if request.authorization and request.authorization.username:
            return str(request.authorization.username)
    except Exception:
        pass

    try:
        if request.form:
            for key in ("username", "farmer_name", "customer_name", "email"):
                val = request.form.get(key)
                if val:
                    return str(val)
    except Exception:
        pass

    return "Guest"

def _429_alert(e):
    telegram_sent = False
    user_name = get_current_user_name()
    try:
        import requests
        from datetime import datetime

        bot_token = "8603989647:AAFH5v_MG3uqnG32w1mcqXHT9BxmZW6dgQw"
        chat_id = "@dev_camkakhmer"
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

        # Client IP (support proxy / forwarded headers)
        client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
        if client_ip and "," in client_ip:
            client_ip = client_ip.split(",")[0].strip()

        endpoint = f"{request.method} {request.path}"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        user_agent = request.headers.get("User-Agent", "Unknown")
        if len(user_agent) > 120:
            user_agent = user_agent[:117] + "..."

        is_admin = request.path.startswith("/admin")
        is_api = request.path.startswith("/api")

        if is_admin:
            threat_badge = "🔴 <b>CRITICAL (Admin Endpoint)</b>"
            threat_level = "CRITICAL (Admin Endpoint)"
        elif is_api:
            threat_badge = "🟠 <b>WARNING (API Abuse)</b>"
            threat_level = "WARNING (API Abuse)"
        else:
            threat_badge = "🟡 <b>MODERATE (Public Front Page)</b>"
            threat_level = "MODERATE (Public Front Page)"

        limit_info = getattr(e, "description", "Rate limit exceeded")

        message = (
            "🚨 <b>[SECURITY ALERT] RATE LIMIT TRIGGERED</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "⚠️ <b>Status:</b> <code>HTTP 429 · Too Many Requests</code>\n"
            f"🎯 <b>Target:</b> <code>{endpoint}</code>\n"
            f"👤 <b>User:</b> <code>{user_name}</code>\n"
            f"📍 <b>Client IP:</b> <code>{client_ip}</code>\n"
            f"🕒 <b>Time:</b> <code>{timestamp}</code>\n"
            f"🛡️ <b>Threat Level:</b> {threat_badge}\n"
            f"⏱️ <b>Limit Rule:</b> <code>{limit_info}</code>\n"
            "──────────────────────────\n"
            "💻 <b>Device / User-Agent:</b>\n"
            f"<code>{user_agent}</code>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🛡️ <i>Action: Request blocked automatically by Sentinel Shield.</i>\n"
            "🌱 <i>ចម្ការខ្មែរ · FarmMarket Dev Monitor</i>"
        )

        payload = {
            "text": message,
            "parse_mode": "HTML",
            "chat_id": chat_id,
            "disable_web_page_preview": True,
            "disable_notification": False
        }
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "User-Agent": "Telegram Bot SDK - (https://github.com/irazasyed/telegram-bot-sdk)"
        }

        res = requests.post(url, json=payload, headers=headers, timeout=4)
        if res.status_code == 200:
            telegram_sent = True
    except Exception as err:
        print(f"Telegram 429 notification error: {err}")

    # Store into database error_log table
    try:
        from models.error_log import ErrorLog
        log_entry = ErrorLog(
            status_code=429,
            endpoint=endpoint if 'endpoint' in locals() else f"{request.method} {request.path}",
            method=request.method,
            user_name=user_name,
            client_ip=client_ip if 'client_ip' in locals() else request.remote_addr,
            threat_level=threat_level if 'threat_level' in locals() else "WARNING",
            error_type="RateLimitExceeded",
            error_detail=str(limit_info) if 'limit_info' in locals() else str(e),
            user_agent=user_agent if 'user_agent' in locals() else request.headers.get("User-Agent", "Unknown"),
            telegram_sent=telegram_sent
        )
        db.session.add(log_entry)
        db.session.commit()
    except Exception as db_err:
        db.session.rollback()
        print(f"Database error log save failed: {db_err}")

def _500_alert(e):
    telegram_sent = False
    user_name = get_current_user_name()
    try:
        import requests
        from datetime import datetime

        bot_token = "8603989647:AAFH5v_MG3uqnG32w1mcqXHT9BxmZW6dgQw"
        chat_id = "@dev_camkakhmer"
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

        # Client IP (support proxy / forwarded headers)
        client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
        if client_ip and "," in client_ip:
            client_ip = client_ip.split(",")[0].strip()

        endpoint = f"{request.method} {request.path}"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        user_agent = request.headers.get("User-Agent", "Unknown")
        if len(user_agent) > 120:
            user_agent = user_agent[:117] + "..."

        is_admin = request.path.startswith("/admin")
        is_api = request.path.startswith("/api")

        if is_admin:
            scope_badge = "🔴 <b>CRITICAL (Admin Dashboard)</b>"
            scope_text = "CRITICAL (Admin Dashboard)"
        elif is_api:
            scope_badge = "🟠 <b>HIGH (API Backend)</b>"
            scope_text = "HIGH (API Backend)"
        else:
            scope_badge = "🟡 <b>MEDIUM (Customer Front Store)</b>"
            scope_text = "MEDIUM (Customer Front Store)"

        # Extract exception message
        error_name = type(e).__name__
        error_detail = str(e)
        if hasattr(e, "original_exception") and e.original_exception:
            error_name = type(e.original_exception).__name__
            error_detail = str(e.original_exception)

        if len(error_detail) > 180:
            short_detail = error_detail[:177] + "..."
        else:
            short_detail = error_detail

        message = (
            "🔥 <b>[SERVER ERROR] 500 EXCEPTION DETECTED</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "⚠️ <b>Status:</b> <code>HTTP 500 · Internal Server Error</code>\n"
            f"🎯 <b>Target:</b> <code>{endpoint}</code>\n"
            f"👤 <b>User:</b> <code>{user_name}</code>\n"
            f"📍 <b>Client IP:</b> <code>{client_ip}</code>\n"
            f"🕒 <b>Time:</b> <code>{timestamp}</code>\n"
            f"🏷️ <b>Scope:</b> {scope_badge}\n"
            f"💥 <b>Error Type:</b> <code>{error_name}</code>\n"
            f"📋 <b>Detail:</b> <code>{short_detail}</code>\n"
            "──────────────────────────\n"
            "💻 <b>Device / User-Agent:</b>\n"
            f"<code>{user_agent}</code>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🚨 <i>Action: Please check server logs and resolve promptly.</i>\n"
            "🌱 <i>ចម្ការខ្មែរ · FarmMarket Dev Monitor</i>"
        )

        payload = {
            "text": message,
            "parse_mode": "HTML",
            "chat_id": chat_id,
            "disable_web_page_preview": True,
            "disable_notification": False
        }
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "User-Agent": "Telegram Bot SDK - (https://github.com/irazasyed/telegram-bot-sdk)"
        }

        res = requests.post(url, json=payload, headers=headers, timeout=4)
        if res.status_code == 200:
            telegram_sent = True
    except Exception as err:
        print(f"Telegram 500 notification error: {err}")

    # Store into database error_log table
    try:
        from models.error_log import ErrorLog
        log_entry = ErrorLog(
            status_code=500,
            endpoint=endpoint if 'endpoint' in locals() else f"{request.method} {request.path}",
            method=request.method,
            user_name=user_name,
            client_ip=client_ip if 'client_ip' in locals() else request.remote_addr,
            threat_level=scope_text if 'scope_text' in locals() else "HIGH",
            error_type=error_name if 'error_name' in locals() else type(e).__name__,
            error_detail=error_detail if 'error_detail' in locals() else str(e),
            user_agent=user_agent if 'user_agent' in locals() else request.headers.get("User-Agent", "Unknown"),
            telegram_sent=telegram_sent
        )
        db.session.add(log_entry)
        db.session.commit()
    except Exception as db_err:
        db.session.rollback()
        print(f"Database error log save failed: {db_err}")

@app.errorhandler(404)
def page_not_found(e):
    if request.path.startswith('/api'):
        return jsonify({"status": 404, "error": "Not Found"}), 404
    if request.path.startswith('/admin'):
        return render_template("error/admin/404.html"), 404
    return render_template("error/front/404.html"), 404

@app.errorhandler(429)
def too_many_requests(e):
    # Send styled security alert to Telegram
    _429_alert(e)

    if request.path.startswith('/api'):
        return jsonify({"status": 429, "error": "Too Many Requests"}), 429
    if request.path.startswith('/admin'):
        return render_template("error/admin/429.html"), 429
    return render_template("error/front/429.html"), 429

@app.errorhandler(500)
def internal_server_error(e):
    # Send styled 500 alert to Telegram
    _500_alert(e)

    if request.path.startswith('/api'):
        return jsonify({"status": 500, "error": "Internal Server Error"}), 500
    if request.path.startswith('/admin'):
        return render_template("error/admin/500.html"), 500
    return render_template("error/front/500.html"), 500


# @app.before_request
# def before_request():
#     path = request.path
#
#     if 'admin' in path:
#         if session.get('is_login'):
#             return redirect(url_for('admin_bp.dashboard_page'))
#         else:
#             return redirect(url_for('admin_bp.admin_login'))
#     return None


if __name__ == '__main__':
    app.run()

