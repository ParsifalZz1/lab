# ModelFlow 测试与验收计划

## 1. 目标

测试覆盖协议正确性、DAG 正确性、故障恢复、并发行为和演示指标。

MVP 的自动化测试不得依赖真实模型密钥、外网或不稳定硬件。

真实模型测试属于受控集成验证，不替代 Mock Worker 的确定性测试。

## 2. 测试分层

| 层级 | 范围 | 运行频率 |
| --- | --- | --- |
| 单元测试 | 状态机、Schema、评分、Reducer | 每次提交 |
| 组件测试 | Registry、DAG Validator、Coordinator | 每次提交 |
| 集成测试 | API、数据库、SSE、Mock Worker | 每次合并 |
| 端到端测试 | 评论分析完整 Run | 每次发布候选 |
| 性能基准 | 串行与并行对比 | 演示前和性能变更后 |
| 真实模型验证 | Adapter 与结构化输出 | 手动或受控 CI |

## 3. Mock Worker 测试夹具

实现可参数化 Mock Worker，而不是在业务测试中伪造内部状态。

它必须支持：正常返回、固定延迟、随机但可设种子的延迟、超时、HTTP 失败、过载拒绝、错误 JSON、错误 Schema、重复回调和取消确认。

Mock Worker 必须按 `EXECUTION_PROTOCOL.md` 注册、心跳和返回 TaskResult。

每个测试应明确 Worker 数量、Capability、容量、延迟和失败脚本。

## 4. 必须的单元测试

- Run、TaskNode、Attempt 和 Worker 状态机拒绝非法迁移。
- DAG Validator 拒绝重复 ID、缺失依赖、自环、有向环和错误输入引用。
- 拓扑排序能正确计算多层 DAG 的 initial ready 集合。
- Capability 匹配拒绝版本、Schema、上下文窗口或地域不满足的 Worker。
- 负载评分和最少活动任务策略在固定输入下可复现。
- 重试策略仅对允许的错误创建新 attempt。
- Result Schema 验证能拒绝缺少必填字段的 Worker 输出。
- Reducer 对重复 Artifact 去重并保留所有来源元数据。

## 5. Registry 组件测试

- 注册后可按 role、Capability 和状态查询到节点。
- 乱序心跳不会覆盖更新的 lease sequence。
- 心跳缺失使节点依次进入 `SUSPECT` 与 `OFFLINE`。
- `DRAINING` Worker 完成存量任务但不接收新 Assignment。
- 容量满的 Worker 不被普通调度选择。
- 不同 failure domain 的候选可被冗余执行策略正确选择。

## 6. DAG 与调度组件测试

- 独立节点在配额允许时同时进入 `SCHEDULED`。
- 下游节点只有在所有 required 依赖成功后进入 `READY`。
- optional 上游失败时下游获得缺失对象并按图策略继续。
- 必需上游不可恢复失败时下游转为 `BLOCKED`。
- 不存在候选 Worker 时节点保持可重调度状态并产生明确错误事件。
- 超时 attempt 被重分配到其他 Worker，且旧结果不能获胜。
- 取消 Run 后不再产生新的 Assignment。

## 7. API 集成测试

- `POST /v1/runs` 校验请求并返回幂等的 `202` 资源。
- 同一幂等键配不同负载返回 `409 IDEMPOTENCY_CONFLICT`。
- Run、DAG、Task 和单 Task 查询遵循授权与脱敏规则。
- SSE 事件顺序随同一 run 单调递增，并可用 `Last-Event-ID` 续接。
- 不存在资源、非法状态取消和错误参数映射到文档规定的错误码。
- Registry 节点身份不能修改其他 `worker_id` 的状态。

## 8. 端到端主场景

输入：5000 条固定评论，分为 50 个 100 条批次。

配置：8 个同能力 Mock Worker，每个最大并发 1，固定 300 至 600 毫秒延迟。

断言：

- 系统生成包含 map/parallel、reduce、final_reduce 的合法 DAG。
- 至少 8 个批次在第一波并发启动。
- 所有批次返回统一 `review_findings.v1` 结果。
- 最终报告包含 Top 3 问题、代表证据和改进建议。
- 查询 API、SSE 时间线和最终 Artifact 的状态一致。

## 9. 故障注入场景

| 场景 | 预期行为 |
| --- | --- |
| 单 Worker 断连 | 租约过期后不再分派，新 attempt 选择其他节点 |
| 单次网络失败 | 在 retry budget 内重试并留下 attempt 记录 |
| Worker 超时 | 旧 attempt 失效，节点重分配或明确失败 |
| 输出格式错误 | Adapter/Coordinator 拒绝结果，按策略重试或失败 |
| 重复结果回调 | 仅第一个获胜结果推进状态 |
| Reducer 输入缺失 | 显式降级，最终结果带缺失说明 |
| 运行取消 | 未启动任务取消，活跃任务收到取消信号 |
| Registry 不可用 | 仅使用未过 TTL 的快照，否则不创建新 Assignment |

## 10. 性能基准

基准必须使用相同数据集、相同 Mock Worker 延迟模型和相同结果契约。

串行基线：一个 Worker 逐批处理所有输入。

并行方案：8 个 Worker 按同一 DAG 与调度策略处理。

记录：端到端耗时、规划耗时、排队时间、执行时间、归约时间、最大并发度、重试数与成功率。

报告加速比时，同时给出输入规模、Worker 数、节点延迟分布和失败情况。

不要把 Brain 规划时间或数据加载时间从任一方案中选择性排除。

## 11. 质量门槛

MVP 合并门槛：格式化和静态检查通过，受影响单元与组件测试通过。

发布候选门槛：端到端主场景、所有故障注入场景和 API 集成测试通过。

演示门槛：8 Worker 并行、超时重试、取消、DAG 可视化和最终结果均可重复展示。

性能门槛：并行方案在固定基准下应明确快于串行基线；具体数值以首次稳定测量后写入项目配置。

## 12. 回归原则

每个 bug 修复必须新增能在修复前失败的最小回归测试。

每个协议字段、错误码和状态变更都至少有一个正向和一个反向测试。

随机测试必须记录种子；涉及时间的测试使用可注入时钟，避免依赖真实等待。

性能测试结果不作为普通单元测试断言，以避免环境噪声造成 CI 不稳定。
