from flask import Blueprint, request, jsonify, session, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
import os
from models.database import get_db, login_required

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'error': '用户名和密码不能为空'}), 400
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE username = %s", (username,))
            if cur.fetchone():
                return jsonify({'error': '用户名已存在'}), 400
            hash_pw = generate_password_hash(password)
            cur.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s)", (username, hash_pw))
            conn.commit()
            user_id = cur.lastrowid
            cur.execute("INSERT INTO health_profile (user_id) VALUES (%s)", (user_id,))
            conn.commit()
        return jsonify({'success': True, 'user_id': user_id}), 201
    finally:
        conn.close()

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, password_hash FROM users WHERE username = %s", (username,))
            user = cur.fetchone()
            if not user or not check_password_hash(user['password_hash'], password):
                return jsonify({'error': '账号或密码错误'}), 401
            session.permanent = True
            session['user_id'] = user['id']
            session['username'] = username
            # 确保老用户的 health_profile 行存在
            cur.execute("INSERT IGNORE INTO health_profile (user_id) VALUES (%s)", (user['id'],))
            conn.commit()
            return jsonify({'success': True, 'user_id': user['id']})
    finally:
        conn.close()

@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})

@auth_bp.route('/user_info', methods=['GET'])
@login_required
def user_info():
    user_id = session['user_id']
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT username, avatar, points, membership_expires_at, membership_plan FROM users WHERE id = %s", (user_id,))
            user = cur.fetchone()
            cur.execute("SELECT * FROM health_profile WHERE user_id = %s", (user_id,))
            profile = cur.fetchone()
            cur.execute("SELECT disease, detail FROM medical_history WHERE user_id = %s", (user_id,))
            history = cur.fetchall()
            cur.execute("SELECT COUNT(*) as cnt FROM tongue_records WHERE user_id = %s", (user_id,))
            tongue_total = cur.fetchone()['cnt']
            today = datetime.now().strftime('%Y-%m-%d')
            cur.execute("SELECT COUNT(*) as cnt FROM tongue_records WHERE user_id = %s AND DATE(created_at) = %s", (user_id, today))
            tongue_today = cur.fetchone()['cnt']
            cur.execute("SELECT COUNT(*) as cnt FROM conversation_history WHERE user_id = %s AND role='user' AND DATE(created_at) = %s", (user_id, today))
            chat_today = cur.fetchone()['cnt']
        import datetime as _dt
        expires = user['membership_expires_at']
        is_vip = bool(expires and expires >= _dt.date.today())
        return jsonify({
            'username': user['username'],
            'avatar': user['avatar'],
            'points': user['points'],
            'profile': profile,
            'medical_history': history,
            'membership_expires_at': expires.isoformat() if expires else None,
            'membership_plan': user['membership_plan'] or '',
            'is_vip': is_vip,
            'tongue_total': tongue_total,
            'tongue_today': tongue_today,
            'chat_today': chat_today
        })
    finally:
        conn.close()

def _or_none(v):
    """将空字符串转为 None，避免 MySQL DECIMAL 列存成 0"""
    return None if v == '' or v is None else v


@auth_bp.route('/save_profile', methods=['POST'])
@login_required
def save_profile():
    data = request.json
    user_id = session['user_id']
    conn = get_db()
    try:
        with conn.cursor() as cur:
            if 'plan_tag' in data and data['plan_tag']:
                cur.execute("""
                    INSERT INTO health_profile (user_id, height, weight, age, gender, plan_tag) 
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE height=VALUES(height), weight=VALUES(weight), age=VALUES(age), gender=VALUES(gender), plan_tag=VALUES(plan_tag)
                """, (user_id, _or_none(data.get('height')), _or_none(data.get('weight')), _or_none(data.get('age')), data.get('gender', ''), data['plan_tag']))
            else:
                cur.execute("""
                    INSERT INTO health_profile (user_id, height, weight, age, gender) 
                    VALUES (%s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE height=VALUES(height), weight=VALUES(weight), age=VALUES(age), gender=VALUES(gender)
                """, (user_id, _or_none(data.get('height')), _or_none(data.get('weight')), _or_none(data.get('age')), data.get('gender', '')))
            cur.execute("DELETE FROM medical_history WHERE user_id = %s", (user_id,))
            diseases = data.get('diseases', [])
            for d in diseases:
                cur.execute("INSERT INTO medical_history (user_id, disease, detail) VALUES (%s, %s, %s)",
                            (user_id, d['disease'], d.get('detail', '')))
            conn.commit()
        return jsonify({'success': True})
    finally:
        conn.close()

