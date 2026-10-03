# AutoDev Core v0.1 Architecture

## Agent Loop

目标闭环是 `ANALYZE -> PLAN -> EXECUTE -> VERIFY -> REFLECT -> RETRY -> FINISH`。当前 Agent 每轮要求 Provider 返回一个 JSON 动作（plan、tool 或 finish），执行后把结果写回状态，并受 `max_iterations` 限制；状态机比一个无界 `while true` 更容易解释、测试和恢复。

## Tool System

工具实现 `Tool` 抽象接口，输入是 JSON 可序列化参数，输出是结构化 `ToolResult`。文件工具通过 `ToolContext.repository_root` 做 `resolve()` 后的 root containment 检查，避免目录穿越。修改通过 `edit_file` 记录 modified files，最终由 `git_diff` 审阅。

## Sandbox

`run_command` 只委托给 `DockerRunner`；runner 接受 timeout、工作目录和资源限制，并返回 stdout、stderr、exit code。当前默认关闭网络、限制 CPU/内存/PID、丢弃 Linux capabilities，并启用 no-new-privileges。模型生成的命令不应直接交给宿主 shell。

## State Model

`AgentState` 使用 Pydantic model，包含 task、repository_path、current_phase、plan、iteration、max_iterations、tool_history、modified_files、last_command_result、test_result、final_status。显式 Enum 使日志和测试稳定。

## Provider abstraction

Agent 只依赖 `LLMProvider` 协议。`OpenAICompatibleProvider` 通过 `LLM_BASE_URL`、`LLM_API_KEY`、`LLM_MODEL` 配置，便于替换兼容服务。provider 层负责 HTTP，不负责仓库修改。

## Logging

每次 run 写 JSONL 事件：run_id、timestamp、phase、LLM/tool call、参数、结果摘要、iteration、成功状态。敏感配置不会被序列化；后续可补充精确耗时字段。

## Benchmark

`benchmarks/cpp_bug_001` 是最小 CMake + CTest 项目。故意的整数除法 bug 让初始测试失败；修复后全部测试通过，作为 AutoDev 第一条端到端演示。

## Why this shape

本版本没有引入 LangChain、数据库或多 Agent：这些会隐藏核心控制流，增加面试解释成本。小型的显式接口允许后续替换 provider、sandbox 和日志存储，而不改变 Agent 状态模型。
