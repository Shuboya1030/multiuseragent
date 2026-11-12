# 控制器二态职责修复：零API验收

**新版controller只输出SELF/ASK；提交仍由共享ordinary executor选择`submit`产生。
没有把历史C的SUBMIT改成SELF，没有重跑真实实验或改变原成绩。**
本次0模型API、0GET、0key读取、0GPU、0正式paid ledger。
累计settled上界USD.069303300＋unknown USD3.432在原USD50内保持不变。
这修复的是已证明的职责缺陷，不证明新策略收益或全部任务失败已解决。

## 最小契约变化

| 边界 | 新合同 |
|---|---|
| 公开runtime | `study4-controller-v2-local-1.2-help-only` |
| 原生单函数 | `study4-native-single-function-help-only-v2` |
| 监督tuple | `study4-v2-three-head-help-only-2` |
| controller | 仅`SELF/ASK`；SELF表示不新增求助，不是执行许可或任务行动指令 |
| ordinary executor | 原五个函数及其参数schema不变；只有它能产生`submit` |
| question | 原schema不变，ASK仍作废proposal、自动发送/收读NPC回复，再普通一步 |

`CONTROL_ACTIONS`统一供Decision验证、JSON/原生control schema及when mask使用。
控制prompt不再给controller提交职责；公开进度齐全也不增加SUBMIT标签。
DAG reference没有待求助依赖时返回SELF，不能以“已交付”作为controller提交命令。
runtime移除了controller SUBMIT替代普通proposal的分支，保留ordinary submit的
公开交付门；SELF不会挡住已产生的write，ASK才按原合同丢弃proposal并刷新普通动作。
四臂继续共用同一普通执行模型、请求、函数权限及调度，不强制交付或改任务答案。

历史三态输入不自动迁移：旧观察版本、含control SUBMIT的历史、
原生`choose_help(SUBMIT)`结果/续接历史、旧监督schema及新增SUBMIT的mask/tuple
均明确拒绝；不取第一动作、不放宽参数、不把SUBMIT映射为SELF。
监督审核重新构建合法tuple/mask校验，避免只查公开哈希却接受旧私有label。
模型输入仍只投影public_input，gold/DAG/未读值/评分不进入公开请求。

新原生provider分支在任何transport/key读取前明确拒绝：**本轮只有零API授权**。
本地恢复/账本测试显式使用local_test与loopback地址，不把旧来源当新版付费批准。
旧真实计划还绑定原源码/协议，不可拿新版decoder重新解释。
此前33次原生v1真实调用单函数通过，只是v1接口实证，不是新版策略收益，
也不是v2实际provider验收。

## 实际本地验收

[机器证据](HELP_ONLY_REPAIR_CHECK.json)；
[新版9个fixture proof](HELP_ONLY_LOCAL_FIXTURE_CHECK.json)；
[新版24个脚本适配案例](HELP_ONLY_LOCAL_ADAPTER_CHECK.json)。
后两者另立文件，原有LOCAL_ACCEPTANCE/LOCAL_ADAPTER报告没有覆盖。

- 新行为回归：controller SUBMIT在解码/Decision/runtime前拒绝，既不应用write，
  也不悄悄SELF；合法SELF保留原write→post→ordinary submit；
  premature ordinary submit仍被公开交付门挡住，不自动补写。
- ASK生命周期与四臂共享/public-only原测试继续通过，含原生call_id、
  proposal未执行receipt及自动回复后继续普通动作。
- 新/旧监督schema、when mask及历史控制输入拒绝；新provider无批准时
  不能创建paid ledger或发送。未启动任何真实重放。

| 测试来源 | 结果与版本边界 |
|---|---|
| 当前v2 discovery | 114发现，108通过，6个旧prompt续跑测试不套用新版 |
| 原冻结`2e5ca00`的6个旧续跑测试 | 单独在原源码运行，6通过；没有删除旧版本门或放宽旧prompt校验 |
| 独立legacy help/native协议 | 12通过 |
| 当前9 fixture / 24 scripted | 通过；不是mini真实推理或研究收益 |

当前可在repo root运行：

```powershell
python -m unittest research.study4.v2.test_native_protocol.HelpOnlyResponsibilityTests -v
python -m unittest discover -s research\study4\v2 -t . -p 'test_*.py' -v
```

六个旧续跑测试依赖原single-action-v2 prompt，仍保留原guard。
不能为了让它们在新版运行而移除冻结检查；本次使用原commit导出的独立包验证，
跳过不代表失败被隐去，也不代表用新版“重现”了旧行为。

## 历史证据保持原样

原actual源码：`2e5ca009ef729d9984c3bcb08f9df5171214ed79`；
原结果发布：`1dbc9febe952aa5100050ce8a9a0bf6f0daf3ca0`；
[原真实报告](NATIVE_FUNCTION_ACTUAL_ZH.md)继续保留。
所有七个actual根目录逐文件指纹不变，包括全部ledger、18条C响应缓存、
请求哈希、preflight、A/B成绩和未完成C记录；unknown未释放/重算。
原结果报告/机器证据/manifest与原发布commit的Git字节一致。

另从原commit导出原源码包，使用原生v1 builder/validator/runtime，
只在新的内存环境喂入C实际保存的18条返回：
全部18个请求SHA、最终state及cycles仍与原actual完全一致，
仍复现`Public file missing`。原源码23文件指纹逐个匹配，
这不是新版decoder接受旧SUBMIT，也不是paid ledger或工具副作用重放。
原actual没有保留原始本地traceback，离线重建栈不伪称原始栈。

## 缺文件读取：只审计，不改语义

当前`read_file`要求公开路径已存在；不存在时抛固定`ValueError`，
runtime标failed/technical_failure，调度整批停。没有返回可恢复tool error，
失败read也没有递增normal_actions。本次局部审计验证该行为及workspace不变。

**性质可区分，当前异常类型尚未区分：**公开workspace中不存在的虚拟文件是
可预期的工具前置条件失败，不等于provider schema、网络或持久化基础设施失败。
当前统一捕获为fatal技术异常，原C因此未完成；不能事后把其内容/T/R补成0，
也不能因模型usage已结算就假装工具成功。

可以设计不泄漏、不吞错的恢复：为已知缺文件返回显式、白名单
`file_not_found`错误，保留原call_id、公开请求路径、失败状态及历史，
由executor在下一普通回合自行选择纠正；禁止包含任意exception message、
私有路径/gold或伪造成功。未知基础设施异常仍应fatal。
但这会改变失败动作计数/预算、pending function receipt、终止及对照轨迹，
必须统一四臂并明确失败尝试是否占一步，不能自动retry、强制交付或无限免费修复。
**这是独立合同选择，本次未实现或默认启用。**

本轮修复和发布后停止。下一次真实验证、补跑开发实验或训练都没有获得本轮授权；
两态修复不能承诺不再出现错误文件、遗漏事实、坏交付或其他失败。
