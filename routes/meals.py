from flask import Blueprint, request, jsonify, session
from datetime import date
from models.database import get_db, login_required
from data.breakfast import BREAKFAST_FOODS
from data.lunch import LUNCH_FOODS
from data.dinner import DINNER_FOODS
from data.categories import CATEGORIES

meals_bp = Blueprint('meals', __name__)

@meals_bp.route('/foods', methods=['GET'])
@login_required
def get_foods():
    return jsonify({
        'breakfast': BREAKFAST_FOODS,
        'lunch': LUNCH_FOODS,
        'dinner': DINNER_FOODS,
        'categories': CATEGORIES
    })

# 保存早午晚餐 (保持原有接口不变)
@meals_bp.route('/save_meals', methods=['POST'])
@login_required
def save_meals():
    data = request.json
    user_id = session['user_id']
    today = date.today().isoformat()
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM daily_meals WHERE user_id = %s AND date = %s", (user_id, today))
            for meal_type in ['breakfast', 'lunch', 'dinner']:
                meal = data.get(meal_type)
                if meal:
                    cur.execute("INSERT INTO daily_meals (user_id, date, meal_type, food_name, calories, price, protein, carbs) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                                (user_id, today, meal_type, meal['name'], meal['calories'], meal['price'], meal.get('protein', 0), meal.get('carbs', 0)))
            conn.commit()
        return jsonify({'success': True})
    finally:
        conn.close()

# 新增：保存单条餐食（用于养生食谱）
@meals_bp.route('/save_meal', methods=['POST'])
@login_required
def save_meal():
    data = request.json
    user_id = session['user_id']
    today = date.today().isoformat()
    meal_type = data.get('meal_type')
    food_name = data.get('food_name')
    calories = data.get('calories', 0)
    price = data.get('price', 0)
    protein = data.get('protein', 0)
    carbs = data.get('carbs', 0)
    conn = get_db()
    try:
        with conn.cursor() as cur:
            # 删除该用户当天同类型的餐食记录，确保一种类型只保留一条
            cur.execute("DELETE FROM daily_meals WHERE user_id = %s AND date = %s AND meal_type = %s", (user_id, today, meal_type))
            cur.execute("INSERT INTO daily_meals (user_id, date, meal_type, food_name, calories, price, protein, carbs) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                        (user_id, today, meal_type, food_name, calories, price, protein, carbs))
            conn.commit()
        return jsonify({'success': True})
    finally:
        conn.close()

@meals_bp.route('/get_daily_meals', methods=['GET'])
@login_required
def get_daily_meals():
    user_id = session['user_id']
    today = date.today().isoformat()
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT meal_type, food_name, calories, price, protein, carbs FROM daily_meals WHERE user_id = %s AND date = %s", (user_id, today))
            meals = cur.fetchall()
        return jsonify({'meals': meals})
    finally:
        conn.close()

