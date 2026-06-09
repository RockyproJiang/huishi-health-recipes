from flask import Blueprint, request, jsonify, session
from datetime import date, timedelta
from models.database import get_db, login_required

checkin_bp = Blueprint('checkin', __name__)

@checkin_bp.route('/checkin', methods=['POST'])
@login_required
def checkin():
    data = request.json
    user_id = session['user_id']
    check_type = data.get('type')
    detail = data.get('detail', '')
    points_map = {'breakfast':10, 'lunch':10, 'dinner':10, 'water':5, 'exercise':20}
    add_points = points_map.get(check_type, 0)
    today = date.today().isoformat()
    conn = get_db()
    try:
        with conn.cursor() as cur:
            if check_type != 'water':
                cur.execute("SELECT id FROM checkin_log WHERE user_id = %s AND date = %s AND type = %s", (user_id, today, check_type))
                if cur.fetchone():
                    return jsonify({'error': '今天已打卡'}), 400
            cur.execute("INSERT INTO checkin_log (user_id, date, type, detail, points_added) VALUES (%s, %s, %s, %s, %s)",
                        (user_id, today, check_type, detail, add_points))
            cur.execute("UPDATE users SET points = points + %s WHERE id = %s", (add_points, user_id))
            cur.execute("INSERT INTO points_log (user_id, change_amount, reason) VALUES (%s, %s, %s)",
                        (user_id, add_points, f"打卡-{check_type}"))
            conn.commit()
        return jsonify({'success': True, 'points_added': add_points})
    finally:
        conn.close()

@checkin_bp.route('/get_water_count', methods=['GET'])
@login_required
def get_water_count():
    user_id = session['user_id']
    today = date.today().isoformat()
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) as cnt FROM checkin_log WHERE user_id = %s AND date = %s AND type = 'water'", (user_id, today))
            row = cur.fetchone()
            return jsonify({'count': row['cnt'] if row else 0})
    finally:
        conn.close()

@checkin_bp.route('/calendar_data', methods=['GET'])
@login_required
def calendar_data():
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    user_id = session['user_id']
    conn = get_db()
    try:
        with conn.cursor() as cur:
            start_date = date(year, month, 1)
            if month == 12:
                end_date = date(year+1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(year, month+1, 1) - timedelta(days=1)
            cur.execute("SELECT DISTINCT date FROM checkin_log WHERE user_id=%s AND date BETWEEN %s AND %s",
                        (user_id, start_date, end_date))
            days = [row['date'].isoformat() for row in cur.fetchall()]
        return jsonify({'checked_dates': days})
    finally:
        conn.close()

@checkin_bp.route('/toggle_calendar', methods=['POST'])
@login_required
def toggle_calendar():
    data = request.json
    date_str = data.get('date')
    user_id = session['user_id']
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM checkin_log WHERE user_id=%s AND date=%s AND type='calendar'", (user_id, date_str))
            existing = cur.fetchone()
            if existing:
                cur.execute("DELETE FROM checkin_log WHERE id=%s", (existing['id'],))
                action = 'deleted'
            else:
                cur.execute("INSERT INTO checkin_log (user_id, date, type, detail, points_added) VALUES (%s, %s, 'calendar', '手动标记', 0)",
                            (user_id, date_str))
                action = 'added'
            conn.commit()
        return jsonify({'success': True, 'action': action})
    finally:
        conn.close()

@checkin_bp.route('/exchange', methods=['POST'])
@login_required
def exchange():
    data = request.json
    item_name = data.get('item')
    points_map = {'月卡会员':10, '半年会员':50, '健身房次卡':20, '月卡体验卡':100}
    cost = points_map.get(item_name)
    if not cost:
        return jsonify({'error': '商品不存在'}), 400
    user_id = session['user_id']
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT points FROM users WHERE id = %s", (user_id,))
            user = cur.fetchone()
            if user['points'] < cost:
                return jsonify({'error': '积分不足'}), 400
            cur.execute("UPDATE users SET points = points - %s WHERE id = %s", (cost, user_id))
            cur.execute("INSERT INTO orders (user_id, item_name, points_cost) VALUES (%s, %s, %s)", (user_id, item_name, cost))
            cur.execute("INSERT INTO points_log (user_id, change_amount, reason) VALUES (%s, %s, %s)",
                        (user_id, -cost, f"兑换-{item_name}"))
            conn.commit()
        return jsonify({'success': True})
    finally:
        conn.close()

@checkin_bp.route('/get_orders', methods=['GET'])
@login_required
def get_orders():
    user_id = session['user_id']
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT item_name, points_cost, created_at FROM orders WHERE user_id = %s ORDER BY created_at DESC", (user_id,))
            orders = cur.fetchall()
        return jsonify({'orders': orders})
    finally:
        conn.close()

@checkin_bp.route('/get_daily_nutrition', methods=['GET'])
@login_required
def get_daily_nutrition():
    user_id = session['user_id']
    today = date.today().isoformat()
    conn = get_db()
    total_cal = total_protein = total_carbs = 0
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT calories, protein, carbs FROM daily_meals WHERE user_id=%s AND date=%s", (user_id, today))
            meals = cur.fetchall()
            for m in meals:
                total_cal += m['calories']
                total_protein += m['protein']
                total_carbs += m['carbs']
            cur.execute("SELECT SUM(calories) as exercise_cal FROM exercise_log WHERE user_id=%s AND DATE(date)=%s", (user_id, today))
            row = cur.fetchone()
            exercise_cal = float(row['exercise_cal']) if row and row['exercise_cal'] else 0
            cur.execute("SELECT COUNT(*) as cnt FROM checkin_log WHERE user_id=%s AND date=%s AND type='water'", (user_id, today))
            water_cnt = cur.fetchone()['cnt']
        return jsonify({'total_calories': total_cal, 'total_protein': total_protein, 'total_carbs': total_carbs,
                        'exercise_calories': exercise_cal, 'water_cups': water_cnt, 'water_target': 8})
    finally:
        conn.close()

