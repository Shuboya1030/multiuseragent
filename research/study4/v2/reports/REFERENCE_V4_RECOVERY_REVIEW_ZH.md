# Reference-v4：条件授权修复与无筛选的26＋214恢复边界

**本轮只做零API修正和核验，付费继续暂停。** 私有完成判定版本为
`study4-reference-completion-4`；公共协议2、模型、NPC、what、普通工具、限制和scorer未改。
这不是新实验结果或恢复批准，不发送POST/GET/probe，不读取key，不启动GPU。

本文件及[新版清单](REFERENCE_V4_AC26_FRESH214_20261112.json)替代
[上轮报告](REFERENCE_CONTRACT_REPAIR_ZH.md)中43候选/197fresh的**正式复用建议**。
原报告、[43候选审计](REFERENCE_REPAIR_REUSE_20261112.json)、52例实际轨迹、
原source/请求/分数/账本均保留，不把旧判断改写成从未发生。

## 1. 不再按B/D的随机回复筛选复用

原43候选中，B9/D8是否逐步等价依赖实际随机生成的回复。
即使不查看分数，保留这些通过者、重新抽样未通过者仍会选择轨迹，
不能作为无偏最终集的构造方式。本轮不再筛选或复用其中任何B/D。

采用协调者指定的固定整体：原13题的**全部A/C共26例**，不是逐例择优。
任何一个共享合同或请求核验失败，整组不获复用；没有“失败的A/C另抽一次”分支。

| 臂 | 整体保留旧完整例 | 必须fresh | 最终目标 |
|---|---:|---:|---:|
| A | 13 | 47 | 60 |
| B | 0 | 60 | 60 |
| C | 13 | 47 | 60 |
| D | 0 | 60 | 60 |
| 合计 | **26** | **214** | **240** |

实际核验通过：26例的**153个全部已记录模型请求**，包括NPC请求，
均由当前builder重建并逐一匹配原指纹。
共享runtime/任务包/组织/NPC与scorer绑定不变；
`phase0.py`除私有`reference_released`外的函数、类、常量和imports AST一致。
调度源码另核对reference调用只在B/D分支，A/C不执行私有完成判定。
因此不是仅凭臂名认定A/C不受影响。

52个原完整记录都核对原hash；receipt和journal精确SHA仍匹配原诊断，
旧九个历史根目录继承核验通过，公开52例压缩证据SHA未变。
旧43审计内容与提交`274c2426365244af80738cac0ce53b7e6a1172b6`一致；
该提交也保留旧审计工具及旧判定版本。
当前工具只核验固定A/C组，**不再对B/D重放决策或按轨迹等价筛选**。

清单保留原240目标slot的逻辑ID及顺序，删除26个已保留slot后恰为214项。
未来获批执行须使用独立新版本run/root命名空间，显式关联这些原目标；
不得打开旧run继续、读取旧settled响应当新抽样、复放旧工具或续接partial52。
原partial52的6个已settled调用仍计费但不计完整例。这里没有反事实前缀续跑。

## 2. 条件授权与撤回：先复现，再修复

全部以下fixture都先从原规格满足h1、L5/B5事实及授权请求上下文。
没有改变任务答案、gold、门或评分器来使测试通过。

| 公开回复/过程 | v3实际离线复现 | v4验收 |
|---|---|---|
| `If approved, authorization_ref: REQ-APR-310` | 错误释放h2 | 不释放 |
| `Once approved, use reference REQ-APR-310` | 错误释放h2 | 不释放 |
| 上述条件头与reference分行 | 两种均错误释放h2 | 两种均不释放 |
| 先真实授予，再明确`previous approval … is revoked` | 错误保留h2 | 清除对应旧授权，不再released |
| 先真实授予，再明确`… is not authorized` | 错误保留h2 | 同上 |
| 引用旧撤回陈述/明确historical record | 会误阻旧grant或将历史当新grant | 不产生新grant，也不撤回已有当前grant |
| 无关设备职责拒绝＋明确当前requisition授权 | 全局拒绝词误阻 | 当前grant仍有效 |
| `has not been revoked`/不能确认是否revoked | 防回归对照 | 不当作明确撤回 |

旧v3运行新增的前四个测试方法时有**9个子例失败**；
修复并加入否定/不确定撤回对照后，下列**39项相关离线测试通过**：

