"""DevDocQA · Gradio UI 总入口

5 个 Tab，演示完整 RAG + KG 链路：
  Tab 1: 基础 RAG（向量检索 + LLM）
  Tab 2: 流式输出
  Tab 3: 自然语言 → Cypher → 答案
  Tab 4: KG-RAG 融合（双路并发）
  Tab 5: ReAct Agent
"""

from __future__ import annotations

from importlib import import_module

import gradio as gr

basic_rag_chain = None
streaming_chain = None
nl_to_cypher_chain = None
kg_rag_chain = None
agent = None


def _safe_import_basic():
    global basic_rag_chain
    if basic_rag_chain is None:
        mod = import_module("01_basic_rag.query")
        basic_rag_chain = mod.build_chain()
    return basic_rag_chain


def _safe_import_streaming():
    global streaming_chain
    if streaming_chain is None:
        mod = import_module("02_lcel_advanced.streaming")
        streaming_chain = mod.build_chain()
    return streaming_chain


def _safe_import_nl2cypher():
    global nl_to_cypher_chain
    if nl_to_cypher_chain is None:
        from langchain_neo4j import GraphCypherQAChain, Neo4jGraph

        from shared import get_llm, settings

        graph = Neo4jGraph(
            url=settings.neo4j_uri,
            username=settings.neo4j_username,
            password=settings.neo4j_password,
            database=settings.neo4j_database,
        )
        nl_to_cypher_chain = GraphCypherQAChain.from_llm(
            cypher_llm=get_llm(temperature=0.0),
            qa_llm=get_llm(temperature=0.0),
            graph=graph,
            verbose=False,
            allow_dangerous_requests=True,
        )
    return nl_to_cypher_chain


def _safe_import_kg_rag():
    global kg_rag_chain
    if kg_rag_chain is None:
        mod = import_module("04_kg_rag.chain")
        kg_rag_chain = mod.build_chain()
    return kg_rag_chain


def _safe_import_agent():
    global agent
    if agent is None:
        mod = import_module("05_langgraph_agent.agent")
        agent = mod.build_agent()
    return agent


# ---------- Tab 处理函数 ----------


def fn_basic_rag(question: str):
    try:
        chain = _safe_import_basic()
        return chain.invoke(question)
    except Exception as e:
        return f"\u274c {type(e).__name__}: {e}\n\n\u63d0\u793a\uff1a\u5148\u8dd1 01_basic_rag/ingest.py \u5165\u5e93\u3002"


def fn_streaming(topic: str):
    try:
        chain = _safe_import_streaming()
        partial = ""
        for token in chain.stream({"topic": topic}):
            partial += token
            yield partial
    except Exception as e:
        yield f"\u274c {type(e).__name__}: {e}"


def fn_nl_to_cypher(question: str):
    try:
        chain = _safe_import_nl2cypher()
        result = chain.invoke({"query": question})
        return result["result"]
    except Exception as e:
        return f"\u274c {type(e).__name__}: {e}\n\n\u63d0\u793a\uff1a\u9700\u8981 Neo4j \u5df2\u542f\u52a8\uff0c\u4e14\u7b2c 3 \u8282 extract+load \u8dd1\u8fc7\u3002"


def fn_kg_rag(question: str):
    try:
        chain = _safe_import_kg_rag()
        return chain.invoke(question)
    except Exception as e:
        return f"\u274c {type(e).__name__}: {e}\n\n\u63d0\u793a\uff1a\u7b2c 1+3 \u8282\u90fd\u8981\u8dd1\u8fc7\u3002"


def fn_agent(question: str, history: list):
    try:
        from langchain_core.messages import HumanMessage

        a = _safe_import_agent()
        config = {"configurable": {"thread_id": "ui-thread"}}

        trace_lines = []
        last_ai = ""
        for step in a.stream(
            {"messages": [HumanMessage(content=question)]},
            config=config,
            stream_mode="values",
        ):
            msg = step["messages"][-1]
            if msg.type == "ai" and getattr(msg, "tool_calls", None):
                for tc in msg.tool_calls:
                    trace_lines.append(f"\U0001f527 {tc['name']}({tc['args']})")
            elif msg.type == "tool":
                preview = msg.content[:100].replace("\n", " ")
                trace_lines.append(f"\u2934 {preview}...")
            elif msg.type == "ai":
                last_ai = msg.content

        trace = "\n".join(trace_lines) if trace_lines else "\uff08\u672a\u8c03\u7528\u5de5\u5177\uff09"
        return last_ai, trace
    except Exception as e:
        return f"\u274c {type(e).__name__}: {e}", ""


