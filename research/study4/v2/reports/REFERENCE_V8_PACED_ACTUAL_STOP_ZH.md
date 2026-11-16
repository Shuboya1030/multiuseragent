# 限速恢复实际结果：73/240，NPC响应头前断连

2026-11-15零API复核。**原runner没有仍在运行，也没有完成240；不能从旧66例进度重启。**
它实际于2026-11-13 19:30:49 UTC写出停止receipt；这是实验HTTP故障，不是会话query错误。
本次“继续啊”的首项只读核对已完成，未发送任何新POST/GET或重试。

## 真实覆盖与费用

原66保留路径之外完成7例，现73完整、18个四臂配对块；
还缺167目标：A42/B42/C41/D42，其中1个partial、166未开始。
73例已全部完成显式、请求/内容hash绑定的非盲AI证据复核，队列0。
没有把partial当业务0、删除NPC错误任务或按表现重抽。

本轮116calls＝115settled＋1unknown；新增usage保守上界0.8753901750。
累计2080calls＝2072settled＋8unknown，无inflight；
settled上界23.0652996750＋unknown预留6.864000＝
**占原50帽29.9292996750，剩20.0707003250**。预留不是确认实付，不释放旧unknown。
全部13个历史继承root重新核对；旧结果、账本、分数和冻结协议不改。

证据：[停止/费用/精确边界/统计JSON](REFERENCE_V8_PACED_STOP_20261115.json)、
[73份公开实际记录](REFERENCE_V8_PACED_STOP_20261115.public.jsonl.gz)、
[显式非盲复核overlay](REFERENCE_V8_PACED_STOP_REVIEWS_20261115.json)。
不发布包含私有NPC系统提示的原journal。

## 节流确实运行；本次并无429证据

所有116次dispatch共用原限速器，最小相邻起始间隔21.094秒；
最后四次约隔21.484、21.516、21.672、21.609秒。
首次冷却按transport创建后的60秒截止，准备后实际剩余等待58.954秒；等待不进入HTTP deadline。

新unknown精确为`reference-v8:phase0:m-high-service-cutover:D:r0:npc:6`；
request hash为`d4ba81a78397e1a9f89a056b0fdf6c1aa794115d23ad42dbcb9b6296d2feeec4`。
请求17,339bytes；HTTP transport在`headers`阶段遇`RemoteDisconnected`，
elapsed2969ms、deadline_expired=false、cleanup_errors为空。
没有HTTP状态、响应正文或限流头，**不能称429、quota或确认无费用**，
更不能猜测为用户续费/会话中断导致。
现有unknown停批机制已生效，没有自动重试。

## 两个旧前缀已真实续接，新停点不可重抽

portal B从原3settled调用后的公共前缀续接，正确取得Liu的QA-DB318并转Jessica。
Jessica后来拒给引用并把QA/date当授权替代；照原NPC错误规则继续到自然终局，未再修oracle追分。
此前conference D的ordinary62独立新attempt也已实际settled，原unknown仍占帽。
该episode在64ordinary动作终局、未submit；实际NPC反复不给授权，没有人为救援或多给步数。

当前service-cutover D停在6个普通动作已完成之后：
question6已settled且**已经send一次**给Li Ming；
7条outgoing、6条实际reply，NPC6响应未知，ordinary6尚未发生。
本partial已有19个settled调用，逐一核对原request/result hash；
pre-question公共state、native history、send后的完整历史和带pending user的NPC对话均已留hash。
下一indices为question7/NPC6/ordinary6。

严格恢复只能：在新namespace明确关联旧unknown，为相同NPC6对话建立一次独立记账attempt；
拿到回复后仅补完已付question6的receipt及ordinary6，再恢复原循环。
不得重新生成question6、重复send、重复执行前6个普通动作或从头抽题。
当前证据证明边界可定位，**尚未建立新执行admission或运行该恢复**。

## 当前研究信息，不是Phase0最终门

下表为全部可用样本描述，C比其他臂多1例；配对统计只用对应已完整任务，不据此过正式门。

| 臂 | n | T | R | excessC | Nauth | Nwaste |
|---|---:|---:|---:|---:|---:|---:|
| A | 18 | .4056 | .3417 | .5000 | .1111 | .1667 |
| B | 18 | .6278 | .2056 | 7.5556 | 0 | .4444 |
| C | 19 | .4158 | .3737 | .5263 | .0526 | .0526 |
| D | 18 | .5556 | −.1083 | 13.2778 | 0 | 0 |

Must平均R：A .3944、B .2722、C .4950、D −.3167；
Optional平均R：A .2889、B .1389、C .2389、D .1000。
18题配对B−A＝−.1361，95%任务bootstrap CI[−.5278,.2000]；
D−A＝−.4500，CI[−1.1972,.0583]。
完整JSON保留质量/成本、安全、内容、交付/submit、ASK、首次联系、拒绝及补救分项。

H1整体仍不能判断：9道Must的A有8道问过，不能预设“不愿问”；2×2不能分离when/whom因果。
H2整体不能判断：C−A局部+.0528，CI跨0。
H3整体不能判断：D−B局部−.3139，CI跨0，不能因局部负值改变终测或训练目标。
H4局部Optional B−A为−.15，CI跨0，尚非整体证实。
H5未测跨执行器，无法判断。
**原0.10门仍为null，不是失败；没有完整60题，不能给出通过/不通过的研究终结论。**
数据是已曝光60题、单repeat、非盲复核及阶段性修复/证据续接，不是独立封存测试或准确可扩展自动奖励。

## 一次明确的恢复选择

原“继续啊”不等于批准无限unknown重试；协调者本条也明确要求新计费unknown保留并报告。
因此当前保持付费停止，只需处理**这一笔新的NPC6 unknown**：
若明确批准一次独立新attempt，可保留全部8unknown和原50帽，
沿73完整＋1原partial＋166未开始继续；所有operation仍共享≥20秒节流、恢复冷却及服务端更长等待。
新unknown或额度不足照旧停止，不增加预算、步骤或改变模型/scorer/0.10门，不另发probe。
剩20.0707不能保证覆盖167目标；此前尾部敏感性已证明50可能不足，
此次七例增量均费又含已付前缀，不能冒充无偏完整成本来保证足够。
没有必要为内部源码版本重新索同一任务授权；真正需要明确的是这次新unknown的一次尝试。
