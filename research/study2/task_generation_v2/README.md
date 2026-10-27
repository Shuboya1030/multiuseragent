# Study 2：六个代表任务（v0.1）

依据 GitHub `5357f36` 的 `12_Study2_Task_Redesign_20261026-1923.md` §13。
范围：Must-help / Optional-help × Low / Medium / High，各一份。没有 Task Evaluator、任务评分器或模型实验。结构等级是设计标签，尚未经独立验证；不以成功率定义难度。

|模板|类别/等级|N|依赖深度|结构分数|核心工作|
|---|---|---:|---:|---:|---|
|m-low-ledger-allocation|Must / Low|4|1|0|为11月发票取得当前成本中心编码|
|m-medium-research-purchase|Must / Medium|8|2|5|当前研发席位决定金额与订单放行权限|
|m-high-service-cutover|Must / High|16|3|8|当前配置→运行就绪→跨冻结窗口的技术授权|
|o-low-campaign-asset|Optional / Low|4|1*|0|默认合法素材可用，营销持有活动专属素材|
|o-medium-event-package|Optional / Medium|8|1*|4|有效标准会务套餐之外，商业权益降低价格|
|o-high-training-schedule|Optional / High|16|1*|8|结合合同归属、培训权益与工时安排，调整班组、师资、时长和成本|

* Optional的深度仅记录，不参与其难度评分。四项分别为N、线索显著性、持有人推断、建议整合工作量。Must四项为N、依赖深度、知识权限分离、联系人推断。Medium采购存在金额条件，因此separation计2分，总分5。

## 使用与材料边界

每份 `templates/<id>/blueprint.json` 是事实唯一来源；`metadata.json` 是机器可读清单。`references/` 是设计者的公共信息路线与完整信息路线，并非执行结果。`tac/` 内只把公开材料和任务原文交给执行Agent；`scenarios.json`仅供NPC后端。不得把整个模板目录挂载给执行Agent。

同一blueprint导出R0、R1目录及simulator声明式包。R0保留真实职位；R1增加统一职责；其他业务材料完全一致。官方未提供的汇报线未杜撰。N表示相关目录及场景NPC数量，TAC其他账号仍然可见。

`simulator/task.json` 是v2声明式数据，不是旧模拟器的即插即用格式。包含私有记录、前置条件与输出契约；旧执行器需要另加adapter。本轮不创建模拟器运行引擎或评分器。

## 构建与部署检查

先在本目录：

```sh
docker build --platform linux/amd64 -f runtime/Dockerfile.base -t tac-study21-ungraded-base:v1 .
python tools/export_tasks.py
python tools/check_packages.py
python tools/deployment_smoke.py
```

检查脚本需要Python与jsonschema；部署需Docker、现有TAC OwnCloud和RocketChat服务。`deployment_smoke.py`会分别构建R0/R1，实际上传到各任务独立OwnCloud路径，并逐字节读取核对。最后留下R1材料；不启动NPC模型、不重置其他任务服务、不覆盖旧SecureScan路径。

官方基础镜像ONBUILD强制要求evaluator.py，因此本项目用外部镜像COPY复用其文件系统，不执行ONBUILD，显式恢复NPC环境变量，并移除评分入口。这是无评分构建变体，不是假评分器。不会调用官方eval.py。

## OpenHands接口与限制

任务镜像提供TAC常规的 `/instruction/task.md`、`/workspace`、`/npc/scenarios.json`、`/utils/populate_data.py`、`dependencies.yml`。执行目标是OpenHands CodeActAgent及真实浏览器/终端，不是之前定制的采购API工具。

**本轮未运行OpenHands，也未测试LLM NPC回复。** 实际部署结果见 `validation/deployment_checks.json`；不能将构建和文件读写成功称为完成rollout。

TAC现有 `evaluation/run_eval.sh` 把执行与评分耦合；本包不提供评分入口，不能直接套用后宣称全链路兼容。后续需一个明确的无评分执行适配：保留官方环境初始化、NPC启动、OpenHands任务执行与trajectory保存，跳过最后评分调用。需另行验证OpenHands运行时构建。此次不安装/执行付费Agent。

完整模型episode前应使用干净隔离服务：清空该episode历史、仅启动该任务NPC场景、加载所选R条件、记录模型及运行配置。不要在本批六份共享服务初始化状态上并行启动NPC，否则不同场景会互相污染。官方init.sh依赖2999 reset服务；本次已有本地服务未部署该管理服务，故仅使用任务级populate/readback验证，不宣称官方reset已通过。

## 未完成的独立质量检查

- 类别必要性、Optional收益与现实性、难度特征的独立复核。
- NPC拒绝、不完整上下文、转介、恢复等真实LLM行为。
- 公开职位及材料是否过度指向答案；高等级尚不能用单次运行证明。
- 人工审核及整个60任务集覆盖；本批不是完整60模板分布。
- 可选收益目前为设计中的结果差异（不是关键词评分）；没有实现评分函数。

六个任务为独立工作流，未强行配对；后续扩展时可自然生成配对版本，使用workflow_pair_id管理依赖。
