from models.product import Product
from extension import db


def get_product_by_id(product_id):
    """Fetch product from database by ID and return dict or None."""
    try:
        prod = db.session.get(Product, int(product_id))
        if prod:
            return prod.to_dict()
    except Exception:
        pass
    return None


def get_product_by_category(category):
    """Fetch products matching category name or substring from database."""
    try:
        prods = Product.query.filter(
            (db.func.lower(Product.category) == str(category).strip().lower()) |
            (Product.category.ilike(f"%{category}%"))
        ).all()
        return [p.to_dict() for p in prods]
    except Exception:
        return []


def get_all_products():
    """Fetch all products from database."""
    try:
        prods = Product.query.order_by(Product.id.asc()).all()
        return [p.to_dict() for p in prods]
    except Exception:
        return []


def cart_increase(cart_list, product_id):
    product_id = int(product_id)
    for item in cart_list:
        if item['id'] == product_id:
            item['qty'] += 1
            return cart_list
    cart_list.append({'id': product_id, 'qty': 1})
    return cart_list


def cart_decrease(cart_list, product_id):
    product_id = int(product_id)
    for item in cart_list:
        if item['id'] == product_id:
            item['qty'] -= 1
            break
    cart_list = [item for item in cart_list if item['qty'] > 0]
    return cart_list


increase_cart_item = cart_increase
decrease_cart_item = cart_decrease
