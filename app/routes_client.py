from flask import Blueprint, render_template, request, jsonify, session
from app import db
from app.models import Category, Dish, Order, OrderItem, Review, Table
from datetime import datetime

client_bp = Blueprint('client', __name__)


@client_bp.route('/')
def index():
    table_id = request.args.get('table', None)
    if table_id:
        session['table_id'] = int(table_id)
    return render_template('client/menu.html', table_id=session.get('table_id'))


@client_bp.route('/api/menu')
def api_menu():
    """返回完整菜单数据（分类+菜品）"""
    categories = Category.query.order_by(Category.sort_order).all()
    result = []
    for cat in categories:
        dishes = Dish.query.filter_by(category_id=cat.id, is_available=True).all()
        result.append({
            'id': cat.id,
            'name': cat.name,
            'dishes': [d.to_dict() for d in dishes]
        })
    return jsonify(result)


@client_bp.route('/api/orders', methods=['POST'])
def create_order():
    """顾客提交订单"""
    data = request.get_json()
    if not data or 'items' not in data:
        return jsonify({'error': '订单数据无效'}), 400

    items_data = data['items']  # [{dish_id, quantity}, ...]
    note = data.get('note', '')
    table_id = data.get('table_id') or session.get('table_id')

    if not items_data:
        return jsonify({'error': '购物车为空'}), 400

    try:
        order = Order(
            table_id=table_id,
            status='Pending',
            customer_note=note,
            created_at=datetime.now()
        )
        db.session.add(order)
        db.session.flush()  # 获取 order.id

        total = 0.0
        for item in items_data:
            dish = Dish.query.get(item['dish_id'])
            if not dish or not dish.is_available:
                continue
            qty = int(item['quantity'])
            oi = OrderItem(
                order_id=order.id,
                dish_id=dish.id,
                quantity=qty,
                price_snapshot=dish.price
            )
            db.session.add(oi)
            total += dish.price * qty
            dish.sales_count += qty

        order.total_amount = round(total, 2)
        db.session.commit()
        return jsonify({'success': True, 'order_id': order.id, 'total': order.total_amount})

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@client_bp.route('/api/reviews', methods=['POST'])
def submit_review():
    """提交评价"""
    data = request.get_json()
    review = Review(
        order_id=data.get('order_id'),
        rating=int(data.get('rating', 5)),
        comment=data.get('comment', ''),
        created_at=datetime.now()
    )
    db.session.add(review)
    db.session.commit()
    return jsonify({'success': True})


@client_bp.route('/order/<int:order_id>')
def order_status(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template('client/order_status.html', order=order)
