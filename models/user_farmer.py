from bson import ObjectId
from extension import mongo


class FarmerDoc(dict):
    def __getattr__(self, key):
        return self.get(key)

    def __setattr__(self, key, value):
        self[key] = value


class USER_FARMER:
    @classmethod
    def _col(cls):
        return mongo.db.farmers

    @classmethod
    def _wrap(cls, doc):
        if not doc:
            return None
        d = FarmerDoc(doc)
        d['id'] = str(doc.get('_id', ''))
        return d

    @classmethod
    def find_all(cls):
        docs = list(cls._col().find())
        return [cls._wrap(d) for d in docs]

    @classmethod
    def find_by_id(cls, farmer_id):
        try:
            doc = cls._col().find_one({"_id": ObjectId(str(farmer_id))})
            return cls._wrap(doc)
        except Exception:
            return None

    @classmethod
    def find_by_name(cls, farmer_name):
        doc = cls._col().find_one({"farmer_name": farmer_name})
        return cls._wrap(doc)

    @classmethod
    def insert(cls, data):
        result = cls._col().insert_one(data)
        return str(result.inserted_id)

    @classmethod
    def update(cls, farmer_id, data):
        try:
            cls._col().update_one({"_id": ObjectId(str(farmer_id))}, {"$set": data})
        except Exception as e:
            print(f"Farmer update error: {e}")

    @classmethod
    def delete(cls, farmer_id):
        try:
            cls._col().delete_one({"_id": ObjectId(str(farmer_id))})
        except Exception as e:
            print(f"Farmer delete error: {e}")

    @classmethod
    def count(cls):
        return cls._col().count_documents({})
