# 原生单函数真实验收及四臂部分结果

**原生接口真实验收通过，四臂批次已实际执行，但在C臂停下：完成2/48，
没有完整四臂block，不能宣称ceiling或新训练完成。**
这次不是继续内存mock。新增33次实际POST全部合法解码并settle；
旧四笔unknown USD3.432不变。累计settled费用上界USD0.069303300，
与unknown合计占原USD50帽USD3.501303300。unknown不是已确认实付。

源码冻结：`2e5ca009ef729d9984c3bcb08f9df5171214ed79`；
协议：`study4-native-single-function-v1`。
依据：[协议/官方来源与费用域](../NATIVE_FUNCTION_PROTOCOL_v1_ZH.md)；
完整数值、原文件指纹、真实调用及逐行轨迹索引：
[机器验收证据](NATIVE_FUNCTION_ACTUAL_CHECK.json)。

## 已真实发生

用户“可以继续”，直接来源 `f0d83ab9-9180-4da1-8ff7-7a2feaf440e1` revision3，
批准一次原生接口preflight，成功后继续原六个曝光开发题×四臂×两次，
同原USD50；不包含新训练、额外采集、终测或GPU。预验与批次分别冻结新根，
但继承全部五个旧run的成本和未知占用，不另开USD50。

1. 一次preflight：1063 input / 21 output，USD0.000980925上界，
   恰一个`read_file` function_call，标准tier、固定mini、合法usage并settle。
   **0环境工具、0episode**；不把API接受函数等同该读取在环境中可执行。
2. 随后启动已冻结原48slot顺序的fresh批次。32次POST均settled，
   新unknown为0；普通动作、`choose_help`及`compose_help_request`均实际通过。
   A/B完成，C中断，D及后续45slot未启动。无重试/GET/工具重放。
3. 原生function结果按call_id记录，ASK前proposal明确未执行，规则NPC回复
   实际send/read自动交付，再执行一个普通动作。没有取多动作第一条、
   合并动作、增大SELF或改官方scorer/阈值。

## 首题同一次重复的实际结果

题目均为曝光的 `o-low-team-lunch`，repeat0；不是终测。
官方scorer固定 `4260bdc626548f59042f318cdf0566490e91b9d5`。

| 臂 | 内容pass | 用户交付 / submit | T | 官方R | 联系次数 / 成本 | 模型call | API费用上界USD |
|---|---|---|---:|---:|---:|---:|---:|
| A：公开when/whom＋公开what | 是 | 是 / 是 | .5 | .5 | 0 / 0 | 9 | .012848550 |
| B：特权when/whom＋公开what | 是 | 是 / 是 | 1 | .9 | 1 / 2 | 5 | .007747575 |
| C：公开when/whom＋特权what | 未完成、未知 | 未完成 / 否 | — | — | 0 / 0 | 18 | .033963600 |
| D：均特权 | 未运行 | — | — | — | — | 0 | 0 |

A交付合法baseline，素食份数为0，Optional-help内容pass但T=.5，
不是所有内容pass都强制T1。B询问HR后把素食份数更新为6，内容质量T1，
联系成本2仍计入，故R=.9而非1。两者未见官方权限/waste/不支持声明错误。
联系成本不是API美元；此处美元按冻结价格与10%保守余量计算，不是供应商账单。

这一个题例提供**特权when/whom相对于A的描述性headroom迹象**：
T高.5、R高.4，多一次成本2的联系；它既不是已训练策略收益，也不是四臂
ceiling证据，不能归因于whom/when单个因素或宣称普遍优于prompt。
C没有发出ASK，what特权根本未触发，不能归因为“what辅助有害”。
0完整四臂block、1题、1重复，不给伪精确配对/组织bootstrap区间；
未运行slot保留缺失，未挑最好重复或调指标。

## C为何停止：不是provider多动作失败

实际持久轨迹显示：

- cycle0：普通`read_file(order.md)`；控制器SELF，读取成功。
- cycle1–7：普通执行器每次提出`write_file(deliverable.json)`，
  控制器连续7次选择旧三态接口允许的SUBMIT。
  公共交付尚未完成，runtime每次阻止submit，**没有应用那7次write proposal**。
  原生receipt明确记录未执行；没有伪造写成功或提前完成。
- 随后普通执行器请求读取尚未创建的`deliverable.json`，控制器SELF。
  请求/函数/参数/usage均合法并settle，但本地文件缺失，runtime抛ValueError，
  按既有fresh-only安全门停整批。C没有内容/质量/奖励评分，不记业务0。

原actual日志只保留异常类别，不含本地栈，不能声称已保留原始traceback。
另做**零API离线重建**：依次喂入C实际保存的18条模型返回，
逐一验证全部18个请求SHA完全一致，最终workspace/history/cycles与
actual partial完全一致，复现 `runtime.py:_normal` 的固定校验
`Public file missing`。重建仅用新的内存环境，不打开paid ledger或真实transport，
帧及provenance在机器证据中；不是再调用模型或重放原episode副作用。

这暴露尚未解决的**控制与普通执行边界**：沿用的三态controller SUBMIT会
取代待执行的普通proposal；虽成功阻止提前提交，却能阻断正常写入。
因此不能声称当前控制器已经严格只做二态when/whom而不干预任务行动。
没有在本批中临时改schema、把SUBMIT偷偷当SELF、强制写正确答案、
忽略缺文件错误或加call“救活”C。原四臂源码与全部实际证据保留。

## 成本与完整性

| 范围 | settled call / 费用上界USD | unknown占用USD |
|---|---:|---:|
| 五个旧run | 10 / .013762650 | 4笔 / 3.432 |
| 本次preflight | 1 / .000980925 | 0 |
| 本次批次 | 32 / .054559725 | 0 |
| 同原USD50累计 | 43 / .069303300 | 4笔 / 3.432 |

累计47次本地dispatch尝试；旧传输unknown不证明供应商实际收到。
无in-flight；unknown未释放、未事后用reported usage结算。
五个历史run所有文件、SFT87与旧32episode/账本逐字节复核不变。
本次preflight及batch也分别保存关闭后的文件指纹、冻结计划/源码/价格绑定。
local测试110个v2＋12个legacy通过；48slot脚本回放仅本地接口验收，
不是48次真实成功。provider验收来自上述33次真实POST而非mock。

## 下一步的真实门

本轮已停付费；没有训练、Colab连接、GPU作业、安装或下载。
进入训练前仍需先解决普通执行边界，而不是先调学习率或重训：
在**新版本**把when/whom限制为SELF/ASK，让submit只由固定执行器普通工具产生，
离线覆盖提前完成、拒绝及未创建文件路径，保持所有臂同一普通能力。
是否将缺文件作为可恢复公开工具错误也须明确统一合同，不能混作模型schema成功。
随后若获准再以同累计帽进行明确新版本开发验收，不能自动重发这次C或假装完成48题。

当前只支持“一题的特权求助可能有质量—成本空间”，不足以通过四臂ceiling门，
也不足以启动新训练/RL或大规模数据生成。真正新任务/组织终测尚须预冻结，
这些六题与旧60题仍只能用于开发，不能反复测试直到胜出。
