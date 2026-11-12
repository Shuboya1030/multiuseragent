# USD50真实四臂实验：首请求接口门停止，尚无任务结果

2026-11-11。**已获独立USD50授权并实际发送1次请求；响应/动作门失败后整批停止，
没有重试，48slot中完整episode为0。** 因此本轮没有四臂headroom或训练收益结论。
本页更新此前“预算尚未批准”的阶段状态，但不改变旧SFT87/32评测和历史报告。

## 授权、顺序与运行约束

用户本轮原文“预算50美元”，对应既定六个已曝光开发题×四臂×2次、规则NPC零模型调用；
全部真实接口验证也包含在同一USD50硬帽。不是此前USD55/70建议，不借旧USD30或其他预算，
不包含训练/RL/新采集/GPU/LLM NPC/终测。Colab已恢复登录，但当前实验不用GPU；
实际GPU资源未核验，不能把旧输出当当前设备。

实际启动前核验本版本driver进程0、目标新批次目录不存在、旧18814无listener。
通过本地93项测试后，冻结全新plan/授权/唯一输出根，再建独立SQLite账本。
固定snapshot `gpt-5.4-mini-2026-03-17`、standard tier及[模型最大费用bound](MODEL_MAXIMUM_BOUND_ZH.md)，
每call先reserve USD.858；规则NPC为已审查结构化适配器，不冒充原始自然语言NPC。

在任何结果出现前，将原提案的全slot hash排序改为**题×重复的四臂相邻block**：
block按seed98211的hash排序，臂按block序号循环轮换。12block使每臂在每个位置各出现3次，
不修改题/臂/重复/24普通步/输出上限，减少预算截断造成无配对结果的风险。
98212/98213只是重复标签，不宣称provider支持随机seed或重复独立性。
首block因此固定为`o-low-team-lunch` repeat0、A→B→C→D，不是观察结果后选题。

[冻结scope脱敏摘录](CEILING50_FROZEN_SCOPE.json)与[实际机器证据](CEILING50_ACTUAL_CHECK.json)
给出原文件SHA/规范plan hash，摘录不是原批准记录或原文件字节。

## 唯一实际请求发生了什么

UTC `2026-11-12T03:32:30` 已终止；实际只有slot00/A的首个ordinary模型请求。
请求是普通JSON工具提案，尚未调用controller、询问NPC或执行任何普通工具。

| 门/证据 | 实际记录 |
|---|---|
| HTTP和顶层JSON | 适配器返回3523bytes JSON，SHA `1538483cd8da1f4adddc0a6a02bb797725c63f682c10f5681f9c2b6428a43765` |
| snapshot | 持久诊断`returned_model_matches=true` |
| actual tier/status | `default` / `completed` |
| reported usage（未settle） | input1101、output133，数值在上界内 |
| 后续门 | `decode_response`/应用输出校验抛`ValueError`，没有返回可执行提案 |
| 停止 | fresh-only driver终止；0cycle、0普通工具、0contact、0完整episode |
| 账本 | calls1、settled0、unknown1、in_flight0；保留USD.8580，占用上限USD50 |
| 重放 | 没有retry/换call ID、没有恢复工具或episode；driver进程已退出 |

这不是凭据/网络连通失败，也不能笼统说模型加载失败。
但**不能说真实provider完整strict-schema/应用接口门已通过**：
现存证据只证明上表这些顶层属性，不证明输出item结构及业务工具参数被适配器接受。

当时为避免保存任意响应正文，只持久化了raw SHA/长度、异常类型及白名单usage/model/tier/status；
未保存原response body或细分失败码。因此离线无法重建究竟是哪一项谓词触发。
从源码能列出的未排除分支包括顶层id/error/incomplete字段、output必须单message、
单output_text、应用JSON形状/合法tool及精确参数等。
**额外reasoning item、工具参数差异等目前都只是候选，不是已确认根因。**
reported usage本身数值合法也不证明执行已走到usage校验那一行。
本轮未为了填补证据而GET响应、重发请求或降低校验门。

原raw在已退出进程中没有保留，现有已授权证据目录也无可恢复raw/response id cache；
这是**失败诊断持久化不充分的工程缺陷**，不是“隐私要求不允许记录任何输出形状”。
已新增纯离线[诊断helper](../response_diagnosis.py)与
[明确标记的8个合成案例](CEILING50_OFFLINE_CANDIDATES.json)，同一原decoder可分别定位
`decode_response`、JSON解析、`validate_output`、`parse_tool`等函数/源码行。
白名单仅保留key集合/值类型/item计数/允许的type和tool枚举，不保留任务值或任意正文；
合成样本不能替代actual原响应，也没有把helper接入原批次重放。

## 费用、结果和未知必须分开

USD.858是保守未决占帽，不是已证实实付。
按reported1101/133和冻结保守单价可计算USD.001567125作为**未结算参考**，
但不能用此释放reservation或改称已认证账单。unknown使整批禁止下一call，即使cap余额看似足够。

| 臂 | 计划episode | 完整/可评分episode | 内容pass、T/R/C、权限/交付/submit |
|---|---:|---:|---|
| A 公共when+whom/what | 12 | 0（首slot接口失败） | 不可估计 |
| B 特权DAG when+whom | 12 | 0 | 不可估计 |
| C 特权what辅助 | 12 | 0 | 不可估计 |
| D 两种特权 | 12 | 0 | 不可估计 |

其余47slot未启动；首slot是infra/接口未完成，不能强标业务失败或T/R=0。
无交付物可作语义复核，无配对差值或不确定性可算；这不说明模型或reference任务能力强弱。
即使后续成功，B/D也只是privileged参考headroom，不能宣传trained-controller收益；
六题为曝光开发回归，不是独立终测。

## 已交付的driver与下一门

[paid_driver.py](../paid_driver.py)复用共享调度、规则NPC、官方scorer、持久ledger及HTTP适配，
新增真实逐call/事件/cycle日志和slot文件；每个事件fsync，只允许fresh批次。
独立批准记录与冻结plan/runtime/scorer/价格/root哈希绑定后才允许建账本或网络。
真实密钥仅使用已有User→Process注入，不输出、写入文件或传Colab。

本地新增5项driver测试加此前88项共93项通过；包含48slot脚本回放（不是mini推理），
以及工具已产生副作用后中断的失败注入：即使模型已settled，第二次启动也拒绝，
不宣称模型缓存等于工具/episode exactly-once。任何中断fail-closed，无自动恢复入口。
另2项离线诊断测试后，完整针对性验收为95项；这仍不是新增真实任务结果。

下一步应先补齐**脱敏且细分的响应形状/失败阶段诊断**，再在独立审查中决定是否需协议修正。
当前原raw缺失，不能伪造重建或依据猜测放宽单message/参数门。
任何新付费尝试都不能绕过本批unknown和fresh标记；
需要先明确处置未决费用、批准是否允许新诊断请求及其计入同USD50的方式，
并重新冻结变更；本轮没有自行启动第二批。
先解决实际接口门，再谈四臂headroom；没有进入训练，也没有涨预算。

原账本、原请求/私有snapshot、批准记录留在隔离session证据目录，不上传；
仅上传必要脱敏指纹和摘要。[本次公开文件指纹](CEILING50_PUBLICATION_MANIFEST.json)
