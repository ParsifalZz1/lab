# GOAL.md

# ModelFlow Project Goal

Version: v1.0

Status: Active

---

# Project

**ModelFlow：基于模型互联网的动态混合 DAG 调度引擎（Dynamic Hybrid DAG Scheduling Engine for Model Internet）**

ModelFlow 是一个面向模型互联网（Model Internet）的智能调度框架。

系统以一个高能力"首脑模型（Brain Model）"作为全局调度中心，根据用户输入自动完成任务分析、任务拆解、DAG 构建、节点调度、并发执行、串并联协作和结果聚合。

项目目标不是构建一个新的大模型，而是构建一套能够管理多个异构模型节点协同工作的调度系统，使模型互联网真正成为一个可调度、可扩展、可并发执行的计算网络。

---

# Mission

构建一个能够自动协调多个模型节点协同工作的动态混合 DAG 调度引擎。

系统能够：

- 自动理解自然语言任务
- 自动分析任务依赖关系
- 自动生成 DAG
- 自动选择模型节点
- 自动调度执行策略
- 自动聚合最终结果
- 自动可视化整个调度过程

最终形成一个适用于模型互联网的通用调度框架。

---

# Vision

将模型互联网从：

> 多个模型简单协作

升级为

> 可调度、可编排、可扩展的分布式模型计算网络。

系统最终应支持：

- 大规模模型节点
- 异构模型能力管理
- 动态资源调度
- 多模型协同推理
- DAG任务编排
- 分布式执行
- 自动容错
- 实时可视化

---

# Core Objectives

整个项目围绕以下七个核心目标展开。

## Objective 1

实现自然语言任务自动拆解。

Brain Model 能够根据用户输入自动生成任务图，而不是依赖人工配置。

---

## Objective 2

构建标准化 DAG。

所有任务必须转换成统一 DAG 表示。

DAG 中每个节点必须包含：

- Task ID
- Dependency
- Execution Type
- Required Capability
- Input
- Output
- Timeout
- Retry Policy

---

## Objective 3

实现模型能力感知。

系统能够实时维护所有 Worker 的能力画像，包括：

- 模型类型
- 支持能力
- Token速度
- 最大上下文
- 当前负载
- 延迟
- 在线状态
- 可用性

调度必须依据能力画像完成，而不是随机选择节点。

---

## Objective 4

实现动态混合调度。

系统能够根据任务类型自动决定：

- Parallel
- Serial
- Committee
- Review
- Reduce

不同执行策略。

---

## Objective 5

实现高并发执行。

对于不存在依赖关系的 DAG 节点：

必须：

- 同时调度
- 同时执行
- 同时返回

整体耗时尽可能接近最长 Worker 的执行时间，而不是所有 Worker 时间之和。

---

## Objective 6

实现统一结果聚合。

所有 Worker 返回统一 JSON。

Brain Model 完成：

- 去重
- 排序
- 合并
- 推理
- 最终回答生成

---

## Objective 7

实现可视化调度过程。

最终 Demo 必须能够展示：

- DAG生成
- 节点选择
- Worker状态
- 任务流转
- 执行时间
- 加速比
- 最终结果

让用户能够观察整个模型互联网运行过程。

---

# MVP

第一阶段（MVP）仅实现以下能力。

必须完成：

✅ Brain Model

✅ Scheduler

✅ Worker Registry

✅ DAG Generator

✅ Parallel Executor

✅ Result Reducer

✅ REST API

✅ Web Demo

MVP 不要求：

- 多模态
- 联邦学习
- 自动模型训练
- 强化学习优化调度

---

# Success Criteria

项目达到以下条件即可认为 MVP 成功。

功能目标：

- 能够自动生成 DAG
- 能够自动调度 Worker
- 能够自动聚合结果
- 能够展示实时执行过程

性能目标：

- 支持至少 8 个 Worker
- 支持动态节点加入
- 支持失败重试
- 支持超时处理
- 支持并发执行

展示目标：

- 能展示动态拓扑图
- 能展示 DAG
- 能展示任务流
- 能展示节点状态
- 能展示耗时统计
- 能展示加速比

---

# Current Stage

当前项目阶段：

Phase 1

Concept Verification（PoC）

当前重点：

- 完成整体架构设计
- 完成核心模块设计
- 完成接口规范
- 完成调度流程
- 完成系统开发

暂未进入：

- 调度算法优化
- Benchmark优化
- 大规模集群部署

---

# Design Principles

整个项目开发过程中必须遵循以下原则。

## Principle 1

Brain Model 只负责调度。

不要让 Brain 完成所有推理。

---

## Principle 2

Worker 尽可能简单。

每个 Worker 只完成一个明确任务。

---

## Principle 3

所有通信必须结构化。

禁止自由文本通信。

统一 JSON Schema。

---

## Principle 4

所有模块必须低耦合。

模块之间只能通过接口通信。

禁止直接共享状态。

---

## Principle 5

所有功能均应支持未来扩展。

新增：

- Worker
- 调度算法
- 推理策略
- 模型类型

不应影响已有架构。

---

# Non Goals

当前阶段明确不开发以下内容。

- 新的大语言模型
- 模型训练框架
- 参数微调系统
- 模型蒸馏
- RLHF
- 联邦学习
- 多模态训练
- 分布式训练平台

本项目仅关注：

模型互联网中的任务调度。

---

# Agent Instructions

所有 Agent 在开发过程中必须遵循以下要求。

始终优先：

1. 保持系统架构一致性。

2. 保持模块职责单一。

3. 优先保证接口稳定。

4. 优先保证代码可扩展。

5. 不允许为了实现局部功能破坏整体架构。

任何新增功能，都必须符合：

ModelFlow → Brain → DAG → Scheduler → Worker → Reducer

这一整体执行流程。

所有开发任务均应围绕本 GOAL.md 展开。

如果需求与 GOAL.md 冲突，应优先遵循 GOAL.md。