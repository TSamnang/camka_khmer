from bson import ObjectId
from extension import mongo
from datetime import date


class ProductDoc(dict):
    def __getattr__(self, key):
        return self.get(key)

    def __setattr__(self, key, value):
        self[key] = value

    @property
    def org_image(self):
        img = self.get('image')
        if not img:
            return "/static/images/bread.jpg"
        img_str = str(img)
        if "/static/uploads/thumb/" in img_str:
            return img_str.replace("/static/uploads/thumb/", "/static/uploads/org/")
        if "/uploads/thumb/" in img_str:
            return img_str.replace("/uploads/thumb/", "/uploads/org/")
        if "/thumb/" in img_str:
            return img_str.replace("/thumb/", "/org/")
        if not img_str.startswith("/") and not img_str.startswith("http"):
            return f"/static/uploads/org/{img_str}"
        return img_str

    @property
    def thumb_image(self):
        img = self.get('image')
        if not img:
            return "/static/images/bread.jpg"
        img_str = str(img)
        if "/static/uploads/org/" in img_str:
            return img_str.replace("/static/uploads/org/", "/static/uploads/thumb/")
        if "/uploads/org/" in img_str:
            return img_str.replace("/uploads/org/", "/uploads/thumb/")
        if "/org/" in img_str:
            return img_str.replace("/org/", "/thumb/")
        if not img_str.startswith("/") and not img_str.startswith("http"):
            return f"/static/uploads/thumb/{img_str}"
        return img_str

    def to_dict(self):
        return Product.to_dict_from_doc(self)


class Product:
    @classmethod
    def _col(cls):
        return mongo.db.products

    @classmethod
    def _wrap(cls, doc):
        if not doc:
            return None
        d = ProductDoc(doc)
        d['id'] = str(doc.get('_id', ''))
        d['price'] = float(d.get('price', 0.0) or 0.0)
        d['stock'] = int(d.get('stock', 0) or 0)
        d['org_image'] = d.org_image
        d['thumb_image'] = d.thumb_image
        return d

    @classmethod
    def find_all(cls, status_filter=None):
        query = {}
        if status_filter and status_filter != 'all':
            query['status'] = {'$regex': f'^{status_filter}$', '$options': 'i'}
        docs = list(cls._col().find(query).sort("_id", -1))
        return [cls._wrap(d) for d in docs]

    @classmethod
    def find_by_id(cls, product_id):
        try:
            doc = cls._col().find_one({"_id": ObjectId(str(product_id))})
            return cls._wrap(doc)
        except Exception:
            return None

    @classmethod
    def find_by_category(cls, category_name):
        if not category_name:
            return []
        cat = category_name.strip()
        docs = list(cls._col().find({
            "$or": [
                {"category": {"$regex": f"^{cat}$", "$options": "i"}},
                {"category": {"$regex": cat, "$options": "i"}}
            ]
        }).sort("_id", 1))
        return [cls._wrap(d) for d in docs]

    @classmethod
    def insert(cls, data):
        data.setdefault('posted', date.today().strftime('%Y-%m-%d'))
        data.setdefault('status', 'Approved')
        data.setdefault('rating', '★★★★★')
        result = cls._col().insert_one(data)
        return str(result.inserted_id)

    @classmethod
    def update(cls, product_id, data):
        try:
            cls._col().update_one({"_id": ObjectId(str(product_id))}, {"$set": data})
        except Exception as e:
            print(f"Product update error: {e}")

    @classmethod
    def delete(cls, product_id):
        try:
            cls._col().delete_one({"_id": ObjectId(str(product_id))})
        except Exception as e:
            print(f"Product delete error: {e}")

    @classmethod
    def count(cls, status_filter=None):
        query = {}
        if status_filter:
            query['status'] = {'$regex': f'^{status_filter}$', '$options': 'i'}
        return cls._col().count_documents(query)

    @classmethod
    def to_dict_from_doc(cls, doc):
        w = cls._wrap(doc)
        if not w:
            return {}
        return {
            "id": w['id'],
            "name": w.get('name', ''),
            "category": w.get('category', ''),
            "category_id": w.get('category_id', ''),
            "origin": w.get('origin', ''),
            "farm": w.get('farm', ''),
            "farmer_id": w.get('farmer_id', ''),
            "unit": w.get('unit', '1 kg'),
            "price": float(w.get('price', 0.0)),
            "stock": int(w.get('stock', 0)),
            "badge": w.get('badge', 'Fresh'),
            "description": w.get('description', ''),
            "rating": w.get('rating', '★★★★★'),
            "image": w.get('thumb_image', ''),
            "org_image": w.get('org_image', ''),
            "posted": w.get('posted', ''),
            "status": w.get('status', 'Approved')
        }


PRODUCT = Product
