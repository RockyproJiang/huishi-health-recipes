import os
import sys
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS

# Force UTF-8 output to prevent terminal garbled text on Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
from config import SECRET_KEY
from models.database import init_db, get_db
from routes import register_blueprints

def create_app():
    # static_folder=None：由下面的 serve_static 接管，以支持旧 .png/.jpg
    # 路径自动回退到压缩后的同名 .webp 文件
    app = Flask(__name__, static_folder=None)
    CORS(app, supports_credentials=True)
    app.secret_key = SECRET_KEY
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = 60 * 60 * 24 * 30  

    @app.after_request
    def _remove_x_powered_by(response):
        response.headers.pop('X-Powered-By', None)
        return response

    init_db()
    register_blueprints(app)

    @app.route('/')
    def index():
        # 用绝对路径：gunicorn / systemd 下当前工作目录不一定是项目根目录
        return send_from_directory(os.path.join(app.root_path, 'templates'), 'index.html')

    @app.route('/static/<path:filename>')
    def serve_static(filename):
        static_root = os.path.join(app.root_path, 'static')
        abs_path = os.path.join(static_root, filename)
        # 图片已统一压缩为 WebP，旧代码里写死的 .png/.jpg 路径自动回退到同名 .webp
        if not os.path.exists(abs_path):
            stem, ext = os.path.splitext(abs_path)
            if ext.lower() in ('.png', '.jpg', '.jpeg'):
                for cand_ext in ('.webp', '.WEBP'):
                    if os.path.exists(stem + cand_ext):
                        abs_path = stem + cand_ext
                        filename = os.path.splitext(filename)[0] + cand_ext
                        break
        response = send_from_directory(static_root, filename, max_age=604800)
        response.headers['Cache-Control'] = 'public, max-age=604800'
        return response

    @app.route('/db_check')
    def db_check():
        result = {"mysql": "ok", "database": "", "tables": []}
        try:
            conn = get_db()
            with conn.cursor() as cur:
                cur.execute("SHOW TABLES")
                rows = cur.fetchall()
                result["tables"] = [list(row.values())[0] for row in rows]
                result["database"] = conn.db.decode() if isinstance(conn.db, bytes) else str(conn.db)
            conn.close()
        except Exception as e:
            result["mysql"] = str(e)
        return jsonify(result)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5001)
