# 慧食图谱 · Linux 服务器部署说明

> 适配路径：`/home/ubuntu/Documents/projects/慧食图谱app`
> 系统：Debian / Ubuntu（有 apt）。CentOS / Alma 把 `apt` 换成 `dnf`。

---

## 一、先说结论：代码改了哪几处

原项目是按 **Windows + `python app.py`** 写的，直接拷到 Linux 上会挂。已改好：

| 文件 | 原来的问题 | 改法 |
|---|---|---|
| `app.py` | `send_from_directory('templates', ...)` 是相对路径，gunicorn/systemd 下 cwd 不是项目根 → **首页 404** | 用 `app.root_path` 拼绝对路径 |
| `config.py` | 数据库写死 `root/1234`，字符集 `utf8` | 改为读环境变量，字符集换 `utf8mb4` |
| `config.py` | 读不到 `.env` | 加 `_load_dotenv()`，启动时自动读项目根 `.env`（不装 python-dotenv，兼容 BOM） |
| `requirements.txt` | **缺 `httpx`（config.py 在用）和 `Pillow`（舌诊压图在用）**，服务器装完直接 500 | 补上，去掉 Windows 专用的 `waitress`，加 `gunicorn` |
| `wsgi.py` | `from waitress import serve`，Linux 上 ImportError | 改标准 WSGI 入口 |

本机已验证：`/`、`/db_check`、`/static/images/*.png`（回退 webp）、`/static/css/style.css` 全部 200。

---

## 二、注意你这个路径的两个坑

路径是 `/home/ubuntu/Documents/projects/慧食图谱app`，比 `/opt/xxx` 多两个问题：

**① `/home/ubuntu` 目录权限是 `750`**，`www-data`、`huishi` 这类用户**进不去**。所以：

- `deploy.sh` 默认让你用 **`ubuntu` 本人**当运行用户（读 `$SUDO_USER`），不改 `/home` 权限
- Nginx **不再直接读项目文件**，全部反代给 gunicorn，绕开权限问题
- 如果你偏要用独立用户，就得 `sudo chmod 755 /home/ubuntu`（安全性下降，不推荐）

**② 路径含中文 `慧食图谱app`**。脚本用引号包了变量，没问题；但**你手敲命令时一定要加引号**：

```bash
cd "/home/ubuntu/Documents/projects/慧食图谱app"     # 对
cd /home/ubuntu/Documents/projects/慧食图谱app        # 也对，但补全时会麻烦
```

---

## 三、服务器上按顺序执行

### 第 0 步：先自检（只读，不改任何东西）

```bash
cd "/home/ubuntu/Documents/projects/慧食图谱app"
bash deploy/check_server.sh
```

把输出贴回来，我就能精确判断还差哪步。它检查：Python / `.venv` 能否用 / 5001 端口有没有被老程序占着 / 已有 systemd 服务 / MySQL / Nginx 已发布站点的关键行 / `/home` 各级目录权限 / 图片数量 / `.env` 状态。

### 第 1 步：装系统依赖

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip mysql-client nginx curl
```

### 第 2 步：跑部署脚本

```bash
cd "/home/ubuntu/Documents/projects/慧食图谱app"
sudo bash deploy/deploy.sh
```

脚本做的事：识别项目路径 → 确定运行用户（默认 `ubuntu`）→ 检测 `.venv`（跨机器拷来的会自动重建）→ 装依赖 → 检查 `.env` → 建库 → 设权限 → 装 systemd → 健康检查。

**第一次跑会主动停下**：`.env` 刚从模板生成，里面是 `CHANGE_ME`。

### 第 3 步：编辑 `.env`

```bash
nano "/home/ubuntu/Documents/projects/慧食图谱app/.env"
```

必改三项：

```ini
FLASK_SECRET_KEY=<下面命令生成>
DB_USER=<你的 MySQL 用户>
DB_PASSWORD=<对应密码>
```

生成密钥：

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

建库（如果还没有）：

```bash
sudo mysql -e "CREATE DATABASE IF NOT EXISTS diet_platform CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

> 如果想让应用用 `ubuntu` 这个 MySQL 账号，先建一下：
> ```bash
> sudo mysql -e "CREATE USER IF NOT EXISTS 'ubuntu'@'localhost' IDENTIFIED BY '你的密码';"
> sudo mysql -e "GRANT ALL PRIVILEGES ON diet_platform.* TO 'ubuntu'@'localhost'; FLUSH PRIVILEGES;"
> ```

### 第 4 步：再跑一次脚本

```bash
sudo bash deploy/deploy.sh
```

这次会跑完全部 7 步，并在最后 curl `/db_check` 验证。

### 第 5 步：确认服务

```bash
systemctl status huishi
journalctl -u huishi -n 50 --no-pager       # 应有 "Database init OK"
curl http://127.0.0.1:5001/db_check
```

### 第 6 步：更新 Nginx 配置

**你说 Nginx 已经发布过了** —— 那就需要把现有站点的 `location` 改成反代到 5001。用 `deploy/nginx.conf` 覆盖最省事：