# ---------- 界面布局 ----------

with gr.Blocks(
    title="DevDocQA \u00b7 \u6280\u672f\u6587\u6863\u667a\u80fd\u95ee\u7b54", theme=gr.themes.Soft()
) as demo:
    gr.Markdown(
        "# \U0001f4da DevDocQA\nLangChain + RAG + \u77e5\u8bc6\u56fe\u8c31 \u00b7 \u6280\u672f\u6587\u6863\u667a\u80fd\u95ee\u7b54\u7cfb\u7edf"
    )

    with gr.Tab("1. \u57fa\u7840 RAG"):
        gr.Markdown("LCEL 4 \u4ef6\u5957\uff1a`retriever | format | prompt | llm | parser`")
        q1 = gr.Textbox(
            label="\u95ee\u9898", value="React \u4e2d useEffect \u7684\u4f9d\u8d56\u6570\u7ec4\u600e\u4e48\u7528\uff1f"
        )
        out1 = gr.Textbox(label="\u7b54\u6848", lines=6)
        gr.Button("\u63d0\u95ee").click(fn_basic_rag, q1, out1)

    with gr.Tab("2. LCEL \u6d41\u5f0f"):
        gr.Markdown("\u6f14\u793a `.stream()` \u2014\u2014 token \u4e00\u4e2a\u4e2a\u5410\u51fa\u6765")
        q2 = gr.Textbox(
            label="\u4e3b\u9898",
            value="\u7528 100 \u5b57\u4ecb\u7ecd FastAPI \u7684\u4f9d\u8d56\u6ce8\u5165\u673a\u5236\u3002",
        )
        out2 = gr.Textbox(label="\u8f93\u51fa", lines=6)
        gr.Button("\u751f\u6210").click(fn_streaming, q2, out2)

    with gr.Tab("3. NL \u2192 Cypher"):
        gr.Markdown(
            "\u81ea\u7136\u8bed\u8a00 \u2192 Cypher \u2192 \u81ea\u7136\u8bed\u8a00\u7b54\u6848\uff08\u9700\u8981 Neo4j\uff09"
        )
        q3 = gr.Textbox(label="\u95ee\u9898", value="Vue \u4e2d\u6709\u54ea\u4e9b\u54cd\u5e94\u5f0f API\uff1f")
        out3 = gr.Textbox(label="\u7b54\u6848", lines=6)
        gr.Button("\u67e5\u8be2").click(fn_nl_to_cypher, q3, out3)

    with gr.Tab("4. KG-RAG \u878d\u5408"):
        gr.Markdown("\u5411\u91cf + \u56fe\u8c31 **\u5e76\u53d1**\u68c0\u7d22\uff0c\u878d\u5408\u56de\u7b54")
        q4 = gr.Textbox(
            label="\u95ee\u9898",
            value="FastAPI \u4e2d\u4f9d\u8d56\u6ce8\u5165\u548c Pydantic \u6a21\u578b\u662f\u4ec0\u4e48\u5173\u7cfb\uff1f",
        )
        out4 = gr.Textbox(label="\u7b54\u6848", lines=8)
        gr.Button("\u63d0\u95ee").click(fn_kg_rag, q4, out4)

    with gr.Tab("5. ReAct Agent"):
        gr.Markdown("LLM \u81ea\u4e3b\u51b3\u5b9a\u8c03\u7528\u54ea\u4e2a\u5de5\u5177")
        q5 = gr.Textbox(
            label="\u95ee\u9898",
            value="React \u548c Vue \u5728\u72b6\u6001\u7ba1\u7406\u4e0a\u6709\u4ec0\u4e48\u4e0d\u540c\uff1f",
        )
        out5 = gr.Textbox(label="\u7b54\u6848", lines=6)
        trace = gr.Textbox(label="\u5de5\u5177\u8c03\u7528\u8f68\u8ff9", lines=6)
        gr.Button("\u63d0\u95ee").click(fn_agent, [q5, gr.State([])], [out5, trace])


if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7860, inbrowser=True)
