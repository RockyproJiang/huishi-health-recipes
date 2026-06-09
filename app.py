import os
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from config import SECRET_KEY
from models.database import init_db, get_db
from routes import register_blueprints

def create_app():
    app = Flask(__name__)
    CORS(app, supports_credentials=True)
    app.secret_key = SECRET_KEY

    init_db()
    register_blueprints(app)

    @app.route('/')
    def index():
        return send_from_directory('templates', 'index.html')

    @app.route('/static/<path:filename>')
    def serve_static(filename):
        return send_from_directory(os.path.join(app.root_path, 'static'), filename)

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
    app.run(debug=True, host='0.0.0.0', port=5000)
