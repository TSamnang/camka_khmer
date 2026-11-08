from flask import Flask, render_template, request, jsonify, session
import json
import os
from config import Config
from extension import mongo, limiter, csrf, core
from front import front_bp
from admin import admin_bp
from api import api_bp
from bakong_khqr import KHQR
from models.category import Category
from models.order import Order
from models.error_log import ErrorLog

static_folder = 'public/static' if os.path.exists(os.path.join(os.path.dirname(__file__), 'public', 'static')) else 'static'
app = Flask(__name__, static_folder=static_folder)
app.config.from_object(Config)

mongo.init_app(app)
limiter.init_app(app)
csrf.init_app(app)
core.init_app(app, resources={
    r"/api/*": {"origins": Config.CORS_ORIGINS}
})


# Context processor to ensure cart_list and categories are always available
@app.context_processor
def inject_defaults():
    try:
        cart_cookie = request.cookies.get('cart_list')
        cart_list = json.loads(cart_cookie) if cart_cookie else []
    except Exception:
        cart_list = []

    try:
        categories = Category.find_all()
    except Exception:
        categories = []

    try:
        pending_order_count = Order.count(status_filter="pending")
    except Exception:
        pending_order_count = 0

    return dict(cart_list=cart_list, categories=categories, pending_order_count=pending_order_count)


app.register_blueprint(front_bp, url_prefix="/")
app.register_blueprint(admin_bp, url_prefix="/admin")
app.register_blueprint(api_bp, url_prefix="/api")
csrf.exempt(api_bp)


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
    endpoint = f"{request.method} {request.path}"
    client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    if client_ip and "," in client_ip:
        client_ip = client_ip.split(",")[0].strip()
    user_agent = request.headers.get("User-Agent", "Unknown")

    try:
        import requests
        from datetime import datetime

        bot_token = Config.TELEGRAM_DEV_BOT_TOKEN
        chat_id = Config.TELEGRAM_DEV_CHAT_ID
        if bot_token and chat_id:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            short_ua = user_agent[:117] + "..." if len(user_agent) > 120 else user_agent

            is_admin = request.path.startswith("/admin")
            is_api = request.path.startswith("/api")
            threat_badge = "🔴 <b>CRITICAL (Admin)</b>" if is_admin else ("🟠 <b>WARNING (API)</b>" if is_api else "🟡 <b>MODERATE</b>")
            limit_info = getattr(e, "description", "Rate limit exceeded")

            message = (
                "🚨 <b>[SECURITY ALERT] RATE LIMIT TRIGGERED</b>\n"
                "────────────────────────\n"
                "⚠️ <b>Status:</b> <code>HTTP 429 · Too Many Requests</code>\n"
                f"🎯 <b>Target:</b> <code>{endpoint}</code>\n"
                f"👤 <b>User:</b> <code>{user_name}</code>\n"
                f"📍 <b>Client IP:</b> <code>{client_ip}</code>\n"
                f"🕒 <b>Time:</b> <code>{timestamp}</code>\n"
                f"🛡️ <b>Threat Level:</b> {threat_badge}\n"
                f"⏱️ <b>Limit Rule:</b> <code>{limit_info}</code>\n"
                "────────────────────────\n"
                f"💻 <b>Device / User-Agent:</b>\n<code>{short_ua}</code>\n"
            )

            payload = {
                "text": message,
                "parse_mode": "HTML",
                "chat_id": chat_id,
                "disable_web_page_preview": True
            }
            res = requests.post(url, json=payload, timeout=4)
            if res.status_code == 200:
                telegram_sent = True
    except Exception as err:
        print(f"Telegram 429 notification error: {err}")

    # Store into MongoDB error_logs collection
    try:
        from datetime import datetime
        ErrorLog.insert({
            'status_code': 429,
            'endpoint': endpoint,
            'method': request.method,
            'user_name': user_name,
            'client_ip': client_ip,
            'threat_level': "HIGH" if request.path.startswith("/admin") else "MODERATE",
            'error_type': "RateLimitExceeded",
            'error_detail': str(getattr(e, 'description', str(e))),
            'user_agent': user_agent,
            'telegram_sent': telegram_sent,
            'created_at': datetime.now()
        })
    except Exception as db_err:
        print(f"Database error log save failed: {db_err}")


