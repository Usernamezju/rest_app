from app import db
from datetime import datetime


class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    sort_order = db.Column(db.Integer, default=0)
    dishes = db.relationship('Dish', backref='category', lazy=True)

    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'sort_order': self.sort_order}


class Dish(db.Model):
    __tablename__ = 'dishes'
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, default='')
    image_path = db.Column(db.String(200), default='')
    is_available = db.Column(db.Boolean, default=True)
    sales_count = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            'id': self.id,
            'category_id': self.category_id,
            'name': self.name,
            'price': self.price,
            'description': self.description,
            'image_path': self.image_path,
            'is_available': self.is_available,
            'sales_count': self.sales_count,
        }


class Table(db.Model):
    __tablename__ = 'tables'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    qr_code_str = db.Column(db.String(100), default='')
    orders = db.relationship('Order', backref='table', lazy=True)

    # --- 新增这个方法 ---
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'qr_code_str': self.qr_code_str
        }


class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    table_id = db.Column(db.Integer, db.ForeignKey('tables.id'), nullable=True)
    total_amount = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='Pending')  # Pending/Cooking/Served/Paid/Cancelled
    created_at = db.Column(db.DateTime, default=datetime.now)
    customer_note = db.Column(db.Text, default='')
    items = db.relationship('OrderItem', backref='order', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'table_id': self.table_id,
            'table_name': self.table.name if self.table else '未知',
            'total_amount': self.total_amount,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'customer_note': self.customer_note,
            'items': [item.to_dict() for item in self.items],
        }


class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    dish_id = db.Column(db.Integer, db.ForeignKey('dishes.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    price_snapshot = db.Column(db.Float, nullable=False)  # 下单时价格快照
    dish = db.relationship('Dish', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'dish_name': self.dish.name if self.dish else '已删除',
            'quantity': self.quantity,
            'price_snapshot': self.price_snapshot,
            'subtotal': self.quantity * self.price_snapshot,
        }


class Review(db.Model):
    __tablename__ = 'reviews'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True)
    rating = db.Column(db.Integer, default=5)
    comment = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.now)

    # --- 也建议为 Review 新增这个方法，防止评价页面报错 ---
    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'rating': self.rating,
            'comment': self.comment,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
