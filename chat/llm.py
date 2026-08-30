"""DeepSeek 模型实例（单例，惰性初始化）。"""

from functools import lru_cache

from django.conf import settings
from langchain_deepseek import ChatDeepSeek


@lru_cache(maxsize=1)
def get_llm() -> ChatDeepSeek:
    """返回流式 ChatDeepSeek 实例。

    未配置 DEEPSEEK_API_KEY 时抛出 RuntimeError，由调用方捕获后转成
    明确的错误事件返回，而不是 500。
    """
    if not settings.DEEPSEEK_API_KEY:
        raise RuntimeError('未配置 DEEPSEEK_API_KEY，请在 backend/.env 中填写后重启服务')

    return ChatDeepSeek(
        model=settings.DEEPSEEK_MODEL,
        api_key=settings.DEEPSEEK_API_KEY,
        base_url=settings.DEEPSEEK_BASE_URL,
        temperature=0.7,
        streaming=True,
    )
