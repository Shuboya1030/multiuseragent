# v8原Phase0限流恢复：66完整路径＋174待完成

2026-11-13。用户委托“限流你决定应该怎么办”，随后确认“按照你说的来吧”。
直接来源分别为`436cdf88-6a13-40ae-8627-2cf2ea0fc274` revision1与
`e7a380f6-ea65-4840-ad16-6d3ff182707d` revision2；
具体节流/一次新attempt选择是协调者在委托内的决策，不冒称用户逐字规定。
这是原60×4×1及累计USD50任务的受限恢复，不增加预算、训练或模型。

## 执行边界

复用[已核验66＋174整批清单及两个前缀](REFERENCE_V8_CONTEXT_RATE_BOUNDARY_20261113.json)。
原67结果/旧错误尾部/账本不改；完整66路径保留，不按结果筛选。
portal B从原3settled调用、ordinary0真实read后的前缀继续，下一人Liu；
conference D还原188settled调用后的完整公共状态、native receipts、消息、NPC对话及公开source cache。
其`ordinary62`建立**一次**新namespace调用，明确关联原unknown请求hash；
不重放旧工具、旧settled调用或改写/释放旧unknown。另172未开始，最终仍240目标。

继承1964 calls/1957 settled/7 unknown；occupied28.1959095000/50，
remaining21.8040905000，unknown预留6.006000继续占帽。
全部新调用及新attempt仍计同帽；新unknown或额度不足停止，无自动重试/GET/probe。
资金情景见[真实停点报告](REFERENCE_V8_CONTEXT_RATE_STOP_ZH.md)，不保证原50完成。

## 已接入的请求前节流

`request_pacing.py`以单个共享`PacedTransport`包住原HTTPTransport：
首次等待至少60s；已知reset/Retry-After更长则优先；ordinary/question/NPC共享同一个顺序发送器。
相邻调用至少20s；当前实现从上次HTTP结束再等待20s，比起始20s更保守。
等待完全在原HTTP请求30s deadline启动之前，不改变prompt、history、输出上限、模型/NPC、
64步、评分或0.10门。429只延长候选not-before并标记停止，绝不发自动重试。
不能保证共享账户其他流量不触发限流，不新建token估算/安装依赖。

每次等待之前已fsync持久化完整model_request、reservation和`pre_send_wait`事件，
包括call-id、等待截止wall时间和“网络deadline未开始”；原已付前缀另外带源hash证明。
长等待不是HTTP timeout，不重复调用；真正进程中断仍保留unknown，禁止自动restart。
绑定7日有效窗口用于原长时任务，不授权额外scope或重启。

## 验证与源码绑定

49项相关离线测试通过，包括假时钟跨三类操作共享节流、90s服务端reset优先、
本地loopback HTTP429安全字段、等待不耗网络deadline，以及429后推进时钟仍不再发送。
新的admission回归拒绝spacing0、两次attempt、释放unknown、换source、删slot或加帽至80。
两个实际前缀hydrate后的公共state hash与已审证书一致，未应用任何工具/付费调用。
原26A/C整组153请求在最终执行源码下再验证：
[本次执行cohort绑定](REFERENCE_V8_PACED_EXECUTION_AC26_20261113.json)。
该cohort文件中的52例旧预算是历史审计数据，不是本次余额。

新入口`python -m research.study4.v2.phase0_context_recovery`只允许新root冻结/check/一次execute；
旧v7入口保持拒绝新源码。原直接rev13研究授权与本次限流恢复确认分开保存。
冻结FROZEN_PLAN/APPROVAL与AUTHORIZATION_SOURCE后，首正式续接兼实际验收，不独立probe。
执行成功、未完成或budget/unknown停点均由同root FINAL_RECEIPT给精确覆盖，不能把工程验收当研究完成。
