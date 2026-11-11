from flask import Blueprint, request, jsonify, session
from datetime import date, timedelta
import json
import re
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


MEMBERSHIP_PLANS = {
    'month': {'days': 30, 'price': 30, 'points': 100, 'name': '一个月会员'},
    'quarter': {'days': 90, 'price': 80, 'points': 280, 'name': '季度会员'},
    'half': {'days': 180, 'price': 150, 'points': 500, 'name': '半年会员'},
    'year': {'days': 365, 'price': 280, 'points': 900, 'name': '年度会员'}
}


def _extend_membership(user_id, plan_key):
    plan = MEMBERSHIP_PLANS.get(plan_key)
    if not plan:
        return None
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT membership_expires_at FROM users WHERE id = %s", (user_id,))
            row = cur.fetchone()
            start = date.today()
            if row and row['membership_expires_at'] and row['membership_expires_at'] > start:
                start = row['membership_expires_at']
            expires = start + timedelta(days=plan['days'])
            cur.execute("UPDATE users SET membership_expires_at = %s, membership_plan = %s WHERE id = %s", (expires, plan_key, user_id))
            conn.commit()
            return plan, expires
    finally:
        conn.close()


@checkin_bp.route('/membership/purchase', methods=['POST'])
@login_required
def purchase_membership():
    plan_key = request.json.get('plan')
    result = _extend_membership(session['user_id'], plan_key)
    if not result:
        return jsonify({'error': '无效的会员方案'}), 400
    plan, expires = result
    return jsonify({'success': True, 'plan': plan['name'], 'expires_at': expires.isoformat()})


@checkin_bp.route('/membership/exchange', methods=['POST'])
@login_required
def exchange_membership():
    plan_key = request.json.get('plan')
    plan = MEMBERSHIP_PLANS.get(plan_key)
    if not plan:
        return jsonify({'error': '无效的会员方案'}), 400
    user_id = session['user_id']
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT points FROM users WHERE id = %s", (user_id,))
            user = cur.fetchone()
            if user['points'] < plan['points']:
                return jsonify({'error': '积分不足'}), 400
            cur.execute("UPDATE users SET points = points - %s WHERE id = %s", (plan['points'], user_id))
            cur.execute("INSERT INTO points_log (user_id, change_amount, reason) VALUES (%s, %s, %s)", (user_id, -plan['points'], f"兑换-{plan['name']}"))
            conn.commit()
    finally:
        conn.close()
    result = _extend_membership(user_id, plan_key)
    plan, expires = result
    return jsonify({'success': True, 'plan': plan['name'], 'expires_at': expires.isoformat()})


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

