from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session, current_app
from app import db
from app.models import Category, Dish, Order, OrderItem, Review, Table
from app.utils import process_upload_image
from datetime import datetime, date, timedelta
from sqlalchemy import func
import os

admin_bp = Blueprint('admin', __name__)


def admin_required(f):
    """简易管理员验证装饰器"""
    from functools import wraps

    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated


@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        pwd = request.form.get('password', '')
        if pwd == current_app.config['ADMIN_PASSWORD']:
            session['admin_logged_in'] = True
            return redirect(url_for('admin.dashboard'))
        return render_template('admin/login.html', error='密码错误')
    return render_template('admin/login.html')


@admin_bp.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin.login'))


# ─── 仪表盘 ───
@admin_bp.route('/')
@admin_required
def dashboard():
    return render_template('admin/dashboard.html')


@admin_bp.route('/api/stats')
@admin_required
def api_stats():
    """今日统计数据"""
    today_start = datetime.combine(date.today(), datetime.min.time())

    today_revenue = db.session.query(func.sum(Order.total_amount)).filter(
        Order.created_at >= today_start, Order.status == 'Paid'
    ).scalar() or 0.0

    today_orders = Order.query.filter(Order.created_at >= today_start).count()
    pending_orders = Order.query.filter(
        Order.status.in_(['Pending', 'Cooking'])).count()

    return jsonify({
        'today_revenue': round(today_revenue, 2),
        'today_orders': today_orders,
        'pending_orders': pending_orders,
    })


@admin_bp.route('/api/revenue_trend')
@admin_required
def api_revenue_trend():
    """近7天收入趋势"""
    days = []
    for i in range(6, -1, -1):
        d = date.today() - timedelta(days=i)
        start = datetime.combine(d, datetime.min.time())
        end = datetime.combine(d, datetime.max.time())
        rev = db.session.query(func.sum(Order.total_amount)).filter(
            Order.created_at >= start, Order.created_at <= end, Order.status == 'Paid'
        ).scalar() or 0.0
        days.append({'date': d.strftime('%m/%d'), 'revenue': round(rev, 2)})
    return jsonify(days)


# ─── 订单管理 ───
@admin_bp.route('/api/orders')
@admin_required
def api_orders():
    status_filter = request.args.get('status', 'active')
    if status_filter == 'active':
        orders = Order.query.filter(Order.status.in_(['Pending', 'Cooking', 'Served'])) \
            .order_by(Order.created_at.desc()).all()
    elif status_filter == 'all':
        orders = Order.query.order_by(Order.created_at.desc()).limit(100).all()
    else:
        orders = Order.query.filter_by(status=status_filter) \
            .order_by(Order.created_at.desc()).limit(50).all()
    return jsonify([o.to_dict() for o in orders])


@admin_bp.route('/api/orders/<int:order_id>/status', methods=['PUT'])
@admin_required
def update_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    data = request.get_json()
    new_status = data.get('status')
    if new_status in ('Pending', 'Cooking', 'Served', 'Paid', 'Cancelled'):
        order.status = new_status
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'error': '无效状态'}), 400


@admin_bp.route('/orders')
@admin_required
def orders_page():
    return render_template('admin/orders.html')


# ─── 菜品管理 CRUD ───
@admin_bp.route('/dishes')
@admin_required
def dishes_page():
    categories = Category.query.order_by(Category.sort_order).all()
    dishes = Dish.query.order_by(Dish.category_id, Dish.id).all()
    return render_template('admin/dishes.html', categories=categories, dishes=dishes)


@admin_bp.route('/api/categories', methods=['GET', 'POST'])
@admin_required
def api_categories():
    if request.method == 'POST':
        data = request.get_json()
        cat = Category(name=data['name'], sort_order=data.get('sort_order', 0))
        db.session.add(cat)
        db.session.commit()
        return jsonify(cat.to_dict())
    cats = Category.query.order_by(Category.sort_order).all()
    return jsonify([c.to_dict() for c in cats])


@admin_bp.route('/api/categories/<int:cat_id>', methods=['DELETE'])
@admin_required
def delete_category(cat_id):
    cat = Category.query.get_or_404(cat_id)
    # 将该分类下的菜品设为未分类
    Dish.query.filter_by(category_id=cat_id).update({'category_id': None})
    db.session.delete(cat)
    db.session.commit()
    return jsonify({'success': True})


