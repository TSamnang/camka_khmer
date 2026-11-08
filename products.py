from models.product import Product


def get_product_by_id(product_id):
    """Fetch product from database by ID and return dict or None."""
    try:
        prod = Product.find_by_id(str(product_id))
        if prod:
            return prod.to_dict()
    except Exception:
        pass
    return None


def get_product_by_category(category):
    """Fetch products matching category name or substring from database."""
    try:
        prods = Product.find_by_category(str(category))
        return [p.to_dict() for p in prods]
    except Exception:
        return []


def get_all_products():
    """Fetch all products from database."""
    try:
        prods = Product.find_all()
        return [p.to_dict() for p in prods]
    except Exception:
        return []


def cart_increase(cart_list, product_id):
    product_id = str(product_id)
    for item in cart_list:
        if str(item.get('id', '')) == product_id:
            item['qty'] = int(item.get('qty', 1)) + 1
            return cart_list
    cart_list.append({'id': product_id, 'qty': 1})
    return cart_list


def cart_decrease(cart_list, product_id):
    product_id = str(product_id)
    for item in cart_list:
        if str(item.get('id', '')) == product_id:
            item['qty'] = int(item.get('qty', 1)) - 1
            break
    cart_list = [item for item in cart_list if int(item.get('qty', 0)) > 0]
    return cart_list


increase_cart_item = cart_increase
decrease_cart_item = cart_decrease
