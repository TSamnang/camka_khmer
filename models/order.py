from datetime import datetime
from extension import db


class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    customer_name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    address = db.Column(db.Text, nullable=False)
    customer_id = db.Column(db.Integer, nullable=True)

    subtotal = db.Column(db.Float, default=0.0, nullable=False)
    delivery = db.Column(db.Float, default=0.0, nullable=False)
    total = db.Column(db.Float, default=0.0, nullable=False)

    payment_status = db.Column(db.String(50), default="Pending", nullable=False)
    status = db.Column(db.String(50), default="Pending", nullable=False)

    md5 = db.Column(db.String(64), nullable=True)
    qr_data = db.Column(db.Text, nullable=True)
    qr_image = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    items = db.relationship('OrderItem', backref='order', cascade='all, delete-orphan', lazy=True)

    @property
    def item_count(self):
        return sum(item.quantity for item in self.items)

    def to_dict(self):
        return {
            "id": self.id,
            "order_number": self.order_number,
            "customer_name": self.customer_name,
            "phone": self.phone,
            "email": self.email or "",
            "address": self.address,
            "customer_id": self.customer_id,
            "subtotal": round(float(self.subtotal), 2),
            "delivery": round(float(self.delivery), 2),
            "total": round(float(self.total), 2),
            "payment_status": self.payment_status,
            "status": self.status,
            "md5": self.md5 or "",
            "qr_image": self.qr_image or "",
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else "",
            "item_count": self.item_count,
            "items": [item.to_dict() for item in self.items]
        }

    def __repr__(self):
        return f"<Order id={self.id} number='{self.order_number}' status='{self.status}'>"


class OrderItem(db.Model):
    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, nullable=True)
    product_name = db.Column(db.String(120), nullable=False)
    product_image = db.Column(db.String(255), nullable=True)
    unit = db.Column(db.String(50), nullable=True, default="1 kg")
    price = db.Column(db.Float, default=0.0, nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    line_total = db.Column(db.Float, default=0.0, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "order_id": self.order_id,
            "product_id": self.product_id,
            "product_name": self.product_name,
            "product_image": self.product_image or "/static/images/bread.jpg",
            "unit": self.unit or "",
            "price": round(float(self.price), 2),
            "quantity": self.quantity,
            "line_total": round(float(self.line_total), 2)
        }

    def __repr__(self):
        return f"<OrderItem id={self.id} order_id={self.order_id} product='{self.product_name}' qty={self.quantity}>"


ORDER = Order
ORDER_ITEM = OrderItem

