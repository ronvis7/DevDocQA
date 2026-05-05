"""第 2 节 · 流式输出（同步 / 异步）

LCEL 的所有 Runnable 都自动支持 .stream() 和 .astream()。
"""

from __future__ import annotations

import asyncio

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from shared import get_llm


def build_chain():
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "你是 1 名优秀的中文写作老师。"),
            ("human", "{topic}"),
        ]
    )
    return prompt | get_llm(temperature=0.7) | StrOutputParser()


def sync_streaming() -> None:
    print("=== 同步流式 .stream() ===")
    chain = build_chain()
    for token in chain.stream({"topic": "用 100 字写一段关于秋天的散文。"}):
        print(token, end="", flush=True)
    print("\n")


async def async_streaming() -> None:
    print("=== 异步流式 .astream() ===")
    chain = build_chain()
    async for token in chain.astream({"topic": "用 100 字写一段关于冬天的散文。"}):
        print(token, end="", flush=True)
    print("\n")


def main() -> None:
    sync_streaming()
    asyncio.run(async_streaming())


if __name__ == "__main__":
    main()
