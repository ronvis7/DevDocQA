"""第 1 节 · 问答脚本（★ LCEL 4 件套核心示例）

读这一份代码就能理解 LangChain 表达式语言（LCEL）的核心范式：
    数据预处理 | prompt | llm | parser

每个 | 左边是输入，右边是消费者；整条链就是函数组合。
"""

from __future__ import annotations

import sys

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough

from shared import get_embedding, get_llm, settings


def format_docs(docs: list[Document]) -> str:
    """把 retriever 返回的 Document 列表拼成一段纯文本，喂给 prompt 的 {context}。"""
    return "\n\n".join(f"[{d.metadata.get('source', '?')}] {d.page_content}" for d in docs)


def build_chain():
    """构建一条最经典的 RAG LCEL 链。"""
    # 1. retriever：把上一节入库的 Chroma 包成一个可调用的检索器
    vectorstore = Chroma(
        persist_directory=str(settings.chroma_persist_dir),
        embedding_function=get_embedding(),
        collection_name="basic_rag",
    )
    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

    # 2. prompt：用 ChatPromptTemplate 留出 {context} 和 {question} 两个槽位
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "你是严谨的问答助手。仅根据 <context> 中的内容回答问题。"
                "如果上下文里没有相关信息，请明确回答「资料中未提及」，不要编造。\n\n"
                "<context>\n{context}\n</context>",
            ),
            ("human", "{question}"),
        ]
    )

    # 3. llm：DeepSeek
    llm = get_llm(temperature=0.0)

    # 4. ★ LCEL 拼装 —— 这一行是整节课的灵魂
    #    左边的 dict 等价于 RunnableParallel：同时跑两路
    #    - "context": 用户问题 → retriever → format_docs → 字符串
    #    - "question": 用户问题 → 直通（RunnablePassthrough）
    #    然后把这个 dict 灌进 prompt → llm → 解析为字符串
    chain = (
        {
            "context": retriever | format_docs,
            "question": RunnablePassthrough(),
        }
        | prompt
        | llm
        | StrOutputParser()
    )
    return chain


def main() -> None:
    chain = build_chain()

    # 命令行参数当问题，没传就用默认问题
    question = " ".join(sys.argv[1:]) or "请用一句话总结这些文档的核心主题。"

    print(f"❓ 问题：{question}\n")
    print("💡 回答：")
    # 用流式输出，看着 token 一个个吐出来更有感觉
    for chunk in chain.stream(question):
        print(chunk, end="", flush=True)
    print("\n")


if __name__ == "__main__":
    main()
