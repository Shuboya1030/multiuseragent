# 单动作prompt v2：一次真实验证在传输层停止

**2026-11-12：本轮获准的一次新验证已尝试；没有取得可解码的响应，记录为
`TransportFailure / unknown`。未恢复48episode实验，没有任务收益或headroom结论。**
旧两笔unknown共USD1.716保持不变，新预留USD0.858继续占帽，合计USD2.574，
仍在原独立USD50内；这不是已结算实付。没有第二probe、GET、重放、工具执行或GPU作业。

机器证据：[实际验收与指纹](PROMPT_V2_VALIDATION_CHECK.json)；
[本轮发布指纹](PROMPT_V2_CONTINUATION_PUBLICATION_MANIFEST.json)。
前次[双动作诊断与prompt修订](SINGLE_DIAGNOSTIC_ACTUAL_ZH.md)是历史记录，不被本报告改写。

## 此次授权和实际执行

用户在“修订prompt验证一次，成功后继续原最多48episode；同USD50、旧unknown继续占帽”
的限定方案后回复`status? continue`。本轮来源为
`b3cd1516-3d61-45fa-8e7b-08d83f526004`、revision 5。
批准记录绑定完整plan、runtime、请求、唯一输出根和旧证据指纹，不是新的USD50预算。

| 项目 | 实际状态 |
|---|---|
| executor | 固定`gpt-5.4-mini-2026-03-17`，standard/default纯文本域 |
| ordinary prompt | 四臂共用`study4-ordinary-single-action-v2`；本回合一个动作后等待结果 |
| 请求语义 | 原首slot `o-low-team-lunch / A / r0`的初始公开状态；更新prompt，不执行输出动作 |
| NPC | 既定结构化规则NPC，零NPC API；本次未触发NPC |
| 请求SHA256 | `45981a05aefa1ecfc257a7eb8d086ab8b6193e808f67e8a8a28f4c541f705e3b` |
| plan SHA256 | `64e372e9752d3413f96905398986e5f2fc755f3f648656d8f3404222fb4b7fe6` |
| 实际运行源码commit | `48130a30bb88457485c3d77ff34428d2207ccab7` |
| 持久reserve | 2026-11-12 19:15:24.342456 UTC，USD0.858 |
| send permit | 19:15:24.345008 UTC；先持久reserve，再进入单次HTTP适配器 |
| 停止 | 19:15:35.503845 UTC；`TransportFailure`转unknown |
| 响应/解码 | 无返回给调用方的完整response bytes、hash、usage或shape；未进入七阶段decoder |
| 工具/episode | 0工具、0联系、0完整episode；未创建本轮48episode批次 |

`model_HTTP_attempts=1`是本地适配器尝试计数，不证明POST已到达provider或provider已完成推理。
累计三次本地dispatch尝试，前两次有响应，本次是否到达provider未知。

## 哪一层失败，能否修复？

**已证实**：新call的持久顺序为`reserved → send_permitted → unknown`，
错误类型`TransportFailure`，响应长度/hash为null，diagnostic为`{}`。
没有`ACTUAL_RESPONSE_SHAPE.json`，因为适配器没有向observer返回raw bytes。
从send permit到记录unknown约11.159秒，不能单凭耗时断言超时原因。

**源码能说明的范围**：[HTTP适配器](../http_transport.py)把
`http.client.HTTPException`、`TimeoutError`或`OSError`统一转换为`TransportFailure`。
连接、发送、获取响应头、读取响应体均可能走这个边界；原始异常细分未被保留。
本次没有HTTP成功状态、错误正文、底层异常类型或精确内部阶段的证据，
不能声称是401、限流、DNS、TLS、网络中断、provider故障或30秒deadline。
也不能声称“HTTP成功但应用拒绝”——那是前次双动作请求的事实，不是本次。

