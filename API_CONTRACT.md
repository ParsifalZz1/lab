# ModelFlow API 契约

## 1. 范围与原则

本文定义控制平面对客户端、Web Demo 和 Worker 的 HTTP 接口。

所有路径以 `/v1` 开头；不兼容变更必须通过新版本发布。

用户任务运行 API 与 Worker Registry API 使用不同授权范围。

请求和响应均使用 `application/json`，事件流使用 `text/event-stream`。

除下载大对象外，所有对象均使用 JSON 引用而非二进制内联。

## 2. 通用约定

每个请求可带 `X-Request-Id`；未提供时服务端生成并在响应中返回。

服务端为每条运行生成 `run_id`，并将其写入后续事件和日志。

创建运行请求支持 `Idempotency-Key`；同一调用方与键返回同一资源或冲突错误。

时间使用 RFC 3339 UTC 字符串，持续时间使用毫秒整数。

资源 ID 是不透明字符串，客户端不得从中推断实现细节。

## 3. 通用响应

成功响应直接返回资源对象，列表响应使用 `items` 与 `next_cursor`。

错误响应采用下列格式：

```json
{
  "error": {
    "code": "DAG_VALIDATION_FAILED",
    "message": "DAG contains a cycle",
    "details": [{"path": "nodes[3].depends_on", "reason": "cycle_detected"}],
    "trace_id": "trace_01J..."
  }
}
```

`message` 面向调用方，`details` 面向程序处理；二者均不得泄露密钥或内部堆栈。

## 4. 错误码

| HTTP | 代码 | 含义 |
| --- | --- | --- |
| 400 | `INVALID_REQUEST` | JSON、字段或查询参数无效 |
| 401 | `UNAUTHENTICATED` | 缺少或无效身份凭证 |
| 403 | `FORBIDDEN` | 调用方没有资源权限 |
| 404 | `NOT_FOUND` | 资源不存在或对调用方不可见 |
| 409 | `IDEMPOTENCY_CONFLICT` | 幂等键复用于不同请求 |
| 409 | `INVALID_STATE_TRANSITION` | 当前资源状态不允许操作 |
| 422 | `DAG_VALIDATION_FAILED` | 计划未通过 DAG 静态校验 |
| 429 | `RATE_LIMITED` | 租户、用户或节点配额耗尽 |
| 503 | `NO_ELIGIBLE_WORKER` | 当前没有满足硬约束的 Worker |
| 503 | `REGISTRY_UNAVAILABLE` | Registry 快照不可用或过期 |

## 5. 创建运行

`POST /v1/runs`

该接口只确认任务被接受，不同步等待模型完成。

```json
{
  "goal": "分析以下电商评论，归纳三个主要缺点并给出建议",
  "input": {
    "comments_ref": "dataset://review-demo-5000"
  },
  "output": {
    "format": "markdown_report",
    "language": "zh-CN"
  },
  "constraints": {
    "max_latency_ms": 60000,
    "max_cost": 10,
    "allow_degraded_result": true
  }
}
```

成功返回 `202 Accepted`：

```json
{
  "run_id": "run_01J...",
  "status": "RECEIVED",
  "created_at": "2026-07-26T14:00:00Z",
  "links": {
    "self": "/v1/runs/run_01J...",
    "events": "/v1/runs/run_01J.../events"
  }
}
```

`input` 可为小型内联 JSON 或受授权的数据引用；服务端必须拒绝二者同时缺失。

## 6. 查询运行

`GET /v1/runs/{run_id}`

响应应包含运行状态、当前 DAG 版本、进度、最终结果引用和降级信息。

```json
{
  "run_id": "run_01J...",
  "status": "EXECUTING",
  "dag_version": 1,
  "progress": {"total": 52, "succeeded": 34, "running": 8, "failed": 0},
  "result": null,
  "degraded": false,
  "created_at": "2026-07-26T14:00:00Z",
  "updated_at": "2026-07-26T14:00:13Z"
}
```

终态为 `SUCCEEDED`、`PARTIALLY_SUCCEEDED`、`FAILED` 或 `CANCELLED`。

## 7. 取消运行

`POST /v1/runs/{run_id}/cancel`

取消是幂等操作。服务端标记未开始节点为取消，并向活跃 attempt 发出取消请求。

响应 `202 Accepted`，返回最新运行快照。

已经完成的结果保留用于审计，但不得再激活下游节点。

## 8. 查询 DAG 与任务

`GET /v1/runs/{run_id}/dag` 返回冻结的 DAG Snapshot、版本和校验摘要。

`GET /v1/runs/{run_id}/tasks?cursor=&limit=` 返回节点运行状态、依赖、assignment 与 attempt 摘要。

`GET /v1/runs/{run_id}/tasks/{task_id}` 返回单节点的输入引用、结果、错误和完整 attempt 历史。

默认应脱敏输入内容；只有具备调试权限的调用方可以读取允许展示的原始字段。

## 9. 事件流

`GET /v1/runs/{run_id}/events`

客户端使用 SSE 接收实时事件，并可使用 `Last-Event-ID` 从上次事件序号续接。

事件格式：

```text
id: 184
event: task.status_changed
data: {"run_id":"run_01J...","task_id":"batch_03","from":"RUNNING","to":"SUCCEEDED","trace_id":"trace_01J..."}

```

最小事件集合包括 `run.status_changed`、`dag.created`、`task.status_changed`、`task.assigned`、`attempt.finished`、`worker.status_changed` 与 `result.ready`。

事件流只是展示和通知通道；查询接口才是资源状态的权威读取方式。

## 10. Registry 接口

下列接口仅供节点或管理员调用：

| 方法 | 路径 | 权限 | 说明 |
| --- | --- | --- | --- |
| `POST` | `/v1/registry/nodes` | `node:register` | 注册或更新节点 |
| `POST` | `/v1/registry/nodes/{id}/heartbeat` | `node:heartbeat` | 续租和上报负载 |
| `POST` | `/v1/registry/nodes/{id}/drain` | `node:drain` | 停止新分派 |
| `DELETE` | `/v1/registry/nodes/{id}` | `node:unregister` | 优雅注销 |
| `GET` | `/v1/registry/nodes` | `registry:read` | 查询候选节点 |

节点请求中的 `{id}` 必须与认证身份绑定的 `worker_id` 一致，管理员例外。

完整注册与心跳字段见 `MODEL_REGISTRY.md`。

## 11. 健康与观测接口

`GET /healthz` 用于进程存活检查，不查询外部依赖。

`GET /readyz` 用于就绪检查，应检查数据库、迁移版本及 Registry 读路径。

`GET /metrics` 仅暴露给受控监控网络，使用所选指标系统的格式。

健康检查不得创建 Run、消耗模型配额或泄露节点端点。

## 12. 鉴权基线

开发环境可使用静态开发令牌，并明确标记为仅本地用途。

生产接口至少区分 `user`、`node`、`operator` 三类主体。

Run 资源必须按租户和创建者授权；节点只能管理自身租约与状态。

模型供应商密钥只存在于服务端密钥存储或 Worker Adapter，不经 API 返回。

## 13. 兼容性规则

新增可选字段不破坏 `v1` 客户端。

删除字段、改变字段语义或改变状态枚举属于不兼容修改。

服务端应忽略未知可选响应字段，但拒绝未知的安全关键请求字段。

所有接口示例和集成测试必须与本文同步更新。
