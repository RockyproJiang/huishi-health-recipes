import multiprocessing
import os

# 监听地址：只监听本机，由 Nginx 反代到 80/443
bind = "127.0.0.1:5001"

# 渲染依赖少量 CPU，2–4 个 worker 足够。
# 机器内存小（<=1G）时建议不要开满，改 2。
workers = int(os.environ.get('GUNICORN_WORKERS', min(4, max(2, multiprocessing.cpu_count()))))
worker_class = "sync"

# 舌诊走视觉模型，单次可能 20 秒以上；不要低于 120
timeout = 180
graceful_timeout = 30
keepalive = 5

# 日志交给 systemd 的 journald 收集
accesslog = "-"
errorlog = "-"
loglevel = "info"

# 先建应用再 fork：init_db() 只在 master 里执行一次，
# 避免 4 个 worker 同时跑 CREATE TABLE 抢 DDL 锁。
# init_db() 执行完会关闭连接，fork 出去的子进程不会共用连接池。
preload_app = True
