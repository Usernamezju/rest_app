"""
数据库初始化脚本 - 创建表并填充测试数据
首次运行: python init_db.py
"""
from app import create_app, db
from app.models import Category, Dish, Table, Order, OrderItem, Review
from datetime import datetime, timedelta
import random

app = create_app()

with app.app_context():
    db.create_all()
    print("✅ 数据库表创建成功！")

    # 检查是否已有数据
    if Category.query.first():
        print("⚠️  数据库已有数据，跳过初始化。如需重置，请删除 instance/guoqing.db 后重新运行。")
    else:
        # ── 创建分类 ──
        cats = [
            Category(name='招牌菜', sort_order=1),
            Category(name='特色蒸菜', sort_order=2),
            Category(name='家常炒菜', sort_order=3),
            Category(name='凉菜', sort_order=4),
            Category(name='汤类', sort_order=5),
            Category(name='主食', sort_order=6),
            Category(name='饮品', sort_order=7),
        ]
        db.session.add_all(cats)
        db.session.flush()

        # ── 创建菜品 ──
        dishes_data = [
            # 招牌菜
            (cats[0].id, '招牌红烧肉', 48.0, '精选五花肉，慢炖入味，肥而不腻'),
            (cats[0].id, '国庆秘制鱼头', 58.0, '鲜活大鱼头，秘制酱料，鲜香浓郁'),
            (cats[0].id, '干锅牛蛙', 52.0, '新鲜牛蛙，麻辣鲜香'),
            (cats[0].id, '铁板黑椒牛肉', 56.0, '澳洲牛肉，黑椒酱汁，嫩滑多汁'),
            # 特色蒸菜
            (cats[1].id, '新沟粉蒸肉', 38.0, '监利特色，米粉裹肉，入口即化'),
            (cats[1].id, '粉蒸排骨', 42.0, '精选肋排，蒸制软烂'),
            (cats[1].id, '清蒸鲈鱼', 55.0, '鲜活鲈鱼，清蒸原味'),
            # 家常炒菜
            (cats[2].id, '农家小炒肉', 32.0, '辣椒炒肉，家常味道'),
            (cats[2].id, '蒜薹炒腊肉', 35.0, '监利土腊肉，蒜薹清脆'),
            (cats[2].id, '番茄炒蛋', 18.0, '经典家常，酸甜可口'),
            (cats[2].id, '麻婆豆腐', 22.0, '麻辣鲜香，下饭神器'),
            (cats[2].id, '酸辣土豆丝', 16.0, '脆嫩爽口'),
            # 凉菜
            (cats[3].id, '凉拌黄瓜', 12.0, '清脆爽口，开胃首选'),
            (cats[3].id, '皮蛋豆腐', 15.0, '清凉爽滑'),
            (cats[3].id, '口水鸡', 28.0, '麻辣鲜香，口感嫩滑'),
            # 汤类
            (cats[4].id, '番茄蛋花汤', 15.0, '酸甜鲜美'),
            (cats[4].id, '排骨莲藕汤', 38.0, '湖北名汤，莲藕粉糯'),
            (cats[4].id, '鱼头豆腐汤', 35.0, '奶白浓汤，鲜美营养'),
            # 主食
            (cats[5].id, '米饭', 3.0, '优质大米'),
            (cats[5].id, '蛋炒饭', 15.0, '粒粒分明'),
            (cats[5].id, '手工面', 12.0, '现做手擀面'),
            # 饮品
            (cats[6].id, '可乐/雪碧', 5.0, '冰镇碳酸饮料'),
            (cats[6].id, '王老吉', 6.0, '凉茶饮品'),
            (cats[6].id, '矿泉水', 3.0, '纯净水'),
        ]
        for cat_id, name, price, desc in dishes_data:
            dish = Dish(category_id=cat_id, name=name, price=price, description=desc,
                        is_available=True, sales_count=random.randint(10, 200))
            db.session.add(dish)

        # ── 创建桌台 ──
        for i in range(1, 11):
            db.session.add(Table(name=f'{i}号桌', qr_code_str=f'table={i}'))
        db.session.add(Table(name='包间A', qr_code_str='table=11'))
        db.session.add(Table(name='包间B', qr_code_str='table=12'))

        # ── 创建模拟历史订单（近7天）──
        db.session.flush()
        all_dishes = Dish.query.all()
        statuses = ['Paid']
        for day_offset in range(7):
            d = datetime.now() - timedelta(days=day_offset)
            num_orders = random.randint(8, 25)
            for _ in range(num_orders):
                order = Order(
                    table_id=random.randint(1, 10),
                    status='Paid',
                    created_at=d.replace(hour=random.randint(10, 21), minute=random.randint(0, 59)),
                    customer_note=''
                )
                db.session.add(order)
                db.session.flush()
                total = 0
                for dish in random.sample(all_dishes, k=random.randint(2, 5)):
                    qty = random.randint(1, 3)
                    oi = OrderItem(order_id=order.id, dish_id=dish.id, quantity=qty, price_snapshot=dish.price)
                    db.session.add(oi)
                    total += dish.price * qty
                order.total_amount = round(total, 2)

        # ── 创建模拟评价 ──
        comments = ['味道很棒，下次还来！', '分量足，实惠。', '服务态度好👍', '粉蒸肉一绝！', '环境可以再好点', '等了太久了']
        for i in range(10):
            r = Review(
                order_id=random.randint(1, 20),
                rating=random.choice([4, 4, 5, 5, 5, 3, 2]),
                comment=random.choice(comments),
                created_at=datetime.now() - timedelta(days=random.randint(0, 7))
            )
            db.session.add(r)

        db.session.commit()
        print("✅ 测试数据填充完成！")
        print(f"   - {len(cats)} 个分类")
        print(f"   - {len(dishes_data)} 个菜品")
        print(f"   - 12 个桌台")
        print(f"   - 多条历史订单和评价")

    print("\n🚀 启动命令: python run.py")
    print("   顾客端: http://localhost:5000/?table=1")
    print("   管理后台: http://localhost:5000/admin (密码: guoqing888)")
