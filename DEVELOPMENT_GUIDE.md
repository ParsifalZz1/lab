# ModelFlow 开发指南

## 1. 推荐基线

本仓库尚未有既定技术栈。为尽快完成 PoC，推荐以下基线：

| 领域 | 推荐选择 | 理由 |
| --- | --- | --- |
| 后端 | Python 3.12 + FastAPI | 异步 HTTP、类型校验与 OpenAPI 适合控制面 API |
| Schema | Pydantic v2 | 与 JSON 协议和 FastAPI 直接对齐 |
| ORM/迁移 | SQLAlchemy 2 + Alembic | 支持 SQLite 开发与 PostgreSQL 演进 |
| 数据库 | SQLite 本地，PostgreSQL 部署 | 先降低启动成本，后满足并发与索引需求 |
| Worker 调用 | `httpx` + `asyncio` | 有界并发与 HTTP Adapter 简洁可测 |
| 事件流 | FastAPI SSE | Web Demo 只需单向实时事件 |
| 前端 | React + TypeScript + Vite | 适合状态密集的 Demo 与 DAG 可视化 |
| 测试 | pytest + httpx TestClient | 支持 API、异步与 Mock Worker 测试 |

这是推荐基线，不是领域架构的一部分。替换技术时必须保持现有 JSON 契约和状态语义。

## 2. 建议目录

```text
backend/
  app/
    api/            # HTTP 路由与请求响应模型
    domain/         # Run、DAG、Registry 的纯领域模型
    services/       # Orchestrator、Scheduler、Reducer
    adapters/       # DB、Worker HTTP、Brain、事件发布
    repositories/   # 持久化读写接口
    workers/        # Mock Worker 与真实 Worker Adapter
    main.py
  tests/
frontend/
  src/
    features/runs/
    features/topology/
    features/dag/
    api/
docs/
```

领域层不得导入 FastAPI、SQLAlchemy 或具体模型厂商 SDK。

Adapter 依赖领域接口，API 层依赖服务层；禁止反向依赖。

## 3. 配置

所有配置来自环境变量，并有 `.env.example` 说明默认开发值。

至少包含：`DATABASE_URL`、`REGISTRY_LEASE_SECONDS`、`REGISTRY_HEARTBEAT_SECONDS`、`EXECUTOR_MAX_CONCURRENCY`、`EVENT_RETENTION_HOURS` 与模型端点配置。

密钥只通过环境或密钥管理系统注入；日志和 API 响应不得输出密钥。

配置对象在启动时一次性校验，缺少关键配置时让服务快速失败。

## 4. 本地启动顺序

1. 创建虚拟环境并安装锁定依赖。
2. 复制 `.env.example` 为本地环境文件并设置开发数据库路径。
3. 执行数据库迁移。
4. 启动后端 API。
5. 启动 8 个可配置的 Mock Worker 或一个批量启动脚本。
6. 启动前端，并提交评论分析任务验证事件流。

具体命令在项目初始化时写入 `README.md`，保持可复制且与 CI 一致。

## 5. 代码约定

所有领域 ID、状态枚举、Schema 名称和错误码集中定义，禁止在路由或前端散落字符串。

所有跨边界函数接收和返回显式 DTO，不透传数据库对象或供应商 SDK 对象。

状态迁移集中放在领域服务中；API handler 与 Worker Adapter 不直接改写状态字段。

每个外部调用必须有超时、错误映射、`trace_id` 和结构化日志。

优先小而可测的函数，不在第一阶段引入通用插件框架。

## 6. 事件与日志

结构化日志至少携带 `trace_id`、`run_id`、`task_id`、`attempt_id` 和 `worker_id` 中可用字段。

领域事件是 Demo 和异步集成的依据；日志不是状态机的可靠来源。

大输入、结果原文和模型提示词默认不进日志，只记录长度、哈希和受控摘要。

调度选择必须记录候选数、淘汰原因、快照版本和最终理由。

## 7. 提交与变更节奏

每个提交聚焦一个可验证行为，例如“支持 Worker 租约过期”或“实现 DAG 环路校验”。

数据库迁移、领域模型、API 契约和测试应在同一变更中同步更新。

修改 `API_CONTRACT.md`、`EXECUTION_PROTOCOL.md` 或状态枚举时，必须更新对应契约测试。

不要把代码格式化、无关重构和行为修改混在一个提交中。

## 8. 首次实现顺序

第一天只完成 Phase 0 与 Phase 1：应用骨架、健康检查、数据库、Run/DAG/Task 数据模型和事件表。

第二天完成 Registry 和 8 个 Mock Worker，使节点可见且可租约过期。

第三天实现模板 DAG、Validator、最少活动任务调度和单层并发执行。

随后再做依赖推进、Reducer、API 事件流和前端，不要先接真实模型。

## 9. 开发完成检查

在标记一项任务完成前，确认：

- 对外对象是否有版本、稳定 ID 和 Schema。
- 状态是否只能沿合法状态机迁移。
- 超时、失败、取消和重试是否有明确行为。
- 日志和事件是否可关联到运行和节点。
- Mock Worker 是否能覆盖该功能的成功与失败路径。
- 文档和测试是否与代码一致。