@checkin_bp.route('/checkin_today', methods=['GET'])
@login_required
def checkin_today():
    """今日多维打卡汇总：饮食 / 饮水 / 运动 / 舌诊 + 连续天数。"""
    user_id = session['user_id']
    today = date.today()
    today_str = today.isoformat()
    conn = get_db()
    try:
        with conn.cursor() as cur:
            # 今日三餐与养生菜
            cur.execute("SELECT meal_type FROM daily_meals WHERE user_id=%s AND date=%s", (user_id, today_str))
            meal_types = {r['meal_type'] for r in cur.fetchall()}

            # 饮水
            cur.execute("SELECT COUNT(*) as cnt FROM checkin_log WHERE user_id=%s AND date=%s AND type='water'",
                        (user_id, today_str))
            water_cups = int(cur.fetchone()['cnt'] or 0)

            # 运动
            cur.execute(
                "SELECT COALESCE(SUM(duration_seconds),0) as secs, COALESCE(SUM(calories),0) as cals, COUNT(*) as cnt "
                "FROM exercise_log WHERE user_id=%s AND DATE(date)=%s", (user_id, today_str))
            ex = cur.fetchone()
            exercise_secs = float(ex['secs'] or 0)
            exercise_cals = float(ex['cals'] or 0)
            exercise_cnt = int(ex['cnt'] or 0)

            # 舌诊
            cur.execute("SELECT COUNT(*) as cnt FROM tongue_records WHERE user_id=%s AND DATE(created_at)=%s",
                        (user_id, today_str))
            tongue_today = int(cur.fetchone()['cnt'] or 0)

            # 打卡记录（用于连续天数）
            cur.execute("SELECT DISTINCT date FROM checkin_log WHERE user_id=%s ORDER BY date DESC LIMIT 400",
                        (user_id,))
            dates = {r['date'] for r in cur.fetchall()}

            cur.execute("SELECT points FROM users WHERE id=%s", (user_id,))
            row = cur.fetchone()
            points = int(row['points'] or 0) if row else 0

        meals_done = [m for m in ('breakfast', 'lunch', 'dinner') if m in meal_types]
        health_done = [m for m in meal_types if str(m).startswith('health_')]

        # 连续打卡：今天或昨天有记录则往回数
        streak = 0
        cursor_day = today if today in dates else today - timedelta(days=1)
        while cursor_day in dates:
            streak += 1
            cursor_day -= timedelta(days=1)

        # 当月打卡天数
        month_days = sum(1 for d in dates if d.year == today.year and d.month == today.month)

        tasks = [
            {
                'key': 'meals',
                'label': '三餐',
                'icon': 'fa-utensils',
                'color': '#C96A3F',
                'done': len(meals_done),
                'total': 3,
                'unit': '餐',
                'completed': len(meals_done) >= 3,
                'action': "openDishCategory('breakfast')",
                'action_label': '去选菜',
                'detail': '、'.join({'breakfast': '早', 'lunch': '午', 'dinner': '晚'}[m] for m in meals_done) or '还没选',
            },
            {
                'key': 'water',
                'label': '饮水',
                'icon': 'fa-droplet',
                'color': '#6F9CA8',
                'done': water_cups,
                'total': 8,
                'unit': '杯',
                'completed': water_cups >= 8,
                'action': 'waterCheckin()',
                'action_label': '+1 杯',
                'detail': f'{water_cups * 200} ml / 1600 ml',
            },
            {
                'key': 'exercise',
                'label': '运动',
                'icon': 'fa-person-running',
                'color': '#7C9166',
                'done': round(exercise_secs / 60),
                'total': 30,
                'unit': '分钟',
                'completed': exercise_secs >= 30 * 60,
                'action': "switchToPage('sportPage')",
                'action_label': '去运动',
                'detail': f'{exercise_cnt} 次 · {round(exercise_cals)} kcal' if exercise_cnt else '今天还没动',
            },
            {
                'key': 'tongue',
                'label': '舌诊',
                'icon': 'fa-camera-retro',
                'color': '#A9855F',
                'done': 1 if tongue_today else 0,
                'total': 1,
                'unit': '次',
                'completed': tongue_today > 0,
                'action': 'openTongueModal()',
                'action_label': '拍舌象',
                'detail': f'今天已拍 {tongue_today} 次' if tongue_today else '还没有记录',
            },
        ]
        done_count = sum(1 for t in tasks if t['completed'])

        return jsonify({
            'success': True,
            'date': today_str,
            'tasks': tasks,
            'done_count': done_count,
            'task_total': len(tasks),
            'streak': streak,
            'month_days': month_days,
            'points': points,
            'health_recipes': len(health_done),
        })
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


def _score_ratio(value, target):
    if not target:
        return 0
    return round(max(0, min(100, (float(value) / float(target)) * 100)))


def _ratio_score(value, low, high):
    value = float(value or 0)
    if low <= value <= high:
        return 100
    if value < low:
        return max(0, 100 - ((low - value) / low) * 100)
    return max(0, 100 - ((value - high) / (1 - high)) * 100)


def _activity_factor(exercise_frequency):
    freq = exercise_frequency or ''
    if '几乎' in freq:
        return 1.2
    if '1-2' in freq or '1-2' in freq:
        return 1.375
    if '3-4' in freq:
        return 1.55
    if '5' in freq or '每天' in freq:
        return 1.725
    return 1.2


def _estimate_target_calories(profile, lifestyle):
    if not profile:
        return 2000
    try:
        height = float(profile.get('height') or 0)
        weight = float(profile.get('weight') or 0)
        age = int(profile.get('age') or 0)
    except (TypeError, ValueError):
        return 2000
    if not height or not weight or not age:
        return 2000

    gender = profile.get('gender') or ''
    is_male = gender in ('男', 'male', 'Male', 'M', 'm')
    bmr = 10 * weight + 6.25 * height - 5 * age + (5 if is_male else -161)
    activity = _activity_factor(lifestyle.get('exercise_frequency')) if lifestyle else 1.2
    return round(max(1200, min(3500, bmr * activity)))


def _diet_score(calories, protein, carbs, target_calories=2000):
    calories = float(calories or 0)
    target_calories = float(target_calories or 0)
    if calories <= 0 or target_calories <= 0:
        return 0
    calorie_score = max(0, min(100, 100 - (abs(calories - target_calories) / target_calories) * 100))
    protein_ratio = (float(protein or 0) * 4) / calories
    carbs_ratio = (float(carbs or 0) * 4) / calories
    macro_score = 0.5 * _ratio_score(protein_ratio, 0.15, 0.25) + 0.5 * _ratio_score(carbs_ratio, 0.45, 0.65)
    return round(0.5 * calorie_score + 0.5 * macro_score)