@auth_bp.route('/upload_avatar', methods=['POST'])
@login_required
def upload_avatar():
    file = request.files.get('avatar')
    if not file:
        return jsonify({'error': '无文件'}), 400
    user_id = session['user_id']
    upload_dir = os.path.join(current_app.root_path, 'static', 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    filename = f"avatar_{user_id}_{int(datetime.now().timestamp())}.png"
    file.save(os.path.join(upload_dir, filename))
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE users SET avatar = %s WHERE id = %s", (filename, user_id))
            conn.commit()
        return jsonify({'avatar': filename})
    finally:
        conn.close()

@auth_bp.route('/change_username', methods=['POST'])
@login_required
def change_username():
    data = request.json
    new_username = data.get('new_username')
    if not new_username:
        return jsonify({'error': '新用户名不能为空'}), 400
    user_id = session['user_id']
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE username = %s AND id != %s", (new_username, user_id))
            if cur.fetchone():
                return jsonify({'error': '用户名已存在'}), 400
            cur.execute("UPDATE users SET username = %s WHERE id = %s", (new_username, user_id))
            conn.commit()
            session['username'] = new_username
        return jsonify({'success': True, 'username': new_username})
    finally:
        conn.close()

@auth_bp.route('/change_password', methods=['POST'])
@login_required
def change_password():
    data = request.json
    old_pw = data.get('old_password')
    new_pw = data.get('new_password')
    if not old_pw or not new_pw:
        return jsonify({'error': '密码不能为空'}), 400
    user_id = session['user_id']
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT password_hash FROM users WHERE id = %s", (user_id,))
            user = cur.fetchone()
            if not user or not check_password_hash(user['password_hash'], old_pw):
                return jsonify({'error': '旧密码错误'}), 401
            new_hash = generate_password_hash(new_pw)
            cur.execute("UPDATE users SET password_hash = %s WHERE id = %s", (new_hash, user_id))
            conn.commit()
        return jsonify({'success': True})
    finally:
        conn.close()


# ========== Extended Profile Management ==========

@auth_bp.route('/full_profile', methods=['GET'])
@login_required
def get_full_profile():
    user_id = session['user_id']
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT username, avatar, points FROM users WHERE id = %s", (user_id,))
            user = cur.fetchone()
            cur.execute("SELECT * FROM health_profile WHERE user_id = %s", (user_id,))
            profile = cur.fetchone()
            cur.execute("SELECT disease, detail FROM medical_history WHERE user_id = %s", (user_id,))
            history = cur.fetchall()
            cur.execute("SELECT * FROM user_preferences WHERE user_id = %s", (user_id,))
            preferences = cur.fetchone()
            cur.execute("SELECT id, goal, status FROM health_goals WHERE user_id = %s ORDER BY id", (user_id,))
            goals = cur.fetchall()
            cur.execute("SELECT * FROM lifestyle_info WHERE user_id = %s", (user_id,))
            lifestyle = cur.fetchone()
            cur.execute("SELECT id, image_path, source, analysis_result, constitution_type, constitution_details, created_at FROM tongue_records WHERE user_id = %s ORDER BY created_at DESC", (user_id,))
            tongue = cur.fetchall()
            cur.execute("SELECT meta_key, meta_value, source, updated_at FROM user_metadata WHERE user_id = %s ORDER BY meta_key", (user_id,))
            metadata = cur.fetchall()
        return jsonify({
            'username': user['username'],
            'avatar': user['avatar'],
            'points': user['points'],
            'profile': profile,
            'medical_history': history,
            'preferences': preferences,
            'goals': goals,
            'lifestyle': lifestyle,
            'tongue_records': tongue,
            'metadata': metadata
        })
    finally:
        conn.close()


@auth_bp.route('/save_preferences', methods=['POST'])
@login_required
def save_preferences():
    data = request.json
    user_id = session['user_id']
    conn = get_db()
    try:
        with conn.cursor() as cur:
            sql = (
                "INSERT INTO user_preferences (user_id, taste_preference, food_restrictions, food_allergies, other_notes) "
                "VALUES (%s, %s, %s, %s, %s) "
                "ON DUPLICATE KEY UPDATE "
                "taste_preference = VALUES(taste_preference), "
                "food_restrictions = VALUES(food_restrictions), "
                "food_allergies = VALUES(food_allergies), "
                "other_notes = VALUES(other_notes)"
            )
            cur.execute(sql, (user_id, data.get('taste_preference', ''),
                  data.get('food_restrictions', ''),
                  data.get('food_allergies', ''),
                  data.get('other_notes', '')))
            conn.commit()
        return jsonify({'success': True})
    finally:
        conn.close()


@auth_bp.route('/save_goals', methods=['POST'])
@login_required
def save_goals():
    data = request.json
    user_id = session['user_id']
    goal_list = data.get('goals', [])
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM health_goals WHERE user_id = %s", (user_id,))
            for g in goal_list:
                if g and g.strip():
                    cur.execute("INSERT INTO health_goals (user_id, goal) VALUES (%s, %s)",
                                (user_id, g.strip()))
            conn.commit()
        return jsonify({'success': True})
    finally:
        conn.close()


@auth_bp.route('/save_lifestyle', methods=['POST'])
@login_required
def save_lifestyle():
    data = request.json
    user_id = session['user_id']
    conn = get_db()
    try:
        with conn.cursor() as cur:
            sql = (
                "INSERT INTO lifestyle_info (user_id, sleep_schedule, exercise_frequency, "
                "alcohol_consumption, smoking, occupation, stress_level, "
                "daily_water_target, other_habits) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) "
                "ON DUPLICATE KEY UPDATE "
                "sleep_schedule = VALUES(sleep_schedule), "
                "exercise_frequency = VALUES(exercise_frequency), "
                "alcohol_consumption = VALUES(alcohol_consumption), "
                "smoking = VALUES(smoking), "
                "occupation = VALUES(occupation), "
                "stress_level = VALUES(stress_level), "
                "daily_water_target = VALUES(daily_water_target), "
                "other_habits = VALUES(other_habits)"
            )
            cur.execute(sql, (user_id, data.get('sleep_schedule', ''),
                  data.get('exercise_frequency', ''),
                  data.get('alcohol_consumption', ''),
                  data.get('smoking', ''),
                  data.get('occupation', ''),
                  data.get('stress_level', ''),
                  data.get('daily_water_target', 0),
                  data.get('other_habits', '')))
            conn.commit()
        return jsonify({'success': True})
    finally:
        conn.close()


@auth_bp.route('/save_metadata', methods=['POST'])
@login_required
def save_metadata():
    data = request.json
    user_id = session['user_id']
    meta_key = data.get('key', '').strip()
    meta_value = data.get('value', '')
    source = data.get('source', 'user')
    if not meta_key:
        return jsonify({'error': 'key is required'}), 400
    conn = get_db()
    try:
        with conn.cursor() as cur:
            sql = (
                "INSERT INTO user_metadata (user_id, meta_key, meta_value, source) "
                "VALUES (%s, %s, %s, %s) "
                "ON DUPLICATE KEY UPDATE "
                "meta_value = VALUES(meta_value), "
                "source = VALUES(source)"
            )
            cur.execute(sql, (user_id, meta_key, meta_value, source))
            conn.commit()
        return jsonify({'success': True, 'key': meta_key})
    finally:
        conn.close()


@auth_bp.route('/delete_metadata', methods=['POST'])
@login_required
def delete_metadata():
    data = request.json
    user_id = session['user_id']
    meta_key = data.get('key', '').strip()
    if not meta_key:
        return jsonify({'error': 'key is required'}), 400
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM user_metadata WHERE user_id = %s AND meta_key = %s",
                        (user_id, meta_key))
            conn.commit()
        return jsonify({'success': True})
    finally:
        conn.close()

@auth_bp.route('/check_login', methods=['GET'])
def check_login():
    return jsonify({'logged_in': 'user_id' in session, 'user_id': session.get('user_id')})

