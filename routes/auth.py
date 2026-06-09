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
            session['user_id'] = user['id']
            session['username'] = username
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
            cur.execute("SELECT username, avatar, points FROM users WHERE id = %s", (user_id,))
            user = cur.fetchone()
            cur.execute("SELECT * FROM health_profile WHERE user_id = %s", (user_id,))
            profile = cur.fetchone()
            cur.execute("SELECT disease, detail FROM medical_history WHERE user_id = %s", (user_id,))
            history = cur.fetchall()
        return jsonify({
            'username': user['username'],
            'avatar': user['avatar'],
            'points': user['points'],
            'profile': profile,
            'medical_history': history
        })
    finally:
        conn.close()

@auth_bp.route('/save_profile', methods=['POST'])
@login_required
def save_profile():
    data = request.json
    user_id = session['user_id']
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO health_profile (user_id, height, weight, age, gender, plan_tag) 
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE height=VALUES(height), weight=VALUES(weight), age=VALUES(age), gender=VALUES(gender), plan_tag=VALUES(plan_tag)
            """, (user_id, data.get('height'), data.get('weight'), data.get('age'), data.get('gender'), data.get('plan_tag', '')))
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

@auth_bp.route('/check_login', methods=['GET'])
def check_login():
    return jsonify({'logged_in': 'user_id' in session, 'user_id': session.get('user_id')})

