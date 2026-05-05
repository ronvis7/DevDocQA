"""第 2 节 · 带对话历史的 RAG 链

挑战：用户后续问"那他呢？"时，retriever 不知道"他"是谁，召回会跑偏。
做法：先用 LLM 把"对话历史 + 当前问题"改写成一个独立问题，再去检索。

这是生产级 RAG 系统标配的一步，叫"history-aware retriever / question rewriter"。
"""

from __future__ import annotations

from langchain_chroma import Chroma
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableLambda

from shared import get_embedding, get_llm, settings

# ① 改写链：历史 + 当前问题 → 独立问题
rewrite_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "下面是用户与助手的对话历史，以及用户的最新提问。"
        "请把最新提问改写为一个**脱离上下文也能理解**的独立问题。"
        "只输出改写后的问题，不要输出多余内容。",
    ),
    MessagesPlaceholder("history"),
    ("human", "{question}"),
])


def build_chain():
    llm = get_llm(temperature=0.0)
    rewrite_chain = rewrite_prompt | llm | StrOutputParser()

    vectorstore = Chroma(
        persist_directory=str(settings.chroma_persist_dir),
        embedding_function=get_embedding(),
        collection_name="basic_rag",
    )
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

    def format_docs(docs):
        return "\n\n".join(d.page_content for d in docs)

    qa_prompt = ChatPromptTemplate.from_messages([
        ("system", "根据 <context> 回答用户问题。\n\n<context>\n{context}\n</context>"),
        MessagesPlaceholder("history"),
        ("human", "{question}"),
    ])

    # ② 完整链：先改写 → 检索 → 拼上下文 → 带历史问答
    chain = (
        RunnableLambda(lambda x: {
            "history": x["history"],
            "question": x["question"],
            "standalone": rewrite_chain.invoke({"history": x["history"], "question": x["question"]}),
        })
        | RunnableLambda(lambda x: {
            "history": x["history"],
            "question": x["question"],
            "context": format_docs(retriever.invoke(x["standalone"])),
            "_standalone": x["standalone"],  # 调试用
        })
        | RunnableLambda(lambda x: (print(f"  [改写为] {x['_standalone']}"), x)[1])  # 打印改写结果
        | qa_prompt
        | llm
        | StrOutputParser()
    )
    return chain


def main() -> None:
    chain = build_chain()
    history: list = []

    rounds = [
        "孙悟空是谁？",
        "他的师父是谁？",        # ← 这里"他"必须靠改写才能检索到
        "他们师徒一共去过几个国家？",
    ]

    for q in rounds:
        print(f"\n❓ 用户：{q}")
        answer = chain.invoke({"history": history, "question": q})
        print(f"💡 助手：{answer}")
        history.extend([HumanMessage(content=q), AIMessage(content=answer)])


if __name__ == "__main__":
    main()
