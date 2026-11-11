#!/usr/bin/env bash
# ============================================================
# 慧食图谱 · 服务器环境自检（只读，不改任何东西）
#
# 用法：
#   cd /home/ubuntu/Documents/projects/慧食图谱app
#   bash deploy/check_server.sh
#
# 把输出整段贴回来，就能判断还差哪几步。
# ============================================================
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

line() { printf '\n===== %s =====\n' "$1"; }

line "0. 基本信息"
echo "项目目录 : $APP_DIR"
echo "目录所有者: $(stat -c '%U:%G' "$APP_DIR" 2>/dev/null)"
echo "当前用户 : $(whoami)  (uid $(id -u))"
echo "系统     : $(. /etc/os-release 2>/dev/null && echo "$PRETTY_NAME")"
echo "架构     : $(uname -m)"

line "1. Python"
if command -v python3 >/dev/null; then
  echo "python3: $(python3 -V 2>&1)  路径 $(command -v python3)"
else
  echo "!! 没有 python3"
fi
python3 -c "import venv; print('venv 模块: OK')" 2>&1 | head -3
command -v uv >/dev/null && echo "uv: $(uv --version 2>&1)" || echo "uv: 未安装（不影响，会退回 python3 -m venv）"

line "2. 现有 .venv 能不能用"
if [ -x "$APP_DIR/.venv/bin/python" ]; then
  echo "存在 .venv/bin/python"
  if "$APP_DIR/.venv/bin/python" -c "import sys; print('可执行，版本', sys.version.split()[0])" 2>&1; then
    :
  else
    echo "!! .venv 不可用（很可能是从别的机器拷来的），需要用 python3 -m venv 重建"
  fi
  echo "--- 已装的关键包 ---"
  "$APP_DIR/.venv/bin/python" -m pip list 2>/dev/null | grep -Ei 'flask|pymysql|openai|httpx|pillow|gunicorn|werkzeug' || echo "（一个都没有 / pip 不可用）"
else
  echo "没有 .venv，需要创建"
fi

line "3. 端口占用（5001 有没有被老程序占着）"
if command -v ss >/dev/null; then
  ss -lntp 2>/dev/null | grep -E ':(5001|8000|80|443)\b' || echo "5001 / 8000 都没在监听"
else
  netstat -lntp 2>/dev/null | grep -E ':(5001|8000)\b' || echo "未找到 ss/netstat"
fi
echo "--- 可能相关的进程 ---"
ps -eo pid,user,cmd 2>/dev/null | grep -Ei 'gunicorn|app\.py|wsgi|flask|uwsgi' | grep -v grep || echo "没有正在跑的 Python Web 进程"

line "4. 已有的 systemd 服务"
systemctl list-units --type=service --all --no-pager 2>/dev/null \
  | grep -Ei 'huishi|diet|flask|图谱' || echo "没有名字像慧食图谱的服务"

line "5. MySQL"
command -v mysql >/dev/null && echo "mysql 客户端: $(command -v mysql)" || echo "!! 没有 mysql 客户端（apt install mysql-client）"
mysqladmin ping 2>/dev/null || mysqladmin -uroot ping 2>/dev/null || echo "mysqladmin ping 失败（可能需要密码或服务没起）"
systemctl is-active mysql 2>/dev/null || systemctl is-active mysqld 2>/dev/null || echo "mysql 服务状态未知"

line "6. Nginx"
if command -v nginx >/dev/null; then
  echo "nginx: $(nginx -v 2>&1)"
  echo "服务状态: $(systemctl is-active nginx 2>/dev/null)"
  echo "--- sites-enabled ---"
  ls -1 /etc/nginx/sites-enabled/ 2>/dev/null || echo "（没有 sites-enabled 目录，可能是 conf.d 布局）"
  ls -1 /etc/nginx/conf.d/*.conf 2>/dev/null
  echo "--- 已发布站点里的关键行 ---"
  for f in /etc/nginx/sites-enabled/* /etc/nginx/conf.d/*.conf; do
    [ -f "$f" ] || continue
    echo "### $f"
    grep -nE 'server_name|listen|root |proxy_pass|location|alias' "$f" 2>/dev/null | head -30
  done
else
  echo "!! 没有 nginx"
fi

line "7. 静态资源路径权限（nginx 若直接读这里，需要能穿过 /home/ubuntu）"
echo "--- 各级目录的其他用户执行位（x = 能进入）---"
p="$APP_DIR"
while [ "$p" != "/" ]; do
  printf '%-60s %s\n' "$p" "$(stat -c '%A %U:%G' "$p" 2>/dev/null)"
  p="$(dirname "$p")"
done
echo "--- 图片目录 ---"
if [ -d "$APP_DIR/static/images" ]; then
  echo "文件数: $(find "$APP_DIR/static/images" -type f | wc -l)"
  echo "后缀分布: $(find "$APP_DIR/static/images" -type f | sed 's/.*\.//' | sort | uniq -c | tr '\n' ' ')"
  echo "总体积: $(du -sh "$APP_DIR/static/images" 2>/dev/null | cut -f1)"
else
  echo "!! 没有 static/images 目录"
fi

line "8. 环境变量文件"
if [ -f "$APP_DIR/.env" ]; then
  echo ".env 存在，权限 $(stat -c '%A' "$APP_DIR/.env")"
  grep -E '^(FLASK_SECRET_KEY|DB_USER|DB_NAME|DB_HOST|DB_PORT|DEEPSEEK_BASE_URL)=' "$APP_DIR/.env" \
    | sed 's/\(FLASK_SECRET_KEY=\).*/\1***(已设置)/' || true
  grep -q 'CHANGE_ME' "$APP_DIR/.env" && echo "!! 还有 CHANGE_ME 占位值" || echo "没有 CHANGE_ME 占位值"
else
  echo "没有 .env（需要从 .env.example 复制并编辑）"
fi

line "9. 关键文件是否齐全"
for f in app.py config.py wsgi.py gunicorn.conf.py requirements.txt templates/index.html static/images; do
  if [ -e "$APP_DIR/$f" ]; then echo "OK   $f"; else echo "缺失 $f"; fi
done

echo ""
echo "===== 自检结束，把上面整段贴回来 ====="
