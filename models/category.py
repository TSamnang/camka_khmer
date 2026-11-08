from bson import ObjectId
from extension import mongo


class CategoryDoc(dict):
    def __getattr__(self, key):
        return self.get(key)

    def __setattr__(self, key, value):
        self[key] = value

    @property
    def org_image(self):
        img = self.get('image')
        if not img:
            return "/static/images/vegetable.jpg"
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
            return "/static/images/vegetable.jpg"
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


class Category:
    @classmethod
    def _col(cls):
        return mongo.db.categories

    @classmethod
    def _wrap(cls, doc):
        if not doc:
            return None
        d = CategoryDoc(doc)
        cid = str(doc.get('_id', ''))
        d['id'] = cid

        # Compute dynamic image properties
        d['org_image'] = d.org_image
        d['thumb_image'] = d.thumb_image

        cat_name = d.get('name', '')
        try:
            d['product_count'] = mongo.db.products.count_documents({
                "$or": [
                    {"category_id": cid},
                    {"category": {"$regex": f"^{cat_name}$", "$options": "i"}}
                ]
            })
        except Exception:
            d['product_count'] = d.get('product_count', 0)
        return d

    @classmethod
    def find_all(cls):
        docs = list(cls._col().find().sort("_id", 1))
        return [cls._wrap(d) for d in docs]

    @classmethod
    def find_by_id(cls, category_id):
        try:
            doc = cls._col().find_one({"_id": ObjectId(str(category_id))})
            return cls._wrap(doc)
        except Exception:
            return None

    @classmethod
    def insert(cls, data):
        result = cls._col().insert_one(data)
        return str(result.inserted_id)

    @classmethod
    def update(cls, category_id, data):
        try:
            cls._col().update_one({"_id": ObjectId(str(category_id))}, {"$set": data})
        except Exception as e:
            print(f"Category update error: {e}")

    @classmethod
    def delete(cls, category_id):
        try:
            cls._col().delete_one({"_id": ObjectId(str(category_id))})
        except Exception as e:
            print(f"Category delete error: {e}")

    @classmethod
    def to_dict_from_doc(cls, doc):
        if not doc:
            return {}
        w = cls._wrap(doc)
        return {
            "id": w['id'],
            "name": w.get('name', ''),
            "description": w.get('description', ''),
            "image": w.get('image', ''),
            "org_image": w.get('org_image', ''),
            "thumb_image": w.get('thumb_image', ''),
            "product_count": w.get('product_count', 0)
        }


CATEGORY = Category
