# 慧食图谱 · Huishi Health Recipes

> 一个本地运行的 AI 饮食管理与健康推荐平台：三餐食谱推荐、体质健康分析、AI 营养师问答、舌象识别、打卡积分与收藏管理。

基于 **Flask + MySQL + DeepSeek** 构建，前端为原生 HTML/CSS/JS 单页应用（无构建步骤），可直接部署到 Linux 服务器走 gunicorn + nginx。

---

## 功能

| 模块 | 说明 |
|---|---|
| 三餐推荐 | 早餐 / 午餐 / 晚餐三套内置知识库（`data/` 下共 180+ 条食谱），按体质、口味偏好、忌口与过敏原自动筛选 |
| 健康食谱库 | 113 KB 结构化健康食谱数据，含食材、热量、营养构成、适用人群 |
| 体质与健康分析 | 身高体重 / 目标 / 作息 / 运动 / 饮食习惯问卷 → 每日热量与三大营养素目标、身体评分 |
| AI 营养师 | DeepSeek 流式对话，支持多会话管理、历史记录持久化、上下文记忆 |
| 舌象识别 | 上传舌象照片，走 DeepSeek 视觉模型输出中医体质倾向与调理建议（`routes/health.py` 的 `/tongue/upload`） |
| 打卡与积分 | 每日饮食打卡、饮水量、热量日历、积分兑换与会员套餐、订单记录 |
| 收藏夹 | 食谱收藏 / 取消 / 批量检查，按用户隔离 |
| 个人中心 | 头像上传、用户名与密码修改、偏好 / 目标 / 作息 / 自定义字段的增删改 |
| 软著材料 | `软著申请材料/` 内含按「后端服务端」「Web 前端」拆分登记的两套计算机软件著作权登记材料 |

## 技术栈

| 层 | 技术 |
|---|---|
| Web 框架 | Flask ≥ 2.3 + flask-cors（Blueprint 分模块路由） |
| 数据库 | MySQL 8（`pymysql`，启动时 `init_db()` 自动建库建表，utf8mb4） |
| AI | DeepSeek 官方 API（OpenAI 兼容，`openai` SDK + `httpx`），支持文本与视觉模型 |
| 认证 | Flask session + `werkzeug.security` 密码哈希 |
| 前端 | 原生 HTML / CSS / JavaScript，ECharts 图表，无前端构建 |
| 部署 | gunicorn + systemd + nginx（见 `deploy/`） |

## 目录结构

```
huishi-health-recipes/
├── app.py                  # Flask 应用工厂：路由、静态文件回退（png→webp）、/db_check 健康检查
├── config.py               # 配置：密钥、MySQL、DeepSeek、模型参数（全部支持环境变量覆盖）
├── wsgi.py                 # WSGI 入口（gunicorn huishi:app）
├── gunicorn.conf.py        # gunicorn 配置
├── models/database.py      # 连接池、建表、权限装饰器（login_required / admin_required）
├── routes/
│   ├── auth.py             # 注册 / 登录 / 档案 / 偏好 / 目标 / 作息
│   ├── meals.py            # 三餐推荐与食谱查询
│   ├── health.py           # AI 对话 / 舌象识别 / 运动记录 / 健康食谱 / 会话管理
│   ├── checkin.py          # 打卡 / 饮水 / 热量日历 / 积分兑换 / 会员 / 订单
│   └── favorites.py        # 收藏 CRUD
├── data/                   # 内置食谱知识库（breakfast / lunch / dinner / health_recipes）
├── templates/index.html    # 单页前端
├── static/                 # css / js / images / uploads
├── deploy/                 # Linux 部署脚本与 systemd / nginx 配置
└── 软著申请材料/             # 计算机软件著作权登记材料（两套）
```

## 快速开始

要求：**Python 3.10+**、**MySQL 8.x**（本地或远程均可）。

```bash
# 1. 安装依赖
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. 配置环境变量（复制模板后填写）
cp .env.example .env
#   必改：FLASK_SECRET_KEY、DB_PASSWORD、DEEPSEEK_API_KEY
#   生成随机密钥：python -c "import secrets; print(secrets.token_hex(32))"

# 3. 启动（首次启动自动建库建表）
python app.py                  # → http://127.0.0.1:5000
```

数据库账号需要有 `CREATE DATABASE` 权限；不想给的话先在 MySQL 里手工建好 `diet_platform` 库（utf8mb4）。

浏览器打开首页后注册账号即可使用。`/db_check` 会返回 MySQL 连接状态与建表结果，排查部署问题先看它。

## 生产部署

```bash
# 服务器上（Debian / Ubuntu）
cd /opt/huishi
cp .env.example .env && nano .env     # 填真实密钥
pip install -r requirements.txt
gunicorn -c gunicorn.conf.py wsgi:app
```

systemd 与 nginx 配置见 `deploy/huishi.service`、`deploy/nginx.conf`，完整步骤（含路径坑、字符集、静态文件回退）见 [`deploy/README.md`](deploy/README.md)。

## 配置项

全部通过环境变量（或项目根的 `.env`，`config.py` 内置极简加载器，不依赖 python-dotenv）：

| 变量 | 说明 |
|---|---|
| `FLASK_SECRET_KEY` | session 签名密钥。**未配置时启动会用一次性随机密钥兜底**（安全，但重启后旧登录失效），生产环境必须显式配置 |
| `DB_HOST` / `DB_PORT` / `DB_USER` / `DB_PASSWORD` / `DB_NAME` | MySQL 连接，默认 `localhost:3306` / `diet_platform` |
| `DEEPSEEK_API_KEY` | DeepSeek API Key。**留空则 AI 对话与舌象识别不可用**，其余功能不受影响 |
| `DEEPSEEK_BASE_URL` | 默认 `https://api.deepseek.com/v1` |
| `FLASK_DEBUG` | 生产环境设 `0` |

> 仓库中不含任何真实密钥。`config.py` 读取不到 Key 时值为空字符串，AI 接口会返回明确的缺 Key 提示，不会静默失败。

## 数据说明

- 食谱与健康知识库是内置的静态数据，不依赖外部接口。
- 用户数据（账号、档案、打卡、收藏、AI 会话）全部存 MySQL，无云端同步。
- 内置食谱的营养数值为公开资料整理，供参考，不构成医学或营养处方。

## 许可

[MIT](LICENSE) © 2025-2026 Rocky (RockyproJiang)

内置食谱与营养数据来源于公开资料整理，仅供学习与个人参考。
