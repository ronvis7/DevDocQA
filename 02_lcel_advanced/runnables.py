"""第 2 节 · Runnable 三大件

把这三个搞透，LCEL 链你就能任意拼装：
    - RunnablePassthrough：原样透传
    - RunnableParallel   ：多路并发，结果合成 dict
    - RunnableLambda     ：把任意 Python 函数变成 Runnable

读完后看 01_basic_rag/query.py 的链，应该能逐位指出每一段是什么 Runnable。
"""

from __future__ import annotations

from langchain_core.runnables import RunnableLambda, RunnableParallel, RunnablePassthrough

from shared import get_llm


def demo_passthrough() -> None:
    print("=" * 60)
    print("① RunnablePassthrough —— 原样透传，常用于把"原始输入"塞进 dict 的某一格")
    print("=" * 60)
    chain = RunnablePassthrough()
    print(chain.invoke("hello"))  # → "hello"
    # 也可以"透传 + 加字段"：assign 在原 dict 上追加
    enriched = RunnablePassthrough.assign(upper=lambda x: x["text"].upper())
    print(enriched.invoke({"text": "hello"}))
    # → {"text": "hello", "upper": "HELLO"}


def demo_parallel() -> None:
    print("\n" + "=" * 60)
    print("② RunnableParallel —— 同时跑多路，结果合成 dict")
    print("=" * 60)

    llm = get_llm()

    # 一次问 LLM 两个角度（情感 + 摘要），并发执行
    parallel = RunnableParallel(
        sentiment=lambda x: llm.invoke(f"用一个词描述这句话的情感：{x}").content,
        summary=lambda x: llm.invoke(f"用十个字以内概括：{x}").content,
    )
    result = parallel.invoke("今天股市暴跌，但我觉得是难得的抄底机会。")
    print(result)
    # → {"sentiment": "...", "summary": "..."}


def demo_lambda() -> None:
    print("\n" + "=" * 60)
    print("③ RunnableLambda —— 任意函数 → Runnable")
    print("=" * 60)

    # 把普通函数包成 Runnable 后，就能用 | 串到链里
    word_count = RunnableLambda(lambda text: {"text": text, "len": len(text)})
    chain = word_count | RunnableLambda(lambda d: f"{d['text']!r} 长度 = {d['len']}")
    print(chain.invoke("LangChain Expression Language"))


def main() -> None:
    demo_passthrough()
    demo_parallel()
    demo_lambda()


if __name__ == "__main__":
    main()
