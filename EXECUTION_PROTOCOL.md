# ModelFlow 执行协议

## 1. 范围

本协议定义 Scheduler、Execution Coordinator、Worker Adapter 和 Worker 间的任务调用语义。

它不定义 DAG 生成规则，也不定义 Worker 的注册与负载查询。

所有对象均带 `protocol_version`，当前版本为 `v1`。

## 2. 设计原则

任务调用必须可追踪、可校验、有截止时间，并尽可能幂等。

Worker 只能执行明确的 TaskEnvelope，不能从隐式上下文猜测目标或依赖。

Coordinator 是 attempt 状态的权威写入者；Worker 只报告自身执行结果。

所有成功结果必须满足节点声明的 `output_contract`。

## 3. 标识与时间

每个请求必须包含 `run_id`、`task_id`、`attempt_id`、`assignment_id` 和 `trace_id`。

`task_id` 表示逻辑节点；同一节点的重试共享 `task_id`、使用不同 `attempt_id`。

`idempotency_key` 在同一 task 与 attempt 语义下稳定，用于抵御网络重放。

`deadline_at` 为绝对 UTC 时间，Worker 在到期前未完成时应停止并返回超时结果。

## 4. TaskEnvelope

```json
{
  "protocol_version": "v1",
  "run_id": "run_01J...",
  "task_id": "extract_batch_03",
  "attempt_id": "attempt_01J...",
  "assignment_id": "asgn_01J...",
  "trace_id": "trace_01J...",
  "idempotency_key": "sha256:...",
  "capability": {"name": "information_extraction", "version": "v1"},
  "objective": "从评论分片提取可验证的产品缺点和证据",
  "input": {"comments_ref": "artifact://input/batch-03"},
  "output_contract": "review_findings.v1",
  "execution": {
    "max_output_tokens": 300,
    "deadline_at": "2026-07-26T14:00:05Z",
    "attempt": 1,
    "priority": 50
  },
  "security": {"data_classification": "internal"}
}
```

`input` 必须是受 Schema 约束的 JSON 或短期可读取的受控引用。

任务不携带全局 DAG、其他 Worker 凭证或不相关的用户数据。

## 5. Worker 接收规则

Worker 收到 Envelope 后依次验证协议版本、身份、截止时间、能力、输入 Schema 与本地容量。

已处理的同一 `idempotency_key` 应返回既有终态结果或明确的进行中状态。

容量满时 Worker 返回 `REJECTED_OVERLOADED`，不得把请求无限期排队而不报告。

能力或输出契约不支持时返回 `REJECTED_UNSUPPORTED`。

Worker 接受任务后应尽快返回 `RUNNING` 回执，或在同步模式中由 Adapter 记录开始事件。

## 6. TaskResult

```json
{
  "protocol_version": "v1",
  "run_id": "run_01J...",
  "task_id": "extract_batch_03",
  "attempt_id": "attempt_01J...",
  "trace_id": "trace_01J...",
  "worker_id": "worker.cn-shanghai.jetson-03.extractor",
  "status": "SUCCEEDED",
  "started_at": "2026-07-26T14:00:01Z",
  "finished_at": "2026-07-26T14:00:03Z",
  "latency_ms": 2190,
  "output_contract": "review_findings.v1",
  "result": {
    "findings": [{"topic": "battery", "count": 17, "evidence": ["..."]}],
    "confidence": 0.84
  },
  "usage": {"input_tokens": 1220, "output_tokens": 246}
}
```

成功结果中的 `result` 必须能通过声明 Schema 验证。

Coordinator 对 `worker_id`、任务关联字段和时序进行二次校验，不能盲目信任远端响应。

## 7. 失败结果

失败、拒绝或取消使用相同对象，并省略 `result`：

```json
{
  "protocol_version": "v1",
  "run_id": "run_01J...",
  "task_id": "extract_batch_03",
  "attempt_id": "attempt_01J...",
  "trace_id": "trace_01J...",
  "worker_id": "worker.cn-shanghai.jetson-03.extractor",
  "status": "FAILED",
  "error": {
    "code": "OUTPUT_SCHEMA_INVALID",
    "message": "required field findings is missing",
    "retryable": true
  }
}
```

