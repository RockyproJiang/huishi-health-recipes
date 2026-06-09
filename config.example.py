"""
⚠️ 配置文件示例
将此文件复制为 config.py 并填写你的配置信息。
config.py 已被 .gitignore 排除，不会被提交到仓库。
"""

import secrets

SECRET_KEY = secrets.token_hex(16)

DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "passwd": "your_password_here",   # 修改为你的数据库密码
    "charset": "utf8"
}

DB_NAME = "diet_platform"

AI_API_KEY = "your_api_key_here"       # 替换为你的 API Key
AI_BASE_URL = "https://your-ai-service.com/v2"

def get_ai_client():
    import openai
    return openai.OpenAI(api_key=AI_API_KEY, base_url=AI_BASE_URL)
