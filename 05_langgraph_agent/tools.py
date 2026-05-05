"""第 5 节 · 把检索包成 @tool

LangGraph 的 Agent 不是预定义的"先检索再生成"管道，而是**让 LLM 自己决定**
何时调哪个工具、调几次。所以前 4 节的检索函数现在要包成"工具"暴露给 LLM。

@tool 装饰器会读：
- 函数名 → 工具名
- docstring → LLM 看到的工具描述（决定它什么时候调你）
- 函数签名 → 工具参数 schema（含类型注解）
"""

from __future__ import annotations

# 复用第 4 节的两个检索函数（已经写好的逻辑直接拿来用）
from importlib import import_module

from langchain_core.tools import tool

_hybrid = import_module("04_kg_rag.hybrid")  # 目录名以数字开头不能 import as identifier


@tool
def vector_search(query: str) -> str:
    """在知识库中做**语义检索**，返回最相关的文档片段。

    适用场景：
    - 用户问开放性问题（"介绍一下 X"、"为什么 X"）
    - 答案藏在原文叙述里，不一定有明确的实体关系

    Args:
        query: 用自然语言写的查询词，可以是问题原文。
    """
    chunks = _hybrid.vector_search(query)
    if not chunks:
        return "（向量检索没有命中任何文档）"
    return "\n\n".join(f"[{c['source']}] {c['content']}" for c in chunks)


@tool
def graph_search(query: str) -> str:
    """在知识图谱中做**关系检索**，返回结构化的三元组。

    适用场景：
    - 用户问"A 的 B 是谁"、"A 和 B 是什么关系"
    - 用户问需要多跳推理的关系问题（"A 的徒弟的师父"）
    - 你已经从向量检索拿到了片段，但需要确认实体间的精确关系

    Args:
        query: 含目标实体名的查询。会自动从 query 里抽取已知实体并扩展邻居。
    """
    facts = _hybrid.graph_search(query)
    if not facts:
        return "（图谱检索没有命中任何实体）"
    return "\n".join(f"- {f['head']} —[{f['relation']}]→ {f['tail']}" for f in facts)