def _tongue_symptom_count(row):
    count = 0
    details = row.get('constitution_details') if isinstance(row, dict) else None
    if isinstance(details, str) and details:
        try:
            details = json.loads(details)
        except (TypeError, ValueError):
            details = None
    if isinstance(details, dict):
        for key in ('symptoms', 'inquiry_questions', 'diagnose_key_words'):
            value = details.get(key)
            if isinstance(value, list) and value:
                count = len(value)
                break
    if not count:
        ctype = (row.get('constitution_type') or '') if isinstance(row, dict) else ''
        if ctype and ctype not in ('舌诊分析', '暂无记录'):
            count = len([part for part in re.split(r'[、,，;；/]', ctype) if part.strip()])
    return count


def _tongue_score(row):
    return max(0, min(100, 80 - 5 * _tongue_symptom_count(row)))


@checkin_bp.route('/get_body_scores', methods=['GET'])
@login_required
def get_body_scores():
    user_id = session['user_id']
    today = date.today()
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT calories, protein, carbs FROM daily_meals WHERE user_id=%s AND date=%s", (user_id, today.isoformat()))
            meals = cur.fetchall()
            total_calories = sum(float(m['calories'] or 0) for m in meals)
            total_protein = sum(float(m['protein'] or 0) for m in meals)
            total_carbs = sum(float(m['carbs'] or 0) for m in meals)

            cur.execute("SELECT COUNT(*) as cnt FROM checkin_log WHERE user_id=%s AND date=%s AND type='water'", (user_id, today.isoformat()))
            water_cups = int(cur.fetchone()['cnt'] or 0)

            cur.execute("SELECT height, weight, age, gender FROM health_profile WHERE user_id=%s", (user_id,))
            profile = cur.fetchone()
            cur.execute("SELECT exercise_frequency FROM lifestyle_info WHERE user_id=%s", (user_id,))
            lifestyle = cur.fetchone()

            start_date = (today - timedelta(days=6)).isoformat()
            cur.execute(
                "SELECT COALESCE(SUM(duration_seconds), 0) as duration_seconds, "
                "COALESCE(SUM(calories), 0) as calories "
                "FROM exercise_log WHERE user_id=%s AND DATE(date) >= %s",
                (user_id, start_date)
            )
            exercise = cur.fetchone()
            exercise_seconds = float(exercise['duration_seconds'] or 0)
            exercise_calories = float(exercise['calories'] or 0)

            cur.execute(
                "SELECT constitution_type, constitution_details FROM tongue_records "
                "WHERE user_id=%s ORDER BY created_at ASC, id ASC",
                (user_id,)
            )
            tongue_rows = cur.fetchall()

        water_ml = water_cups * 200
        water_target_ml = 1600
        water_score = _score_ratio(water_ml, water_target_ml)
        target_calories = _estimate_target_calories(profile, lifestyle)
        diet_score = _diet_score(total_calories, total_protein, total_carbs, target_calories)
        exercise_minutes = round(exercise_seconds / 60)
        exercise_score = round(0.6 * _score_ratio(exercise_minutes, 150) + 0.4 * _score_ratio(exercise_calories, 2000))

        physique_has_data = bool(tongue_rows)
        if physique_has_data:
            first_row = tongue_rows[0]
            last_row = tongue_rows[-1]
            first_type = first_row['constitution_type'] or '舌诊分析'
            last_type = last_row['constitution_type'] or '舌诊分析'
            first_score = 50
            last_score = 80
        else:
            first_type = '暂无记录'
            last_type = '暂无记录'
            first_score = 50
            last_score = 80

        return jsonify({
            'water': {
                'score': water_score,
                'value_ml': water_ml,
                'target_ml': water_target_ml
            },
            'diet': {
                'score': diet_score,
                'optimal_score': 100,
                'calories': round(total_calories),
                'protein': round(total_protein, 1),
                'carbs': round(total_carbs, 1),
                'target_calories': target_calories,
                'target_protein': round(target_calories * 0.20 / 4, 1),
                'target_carbs': round(target_calories * 0.55 / 4, 1)
            },
            'exercise': {
                'score': exercise_score,
                'days': 7
            },
            'physique': {
                'has_data': physique_has_data,
                'first_score': first_score,
                'last_score': last_score,
                'delta': last_score - first_score,
                'first_type': first_type,
                'last_type': last_type
            }
        })
    finally:
        conn.close()

