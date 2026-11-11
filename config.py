import os
import secrets
import openai
import httpx


def _load_dotenv():
    """把项目根目录的 .env 读进环境变量（不覆盖已有的）。

    这样无论用 systemd / gunicorn / python app.py 启动，
    只要项目根有 .env 就能生效，不依赖额外依赖 python-dotenv。
    已存在的真实环境变量优先级更高。
    """
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if not os.path.isfile(env_path):
        return
    try:
        # utf-8-sig：兼容 Windows 记事本 / PowerShell 保存时带的 BOM
        with open(env_path, encoding='utf-8-sig') as f:
            for raw in f:
                line = raw.strip().lstrip('\ufeff')
                if not line or line.startswith('#') or '=' not in line:
                    continue
                key, val = line.split('=', 1)
                key = key.strip()
                if key.startswith('export '):
                    key = key[7:].strip()
                val = val.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = val
    except Exception as e:
        print('读取 .env 失败:', e)


_load_dotenv()

SECRET_KEY = os.environ.get('FLASK_SECRET_KEY')
if not SECRET_KEY:
    # 未配置 .env 时用一次性随机密钥兜底：安全，但重启后旧 session 会失效
    SECRET_KEY = secrets.token_hex(32)
    print('[警告] 未设置 FLASK_SECRET_KEY，已使用临时随机密钥（生产环境请在 .env 中配置）')

DB_CONFIG = {
    "host": os.environ.get('DB_HOST', 'localhost'),
    "port": int(os.environ.get('DB_PORT', '3306')),
    "user": os.environ.get('DB_USER', 'root'),
    "passwd": os.environ.get('DB_PASSWORD', '1234'),
    "charset": "utf8mb4"
}
DB_NAME = os.environ.get('DB_NAME', 'diet_platform')

# ===== AI 服务配置（DeepSeek 官方 API，OpenAI 兼容）=====
# 换 key 时只改下面这一行即可（也支持通过环境变量覆盖）
AI_API_KEY = os.environ.get('DEEPSEEK_API_KEY', '')
AI_BASE_URL = os.environ.get('DEEPSEEK_BASE_URL', 'https://api.deepseek.com/v1')

# 文本对话模型（营养师 / 方案生成）
AI_MODEL = 'deepseek-flash'
# 视觉模型（舌象识别）—— deepseek-flash 支持 image 输入
AI_VISION_MODEL = 'deepseek-flash'
# 视觉模型会先输出思维链再输出正文，token 需要给足，否则正文会被截断
AI_MAX_TOKENS = 2600
AI_VISION_MAX_TOKENS = 3000
AI_TEMPERATURE = 0.7

# 读图请求首字节可能较慢，超时放宽到 120s
AI_TIMEOUT = httpx.Timeout(120.0, connect=15.0)


def get_ai_client():
    http_client = httpx.Client(
        timeout=AI_TIMEOUT,
        follow_redirects=True
    )
    return openai.OpenAI(
        api_key=AI_API_KEY,
        base_url=AI_BASE_URL,
        http_client=http_client,
        max_retries=2
    )