错误消息用于诊断，禁止包含原始敏感内容、访问令牌或模型内部提示词。

## 8. Attempt 状态

```text
CREATED -> DISPATCHED -> ACCEPTED -> RUNNING -> SUCCEEDED
                                      |            |
                                      v            v
                                   FAILED       REPORTED

DISPATCHED/ACCEPTED/RUNNING -> TIMED_OUT
DISPATCHED/ACCEPTED/RUNNING -> CANCELLED
DISPATCHED -> REJECTED
```

`REPORTED` 是 Coordinator 已持久化最终结果的内部状态。

一个 attempt 只能拥有一个终态结果；重复回调按 `attempt_id` 幂等忽略。

## 9. 错误分类

| 代码 | 默认可重试 | 说明 |
| --- | --- | --- |
| `NETWORK_UNAVAILABLE` | 是 | 传输层无法建立或中断 |
| `DEADLINE_EXCEEDED` | 是 | Worker 或 Coordinator 截止超时 |
| `REJECTED_OVERLOADED` | 是 | 节点当前无可用容量 |
| `WORKER_OFFLINE` | 是 | 租约失效或端点不可用 |
| `OUTPUT_SCHEMA_INVALID` | 视策略 | 输出无法通过契约校验 |
| `MODEL_EXECUTION_ERROR` | 视策略 | 底层推理异常 |
| `REJECTED_UNSUPPORTED` | 否 | 能力、版本或契约不支持 |
| `INPUT_SCHEMA_INVALID` | 否 | 调用方输入不合法 |
| `AUTHORIZATION_FAILED` | 否 | 身份或权限错误 |
| `CANCELLED` | 否 | run 或 task 被取消 |

节点的 RetryPolicy 可以收紧默认值，但不得把输入或权限错误自动无限重试。

## 10. 超时

Coordinator 在派发前将节点的 `timeout_ms` 转换为 `deadline_at`。

Worker 需要自行检查剩余时间；Coordinator 也必须在本地设置略长的传输保护超时。

超过 deadline 的晚到成功结果不得激活下游节点，除非 Coordinator 已明确接受该 attempt。

超时后优先选择不同 failure domain 重分配。

## 11. 重试与幂等

每次重试创建新的 `attempt_id` 和递增的 `execution.attempt`。

同一 attempt 的网络重放保持同一 `idempotency_key`。

Coordinator 只有在该 task 未有获胜终态且重试预算未耗尽时才创建新 attempt。

若多个推测 attempt 同时成功，最先完成且通过校验者获胜，其他结果标记为 `SUPERSEDED`。

## 12. 取消协议

取消请求包含 `run_id`、`task_id`、`attempt_id`、原因和 `trace_id`。

Worker 应停止可中断工作并返回 `CANCELLED`；无法中断的调用允许自然结束。

Coordinator 在发送取消后立即阻止该 attempt 的结果驱动下游状态。

取消操作幂等，未知或已终态 attempt 返回当前状态而不是报错。

## 13. 输出校验与规范化

Adapter 负责把供应商响应转换为 TaskResult，但不得自行猜测缺失业务字段。

Coordinator 在接收时验证 Envelope/Result 关联、状态、时间、Capability 和输出 Schema。

解析失败可由格式修复 Worker 处理；原任务的结果仍应记为失败或需要审查。

通过校验的结果写为不可变 Artifact，并以引用交给下游节点。

## 14. 安全与数据最小化

TaskEnvelope 只携带完成该任务所必需的数据和短期访问引用。

引用必须受 run、任务、租户和过期时间约束，Worker 不应能枚举其他 Artifact。

Worker 认证身份必须与 Assignment 中的 `worker_id` 一致。

任何日志采样都应默认排除 `input` 与 `result` 的原文。

## 15. PoC 适配要求

第一个 Mock Worker 使用 HTTP JSON 实现本协议，并可配置延迟、错误、格式错误和超时。

真实模型 Adapter 必须通过相同的契约测试，不能直接返回供应商私有格式。

PoC 先支持同步 HTTP；异步回调或队列模式必须保持相同字段与状态语义。
