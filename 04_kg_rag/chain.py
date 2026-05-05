"""第 4 节 · KG-RAG 融合链（★ 本项目高潮）

完整流程：
    用户问题
       ↓
    RunnableParallel ──▶ 向量检索（chunk 列表）
                    └──▶ 图谱检索（三元组列表）
       ↓
    格式化为统一 context
       ↓
    prompt → llm → parser → 答案

亮点：两路检索 **并发** 执行，互相不阻塞；最终给 LLM 的 context 既有"原文片段"又有
"结构化事实"，回答既精准又有依据。
"""

from __future__ import annotations

import sys

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough

from shared import get_llm

from .hybrid import graph_retriever, vector_retriever


def _format_context(payload: dict) -> str:
    """把两路结果拍平成一段给 LLM 看的 context。"""
    chunks = payload.get("vector_chunks", [])
    facts = payload.get("graph_facts", [])

    parts = []
    if chunks:
        parts.append("【原文片段】")
        for c in chunks:
            parts.append(f"- 出处《{c['source']}》：{c['content'][:300]}")
    if facts:
        parts.append("\n【图谱事实】")
        for f in facts:
            parts.append(f"- {f['head']} —[{f['relation']}]→ {f['tail']}")
    return "\n".join(parts) if parts else "（未检索到相关资料）"


PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "你是知识问答助手。下面 <context> 既包含原文片段，也包含结构化的"
            "知识图谱事实。请综合两类信息回答用户问题，并在每个关键论断后用方括号"
            "标注信息来源类型，例如 [片段] 或 [图谱]。如果信息不足，明确说明。\n\n"
            "<context>\n{context}\n</context>",
        ),
        ("human", "{question}"),
    ]
)


def build_chain():
    llm = get_llm(temperature=0.0)

    # ★ 整条链只有这一个表达式
    chain = (
        RunnableParallel(
            # 两路检索并发执行
            vector_chunks=vector_retriever,
            graph_facts=graph_retriever,
            question=RunnablePassthrough(),  # 原始问题也透传，prompt 里要用
        )
        # 把上一步的 dict 变成 prompt 需要的两个键
        | (lambda x: {"context": _format_context(x), "question": x["question"]})
        | PROMPT
        | llm
        | StrOutputParser()
    )
    return chain


def main() -> None:
    chain = build_chain()
    question = " ".join(sys.argv[1:]) or "孙悟空的师父和师弟分别是谁？"

    print(f"❓ 问题：{question}\n")

    # 先打印两路检索结果（调试视角）
    print("🔎 向量检索：")
    for c in vector_retriever.invoke(question)[:3]:
        print(f"  - 《{c['source']}》：{c['content'][:80]}...")
    print("\n🕸️  图谱检索：")
    for f in graph_retriever.invoke(question)[:8]:
        print(f"  - {f['head']} —[{f['relation']}]→ {f['tail']}")

    # 最终回答（流式）
    print("\n💡 综合回答：")
    for token in chain.stream(question):
        print(token, end="", flush=True)
    print()


if __name__ == "__main__":
    main()
