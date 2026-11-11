#!/usr/bin/env bash
# ============================================================
# 慧食图谱 · 服务器部署脚本（Debian / Ubuntu）
#
# 用法：
#   cd /home/ubuntu/Documents/projects/慧食图谱app
#   sudo bash deploy/deploy.sh
#
# 设计要点：
#   - 自动识别项目目录（本脚本的上上级），不要求放在 /opt
#   - 默认用「调用 sudo 的那个人」当运行用户（例如 ubuntu），
#     这样服务能读到 /home/ubuntu 下的文件，不用改 /home 权限
#   - 幂等：重复执行安全，不会覆盖已有 .env 和数据库数据
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="${APP_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"

# 运行用户：优先用 sudo 的发起者，其次用目录所有者
if [ -z "${APP_USER:-}" ]; then
  if [ -n "${SUDO_USER:-}" ] && [ "$SUDO_USER" != "root" ]; then
    APP_USER="$SUDO_USER"
  else
    APP_USER="$(stat -c '%U' "$APP_DIR")"
  fi
fi
SERVICE_NAME="huishi"

echo "===== 1/7 检查运行环境 ====="
if [ "$(id -u)" -ne 0 ]; then
  echo "请用 sudo 运行：sudo bash deploy/deploy.sh"
  exit 1
fi
command -v python3 >/dev/null || { echo "缺少 python3，请先：sudo apt install -y python3 python3-venv python3-pip"; exit 1; }
echo "项目目录 : $APP_DIR"
echo "运行用户 : $APP_USER"
python3 -V

if [ ! -f "$APP_DIR/app.py" ] || [ ! -f "$APP_DIR/wsgi.py" ]; then
  echo "错误：$APP_DIR 下没有 app.py / wsgi.py，确认项目拷完整了"
  exit 1
fi
if ! id "$APP_USER" >/dev/null 2>&1; then
  echo "错误：用户 $APP_USER 不存在。可用 APP_USER=xxx 指定一个已存在的用户"
  exit 1
fi

echo "===== 2/7 准备 Python 虚拟环境 ====="
cd "$APP_DIR"
# 现有 .venv 可能是从别的机器拷来的（架构/解释器路径不同），先试能不能执行
if [ -x ".venv/bin/python" ] && .venv/bin/python -c "import sys" >/dev/null 2>&1; then
  echo "检测到可用 .venv，复用"
else
  [ -d ".venv" ] && echo "现有 .venv 不可用（多半是跨机器拷贝的），重建"
  rm -rf .venv
  if command -v uv >/dev/null 2>&1; then
    uv venv --python 3.11 .venv
  else
    python3 -m venv .venv
  fi
fi
.venv/bin/python -m pip install --upgrade pip -q
echo "安装依赖（首次约 1–2 分钟）…"
.venv/bin/python -m pip install -r requirements.txt

echo "===== 3/7 检查环境变量文件 ====="
if [ ! -f ".env" ]; then
  cp .env.example .env
  chmod 600 .env
  cat > /tmp/huishi_env_hint.txt <<'EOF'
已将 .env.example 复制为 .env，请编辑它：

  sudo nano <项目目录>/.env

必改三项：
  FLASK_SECRET_KEY  用下面命令生成一个：
                      python3 -c "import secrets; print(secrets.token_hex(32))"
  DB_USER           你的 MySQL 用户名
  DB_PASSWORD       对应的密码

如果数据库还没建，先执行（用能登 mysql 的账号）：
  sudo mysql -e "CREATE DATABASE IF NOT EXISTS diet_platform CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

改完再跑一次：sudo bash deploy/deploy.sh
EOF
  sed -i "s#<项目目录>#$APP_DIR#" /tmp/huishi_env_hint.txt
  cat /tmp/huishi_env_hint.txt
  rm -f /tmp/huishi_env_hint.txt
  exit 0
fi
if grep -q "CHANGE_ME" .env; then
  echo ""
  echo "!!  .env 里还有 CHANGE_ME 占位值，请改完再跑一次："
  grep -n "CHANGE_ME" .env
  echo ""
  exit 0
fi

echo "===== 4/7 数据库连通性 ====="
set -a; . "$APP_DIR/.env"; set +a
if command -v mysql >/dev/null 2>&1; then
  if mysql -h"${DB_HOST:-localhost}" -P"${DB_PORT:-3306}" -u"${DB_USER}" -p"${DB_PASSWORD}" \
       -e "CREATE DATABASE IF NOT EXISTS \`${DB_NAME:-diet_platform}\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" 2>/dev/null; then
    echo "数据库 ${DB_NAME:-diet_platform} 就绪（表由应用启动时 init_db 自动创建）"
  else
    echo "警告：连不上 MySQL 或没有建库权限（账号：${DB_USER}）。"
    echo "      应用启动时若要建库也会失败，请检查 .env 里的 DB_USER / DB_PASSWORD。"
  fi
else
  echo "警告：未安装 mysql 客户端，跳过检查（apt install -y mysql-client）"
fi

echo "===== 5/7 权限设置 ====="
mkdir -p "$APP_DIR/static/uploads/tongue"
chown -R "$APP_USER":"$APP_USER" "$APP_DIR"
chmod 600 "$APP_DIR/.env"
chmod -R u+rwX "$APP_DIR/static/uploads"
echo "已把 $APP_DIR 归属到 $APP_USER"

echo "===== 6/7 安装 systemd 服务 ====="
sed "s#/opt/huishi#$APP_DIR#g; s#^User=huishi#User=$APP_USER#; s#^Group=huishi#Group=$APP_USER#" \
  "$APP_DIR/deploy/$SERVICE_NAME.service" > "/etc/systemd/system/$SERVICE_NAME.service"
systemctl daemon-reload
systemctl enable "$SERVICE_NAME" >/dev/null
systemctl restart "$SERVICE_NAME"
sleep 3
systemctl --no-pager status "$SERVICE_NAME" || true

echo "===== 7/7 健康检查 ====="
if curl -fsS --max-time 10 http://127.0.0.1:5001/db_check >/tmp/huishi_dbcheck.json 2>/dev/null; then
  head -c 400 /tmp/huishi_dbcheck.json; echo
  echo "OK：应用已在本机 5001 端口正常响应"
else
  echo "!! 5001 没有响应，看日志排查："
  echo "   journalctl -u $SERVICE_NAME -n 60 --no-pager"
fi
rm -f /tmp/huishi_dbcheck.json

echo ""
echo "===== 完成 ====="
echo "查看日志：journalctl -u $SERVICE_NAME -f"
echo ""
echo "Nginx（若还没配）："
echo "  sudo cp $APP_DIR/deploy/nginx.conf /etc/nginx/sites-available/huishi"
echo "  sudo sed -i 's#your-domain.com#你的域名或IP#' /etc/nginx/sites-available/huishi"
echo "  sudo ln -sf /etc/nginx/sites-available/huishi /etc/nginx/sites-enabled/"
echo "  sudo nginx -t && sudo systemctl reload nginx"
