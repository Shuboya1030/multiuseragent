# Reference-v5：补齐三种签发字段，付费仍暂停

已确认同根遗漏：v4只把authorization/mandate/signoff/attestation类字段视为授权，
没有把原release_rule要求前置后签发的以下三种reference送入同一条件/撤回路径。
**仅扩展字段角色集合，没有任务ID、答案值或按表现分支，没有新增分类器。**
私有版本现为`study4-reference-completion-5`；公共协议2和scorer未变。

| 原任务 | 字段 | 原节点要求 |
|---|---|---|
| service-cutover | readiness_reference | allocation之后；revision、replicas、window、rollback context齐备才释放readiness |
| research-purchase | release_reference | allocation之后；current revision、amount、budget齐备才release |
| incident-postmortem | publication_reference | root cause节点之后；root cause和duration齐备才批准publication |

## 离线复现与最小修复

新增一个表驱动测试，从每题**原DAG与hidden record**生成前置节点、持有人、
上下文及预期reference，不在实现中编码题号或具体答案。
每种字段分别测试`If approved, field: value`、`Once approved, use reference value`，
以及真实授予后同scope明确`is revoked`/`is not authorized`。
v4上**12个子例全部失败**：条件被当授予，撤回仍保留旧grant。

实现只增加`ISSUED_REFERENCE_FIELDS`中的这三个字段名并进入既有grant机制，
同步私有版本、调度说明与准入绑定。修后上述12子例通过；
每个情景还验证随后真实重新授权可成立、`has not been revoked`不会误撤回。
原条件/否定/引用/历史/无关拒绝、重新授权、ledger/backup及95节点canonical回归保持通过：

```text
python -m unittest research.study4.v2.test_reference_completion research.study4.v2.test_phase0 research.study4.v2.test_transport_diagnosis -q
Ran 40 tests ... OK
```

这仍是有界确定性判定，不是任意自然语言准确率或新策略收益证明。

## 新版26＋214整体核验与绑定

[新清单：REFERENCE_V5_AC26_FRESH214_20261112.json](REFERENCE_V5_AC26_FRESH214_20261112.json)。
原13题**全部26例A/C整体通过**共享源/环境/任务包/NPC/scorer及153个全部请求指纹核验；
仍为all-or-none，不筛选B/D。剩214fresh：**A47/B60/C47/D60**。
95节点编译合同、214目标及顺序、预算与v4清单完全一致。
原52实际、43审计、v4清单/报告均保留；原ledger字节SHA仍为
`fc6b9248e775db250682dd70af23caffb1956c5868114b429acff4f6f4d1537b`。

| 绑定 | SHA256 |
|---|---|
| v5 manifest canonical fingerprint | `21c36555e2c031b631a40f1ab0bda9a7ecac33efc6fab04332af0b46f8142c3e` |
| v5 reference源码（LF） | `6d66416b9f57951f5336b53cfffcdca39f1bdebb4482a681ebaa5f02c270173c` |

累计仍1022calls/1016settled/6unknown、0inflight，占原USD50帽
**15.6292364250**，余**34.3707635750**，unknown5.148不释放。
214分臂费用情景仍为USD29.7124；去已证长loop的敏感性情景USD7.1807，
均不是完成保证。细账、选择偏差解释及旧暂停边界见
[v4报告](REFERENCE_V4_RECOVERY_REVIEW_ZH.md)，其正式版本绑定由本v5清单替代。

## 恢复请求的精确边界

**仍必须有一条新的直接用户授权。** 本条coordinator指令只批准离线修复；
原revision10也不能作为v5的付费恢复来源。当前provider `make_plan`及`validate_binding`
依然硬拒绝；本清单是离线核验绑定，不是已获批准、可直接启动的provider计划。

供协调者向用户呈现的**建议授权范围**（不是已经取得的用户原话）：

> 按已核验reference-v5及26＋214清单，整体保留原26例A/C，
> 仅在新run命名空间fresh运行其余214例（A47/B60/C47/D60）。
> 沿用原累计USD50，继承全部1022calls及15.629236425占用，
> 六笔unknown5.148不得释放；所有后续模型调用都计同帽，不新增预算。
> 首个目标任务的fresh B/D与已核验A/C组成配对块兼实际验收，
> 不独立probe，不重放已settled结果/工具或续接旧partial。
> 新unknown、无法安全恢复或预算不足立即停批，无自动重试/GET/换端点。
> 模型、NPC、公开输入合同、普通工具、64步、scorer、240总规模与0.10门不变；
> 不启动训练/RL/GPU、额外采集、模型对照或终测。

收到带可验证source ID/revision的直接用户批准后，仍须先把**新run/root、
26保留映射、214fresh目标、累计账目与批准来源**接入受限准入计划。
该必要准入绑定会改变admission源码：须重新冻结最终source/manifest并重核整组A/C，
再准许首个正式请求，不能拿本离线清单的hash冒充解禁后源码hash。
这里只说明这项恢复前置，未启用或执行它；无需另发provider连通性probe。

本轮**0模型API/GET/key读取/GPU/实际重放**。训练门仍未判；
完成本修复后停止，等待协调者呈现上述恢复范围并取得直接授权。
