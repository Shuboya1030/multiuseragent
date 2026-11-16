# 实际81/240：已恢复NPC6，随后ordinary20在connect/gaierror停止

2026-11-15当地晚间（receipt为2026-11-16 05:06:49 UTC）。
**此次真实执行新增8完整例，现81完整/20个四臂配对块；不是240完成。**
新unknown已按原门停止，无在途或活跃runner，未发送重试、GET或独立probe。
shell退出0仅表示runner已正常写出停止receipt，不代表研究完整完成。

## 真实费用与证据

本轮145calls＝144settled＋1unknown，新增settled usage上界0.8312733000。
累计**2225calls＝2216settled＋9unknown**；
settled23.8965729750＋held7.722000＝
**占原50帽31.6185729750，剩18.3814270250**。
无任何旧unknown释放，不假设新DNS错误应退费；这是保守usage/预留上界而非账单。
81例全部完成请求/内容hash绑定的显式非盲AI复核，队列0；
剩159目标＝原partial1＋158未开始，A39/B40/C40/D40。
全部14个继承root及144个新settled收费逐一重核，原文件/分数/账本不改。

新unknown：
`reference-v8-npc6:phase0:m-high-plugin-purchase:B:r0:ordinary:20`，
hash `ebe6e7ef0caa7e27e8c0cfb703a8a27a25414dec1f7ec52f2b687321009b2e2e`，
49,096bytes。持久诊断为`stage=connect, cause_type=gaierror`，
elapsed11,906ms，deadline_expired=false，cleanup_errors为空。
没有HTTP状态、响应body或限流头，**不是已证429，也不是上一笔headers断连**。

完整材料：[停止/费用/前缀/源码调用链/fixture/统计JSON](REFERENCE_NPC6_DNS_STOP_20261115.json)、
[81份原始公开记录](REFERENCE_NPC6_DNS_STOP_20261115.public.jsonl.gz)、
[显式复核overlay](REFERENCE_NPC6_DNS_STOP_REVIEWS_20261115.json)。
不发布私有NPC系统journal、原始完整headers或凭据。

## 这次DNS错误能证明到哪一步

冻结执行源码`903705c49cd476aa89735ccb2f55ecc22e39727e`的`HTTPTransport.send`：
先`HTTPSConnection(...); connection.connect()`；
成功后才设置`stage=send`并执行`connection.request("POST", ...)`。
这次仍停在connect，因此**该应用路径没有到达HTTP POST请求写入语句**。
不能把49,096bytes（准备好的body长度）称作已发字节。

同一Python3.12.10实际stdlib源码进一步显示：
`HTTPSConnection.connect → HTTPConnection.connect → socket.create_connection`，
后者在建立socket前先迭代`getaddrinfo(host, port, ..., SOCK_STREAM)`。
默认直接HTTPS、无proxy/redirect/tunnel设置；普通路径与解析失败一致。
本次没有持久化getaddrinfo入口/返回或socket计数、异常栈；
**不将“默认DNS先于socket的源码证明”伪装成当时逐socket观测**。
最强的直接结论是POST分支未进入；默认解析失败发生于新socket创建前，
但本报告不声称有当时独立抓包证据或借此释放保留额。

新增的仅是session内本地fixture，不改任何执行源码：
将`getaddrinfo`固定抛gaierror，并令socket构造/HTTP.request一旦触发即失败。
真实durable local-test调用得到同类connect/gaierror，计数DNS1、socket0、HTTP0；
ledger仍unknown1并保留.858，第二次同call被门拒绝且DNS计数仍1。
该fixture只证明调用顺序/不自动重试，不证明历史具体DNS返回内容。
协调者随后一次无HTTP的Resolve-DnsName目前成功，仅是之后可解析，不证明历史无费用。

## 精确前缀与一次有限恢复选择

plugin-purchase B已30settled前缀（question5＋NPC5＋ordinary20），
5outgoing/5read、20普通动作已完成；ordinary20尚无result、控制SELF和该普通工具均未应用。
最后一次已应用ordinary19是submit被业务门拒绝，仍是普通实验结果，不是技术停机原因。
现indices为question5/NPC5/ordinary20。
request中的公开state/workspace/完整native receipts与实际incomplete记录逐项相等；
30个request/result hash逐一匹配。
当前原builder已零API重建出**完全相同ordinary20请求**。

