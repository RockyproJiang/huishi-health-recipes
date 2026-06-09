import pymysql
import pymysql.cursors
from config import DB_CONFIG, DB_NAME
from functools import wraps
from flask import session, jsonify


def init_db():
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute(f'CREATE DATABASE IF NOT EXISTS {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci')
        conn.select_db(DB_NAME)

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                avatar VARCHAR(255) DEFAULT 'default.png',
                points INT DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS health_profile (
                user_id INT PRIMARY KEY,
                height DECIMAL(5,2),
                weight DECIMAL(5,2),
                age INT,
                gender VARCHAR(10),
                plan_tag VARCHAR(50) DEFAULT '',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        try:
            cursor.execute('ALTER TABLE health_profile ADD COLUMN plan_tag VARCHAR(50) DEFAULT \'\'')
        except pymysql.err.OperationalError:
            pass

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS medical_history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                disease VARCHAR(50),
                detail VARCHAR(255),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_meals (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                date DATE,
                meal_type VARCHAR(20),
                food_name VARCHAR(100),
                calories INT,
                price DECIMAL(5,2),
                protein DECIMAL(5,1),
                carbs DECIMAL(5,1),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        for col, col_def in [('protein', 'DECIMAL(5,1)'), ('carbs', 'DECIMAL(5,1)')]:
            try:
                cursor.execute(f'ALTER TABLE daily_meals ADD COLUMN {col} {col_def}')
            except pymysql.err.OperationalError:
                pass

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS checkin_log (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                date DATE,
                type VARCHAR(20),
                detail VARCHAR(100),
                points_added INT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS points_log (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                change_amount INT,
                reason VarCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                item_name VARCHAR(100),
                points_cost INT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exercise_log (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                type VARCHAR(20),
                name VARCHAR(100),
                duration_seconds INT,
                calories DECIMAL(8,2),
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                title VARCHAR(100) DEFAULT '新对话',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversation_history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                conversation_id INT DEFAULT NULL,
                role VARCHAR(10),
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
            )
        ''')
        try:
            cursor.execute('ALTER TABLE conversation_history ADD COLUMN conversation_id INT DEFAULT NULL')
        except pymysql.err.OperationalError:
            pass
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS favorites (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                item_type VARCHAR(20),
                item_name VARCHAR(100),
                item_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY unique_fav (user_id, item_type, item_name),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        conn.commit()
        cursor.close()
        conn.close()
        print('Database init OK')
    except Exception as e:
        print('Database init FAILED:', e)
        raise

def get_db():
    return pymysql.connect(**DB_CONFIG, db=DB_NAME, cursorclass=pymysql.cursors.DictCursor)

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': '未登录'}), 401
        return f(*args, **kwargs)
    return decorated
