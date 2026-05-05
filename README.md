# DevDocQA

[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org)
[![LangChain](https://img.shields.io/badge/LangChain-1.2+-green.svg)](https://github.com/langchain-ai/langchain)
[![LangGraph](https://img.shields.io/badge/LangGraph-1.0+-purple.svg)](https://github.com/langchain-ai/langgraph)
[![Gradio](https://img.shields.io/badge/Gradio-5-orange.svg)](https://gradio.app)
[![License](https://img.shields.io/badge/license-MIT-lightgrey.svg)](LICENSE)
[![tests](https://github.com/ronvis7/DevDocQA/actions/workflows/test.yml/badge.svg)](https://github.com/ronvis7/DevDocQA/actions/workflows/test.yml)

> 基于 LangChain + RAG + 知识图谱的技术文档智能问答系统

面向开发者的日常查询场景：把 React、Vue、FastAPI 等主流框架的官方文档丢进去，用自然语言提问，系统自动检索最相关的内容并给出答案。

---

## 项目概述

作为开发者，查文档是最高频的操作之一。但传统搜索只能做关键词匹配，搜"useEffect 的依赖数组怎么用"往往返回一堆不相关页面。DevDocQA 通过 **向量语义检索 + 知识图谱关系查询** 双路融合，理解你的真实意图，精准定位文档片段。

### 技术亮点

- **LangChain LCEL 管道**：`retriever | prompt | llm | parser` 一行链组合，清晰可读
- **双路融合检索**：向量召回（语义相似）+ 图谱查询（实体关系），并发执行
- **LangGraph ReAct Agent**：从预定义管道升级到 LLM 自主决策调用哪个检索工具
- **结构化知识抽取**：`with_structured_output` 从文档中自动抽取技术概念间的关系
- **流式输出**：token 级实时响应，打字机效果

### 技术栈

| 维度 | 选型 | 说明 |
|:---|:---|:---|
| LLM | DeepSeek v4 | OpenAI 兼容协议，性价比高 |
| Embedding | BAAI/bge-small-zh-v1.5（本地） | 中文友好，无需额外 API Key |
| 向量库 | Chroma | 零配置，本地持久化 |
| 知识图谱 | Neo4j + Cypher | 行业标准图数据库 |
| Agent 框架 | LangGraph | ReAct Agent，工具自主调度 |
| UI | Gradio | 一键启动，5 个 Tab 展示全链路 |

---

## 快速开始

```bash
cd DevDocQA

# 1. 配置
copy .env.example .env
# 编辑 .env，填入 DEEPSEEK_API_KEY

# 2. 安装依赖
uv sync

# 3. 启动 Neo4j（第 3 步起需要）
docker compose up -d neo4j

# 4. 构建向量索引
uv run python 01_basic_rag/ingest.py

# 5. 基础问答测试
uv run python 01_basic_rag/query.py "React 中 useEffect 的依赖数组怎么用？"

# 6. 构建知识图谱
uv run python 03_knowledge_graph/extract.py
uv run python 03_knowledge_graph/load_to_neo4j.py

# 7. KG-RAG 融合问答
uv run python -m 04_kg_rag.chain "FastAPI 的依赖注入和 Pydantic 模型是什么关系？"

# 8. Agent 自主检索
uv run python -m 05_langgraph_agent.agent "React 和 Vue 在状态管理上有什么不同？"

# 9. 启动 Web UI
uv run python app.py   # 浏览器打开 http://localhost:7860
```

---

## 为什么做这个项目

**痛点**：开发者每天查文档，但传统全文搜索只做字面匹配——搜「useEffect 依赖数组怎么用」常常返回一堆只命中关键词、却答非所问的页面；跨框架问「React 和 Vue 状态管理有什么不同」更是无从下手。

**RAG 解决了一半**：把文档切块、嵌入、向量召回，能按语义找到相关片段，但**遇到关系型问题就很弱**——「FastAPI 依赖注入和 Pydantic 模型是什么关系」这种问题，向量检索拿不到「关系」这层信息。

**所以双路融合**：向量检索（RAG）擅长语义召回，知识图谱（KG）擅长实体关系召回，两者**并发执行 + 结果融合**才是技术文档场景的最优解。本项目用 `RunnableParallel` 实现并发，再交给 LLM 综合作答。

**为什么从 LCEL 一路演进到 Agent**：LCEL 管道是固定流水线（永远先检索再生成），Agent 让 LLM 自主决定「这个问题该用 vector / graph / 还是不需要检索」。本项目五层模块代表了从「死板管道」到「自主决策」的完整演进路径，便于读者对照学习 LangChain 的不同抽象层级。

**为什么不用 RetrievalQA**：LangChain 官方在 1.0 已将 `RetrievalQA` 标记 deprecated，新代码应直接用 LCEL pipe 语法。本项目所有链路均以 `retriever | format | prompt | llm | parser` 风格编写。

---

## 系统架构

```
┌─────────────────────────────────────────────────────┐
│                    Gradio UI                         │
│   Tab 1: 基础RAG | Tab 2: 流式 | Tab 3: NL→Cypher   │
│   Tab 4: KG-RAG融合 | Tab 5: ReAct Agent            │
└──────────────────────┬──────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
   ┌─────────┐   ┌──────────┐   ┌──────────┐
   │ LCEL 链 │   │ KG-RAG   │   │ LangGraph│
   │ 管道式  │   │ 融合链   │   │ Agent   │
   └────┬────┘   └────┬─────┘   └────┬─────┘
        │              │              │
   ┌────┴────┐   ┌────┴─────┐   ┌────┴─────┐
   │ Chroma  │   │ Chroma   │   │ vector_  │
   │ 向量检索 │   │ + Neo4j  │   │ search() │
   │         │   │ 并发检索  │   │ graph_   │
   │         │   │          │   │ search() │
   └─────────┘   └──────────┘   └──────────┘
```

### 五层递进设计

| 层 | 模块 | 核心能力 | LangChain 知识点 |
|:---|:---|:---|:---|
| 1 | `01_basic_rag/` | 文档→向量→问答 | LCEL 管道组合、RunnablePassthrough |
| 2 | `02_lcel_advanced/` | 流式、历史感知 | `.stream()`、RunnableWithMessageHistory |
| 3 | `03_knowledge_graph/` | 实体抽取→Neo4j | `with_structured_output`、Cypher |
| 4 | `04_kg_rag/` | 双路并发融合 | `RunnableParallel`、检索融合 |
| 5 | `05_langgraph_agent/` | ReAct 自主决策 | `create_react_agent`、tool 装饰器 |

---

## 项目结构

```
DevDocQA/
├── shared/                  # 跨模块复用：配置/LLM/Embedding/文档加载
├── 01_basic_rag/            # 基础 RAG：入库 + LCEL 问答
├── 02_lcel_advanced/        # 进阶：流式、多查询、历史感知
├── 03_knowledge_graph/      # 知识图谱：三元组抽取 → Neo4j
├── 04_kg_rag/               # KG-RAG 融合：向量+图谱并发检索
├── 05_langgraph_agent/      # LangGraph Agent：从管道到 Agent
├── data/tech_docs/          # 技术文档（React / Vue / FastAPI）
├── tests/                   # 测试用例
├── app.py                   # Gradio Web UI 总入口
├── docker-compose.yml       # Neo4j 容器
└── pyproject.toml           # 依赖管理
```

---

## License

MIT