**离线验证**：新增一个四子案例的无socket注入测试，分别在connect、request、
getresponse、read抛出不同标准传输异常，均得到同样的unknown与空diagnostic。
它证明仅靠当前持久类型无法区分这些候选，不复现或确定本次具体根因。
因此没有据猜测更改timeout、endpoint、重试、输出schema或挑选首个动作。

三次请求必须分开解释：

| 尝试 | 已知边界 | 不可推断 |
|---|---|---|
| 原ceiling首call | HTTP返回有usage，随后本地ValueError；旧诊断不足，原body不可恢复 | 不能断言也是双动作 |
| 原单请求诊断 | HTTP completed/default，有usage；两条assistant动作`write_file`和`post_channel`，在`output_items`严格拒绝 | 不能证明prompt措辞就是因果根因 |
| 本次prompt v2验证 | 传输适配器未返回完整body，`TransportFailure`；0工具 | 无法检验新prompt是否单动作、provider是否接受/完成该请求 |

## 同一个USD50费用边界

| 账目 | unknown保留上界 | settled上界 |
|---|---:|---:|
| 原ceiling首call | USD0.858 | USD0 |
| 原单请求诊断 | USD0.858 | USD0 |
| 本次prompt v2验证 | USD0.858 | USD0 |
| 累计 | **USD2.574** | **USD0** |

原两笔没有被打开为active ledger、改写、结算或释放。
本次使用新版本记录，但其每次admission都先计入旧USD1.716，
不是通过换namespace获得新帽。帽内未占用USD47.426不代表有权自动继续请求。
保守模型最大reserve为272000input＋128000output、含10%uplift；
每次实际wire输出上限仍1024。不能把reserve当实付，也不保证含税费等所有账单。
本次无usage，不能计算或猜测本次实际费用；前两次usage参考也没有用于结算unknown。

## 已完成的最小恢复安全门

代码见[ceiling_continuation.py](../ceiling_continuation.py)和
[针对性测试](../test_ceiling_continuation.py)：

1. 两个旧ledger与全部冻结文件逐字节核对，只用immutable只读连接查询旧状态；
   持有旧run的OS mutex，新run有独立mutex；旧未知一直占原总帽。
2. 验证只允许冻结ordinary请求、index 0、一次HTTP且0工具；
   请求/批准/source/版本漂移和重复启动在发送前拒绝。
3. 只有验证合法settle且无unknown，才允许同版本、原六题×四臂×两次的fresh-only批次；
   原均衡相邻四臂顺序、24action上限和工具合同不变。
   新批次须累计旧unknown与preflight settled费用，并扣除之前call/token暴露。
4. 本地脚本48slot条件继续、互斥、余额不足、unknown保留USD2.574、
   工具生效后中断禁止重放均有测试；这不是48次真实推理或ceiling成功。
   episode/tool exactly-once恢复未被宣称已证明，中断后仍整批停、不恢复。

本轮**99项v2离线测试＋12项旧协议回归通过**。
本地mock/loopback不是provider服务端验收，99项成功不能代替本次失败的真实验证。
prompt、严格多message/坏参数拒绝、SELF一步及全部历史模型/评分/结果保持不变。

## 研究结论与下一门

原定48slot未开始，四臂真实内容pass、用户交付、桥接submit、T、官方R、
联系成本、权限安全及配对/组织不确定性**全部无新可计算样本**。
不能将infra incomplete当业务失败、T/R=0，也不能从脚本perfect结果推论真实oracle headroom。
旧六曝光开发题仍不是独立终测。

当前限制是**真实调用的可靠性和可观测性**，尚未到能据任务结果决定下一训练的阶段。
后续若要重试或新增诊断，须新的明确真实请求授权；
若增加传输阶段诊断，应只保存固定阶段、异常类型和状态码等白名单，不保存凭据/headers/任意错误正文，
并先做本地故障测试。是否改变timeout或其他传输配置必须显式版本化，不由这次未知原因推出。
目前停止全部付费；没有新训练、采集、RL、终测、Colab连接或GPU作业。
