# 第 5 节 · 从 LCEL 升级到 LangGraph Agent

## 这一节为什么存在

前 4 节我们写的 LCEL 链都是**固定流程**：每次都先检索、再生成。

但真实业务里：
- 简单问题不需要检索，多跑一次浪费 token
- 复杂问题可能要先 graph_search 找实体，再 vector_search 看上下文
- 用户多轮对话，第二轮可能不需要再检索

固定流程做不到"看情况"。**Agent** 范式让 LLM 自己决定什么时候调什么工具。

## 跑

```powershell
uv run python -m 05_langgraph_agent.agent "孙悟空的师父是谁？再介绍一下他师父。"
```

会看到 Agent 的执行轨迹（`🔧 调用工具 → ⤴ 工具返回 → 💡 最终回答`），
这就是 Yuxi 在线上跑的同一种模式。

## ★ 与 Yuxi 的对照（重要）

把 `agent.py` 和 Yuxi 的 `backend/package/yuxi/agents/buildin/chatbot/graph.py` 摆一起看：

| | 这里（mini-rag-kg） | Yuxi |
|---|---|---|
| 创建 Agent | `create_react_agent(model, tools, prompt, checkpointer)` | `create_agent(model, system_prompt, middleware, state_schema, checkpointer)` |
| Tools | 2 个：vector_search / graph_search | 3+N 个：list_kbs / get_mindmap / query_kb + MCP 工具 |
| Middleware | 无 | 9 个：FilesystemMiddleware / KnowledgeBaseMiddleware / SkillsMiddleware / RuntimeConfigMiddleware / SubAgentMiddleware / SummaryOffloadMiddleware / TodoListMiddleware / PatchToolCallsMiddleware / ModelRetryMiddleware |
| Checkpointer | InMemorySaver（重启即失） | AsyncPostgresSaver（持久化） |
| Prompt | 一段静态字符串 | `build_prompt_with_context(context)` 运行时动态生成 |

**结论**：Yuxi 不是用了什么不同的"魔法"，它是 `create_agent` + 一堆**中间件**。

中间件的作用：
- `RuntimeConfigMiddleware`：让前端能在每次对话动态切换 model / tools / system_prompt
- `SummaryOffloadMiddleware`：上下文超 90k tokens 自动压缩
- `KnowledgeBaseMiddleware`：注入 list_kbs / query_kb 这类知识库工具
- `SkillsMiddleware`：把"技能"提示词拼进 system_prompt
- `SubAgentMiddleware`：把子智能体当作工具暴露

读完本节再翻 Yuxi 那 9 个 middleware，应该感觉不那么神秘了 —— 它们都是
"在 model_call 前/后干一些事"，不影响核心范式。

## LCEL 还是 Agent，怎么选？

| 特征 | 选 LCEL | 选 Agent |
|---|---|---|
| 流程固定 | ✅ | |
| 性能要求高（更少 token） | ✅ | |
| 易于调试与回放 | ✅ | |
| 用户问题千变万化 | | ✅ |
| 工具可能不调用 / 多次调用 | | ✅ |
| 需要多步规划 | | ✅ |

**经验法则**：先 LCEL 写，写不下去了（要 if/else 决定走哪条路）再升 Agent。
