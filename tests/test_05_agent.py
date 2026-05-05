"""第 5 节：Agent 与 tool 的结构测试。"""

from __future__ import annotations


def test_tools_are_decorated():
    from importlib import import_module

    mod = import_module("05_langgraph_agent.tools")
    # @tool 装饰后会有 .name 和 .description 属性
    assert mod.vector_search.name == "vector_search"
    assert mod.graph_search.name == "graph_search"
    assert mod.vector_search.description
    assert mod.graph_search.description


def test_agent_constructs():
    from importlib import import_module

    mod = import_module("05_langgraph_agent.agent")
    agent = mod.build_agent()
    assert agent is not None
    # ReAct agent 编译完是一个 CompiledStateGraph
    assert hasattr(agent, "stream")
    assert hasattr(agent, "invoke")
