"""Embedding 工厂：本地 HuggingFace 模型，零 API key。

为什么本地跑？
- DeepSeek 没有 embedding 接口，单 API key 跑不通；
- 学习项目最忌"配置三个 key 才能 hello world"，本地模型免去这一步。

用什么模型？
- BAAI/bge-small-zh-v1.5：~100MB，512 维，CPU 上 ~50 chunks/秒，中文友好；
- 想换大模型，把 model_name 改成 BAAI/bge-base-zh-v1.5（~400MB / 768 维）
  或 BAAI/bge-m3（~2GB / 1024 维，质量最佳但 CPU 慢）。

第一次运行会从 HuggingFace 下载模型（约 100MB），之后会缓存到 ~/.cache/huggingface。
国内用户如果连不上 HF，下方会自动切到 hf-mirror.com。

对照 Yuxi：backend/package/yuxi/models/embed.py 走 SiliconFlow 远程 API；
我们这里换成本地，但接口（Embeddings 协议）完全一样，应用层无感。
"""

from __future__ import annotations

import os

# 国内访问 HuggingFace 的镜像。如果系统已设置 HF_ENDPOINT 就尊重，否则用 hf-mirror。
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

from langchain_core.embeddings import Embeddings  # noqa: E402
from langchain_huggingface import HuggingFaceEmbeddings  # noqa: E402

# 模块级缓存：避免每次调用都重新加载模型（加载耗时 3-5 秒）
_cached: Embeddings | None = None


def get_embedding() -> Embeddings:
    """获取 BAAI/bge-small-zh-v1.5 本地嵌入模型（512 维）。"""
    global _cached
    if _cached is not None:
        return _cached

    _cached = HuggingFaceEmbeddings(
        model_name="BAAI/bge-small-zh-v1.5",
        model_kwargs={"device": "cpu"},
        # bge 系列推荐归一化，方便后续用余弦相似度
        encode_kwargs={"normalize_embeddings": True, "batch_size": 32},
    )
    return _cached