```bash
# 先看看你现在配的是什么
ls -1 /etc/nginx/sites-enabled/
sudo nginx -T | grep -nE 'server_name|root |proxy_pass' | head -20

# 备份现有的
sudo cp /etc/nginx/sites-available/<你原来的站点名> /root/nginx-backup-$(date +%F).conf

# 用新的
sudo cp "/home/ubuntu/Documents/projects/慧食图谱app/deploy/nginx.conf" /etc/nginx/sites-available/huishi
sudo sed -i 's#your-domain.com#你的域名或公网IP#' /etc/nginx/sites-available/huishi
sudo ln -sf /etc/nginx/sites-available/huishi /etc/nginx/sites-enabled/huishi
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
```

如果你**不想覆盖**现有站点，只需要保证它有这一段（其余保留）：

```nginx
location / {
    proxy_pass http://127.0.0.1:5001;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_read_timeout 180s;
    proxy_send_timeout 180s;
    client_max_body_size 10m;
}
```

⚠️ **关键**：现有的 Nginx 里如果还有 `root` 指向旧项目目录、或者 `try_files` 直接返回静态文件，**必须删掉**，否则 `/` 会返回旧文件或 404。

### 第 7 步：HTTPS（有域名的话）

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d 你的域名
```

---

## 四、几个必须知道的细节

### 1. 图片是 `.webp`，但代码里写的是 `.png`

191 张图已全转 WebP（360MB → 12.6MB）。为不改 60 多处硬编码路径，靠 Flask 的 `serve_static()` 兜底：找不到 `xxx.png` 就自动找 `xxx.webp`。

因为 Nginx 现在纯反代、不碰文件系统，**这个兜底只依赖 Flask 层，不需要 Nginx 里再写 `try_files`**。

所以 `static/images/` 下**只有 `.webp` 是对的，不要往里补 `.png`**。

### 2. `.venv` 是从别的机器拷来的

项目里的 `.venv` 是 `/home/rocky/.local/share/uv/python/cpython-3.11-linux-x86_64-gnu` 建的，在你这台机器上大概率跑不起来（解释器路径硬编码在 `pyvenv.cfg` 里）。脚本会先试 `python -c "import sys"`，失败就 `rm -rf .venv` 用本机 `python3 -m venv` 重建，并补装 Pillow / gunicorn（原 `.venv` 里这两个都没有）。

### 3. 运行用户 = `ubuntu`（不是你新建的 huishi）

因为 `/home/ubuntu` 是 `750`。脚本默认 `APP_USER=$SUDO_USER`。想换：

```bash
sudo APP_USER=huishi bash deploy/deploy.sh     # 但需要先 chmod 755 /home/ubuntu
```

检查当前服务用的是谁：

```bash
systemctl cat huishi | grep -E 'User|WorkingDirectory'
```

### 4. 舌诊慢，别把 timeout 调小

视觉模型单次 10–22 秒。`gunicorn.conf.py` 是 `timeout = 180`，Nginx 是 `proxy_read_timeout 180s`。调小会 502。

### 5. `preload_app = True` 是有意的

这样 `init_db()` 只在 master 进程执行一次；否则 4 个 worker 同时跑 `CREATE TABLE` 会抢 DDL 锁。`init_db()` 结束时会关连接，fork 后的子进程不会共用。

### 6. 数据库要不要迁移旧数据

新库什么都不用做，`init_db()` 自动建表。要保留旧数据：

```bash
# 本机 Windows
mysqldump -u root -p1234 --default-character-set=utf8mb4 diet_platform > diet_platform.sql
# 传到服务器后
mysql -u <DB_USER> -p diet_platform < diet_platform.sql
```

然后 `sudo systemctl restart huishi`。

### 7. 发布新代码

```bash
cd "/home/ubuntu/Documents/projects/慧食图谱app"
# 覆盖文件
sudo chown -R ubuntu:ubuntu .
sudo systemctl restart huishi
journalctl -u huishi -f
```

---

## 五、常见报错对照

| 现象 | 原因 | 解决 |
|---|---|---|
| `Permission denied` 打开 templates | 服务用户不是文件所有者 | `sudo chown -R ubuntu:ubuntu <项目目录>` |
| 首页返回旧页面 / 404 | Nginx 里还有旧 `root` 或 `try_files` | 改成纯反代，见第 6 步 |
| `ModuleNotFoundError: PIL` | `.venv` 是旧的、没重建 | `rm -rf .venv` 后重跑脚本 |
| `ModuleNotFoundError: waitress` | 用了旧 `wsgi.py` | 用仓库里的新 `wsgi.py` |
| `Database init FAILED: 1045 Access denied` | `.env` 的 DB 账号密码错 | 改 `.env`，`mysql -u X -p` 手工试一下 |
| 502 Bad Gateway | gunicorn 没起来 / 端口不对 | `journalctl -u huishi -n 60`，`curl 127.0.0.1:5001` |
| 图片全裂 | 请求打到了旧 Nginx root 而不是 Flask | 确认静态也走 `proxy_pass` |
| 上传头像 500 | `static/uploads` 不可写 | `sudo chown -R ubuntu:ubuntu static/uploads` |
| 中文乱码 | 库不是 utf8mb4 | 重建库：`CHARACTER SET utf8mb4` |
| `address already in use :5001` | 老程序还占着端口 | `sudo ss -lntp \| grep 5001` 找到 PID 杀掉 |

---

## 六、本地 Windows 开发不受影响

`python app.py` 仍可用。`config.py` 读不到环境变量时用的还是原来的默认值（`root/1234/diet_platform`），本机不用改任何东西。
