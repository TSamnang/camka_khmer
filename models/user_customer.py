from bson import ObjectId
from extension import mongo


class CustomerDoc(dict):
    def __getattr__(self, key):
        return self.get(key)

    def __setattr__(self, key, value):
        self[key] = value


class USER_CUSTOMER:
    @classmethod
    def _col(cls):
        return mongo.db.customers

    @classmethod
    def _wrap(cls, doc):
        if not doc:
            return None
        d = CustomerDoc(doc)
        d['id'] = str(doc.get('_id', ''))
        return d

    @classmethod
    def find_all(cls):
        docs = list(cls._col().find())
        return [cls._wrap(d) for d in docs]

    @classmethod
    def find_by_id(cls, customer_id):
        try:
            doc = cls._col().find_one({"_id": ObjectId(str(customer_id))})
            return cls._wrap(doc)
        except Exception:
            return None

    @classmethod
    def find_by_email(cls, email):
        if not email:
            return None
        doc = cls._col().find_one({"customer_email": {"$regex": f"^{email.strip()}$", "$options": "i"}})
        return cls._wrap(doc)

    @classmethod
    def find_by_phone(cls, phone):
        if not phone:
            return None
        doc = cls._col().find_one({"phoneNumber": phone.strip()})
        return cls._wrap(doc)

    @classmethod
    def insert(cls, data):
        result = cls._col().insert_one(data)
        return str(result.inserted_id)

    @classmethod
    def update(cls, customer_id, data):
        try:
            cls._col().update_one({"_id": ObjectId(str(customer_id))}, {"$set": data})
        except Exception as e:
            print(f"Customer update error: {e}")

    @classmethod
    def delete(cls, customer_id):
        try:
            cls._col().delete_one({"_id": ObjectId(str(customer_id))})
        except Exception as e:
            print(f"Customer delete error: {e}")

    @classmethod
    def count(cls):
        return cls._col().count_documents({})
