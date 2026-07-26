# ModelFlow 数据与事件设计

## 1. 目标

本文定义 MVP 的持久化实体、状态所有权、事件序列和恢复原则。

数据模型必须支持运行查询、可视化回放、失败重试和最终结果追溯。

数据库实现可从 SQLite 演进到 PostgreSQL，但领域字段与事件语义保持稳定。

## 2. 数据所有权

| 实体 | 权威写入者 | 说明 |
| --- | --- | --- |
| `Run` | Orchestrator | 用户任务的一次运行 |
| `DagSnapshot` | DAG Service | 已校验、不可变的图版本 |
| `TaskNode` | Orchestrator | DAG 节点的运行时状态 |
| `TaskAttempt` | Execution Coordinator | 一次实际 Worker 调用 |
| `Assignment` | Scheduler | 调度决定与依据 |
| `WorkerRecord` | Registry | 节点配置、能力和当前状态 |
| `Lease` | Registry | 节点租约与心跳序号 |
| `Artifact` | Reducer/Coordinator | 已验证的结构化结果或引用 |
| `DomainEvent` | Outbox | 追加式状态变化记录 |

跨模块可以读取这些实体的受控视图，但不能绕过权威写入者修改状态。

## 3. Run

```text
Run(
  run_id PK, tenant_id, request_id, idempotency_key,
  goal, input_ref, output_constraints,
  status, dag_version, degraded,
  created_at, updated_at, completed_at, failure_code
)
```

对 `(tenant_id, idempotency_key)` 建立唯一约束。

`goal` 可存脱敏摘要；大输入以 `input_ref` 指向受控对象存储。

`status` 只由 Orchestrator 按状态机更新。

## 4. DAG 与节点

```text
DagSnapshot(dag_id PK, run_id FK, version, definition_json, validation_summary, created_at)
TaskNode(task_id PK, run_id FK, dag_version, type, objective, depends_on_json,
         input_json, output_contract, required_capabilities_json,
         status, optional, priority, retry_policy_json, timeout_ms,
         ready_at, started_at, finished_at, winner_attempt_id)
```

`DagSnapshot.definition_json` 是审计来源，不允许在原版本原地更新。

`TaskNode` 是为执行和查询优化的投影，可从 Snapshot 重建。

对 `(run_id, status, priority)` 和 `task_id` 建立查询索引。

## 5. Assignment 与 Attempt

```text
Assignment(assignment_id PK, run_id FK, task_id FK, worker_id,
           registry_snapshot_version, reason_json, deadline_at, created_at)
TaskAttempt(attempt_id PK, assignment_id FK, run_id FK, task_id FK, worker_id,
            ordinal, idempotency_key, status, dispatched_at, started_at, finished_at,
            latency_ms, error_code, error_message, result_artifact_id)
```

同一 task 的 `ordinal` 递增且唯一。

Attempt 终态写入与 TaskNode 的获胜结果选择需要事务或比较交换保护。

`error_message` 只保留经过脱敏的诊断文本。

## 6. Worker、Capability 与租约

```text
WorkerRecord(worker_id PK, role, display_name, endpoint_json, capabilities_json,
             resources_json, location_json, failure_domain, status, version, updated_at)
Lease(lease_id PK, worker_id FK, sequence, issued_at, expires_at, last_seen_at)
WorkerMetric(worker_id, capability_key, observed_at, active_tasks, queue_depth,
             latency_ms, success, tokens_per_second)
```

Worker 的声明配置与短期指标分表保存，避免心跳频繁改写静态记录。

Registry 仅接受租约匹配且 `sequence` 更大的心跳。

对 `expires_at`、`status` 和 Capability 检索字段建立索引。

## 7. Artifact

```text
Artifact(artifact_id PK, run_id FK, task_id FK NULL, attempt_id FK NULL,
         kind, contract, content_json, object_ref, content_hash,
         source_metadata_json, created_at, expires_at)
```

小型结构化 JSON 可存在 `content_json`；大型文本、数据集和附件使用 `object_ref`。

`content_hash` 用于去重和重放校验。

`source_metadata_json` 至少记录 task、attempt、Worker、时间与置信度。

## 8. 事件存储

```text
DomainEvent(event_id PK, sequence, topic, aggregate_type, aggregate_id,
            run_id, task_id NULL, worker_id NULL, trace_id,
            payload_json, occurred_at, published_at)
```

`sequence` 对同一 run 单调递增，作为 SSE 的恢复游标。

事件写入与对应实体更新必须在同一数据库事务中完成，采用 Outbox 模式异步发布。

事件消费者按 `event_id` 幂等处理，不能假设至少一次投递不会重复。

## 9. 关键事件

| Topic | 触发条件 | 关键载荷 |
| --- | --- | --- |
| `run.created` | Run 已接受 | 状态、目标摘要 |
| `run.status_changed` | Run 状态变化 | 前后状态、原因 |
| `dag.created` | DAG 校验通过 | DAG 版本、节点数、拓扑深度 |
| `task.status_changed` | 节点状态变化 | 前后状态、task_id |
| `task.assigned` | Assignment 创建 | worker、理由、快照版本 |
| `attempt.finished` | attempt 终态 | 状态、时延、错误、Artifact |
| `worker.status_changed` | Worker 状态变化 | 前后状态、租约原因 |
| `result.ready` | 最终 Artifact 可读 | Artifact、降级标记 |

事件载荷要足以渲染 Demo，但不嵌入敏感原文或大对象。

## 10. 状态一致性

TaskNode 的状态推进使用条件更新，例如仅当当前状态为 `RUNNING` 时接受该 attempt 的成功回调。

重复回调、晚到回调和已取消 attempt 的结果必须被记录但不能重复推进下游。

下游依赖计数更新与 `READY` 事件写入必须原子化。

Run 终态只能在所有必需 TaskNode 达到终态后由 Orchestrator 写入。

## 11. 恢复策略

服务重启后扫描所有非终态 Run。

已成功且拥有 Artifact 的 TaskNode 不重复执行。

处于 `DISPATCHED`、`ACCEPTED` 或 `RUNNING` 的 attempt 按 deadline、Worker 租约和幂等键确认状态。

无法确认的 attempt 进入超时或可重试路径，不能假定成功。

事件投递失败不影响数据库状态；Outbox 发布器应从 `published_at IS NULL` 恢复。

## 12. 保留与脱敏

开发环境可保留完整调试数据，但不得使用真实敏感数据。

生产环境按租户策略设置 Run、Artifact、事件和指标的保留期。

日志、事件和错误信息默认仅记录输入摘要与内容哈希。

删除 Run 时应级联删除或失效其短期 Artifact 引用，并记录审计事件。

## 13. 最小迁移顺序

1. 建立 Run、DagSnapshot、TaskNode 与 Artifact。
2. 建立 WorkerRecord、Lease 与 WorkerMetric。
3. 建立 Assignment 与 TaskAttempt。
4. 建立 DomainEvent 与 Outbox 发布器。
5. 为查询、租约扫描、任务调度和 SSE 续接补充索引。

每项迁移需提供向前迁移和最小回滚说明，禁止依赖手工修改生产数据。
