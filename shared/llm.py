"""LLM 工厂：返回一个指向 DeepSeek 的 ChatOpenAI 实例。

为什么用 langchain_openai.ChatOpenAI 而不是 langchain-deepseek？
- DeepSeek 完全兼容 OpenAI 协议，ChatOpenAI 即插即用；
- 减少一个依赖，初学者只需理解一个类；
- 想换 SiliconFlow / OpenRouter 也只改 base_url，不用换类。

对照 Yuxi：backend/package/yuxi/agents/models.py:load_chat_model 做了多家适配，
我们这里刻意不做，单一 provider 才能让学习焦点放在 LCEL 而不是适配。
"""

from __future__ import annotations

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from shared.config import settings


def get_llm(temperature: float = 0.0, **kwargs) -> BaseChatModel:
    """获取一个 DeepSeek chat 模型。

    Args:
        temperature: 默认 0，问答场景要稳定；想发挥创造性可调高。
        **kwargs: 透传给 ChatOpenAI（如 max_tokens、model_kwargs 等）。
    """
    return ChatOpenAI(
        model=settings.deepseek_model,
        api_key=SecretStr(settings.deepseek_api_key),
        base_url=settings.deepseek_base_url,
        temperature=temperature,
        stream_usage=True,  # 流式时也能拿到 usage 统计
        **kwargs,
    )
