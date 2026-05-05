"""第 5 节 · 用 LangGraph create_react_agent 替换 LCEL 链

到这里，把第 1+3 节的检索都包成 tool，丢给一个 ReAct Agent。
LLM 会**自主决定**：

    - 这个问题需要先看原文片段（vector_search）？
    - 还是直接查关系（graph_search）？
    - 还是两个都要调？调几次？

这就是 Yuxi 的范式 —— 区别只是 Yuxi 的 chatbot/graph.py 还堆了一打 middleware。
"""

from __future__ import annotations

import sys

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import create_react_agent

from shared import get_llm

from .tools import graph_search, vector_search


SYSTEM_PROMPT = """你是知识助手。回答问题前请先调用工具检索。
工具选择策略：
- 关系类问题（A 的师父 / A 和 B 的关系）→ 优先 graph_search
- 描述类问题（介绍 X / 为什么 X）→ 优先 vector_search
- 复杂问题 → 两者结合，可多次调用

回答时：
1. 必须基于工具返回的内容，不要编造
2. 在结论后用方括号注明来源类型，如 [片段] 或 [图谱]
3. 工具如果没命中，直接告诉用户"资料中未提及"
"""


def build_agent():
    return create_react_agent(
        model=get_llm(temperature=0.0),
        tools=[vector_search, graph_search],
        prompt=SYSTEM_PROMPT,
        checkpointer=InMemorySaver(),  # 内存版即可，重启就丢
    )


def main() -> None:
    agent = build_agent()
    question = " ".join(sys.argv[1:]) or "孙悟空和唐僧之间是什么关系？详细介绍一下他们。"
    config = {"configurable": {"thread_id": "demo"}}

    print(f"❓ 问题：{question}\n")
    print("🤖 Agent 执行轨迹：\n")

    # stream_mode='values' 会在每次 state 变更时吐出当前完整 state
    for step in agent.stream(
        {"messages": [HumanMessage(content=question)]},
        config=config,
        stream_mode="values",
    ):
        last = step["messages"][-1]
        if last.type == "ai" and getattr(last, "tool_calls", None):
            for tc in last.tool_calls:
                print(f"  🔧 调用工具 {tc['name']}({tc['args']})")
        elif last.type == "tool":
            preview = last.content[:120].replace("\n", " ")
            print(f"  ⤴ 工具返回：{preview}{'...' if len(last.content) > 120 else ''}")
        elif last.type == "ai":
            print(f"\n💡 最终回答：\n{last.content}")


if __name__ == "__main__":
    main()
