# SecureScan 复杂任务：真实 TAC 服务试跑

2026-10-26（America/Vancouver）。这是独立工程 smoke，不属于旧 R0/R1，也不是新正式 R1。

## 已完成什么

已部署并实际运行 TAC 的 OwnCloud、RocketChat、MongoDB、Sotopia Redis 和官方任务容器。十名同事使用官方 Sotopia/RocketChat 运行器，实际回复由 `claude-haiku-5-5` 生成。执行 Agent 也使用该模型。**执行端是自定义原生工具/API harness，不是 OpenHands 浏览器基线**；未测浏览器导航和页面理解。

一次执行，14 次执行模型调用、3 次 NPC 模型调用、3 次联系人交互，28.85 秒（仅 episode，不包括部署）；费用估计 **$0.0077938**，不是账单。没有重新运行模型以获得成功结果。

原始 TAC 评分 **2/3**：流程及真实频道交付通过，严格 artifact 失败。唯一差异是 `EU-only processing` 与 `EU-only`。事后显式同义归一化后业务字段匹配；原始评分保持不变，不能称为预先冻结评分全通过。

入口：[完整试跑报告](runs/tac_haiku_20261026_01/rollout_report.md)、[原始 trace](runs/tac_haiku_20261026_01/trace.jsonl)、[业务答案](runs/tac_haiku_20261026_01/answer.json)、[TAC 原始评分](runs/tac_haiku_20261026_01/tac_evaluation.json)、[审计](runs/tac_haiku_20261026_01/completion_audit.json)。

## 任务结构

| 参数 | 本例 |
|---|---|
| 候选池 | 10名相关目录员工，均来自TAC原有角色 |
| 依赖深度 | 3个求助节点：当前需求 → 风险处置 → 采购授权 |
| 知识与权限 | separate；三节点由不同人负责 |
| 强干扰项 | 3：低额度权限、过期事实、其他团队范围 |
| 推断 | 查文档并组合当前需求、数据类别、控制要求及金额门槛 |
| 结构难度 | 保守计9/10，高难度；不按模型是否成功倒推难度 |

旧试用数据为18席×$480=$8,640；真实需求为24席×$480=$11,520。后者超过技术部门$10,000授权上限，必须推断到财务权限。任务描述没有点名应联系哪个人，也没有给出正确席位、预算或授权编号。

三位有效联系人：Wang Fang掌握当前分配；Liu Qiang负责跨团队风险审查；David Wong负责超出部门限额的支出。Sarah Johnson是低额度权限干扰，Mike Chen持有过期试用事实，Li Ming仅负责Database团队。

**N 的边界：**10表示相关目录及已配置的NPC池，未删除TAC其他账户。服务中能枚举到更多账户，不等同“只能联系十个人”。本次池外联系为0。以后做候选规模实验必须预先选择目录规模还是技术访问限制，不能混用。

## 构建与复现

- 单一数据蓝图：`design/blueprint.json`。`design/export_task.py`生成文档与Sotopia场景；评分器和运行适配代码是单独人工实现，尚非通用任务生成器。
- TAC包：`tac_package/`，已用官方task-base-image:1.0.0在linux/amd64模式构建成功；包含task.md、checkpoints、scenarios、dependencies、Dockerfile、Makefile、populate_data及evaluator。
- 官方源代码提交见运行input_manifest。基础镜像自带ONBUILD流程加密评分器；执行模型不接收gold、scenarios或评分代码，也没有任意文件/终端访问工具。
- `runtime/compose.yml`来自TAC官方配置，仅启动任务所需服务。未启动GitLab、Plane、Collabora；本例只读Markdown，因此无需Office编辑器。端口仅绑定本机。
- 官方数据库从servers-api-server镜像恢复，官方Redis population加载员工；Sotopia策略保持LLM角色扮演，不换成确定性同事。
- Sotopia旧版只接OpenAI格式，本地`llm_bridge.py`转发到Anthropic。它不实现同事决策规则；禁用官方Sotopia末尾无关的额外LLM评分。修改后的server模块保留在runtime中，源项目MIT许可见下方链接。
- 上游launcher会打印密钥，因此使用`launch_npcs.py`传环境变量并把含登录会话的原始NPC日志留在容器私有目录，不上传。脱敏LLM请求、可见响应与usage完整保存在运行目录；不保存私有推理文本。
- `runtime/run_agent.py`通过真实服务API列目录、读文件、发/读私信、写容器工作区文件、发布频道消息。工具接口及实际请求都在run_manifest/api_io中。不是官方OpenHands配置，不能与浏览器基线直接作能力比较。
- Docker Desktop 4.97.0，Engine29.9.2；宿主ARM64，任务与服务使用官方x86镜像兼容执行。主机8GiB，Docker约4GiB。

离线审计：`python runtime/audit_run.py`；离线边界检查：`python design/test_evaluator.py`。不要盲目再次执行`run_agent.py`：默认同一run目录会追加日志；新实验应冻结新run_id并重置隔离服务。

模型成本按已核对的Haiku≤100k输入价格：$0.10/M输入、$0.50/M输出。本轮是当前已配置三模型中最低成本方案；不是对全市场模型的最低价保证。[官方价格](https://www.anthropic.com/claude/haiku)。

## 还不能启动整批新R1的原因

1. 本次只验证成功路径，未覆盖真实NPC拒绝、误授权、错误顺序与修复；132个离线边界用例不能替代这些对话。
2. 修订格式等价规则并在下一版本采集前冻结，原样保留本次2/3。
3. 评分器的token匹配仍可能在否定句、转述或伪造上下文中误判；正式版需要针对性测试，不能只认授权编号。
4. 两名人工可解性/现实性审核和整个任务集泄漏审查尚未完成；不得声称所有新设计gate通过。
5. 一条高结构复杂度任务成功不代表任务太简单，也不证明候选规模或深度有统计效应。不按成功率调难度。
6. 如果论文目标包含TAC浏览器操作，需要再验证OpenHands浏览器轨；本轮服务API轨已清楚标注。

建议下一步先冻结v0.2评分及NPC边界用例，再决定一个小型TAC验证集合，最后才讨论整批Study2.1 R1。没有启动任何整批采集。

来源：[用户重设计文档](../../../../12_Study2_Task_Redesign_20261026-1259.md)、[TAC官方MIT项目](https://github.com/TheAgentCompany/TheAgentCompany)、[评测机制](https://github.com/TheAgentCompany/TheAgentCompany/blob/main/docs/EVALUATION.md)。本任务业务数据为新构造；人员角色沿用TAC。
