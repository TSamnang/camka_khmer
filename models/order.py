from bson import ObjectId
from extension import mongo
from datetime import datetime


class OrderDoc(dict):
    def __getattr__(self, key):
        return self.get(key)

    def __setattr__(self, key, value):
        self[key] = value

    def to_dict(self):
        return Order.to_dict_from_doc(self)


class Order:
    @classmethod
    def _col(cls):
        return mongo.db.orders

    @classmethod
    def _wrap(cls, doc):
        if not doc:
            return None
        d = OrderDoc(doc)
        d['id'] = str(doc.get('_id', ''))
        d['subtotal'] = round(float(d.get('subtotal', 0.0) or 0.0), 2)
        d['delivery'] = round(float(d.get('delivery', 0.0) or 0.0), 2)
        d['total'] = round(float(d.get('total', 0.0) or 0.0), 2)

        raw_items = d.get('items', [])
        cleaned_items = []
        for i in raw_items:
            i_dict = dict(i)
            if '_id' in i_dict:
                i_dict['id'] = str(i_dict['_id'])
            elif 'id' not in i_dict and 'product_id' in i_dict:
                i_dict['id'] = str(i_dict['product_id'])
            i_dict['price'] = round(float(i_dict.get('price', 0.0) or 0.0), 2)
            i_dict['quantity'] = int(i_dict.get('quantity', i_dict.get('qty', 1)) or 1)
            i_dict['line_total'] = round(float(i_dict.get('line_total', i_dict['price'] * i_dict['quantity']) or 0.0), 2)
            cleaned_items.append(i_dict)
        d['items'] = cleaned_items
        d['item_count'] = sum(i['quantity'] for i in cleaned_items)
        return d

    @classmethod
    def find_all(cls, status_filter=None, payment_status=None, phone=None, order_number=None, limit=200):
        query = {}
        if status_filter and status_filter != 'all':
            query['status'] = {'$regex': f'^{status_filter.strip()}$', '$options': 'i'}
        if payment_status:
            query['payment_status'] = {'$regex': f'^{payment_status.strip()}$', '$options': 'i'}
        if phone:
            query['phone'] = {'$regex': phone.strip(), '$options': 'i'}
        if order_number:
            query['order_number'] = {'$regex': order_number.strip(), '$options': 'i'}

        docs = list(cls._col().find(query).sort("created_at", -1).limit(limit))
        return [cls._wrap(d) for d in docs]

    @classmethod
    def find_by_id(cls, order_id):
        try:
            doc = cls._col().find_one({"_id": ObjectId(str(order_id))})
            return cls._wrap(doc)
        except Exception:
            return None

    @classmethod
    def find_latest(cls):
        doc = cls._col().find_one({}, sort=[("created_at", -1)])
        return cls._wrap(doc)

    @classmethod
    def insert(cls, data):
        data.setdefault('created_at', datetime.utcnow())
        data.setdefault('updated_at', datetime.utcnow())
        result = cls._col().insert_one(data)
        return str(result.inserted_id)

    @classmethod
    def update_status(cls, order_id, status):
        try:
            cls._col().update_one(
                {"_id": ObjectId(str(order_id))},
                {"$set": {"status": status, "updated_at": datetime.utcnow()}}
            )
        except Exception as e:
            print(f"Order status update error: {e}")

    @classmethod
    def update_payment_status(cls, order_id, payment_status):
        try:
            cls._col().update_one(
                {"_id": ObjectId(str(order_id))},
                {"$set": {"payment_status": payment_status, "updated_at": datetime.utcnow()}}
            )
        except Exception as e:
            print(f"Order payment update error: {e}")

    @classmethod
    def update_fields(cls, order_id, fields):
        try:
            fields['updated_at'] = datetime.utcnow()
            cls._col().update_one({"_id": ObjectId(str(order_id))}, {"$set": fields})
        except Exception as e:
            print(f"Order update fields error: {e}")

    @classmethod
    def delete(cls, order_id):
        try:
            cls._col().delete_one({"_id": ObjectId(str(order_id))})
        except Exception as e:
            print(f"Order delete error: {e}")

    @classmethod
    def count(cls, status_filter=None):
        query = {}
        if status_filter and status_filter != 'all':
            query['status'] = {'$regex': f'^{status_filter.strip()}$', '$options': 'i'}
        return cls._col().count_documents(query)

    @classmethod
    def total_revenue(cls):
        try:
            pipeline = [
                {"$match": {"payment_status": {"$regex": "^paid$", "$options": "i"}}},
                {"$group": {"_id": None, "total": {"$sum": "$total"}}}
            ]
            result = list(cls._col().aggregate(pipeline))
            return float(result[0]['total']) if result else 0.0
        except Exception:
            return 0.0

    @classmethod
    def to_dict_from_doc(cls, doc):
        w = cls._wrap(doc)
        if not w:
            return {}
        created_val = w.get('created_at')
        if isinstance(created_val, datetime):
            c_str = created_val.strftime("%Y-%m-%d %H:%M:%S")
        else:
            c_str = str(created_val or '')

        return {
            "id": w['id'],
            "order_number": w.get('order_number', ''),
            "customer_name": w.get('customer_name', ''),
            "phone": w.get('phone', ''),
            "email": w.get('email', ''),
            "address": w.get('address', ''),
            "customer_id": w.get('customer_id', ''),
            "subtotal": round(float(w.get('subtotal', 0.0)), 2),
            "delivery": round(float(w.get('delivery', 0.0)), 2),
            "total": round(float(w.get('total', 0.0)), 2),
            "payment_status": w.get('payment_status', 'Pending'),
            "status": w.get('status', 'Pending'),
            "md5": w.get('md5', ''),
            "qr_image": w.get('qr_image', ''),
            "created_at": c_str,
            "item_count": w.get('item_count', 0),
            "items": [
                {
                    "id": str(i.get('id', '')),
                    "product_id": i.get('product_id', ''),
                    "product_name": i.get('product_name', i.get('name', '')),
                    "product_image": i.get('product_image', i.get('image', '/static/images/bread.jpg')),
                    "unit": i.get('unit', ''),
                    "price": round(float(i.get('price', 0.0)), 2),
                    "quantity": int(i.get('quantity', 1)),
                    "line_total": round(float(i.get('line_total', 0.0)), 2)
                }
                for i in w.get('items', [])
            ]
        }


ORDER = Order
OrderItem = Order
ORDER_ITEM = Order