@admin_bp.route('/api/dishes', methods=['POST'])
@admin_required
def add_dish():
    name = request.form.get('name')
    price = float(request.form.get('price', 0))
    category_id = request.form.get('category_id') or None
    description = request.form.get('description', '')

    image_file = request.files.get('image')
    image_path = ''
    if image_file:
        image_path = process_upload_image(
            image_file, current_app.config['UPLOAD_FOLDER'])

    dish = Dish(
        name=name, price=price,
        category_id=int(category_id) if category_id else None,
        description=description,
        image_path=image_path,
        is_available=True
    )
    db.session.add(dish)
    db.session.commit()
    return jsonify(dish.to_dict())


@admin_bp.route('/api/dishes/<int:dish_id>', methods=['PUT'])
@admin_required
def update_dish(dish_id):
    dish = Dish.query.get_or_404(dish_id)
    dish.name = request.form.get('name', dish.name)
    dish.price = float(request.form.get('price', dish.price))
    dish.description = request.form.get('description', dish.description)
    cat_id = request.form.get('category_id')
    if cat_id is not None:
        dish.category_id = int(cat_id) if cat_id else None
    dish.is_available = request.form.get('is_available', 'true') == 'true'

    image_file = request.files.get('image')
    if image_file and image_file.filename:
        # 删除旧图
        if dish.image_path:
            old_path = os.path.join(
                current_app.config['UPLOAD_FOLDER'], dish.image_path)
            if os.path.exists(old_path):
                os.remove(old_path)
        dish.image_path = process_upload_image(
            image_file, current_app.config['UPLOAD_FOLDER'])

    db.session.commit()
    return jsonify(dish.to_dict())


@admin_bp.route('/api/dishes/<int:dish_id>', methods=['DELETE'])
@admin_required
def delete_dish(dish_id):
    dish = Dish.query.get_or_404(dish_id)
    if dish.image_path:
        img_path = os.path.join(
            current_app.config['UPLOAD_FOLDER'], dish.image_path)
        if os.path.exists(img_path):
            os.remove(img_path)
    db.session.delete(dish)
    db.session.commit()
    return jsonify({'success': True})


# ─── 评价管理 ───
@admin_bp.route('/reviews')
@admin_required
def reviews_page():
    reviews = Review.query.order_by(Review.created_at.desc()).all()
    return render_template('admin/reviews.html', reviews=reviews)


# ─── 桌台管理界面 ───
@admin_bp.route('/tables')
@admin_required
def tables_page():
    """这是浏览器访问的页面地址：http://localhost:5000/admin/tables"""
    # 只需要返回模板，数据由下面的 GET API 异步加载
    return render_template('admin/tables.html')

# ─── 桌台管理 API (供前端 JS 调用) ───

@admin_bp.route('/api/tables', methods=['GET'])
@admin_required
def get_tables_api():
    """获取桌台列表"""
    tables = Table.query.order_by(Table.id).all()
    return jsonify([t.to_dict() for t in tables])

@admin_bp.route('/api/tables', methods=['POST'])
@admin_required
def add_table():
    """添加新桌台"""
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({'error': '名称不能为空'}), 400
    t = Table(name=data['name'], qr_code_str=data.get('qr_code_str', ''))
    db.session.add(t)
    db.session.commit()
    return jsonify(t.to_dict())

@admin_bp.route('/api/tables/<int:table_id>', methods=['DELETE'])
@admin_required
def delete_table(table_id):
    """删除桌台"""
    t = Table.query.get_or_404(table_id)
    db.session.delete(t)
    db.session.commit()
    return jsonify({'success': True})

@admin_bp.route('/api/tables/<int:table_id>', methods=['PUT'])
@admin_required
def update_table(table_id):
    """修改桌台信息"""
    t = Table.query.get_or_404(table_id)
    data = request.get_json()
    if 'name' in data:
        t.name = data['name']
    if 'qr_code_str' in data:
        t.qr_code_str = data['qr_code_str']
    db.session.commit()
    return jsonify(t.to_dict())