```text
python -m unittest research.study4.v2.test_reference_completion research.study4.v2.test_phase0 research.study4.v2.test_transport_diagnosis -q
```

最小改动在[reference_completion.py](../reference_completion.py)：

- 条件头同时约束直接field evidence及后续分行值，不再只约束grant heading。
- 明确当前、同持有人/实际请求绑定且指向同一grant值的撤回，移除旧field source及released状态。
  撤回不是需要重新取得前置的“新grant”，不能因后续状态查询没有再抄L5/B5而忽略。
  `withdrawals`保留前次授予、撤回回复及对应请求ID，原证据不删除。
- 条件、引用/明确历史陈述、真实撤回、无法确认和无关职责拒绝不再混为一个REFUSAL结果；
  旧grant被撤回后，新的合法当前授权仍可在满足前置/context后重新成立。

原60题/95节点合同仍从原DAG/release_rule/required_context/output编译；
ledger/backup实际首回复、缺值/错误/冲突、跨回复累积、授权前置及公私隔离回归仍通过。
**这不是任意自然语言都已正确分类的证明**：含糊/冲突仍需源绑定复核，
不能将当前有限marker识别器宣称为完美语义oracle，也不能承诺解决全部任务失败。

## 3. 新版绑定与未变预算

正式恢复机器清单：`REFERENCE_V4_AC26_FRESH214_20261112.json`。
它绑定新runtime、私有源码LF SHA、当前核验工具SHA、原plan、原43审计、
各原记录hash、26整体保留策略及214个fresh目标；`paid_recovery_disabled=true`。

| 绑定 | 值 |
|---|---|
| manifest canonical fingerprint | `08048d01e71e8933c2c23ff254dd01cf8069ef919b4034c7b03eb46ae8bdc232` |
| 原actual plan fingerprint | `10becfc13f4c3d39ce39fc0098775b8a87c4f190d7927d59b92bc2421fe6ae23` |
| 新reference源码SHA256（LF） | `f2d8a093abf8126b0fd4ac0927b0512f48044e1876c43171e7ccb3af89089bca` |
| 只读核验时原actual ledger SHA256 | `fc6b9248e775db250682dd70af23caffb1956c5868114b429acff4f6f4d1537b` |

可重复核验（输出排他创建，不能覆盖旧证据）：

```text
python research\study4\v2\tools\audit_reference_reuse.py ACTUAL_ROOT NEW_OUTPUT_JSON
```

累计仍为**1022calls/1016settled/6unknown**，0inflight；
本次没有增加调用。settled费用上界USD10.4812364250，
unknown继续预留USD5.148000，占原50帽**USD15.6292364250**，
剩**USD34.3707635750**。unknown不是确认实付，usage上界也不是最终账单。

费用情景按全部原52例、原usage和实际分臂数量外推，不按分数挑样：

| 214fresh情景 | 估计USD | 解释 |
|---|---:|---|
| 按A47/B60/C47/D60分臂加权原实测均费 | **29.7124** | 约2787模型calls；不是214calls |
| 分臂敏感性：仅移除已证明ledger D异常loop的费用和1例分母 | **7.1807** | 不是保证修后没有长尾 |
| 不分臂的全部52均费/其余51均费 | 26.7901 / 6.5151 | 仅附加情景；主估计采用上述分臂权重 |

主情景低于剩余预算，但这13题不是全部60题的可靠成本上界；
修后B/D分布也可能变化。64步长尾、NPC拒绝、429、新unknown及每call .858预留
都可能提前停批，不能承诺214一定完成，不释放旧unknown或新增预算。

## 4. 当前停止点

`make_plan(provider)`及`validate_binding(provider)`仍硬拒绝，绑定标识同步v4；
旧授权不能执行新源。本轮仅交214清单和修复证据，等待恢复边界核验，
**不自动POST，不另发独立probe，不启动训练/RL/GPU或终测**。

当前只有旧52事实及可整体保留的26 A/C，不是修后完整四臂集；
R均值B−A或D−A≥.10的Phase0门仍未判。
原60题等权、Must/Optional分列、CI不附加门、H1识别限制与H5未测均不变，
不能凭此离线修复声称训练收益或模型能力结论。
