# 🥗 慧食健康食谱平台 (Huishi Health Recipes)

基于 **Flask** (Python) 的健康饮食管理与 AI 智能推荐系统。支持三餐推荐、体质健康分析、AI 问答、签到打卡、收藏管理等功能，集成 **MySQL** 数据库。

## ✨ 功能特性

- **🍳 三餐推荐** — 按早餐/午餐/晚餐分类浏览健康食谱
- **🏥 体质健康分析** — 舌诊、脉诊等体质测评
- **🤖 AI 智能问答** — 集成 AI 大模型，提供个性化饮食建议
- **✅ 签到打卡** — 每日健康打卡记录
- **❤️ 收藏管理** — 收藏喜欢的食谱
- **👤 个人资料** — 用户信息管理与健康档案
- **🏃 运动指导** — 提供运动方式建议（跑步/游泳/瑜伽等）
- **🧠 健康知识** — 养生茶、养生汤、药膳食谱等专题

## 🛠️ 技术栈

- **后端**: Python Flask 3.x
- **数据库**: MySQL + PyMySQL
- **AI**: OpenAI 兼容接口 (讯飞星火等)
- **前端**: HTML + CSS + JavaScript (Vue)
- **认证**: Session-based 用户认证

## 🚀 快速开始

### 1. 环境要求
- Python 3.10+
- MySQL 5.7+
- pip (Python 包管理器)

### 2. 配置数据库

`ash
# 创建 MySQL 数据库
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS diet_platform CHARACTER SET utf8mb4;"
`

### 3. 配置项目

`ash
# 复制配置文件并填写你的信息
cp config.example.py config.py
# 然后编辑 config.py，填入你的数据库密码和 AI API Key
`

### 4. 安装并运行

`ash
# 创建虚拟环境 (可选)
python -m venv .venv
.venv\\Scripts\\activate   # Windows

# 安装依赖
pip install -r requirements.txt

# 启动服务 (默认 http://0.0.0.0:5000)
python app.py
`

应用自动创建数据库表，首次启动无需手动建表。

## 📁 项目结构

`
huishi-health-recipes/
├── app.py                  # 应用入口
├── config.py               # 配置文件 (已排除，需自行创建)
├── config.example.py       # 配置示例
├── requirements.txt        # Python 依赖
├── .gitignore              # Git 忽略规则
├── models/
│   └── database.py         # 数据库模型与初始化
├── routes/
│   ├── auth.py             # 用户认证 (登录/注册)
│   ├── meals.py            # 三餐管理
│   ├── health.py           # 健康分析
│   ├── checkin.py          # 签到打卡
│   └── favorites.py        # 收藏管理
├── data/
│   ├── breakfast.py        # 早餐食谱数据
│   ├── lunch.py            # 午餐食谱数据
│   ├── dinner.py           # 晚餐食谱数据
│   ├── health_recipes.py   # 健康食谱
│   ├── health_recipes_dish.py
│   ├── health_recipes_porridge.py
│   ├── health_recipes_soup.py
│   ├── health_recipes_soup_new.py
│   ├── health_recipes_tea.py
│   ├── health_recipes_tea_new.py
│   └── categories.py       # 分类数据
├── static/
│   ├── css/style.css       # 样式文件
│   ├── js/app.js           # 前端逻辑
│   ├── js/vue-app.js       # Vue 前端组件
│   └── images/             # 三餐菜品、茶饮、汤品等图片资源
└── templates/
    └── index.html           # 主页面模板
`

## ⚙️ 配置项说明

配置文件 config.py 需要手动创建（从 config.example.py 复制）：

| 配置项 | 说明 |
|--------|------|
| SECRET_KEY | Session 加密密钥，首次启动自动生成 |
| DB_CONFIG.host | MySQL 主机地址 (默认 localhost) |
| DB_CONFIG.port | MySQL 端口 (默认 3306) |
| DB_CONFIG.passwd | 数据库密码 |
| DB_NAME | 数据库名称 (默认 diet_platform) |
| AI_API_KEY | AI 服务 API Key |
| AI_BASE_URL | AI 服务地址 |

## 🔒 安全说明

- config.py 包含数据库密码和 AI API Key，已被 .gitignore 排除
- 上传前已从本仓库中移除 config.py，请按步骤自行创建
- 请勿将包含敏感信息的 config.py 提交到公共仓库

## 📃 许可

MIT License