若用户选择恢复，只需一次新namespace独立ordinary20 attempt，
保留原81完整、30settled前缀、全部9unknown及原50帽；
收到result后按原loop顺序追加一次SELF控制事件、执行ordinary20一步及其receipt，
再回到原循环；不重新问人、不重send、不重做已完成工具、不从头抽题。
当前**未授权/未建立/未执行这一新attempt**，上一次只批准NPC6，不能自动扩成此笔。

有限故障处理建议（不要求新依赖或更改研究合同）：

| 已有证据类型 | 本次可作结论 | 预算内有限恢复边界 |
|---|---|---|
| 本次connect/gaierror＋冻结调用顺序 | POST分支未进入；默认路径是发送前解析失败 | 已有之后的DNS成功可作环境信号；若明确批准，只给同ordinary20一次新attempt，仍冷却60秒、统一≥20秒，旧预留保留 |
| 明确HTTP429及安全type/code/限速头 | 服务端已返回错误；rate与quota按实际字段区分，未知仍unknown | 使用已保存reset/Retry-After作请求前等待依据，不把等待当授权；当前没有第二次429，不能用“限流”解释此故障 |
| 已send后headers断连/无响应 | 是否执行/计费未知，不能由当前DNS状态推翻 | 精确保留逻辑前缀，需对应一次新attempt决定；不自动重试/GET/换端点 |

任何新unknown或额度不足照旧停止，不是无限重试方案。
每次调用仍须先有.858预留空间；剩18.3814不是可任意耗尽的API额外授权。
若159目标平均后续净usage分别为.05/.10/.15美元（**假设敏感性，不是预测**），
则约需7.95/15.90/23.85美元；最后一项超过余款5.4686，
而局部余款不足一次预留时还会更早停。
带已付前缀的8例新增均费不能当无偏未来成本，64步尾部仍可能使原50不够。
保持原帽，不降步数、不删任务、不加预算，也不因此提前宣布训练门失败。

## 当前研究描述，不是终结论

| 臂 | 完整n | T | R | excessC | Nauth | Nwaste |
|---|---:|---:|---:|---:|---:|---:|
| A | 21 | .3857 | .3310 | .4286 | .0952 | .1429 |
| B | 20 | .5650 | .1400 | 7.7000 | 0 | .4000 |
| C | 20 | .3950 | .3550 | .5000 | .0500 | .0500 |
| D | 20 | .5250 | −.1250 | 13.0000 | 0 | 0 |

20题配对B−A＝−.1675，任务bootstrap95%CI[−.5225,.1400]；
D−A＝−.4325，CI[−1.1000,.0350]。
Must平均R：A .3955、B .1600、C .4950、D −.3350；
Optional平均R：A .2600、B .1200、C .2150、D .0850。
CI不是额外门，缺失不记0；**原0.10门仍null，不能判通过或失败**。

本轮真实例揭示“路由进度辅助≠保证what正确”：
service-cutover B先从Li实际获得A-9/6，再获得02:30-03:00，内容复核承认跨回复完成allocation；
但固定执行器后来仍向Liu发送旧A-6/4/01:00，实际readiness被拒。
D从恢复的NPC6之后继续收到缺window回复，在原界限内自然终局；
没有把普通拒绝再次当provider故障，也没有给gold修what/补答案。
campaign asset的实际正确Cedar素材被保留；不因同句拒给不属其职责的headline而抹掉素材事实。
这些都是非盲逐项复核，不是已验证可扩展自动奖励。

H1整体未判，Must A已有10/11问过，不能预设它不愿问；
H2仅局部C−A+.0475、CI跨0；H3局部D−B−.265、CI跨0；
H4局部Optional B−A−.14、CI跨0；H5跨执行器仍未测。
2×2不能分离when/whom因果，B/D是private任务进度路由参考，不是完美oracle或可保证复制的训练效果。
仍披露60题已曝光、单repeat、阶段修复/证据续接、非盲复核；不按成绩改门、不启动训练。
