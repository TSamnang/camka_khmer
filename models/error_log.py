from extension import mongo
from datetime import datetime


class ErrorLogDoc(dict):
    def __getattr__(self, key):
        return self.get(key)

    def __setattr__(self, key, value):
        self[key] = value


class ErrorLog:
    @classmethod
    def _col(cls):
        return mongo.db.error_logs

    @classmethod
    def _wrap(cls, doc):
        if not doc:
            return None
        d = ErrorLogDoc(doc)
        d['id'] = str(doc.get('_id', ''))
        return d

    @classmethod
    def insert(cls, data):
        data.setdefault('created_at', datetime.now())
        result = cls._col().insert_one(data)
        return str(result.inserted_id)

    @classmethod
    def find_all(cls):
        docs = list(cls._col().find().sort("created_at", -1))
        return [cls._wrap(d) for d in docs]


ERROR_LOG = ErrorLog
