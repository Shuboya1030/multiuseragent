# Study4设计合同v1.1：先共享协议与验收，再付费ceiling

2026-11-11。依据用户提交`c034383708bbb4f9f2b9a5e27f63f8204d999c12`
及随后批准的评审修订。[原v1](../STUDY4_CONTROLLER_DESIGN_v1.md)、
[建议原文](../ADVICE_FROM_PAPER_SESSION_20261111.md)保留；有冲突时新阶段以本文为准，
不回改SFT87、旧32episode/原分数或旧预算。

## 顺序与执行范围

1. **本阶段**：共享普通工具/公开进度/停止接口、本地mock、DAG参考/规则NPC最小fixture、
   监督可辨识与来源检查。没有mini/GPU调用、凭据读取、receiver或新付费ledger。
2. **下一授权门**：小型四臂真实ceiling pilot。协议/scorer/task/重复数/价格/预算先冻结，再运行。
3. ceiling后才讨论生成器扩展、真实executor环境验收与监督训练；5000题、GRPO/PPO/IQL/CQL均未实施/未授权。

本地fixture可解不等于真实mini循环已修好，不等于Phase2生成器完成，
也不能把“规则NPC免费”误写成executor rollout免费。

## 共享执行协议（`study4-controller-v2-local-1.1`）

- 所有臂普通行动都经过同一个`ordinary_request`：相同schema、公共观察、进度与措辞；
  请求中不加入arm名、gold或权限特权。原服务的虚拟workspace、工具envelope与消息身份语义复用。
- 控制动作SELF（兼容旧称NO_ASK）、ASK(person,intent,include_value_ids)、SUBMIT。
  SELF是恰好一个普通工具动作，既不命令post也不禁止submit。
  SUBMIT只是提交意图：**公共交付尚未完成时不可直接结束**；满足交付门后仍由执行器生成submit命令/答案，
  控制器不写最终答案。未满足门记录可恢复的`submission_blocked`，不自动成功。
- ASK：执行器用公开intent及选定已有值生成问题→消息发送→规则NPC实际回复→自动交付，
  然后执行器恰好一个普通动作。没有额外controller SELF批准读消息。
  拒绝也是可见回复，不伪造成release，之后可补充所缺上下文再次问。
- 普通schema包含read_file、write_file、list_files、post_channel、submit；
  `send_message`与`read_messages`不在普通模型allowlist，读消息是环境交付，不允许Agent偷偷联系。
- 公共progress分开记录文件有效JSON/公开必需fields是否存在、artifact revision、
  发布摘要所指revision、submit receipt。文件更新后旧摘要不会满足最新交付门；
  post重复不清历史，不禁止收到新事实后的修订。
- **业务/内容**由独立评分判定；**用户交付**与**桥接submit**另报。
  信息拿齐不是交付完成；交付完成/submit也不是内容正确、授权有效或自动业务pass。
- 私有环境异常/未确认写失败停止并保留事件，不重试；非法模型命令明确报错。

### 决策点与限额

目标决策点：start、实际reply（包括拒绝）、拟write交付物/submit之前、每4普通步安全检查。
本阶段提供原因检测与单cycle接口，不把mock驱动称完整真实key-point runner。
默认24普通行动/最多24联系，环境send/read不算普通行动；非法提前submit也消耗一个普通行动机会。
关键点去重、待执行proposal失效与真实API调用绑定须在ceiling runner冻结时验收。

## 公共状态、what与监督可辨识

输入只由`PublicTask`与实际事件投影：公开目录/价格/请求intent、public documents、
工具结果、已发送问题、已读回复、公开交付progress与已获值来源。
不输入gold DAG、task class、required_context、未读facts、evaluator或未来reply。
环境snapshot另存私有对象，不能作为模型观察。

本阶段结构化规则回复中每个facts值带稳定value ID、message ID和person来源；
同key不同值都保留为不同ID，不静默覆盖。普通文件中的计划值不是NPC批准；
不把一次拒绝中的关键词/引用解析成已获grant。
自由自然语言事实提取未实施，须另审来源/语义等价/冲突策略。
当前fixture what请求强制公开intent前缀与key=value引用，确定性检查字段和值绑定，
不把在别处引用同一数字、否定/引用intent当有效请求。真实mini对该格式的遵守程度未验收。

公开task提供intent目录（任务操作语义，不含私有依赖/隐藏条件）。
部署policy/固定executor从公开任务选intent；what head只能选**已读来源**的value IDs。
问题措辞由固定executor产生，验证它保留intent和选定key/value，遗漏则停止，不由系统悄悄补齐。
当前what标签的私有推导只属于离线监督/特权臂，不作为部署input。

训练标签可读私有参考，但须登记target来源/合法多解和公开可辨识性：
同公开观察若可接受动作集有交集，保留多标签，不硬指定唯一人；若没有交集，
标`unidentifiable`并阻止该标签进入“唯一正确可学习”训练。
这只是对被检查状态的必要一致性检查，不证明整个生成器全局可辨识。
任务ID/gold名称不能作为观察差异的掩护；审计签名去除task/episode/value/message标识，只保留公开内容及来源结构。
通过不意味着oracle标签已获得真实utility优化证明。

## DAG参考而非理论最优oracle

