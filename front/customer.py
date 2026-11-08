from front import front_bp
from flask import render_template, request, redirect, url_for, session
from werkzeug.security import check_password_hash, generate_password_hash
from extension import csrf
from models.user_customer import USER_CUSTOMER


@front_bp.get('/login')
def login():
    next_url = request.args.get('next', '').strip()
    msg = request.args.get('msg', '').strip()
    if session.get('is_customer_login'):
        return redirect(next_url if next_url.startswith('/') else url_for('front_bp.homepage'))
    return render_template('front/login.html', next_url=next_url, msg=msg)


@front_bp.post('/login')
@csrf.exempt
def login_post():
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '').strip()
    next_url = request.form.get('next', '').strip() or request.args.get('next', '').strip()

    if not email or not password:
        return render_template(
            'front/login.html',
            error="Please enter both your email and password.",
            next_url=next_url
        )

    customer = USER_CUSTOMER.find_by_email(email)

    if not customer or not check_password_hash(customer.get('password', ''), password):
        return render_template(
            'front/login.html',
            error="Invalid email or password. Please try again.",
            next_url=next_url
        )

    # Set authenticated customer session
    session['customer_id'] = customer['id']
    session['customer_name'] = customer.get('customer_name', '')
    session['customer_email'] = customer.get('customer_email', '')
    session['is_customer_login'] = True

    if next_url and next_url.startswith('/'):
        return redirect(next_url)
    return redirect(url_for('front_bp.homepage'))


@front_bp.get('/register')
def register():
    next_url = request.args.get('next', '').strip()
    if session.get('is_customer_login'):
        return redirect(next_url if next_url.startswith('/') else url_for('front_bp.homepage'))
    return render_template('front/register.html', next_url=next_url)


@front_bp.post('/register')
@csrf.exempt
def register_post():
    form = request.form
    firstname = form.get('firstname', '').strip()
    lastname = form.get('lastname', '').strip()
    email = form.get('email', '').strip()
    phone = form.get('phone', '').strip()
    password = form.get('password', '').strip()
    address = form.get('address', '').strip() or "Phnom Penh"
    next_url = form.get('next', '').strip()

    if not firstname or not email or not password:
        return render_template(
            'front/register.html',
            error="First name, email, and password are required.",
            next_url=next_url
        )

    # Check if email or phone already registered
    existing_email = USER_CUSTOMER.find_by_email(email)
    if existing_email:
        return render_template(
            'front/register.html',
            error="An account with this email address already exists. Please log in.",
            next_url=next_url
        )

    if phone:
        existing_phone = USER_CUSTOMER.find_by_phone(phone)
        if existing_phone:
            return render_template(
                'front/register.html',
                error="An account with this phone number already exists.",
                next_url=next_url
            )

    h_password = generate_password_hash(password)
    full_name = f"{firstname} {lastname}".strip() or firstname

    customer_id = USER_CUSTOMER.insert({
        'customer_name': full_name,
        'customer_email': email,
        'phoneNumber': phone or "012345678",
        'location': address,
        'role': "Customer",
        'status': "Active",
        'profile': "/static/images/default-avatar.png",
        'password': h_password
    })

    # Log customer in immediately
    session['customer_id'] = customer_id
    session['customer_name'] = full_name
    session['customer_email'] = email
    session['is_customer_login'] = True

    if next_url and next_url.startswith('/'):
        return redirect(next_url)
    return redirect(url_for('front_bp.homepage'))


@front_bp.get('/logout')
def logout():
    session.pop('customer_id', None)
    session.pop('customer_name', None)
    session.pop('customer_email', None)
    session.pop('is_customer_login', None)
    return redirect(url_for('front_bp.homepage'))