def _500_alert(e):
    telegram_sent = False
    user_name = get_current_user_name()
    endpoint = f"{request.method} {request.path}"
    client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    if client_ip and "," in client_ip:
        client_ip = client_ip.split(",")[0].strip()
    user_agent = request.headers.get("User-Agent", "Unknown")
    error_name = type(e).__name__
    error_detail = str(e)

    try:
        import requests
        from datetime import datetime

        bot_token = Config.TELEGRAM_DEV_BOT_TOKEN
        chat_id = Config.TELEGRAM_DEV_CHAT_ID
        if bot_token and chat_id:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            short_ua = user_agent[:117] + "..." if len(user_agent) > 120 else user_agent
            short_detail = error_detail[:177] + "..." if len(error_detail) > 180 else error_detail

            is_admin = request.path.startswith("/admin")
            is_api = request.path.startswith("/api")
            scope_badge = "🔴 <b>CRITICAL (Admin)</b>" if is_admin else ("🟠 <b>WARNING (API)</b>" if is_api else "🟡 <b>Front Page</b>")

            message = (
                "🔥 <b>[SERVER ERROR] 500 EXCEPTION DETECTED</b>\n"
                "────────────────────────\n"
                "⚠️ <b>Status:</b> <code>HTTP 500 · Internal Server Error</code>\n"
                f"🎯 <b>Target:</b> <code>{endpoint}</code>\n"
                f"👤 <b>User:</b> <code>{user_name}</code>\n"
                f"📍 <b>Client IP:</b> <code>{client_ip}</code>\n"
                f"🕒 <b>Time:</b> <code>{timestamp}</code>\n"
                f"🏷️ <b>Scope:</b> {scope_badge}\n"
                f"💥 <b>Error Type:</b> <code>{error_name}</code>\n"
                f"📋 <b>Detail:</b> <code>{short_detail}</code>\n"
                "────────────────────────\n"
                f"💻 <b>Device / User-Agent:</b>\n<code>{short_ua}</code>\n"
            )

            payload = {
                "text": message,
                "parse_mode": "HTML",
                "chat_id": chat_id,
                "disable_web_page_preview": True
            }
            res = requests.post(url, json=payload, timeout=4)
            if res.status_code == 200:
                telegram_sent = True
    except Exception as err:
        print(f"Telegram 500 notification error: {err}")

    # Store into MongoDB error_logs collection
    try:
        from datetime import datetime
        ErrorLog.insert({
            'status_code': 500,
            'endpoint': endpoint,
            'method': request.method,
            'user_name': user_name,
            'client_ip': client_ip,
            'threat_level': "HIGH" if request.path.startswith("/admin") else "MODERATE",
            'error_type': error_name,
            'error_detail': error_detail,
            'user_agent': user_agent,
            'telegram_sent': telegram_sent,
            'created_at': datetime.now()
        })
    except Exception as db_err:
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
    _429_alert(e)
    if request.path.startswith('/api'):
        return jsonify({"status": 429, "error": "Too Many Requests"}), 429
    if request.path.startswith('/admin'):
        return render_template("error/admin/429.html"), 429
    return render_template("error/front/429.html"), 429


@app.errorhandler(500)
def internal_server_error(e):
    _500_alert(e)
    if request.path.startswith('/api'):
        return jsonify({"status": 500, "error": "Internal Server Error"}), 500
    if request.path.startswith('/admin'):
        return render_template("error/admin/500.html"), 500
    return render_template("error/front/500.html"), 500


if __name__ == '__main__':
    app.run()