规则NPC独立检查prior release、context值、请求intent及admissible holder；
没有事实的同事给明确无资料/公开团队referral，不透露隐藏当前值。
参考策略选择就绪未释放节点的合法联系人、只引用已读值，**仍由普通执行器完成artifact/post/submit**。
部分回复后其余节点仍未满足，可继续问；并行依赖、referral/delegation及阈值在小fixture中覆盖。

Optional路径必须显式冻结`baseline`或`improve`及目标理由。
本阶段没有用贪心DAG算法证明全局最优或准确ceiling：最便宜合法节点组合未考虑
共享一次请求、多字段释放、随机executor、候选子集或多种Optional收益路径。
特权参考解不了、公开监督不可辨识或fixture有歧义时必须单列，不硬造最优标签。

四臂：A公共native when/whom/what；B特权DAG when/whom＋executor what；
C公共native when/whom＋**gold选相关已获字段的特权what辅助**；D两种特权。
C不是普通部署baseline，B/D也不是已证明理论上界。共享普通执行接口不代表同执行器表现或跨LLM效果已证明。

## 新scorer绑定：以实读源码为准

只读核对仓库`Shuboya1030/tribalbench` commit
`4260bdc626548f59042f318cdf0566490e91b9d5`，`scorer/scorer.py`，
`GRADER_VERSION=tribalbench-1.0`，原文件SHA256
`e6b47e4a251bdc44d2fbfe389e12b81273e6472092958fe04e33297f28a33e78`。
来源与实际公式见[绑定](configs/scorer_binding.json)。

**源码R**：`T - .05*max(0,C-C_star) - .3*Nauth - .1*max(0,Nwaste-Nauth)`。
Must的C_star是每DAG节点最便宜admissible联系成本之和；Optional C_star=0。
Nwaste=wrong_person+redundant，Nauth是其中授权关键词相关计数，最后项避免重复罚。
README/设计公式没有完整表达这些区别，不能照抄成已执行奖励。
源码另有`R_all_contacts`；旧SFT87用旧scorer/R，**不可直接替换或混称可比**。
自然语言evidence未审时scorer可返回unknown/T null，不得补0或自动通过。

本阶段未复制/执行该scorer、未调用远端任务代码。
fixture checker明确叫`local-fixture-proof-v1`，不是TribalBench评分。
正式runner须取得上述固定字节/授权来源、复核输出binding/evidence并单独验收，
否则官方scoring gate仍blocked。不能另造同名scorer。

## Split与统计纠正

原60题已用于训练、checkpoint选择、诊断与拟Phase0，名称是“既有基准迁移/回归”，
不是untouched external final test。真正终测先预冻结新任务家族、role/knowledge/authority映射与组织，
不参与生成器/模型/超参选择；按canonical结构去重，不只换名。

候选50org规划：40个development org的任务分成train families与dev-in-org heldout families，
**不是40org all tasks都train**；另5dev-new-org、5test-new-org。
family group同org内不跨train/dev；test org与train/dev在结构与映射级隔离，
跨org重复template若测的是新org而非新family要明确标出，不混称两种泛化。
最终seed/名单/去重指纹尚未冻结，本阶段不生成该split也不宣称完成5000题。

组织泛化用org级或hierarchical bootstrap，保留同题/重复配对；只有5test org统计能力有限。
joint/what增益须superiority差值区间；`L-full >= Seq/L-ww`不能证明增益。
noninferiority要预声明有研究理由的margin；相等/区间跨0如实作描述性结果。
不得根据当前结果挑threshold、调最终test或事后改lambda。

## 模型/上下文候选仍有门

保留three-head when/candidate-shared-whom/value-selection-what方向；分类/稳定action-ID不靠人名token输出。
Qwen1.5B、rank16/alpha32、lr1e-4与MLP/marker方案仅候选，不把旧lr低/长label必低或循环完全无关控制器写成因果事实。
特殊marker tokenizer/embedding、梯度与train-only拟合性须先验收；不下载/训练本阶段模型。

6k是新版本候选，旧4352不变。当前local `context_view`接受外部token counter，
只可剔除最早的普通history事件，并登记被省略的事件ID；保护所有回复/来源/summary/公共task/最新proposal。
protected部分仍超限则`ContextOverflow`停止，不静默丢回复/summary、不筛掉超长样本假装全量。
counter不等于实际Qwen tokenizer；本阶段只mock验证这个合同，未通过真实6k容量门。

## 变更摘要

| v1说法/风险 | v1.1修订 |
|---|---|
| ceiling先于接口mock | 先共享接口/mock，再经独立授权的ceiling |
| all nodes齐→SUBMIT | 信息/授权、公开交付、桥接submit独立；SUBMIT不可跳过交付 |
| DAG oracle/唯一正确标签 | 特权参考、Optional显式路径、多标签/不可辨识处理 |
| 60 untouched final external | 已暴露基准回归；真正新终测另冻结 |
| train org all tasks兼dev-in-org | 同org family partition、去重/seed另冻结 |
| 规则NPC→rollout免费 | fixed mini仍付费，所有阶段计executor与GPU |
| 直接公式/版本名 | 实读固定scorer字节、Optional与auth/waste差异，官方执行仍待接入 |
| lr低/长label/SELF无关因果断言 | 已证实与待消融假设分级；本阶段不训练 |

[阶段报告](reports/PHASE1_LOCAL_ZH.md) · [ceiling方案与待签预算](CEILING_PILOT_ZH.md)
