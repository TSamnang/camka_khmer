import os
import sqlite3
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
mongo_uri = os.getenv("MONGO_URI")
if not mongo_uri:
    print("No MONGO_URI found in .env")
    exit(1)

client = MongoClient(mongo_uri)
db = client.get_default_database()
if db is None or db.name == 'admin':
    db = client['camkakhmer']

print(f"Connecting to MongoDB database: {db.name}")

sqlite_path = 'instance/mydb.sqlite3'
if not os.path.exists(sqlite_path):
    print(f"SQLite file not found at {sqlite_path}")
    exit(1)

conn = sqlite3.connect(sqlite_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# 1. Migrate farmers
cur.execute("SELECT * FROM user_farmer")
farmers = [dict(r) for r in cur.fetchall()]
if farmers and db.farmers.count_documents({}) == 0:
    for f in farmers:
        f.pop('id', None)
    db.farmers.insert_many(farmers)
    print(f"Migrated {len(farmers)} farmers.")
else:
    print(f"Farmers: {db.farmers.count_documents({})} in MongoDB.")

# 2. Migrate customers
cur.execute("SELECT * FROM user_customer")
customers = [dict(r) for r in cur.fetchall()]
if customers and db.customers.count_documents({}) == 0:
    for c in customers:
        c.pop('id', None)
    db.customers.insert_many(customers)
    print(f"Migrated {len(customers)} customers.")
else:
    print(f"Customers: {db.customers.count_documents({})} in MongoDB.")

# 3. Migrate categories
cur.execute("SELECT * FROM category")
categories = [dict(r) for r in cur.fetchall()]
cat_id_map = {}
if categories and db.categories.count_documents({}) == 0:
    for c in categories:
        old_id = c.pop('id')
        res = db.categories.insert_one(c)
        cat_id_map[old_id] = str(res.inserted_id)
    print(f"Migrated {len(categories)} categories.")
else:
    print(f"Categories: {db.categories.count_documents({})} in MongoDB.")

# 4. Migrate products
cur.execute("SELECT * FROM product")
products = [dict(r) for r in cur.fetchall()]
prod_id_map = {}
if products and db.products.count_documents({}) == 0:
    for p in products:
        old_id = p.pop('id')
        old_cid = p.get('category_id')
        if old_cid in cat_id_map:
            p['category_id'] = cat_id_map[old_cid]
        res = db.products.insert_one(p)
        prod_id_map[old_id] = str(res.inserted_id)
    print(f"Migrated {len(products)} products.")
else:
    print(f"Products: {db.products.count_documents({})} in MongoDB.")

# 5. Migrate orders (with embedded items) and order_items collection
cur.execute("SELECT * FROM orders")
orders = [dict(r) for r in cur.fetchall()]
cur.execute("SELECT * FROM order_items")
items = [dict(r) for r in cur.fetchall()]

if orders and db.orders.count_documents({}) == 0:
    for o in orders:
        old_oid = o.pop('id')
        cat_str = o.get('created_at')
        if cat_str and isinstance(cat_str, str):
            try:
                o['created_at'] = datetime.strptime(cat_str[:19], '%Y-%m-%d %H:%M:%S')
            except Exception:
                o['created_at'] = datetime.utcnow()
        else:
            o['created_at'] = datetime.utcnow()

        order_items = []
        for i in items:
            if i.get('order_id') == old_oid:
                i_copy = dict(i)
                i_copy.pop('id', None)
                i_copy.pop('order_id', None)
                order_items.append(i_copy)
        o['items'] = order_items

        db.orders.insert_one(o)
    print(f"Migrated {len(orders)} orders with embedded items.")
else:
    print(f"Orders: {db.orders.count_documents({})} in MongoDB.")

# Standalone order_items collection
if items and db.order_items.count_documents({}) == 0:
    for it in items:
        it.pop('id', None)
    db.order_items.insert_many(items)
    print(f"Migrated {len(items)} order_items.")
else:
    print(f"Order Items: {db.order_items.count_documents({})} in MongoDB.")

# 6. Migrate error_log
cur.execute("SELECT * FROM error_log")
error_logs = [dict(r) for r in cur.fetchall()]
if error_logs and db.error_logs.count_documents({}) == 0:
    for e in error_logs:
        e.pop('id', None)
        if 'telegram_sent' in e:
            e['telegram_sent'] = bool(e['telegram_sent'])
    db.error_logs.insert_many(error_logs)
    print(f"Migrated {len(error_logs)} error logs.")
else:
    print(f"Error logs: {db.error_logs.count_documents({})} in MongoDB.")

conn.close()
print("Migration completed successfully!")
