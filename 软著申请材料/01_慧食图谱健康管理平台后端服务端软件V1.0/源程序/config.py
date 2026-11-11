# -*- coding: utf-8 -*-
"""
全局配置模块。

安全说明：本软件所有涉及密钥、口令、第三方接口凭据的敏感信息均不写入源码，
统一从运行环境的环境变量（Environment Variable）读取。请勿在源码中硬编码任何真实密钥。
"""
import os
import openai
import httpx


# Flask 会话密钥：必须通过环境变量 FLASK_SECRET_KEY 配置。
# 未配置时仅作为开发期占位值，正式部署务必设置为随机长字符串。
SECRET_KEY = os.environ.get('FLASK_SECRET_KEY', 'dev-only-insecure-secret-key')

# 数据库连接配置：账号、口令一律从环境变量读取，避免明文入库源码。
DB_CONFIG = {
    "host": os.environ.get('DB_HOST', 'localhost'),
    "port": int(os.environ.get('DB_PORT', '3306')),
    "user": os.environ.get('DB_USER', 'root'),
    "passwd": os.environ.get('DB_PASSWORD', ''),
    "charset": "utf8"
}
DB_NAME = os.environ.get('DB_NAME', 'diet_platform')

# AI 营养助手接入配置：密钥与网关地址从环境变量读取。
# 未配置时返回空串，运行期调用将提示未配置。
AI_API_KEY = os.environ.get('AI_API_KEY', '')
AI_BASE_URL = os.environ.get('AI_BASE_URL', '')

# 舌诊图像分析与第三方图床接入凭据：从环境变量读取，避免硬编码。
TONGUE_APPCODE = os.environ.get('TONGUE_APPCODE', '')
TONGUE_DIAGNOSE_URL = os.environ.get('TONGUE_DIAGNOSE_URL', '')
IMG_HOST_IMGBB_KEY = os.environ.get('IMG_HOST_IMGBB_KEY', '')
IMG_HOST_FREEIMAGE_KEY = os.environ.get('IMG_HOST_FREEIMAGE_KEY', '')


def get_ai_client():
    """构造 AI 营养助手的 OpenAI 兼容客户端。"""
    http_client = httpx.Client(
        timeout=httpx.Timeout(30.0, connect=10.0),
        follow_redirects=True
    )
    return openai.OpenAI(
        api_key=AI_API_KEY,
        base_url=AI_BASE_URL,
        http_client=http_client,
        max_retries=2
    )
