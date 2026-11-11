"""
WSGI 入口（Linux 生产环境用 gunicorn 调用）

    gunicorn -c gunicorn.conf.py wsgi:app

Windows 本地开发仍可 `python app.py`（Flask 自带服务器）。
"""
import os

from app import create_app

app = create_app()

if __name__ == '__main__':
    # 仅用于本地直接调试；生产环境请用 gunicorn
    port = int(os.environ.get('PORT', '5001'))
    app.run(host='0.0.0.0', port=port, debug=False)
