# 正式 Phase0：真实部分结果、HTTP429停机与两项零API修复

**未完成正式 Phase0，不能宣布训练门通过或不通过。** 正式调用已经发生：完成25/720 episodes，其中6个完整四臂块，均只有repeat0；第26slot因NPC HTTP429停机，余695slot未完成。随后只做离线分析和已证明实现缺陷的修复，0新增API/GET/key读取/GPU/重放/续批。

实际源冻结于 `ce88a589e5cb6f007a7d3bd2c945b5daf3c7fd89`，协议 `study4-formal-phase0-native-llmnpc-1`；修后为显式协议2，**没有真实运行**，不能混入旧数据。原始25条成绩/请求/账本不改写。

审查材料：[机器证据、完整冻结顺序与费用](PHASE0_ACTUAL_STOP_CHECK.json)、
[内容绑定非盲AI复核](PHASE0_ACTUAL_REVIEWS.json)、
[25条完整公共轨迹及实际交付物](PHASE0_ACTUAL_COMPLETED25.jsonl.gz)。
后者不含API认证、HTTP headers或NPC私有system。源文档和原冻结合同继续保留。

## 1. 六个完整块：有真实差异，但不是最终研究答案

下表为同题repeat0的官方R。`?`保留真实语义复核不确定性，不填0，也不把raw候选数冒充已审定值。

| 类别 / 任务 | A 自主 | B 参考when/whom | C 自主+what | D 参考+what |
|---|---:|---:|---:|---:|
| Must / service-credit | 1 | .2 | .5 | 1 |
| Optional / partner-crawl | .95 | .95 | .95 | .95 |
| Must / model-release | .2 | .3 | .2 | −.1 |
| Optional / backup-window | .5 | −.4 | .5 | .2 |
| Must / campaign-spend | .5 | .85 | 0 | 1 |
| Optional / brochure-translation | 0 | ? | 0 | −.6 |

Brochure B的`.08`框架费率和后续12000字解释，涉及跨回复/公开计算能否认证完整信息节点的歧义；2项保持unknown。不能因最终artifact本身错误，就跳过会影响Nwaste的证据问题。其余复核明确标为**非盲AI直接阅读**、绑定实际请求及回复UTF8 SHA256，不宣称独立人审或可扩展准确自动奖励。

| 六题repeat0描述性指标 | A | B | C | D |
|---|---:|---:|---:|---:|
| T均值，全部6题 | .5333 | .5167 | .3667 | .6833 |
| R均值，全部6题 | .5250 | unknown | .3583 | .4083 |
| 公开内容全对 / Optional合法基线通过 | 3/6 | 2/6 | 2/6 | 4/6 |
| 官方base_pass（含私有DAG，仅审计） | 2/6 | 2/6 | 2/6 | 3/6 |
| excess C均值 | .1667 | 5 | .1667 | 4.8333 |
| Nauth总数 | 0 | 0 | 0 | 0 |
| Nwaste总数 | 0 | unknown | 0 | 2 |
| 已交付 / ordinary submit | 6/6 | 6/6 | 6/6 | 6/6 |
| 至少ASK一次 | 4/6 | 6/6 | 4/6 | 6/6 |
| 首次联系合适（有联系者） | 3/4 | 6/6 | 3/4 | 6/6 |
| 官方拒绝计数 | 1 | ≥10 | 1 | 17 |
| 官方补救节点数 | 0 | 1 | 0 | 0 |
| 实际全部角色calls | 33 | 79 | 35 | 94 |
| usage计价上界USD | .078775125 | .250007175 | .085163925 | .839376450 |

内容/合法基线列不把未公开DAG顺序自动当作公开业务要求；官方base_pass另列。Nauth=0也不认证artifact中的批准/签名，post/submit不代替内容检查。R中的C是同事打扰成本，不是API美元；上下文重复主要消耗执行预算，不是直接把美元扣进R。

Must三题R均值A/B/C/D=.5667/.4500/.2333/.6333；Optional三题A/C=.4833、D=.1833，B整体unknown。第25个未配对完成slot是support-renewal的C：T/R=.75/.75，不能混进上述六题比较。未完成的D不记业务0。

仅作探索性描述：六题repeat0的D−A=−.1167，任务配对bootstrap95%区间[−.3667,.1833]。这不是原定“三重复后60题等权”的正式区间，更不是跨组织区间。没有任何任务完成三重复，正式mean(B−A)或mean(D−A)≥.10的门**未判定**；也不根据此小样本改门、挑repeat或宣布只有执行器是瓶颈。

实际机制已经可见：campaign中参考路由帮助联系第二位审批人，B/D优于A；service-credit中B问对人却反复漏问正确比例；model-release中已提供EV-19仍被NPC要求额外材料，参考字面进度还造成重复联系。A在三道Must均主动ASK，首联2/3合适，与“mini几乎不问”的预期不同，但样本不足推断总体。

## 2. H1–H5当前判定

| 假设 | 判定 | 依据和不能推出的结论 |
|---|---|---|
| H1：Must主要受益于逼mini问 | 无法判断；当前前提有反例线索 | 三道Must的A均问；Must D−A约+.0667、B−A约−.1167。2×2不能独立识别when与whom因果贡献。 |
| H2：C−A很小 | 无法判断 | 当前C−A=−.1667，但只有repeat0，且若干差异在首次无历史补全时已出现，包含随机回答差异；“很小”无预注册数值阈值。 |
| H3：D−B>0 | 无法判断；有局部正例 | campaign D−B=.15、service-credit=.8，model-release却为−.4；一题R未决且旧what实现不忠实。 |
| H4：Optional B−A不正 | 无法判断；局部方向支持 | crawl相同、backup B−A=−.9，brochure B未决；不能从三题外推总体成本权重。 |
| H5：换强执行器后差值变小 | 无法判断 | 只跑固定mini，没有GPT-5.4匹配对照；不扩范围。 |

因此**不启动训练**。若后续有效Phase0过门，才按证据选择when核心、公开职责whom SFT、公开what规则等条件方案；当前不足以默认when-only或三头齐训。问题组成/被拒补救与NPC可靠性是实际已见瓶颈，而非已经证明单一根因。

## 3. 停机与费用：不是余额耗尽

2026-11-12 21:58 UTC停止：331新calls，330 settled、1 unknown，无in-flight。新NPC请求收到HTTP429；持久诊断为`stage=status`、1547ms、`deadline_expired=false`、241642 request bytes。没有保存可区分rate/TPM/quota的响应正文，**不能从长度推出429的原因**。不改timeout/endpoint、不重试、不GET。

| 同一原USD50累计项目 | USD |
|---|---:|
| 旧settled计价上界 | .069303300 |
| 本轮330 settled计价上界 | 3.892921725 |
| 合计settled计价上界 | 3.962225025 |
| 旧4 unknown保留 | 3.432 |
| 新unknown保留 | .858 |
| 合计占帽 | 8.252225025 |
| 剩余额度（已扣全部unknown） | 41.747774975 |

unknown是保守占帽，不是确认实付。所有NPC/question/executor/preflight均共帽；未打开另一个50。七个旧root原字节和原47call状态再次核对不变。

## 4. 127651 tokens的实际来源，不是“正常长对话”一句带过

问题slot为`m-med-support-renewal:D:r0`。实际28 ASK、27已读、27ordinary动作；question28 settled、ordinary27 settled、NPC27 settled+1 unknown。82 settled单独计价USD2.625319125。记录中7次write、1次post、13次submission_blocked。

| actual结构 | 首次 | 最后 |
|---|---:|---:|
| Agent请求bytes | 8332 | 569996 |
| Agent真实usage input tokens | 1648 | 127651 |
| NPC请求bytes | 2408 | 241642 |

最后Agent请求只有一个当前state，但state自身253726 bytes（history247402）外，还附108个native function/history items共290664 bytes；同一批公开消息被state.history与工具receipt重复表达。**不是递归嵌套旧完整state。**

更大膨胀来自旧public_what每次追加全部旧回复原文；最后NPC请求中，精确离线字节分解有223996 bytes来自这些重复appendices，去掉仅用于分解的片段后自然问答结构17646 bytes。实际NPC system仅1份、同一联系人27个user/26个assistant；0次回复回显该appendix结构，排除“NPC抄整段历史再递归”的解释。该离线分解从未发送，不是建议删除原始受保护证据。

另一个已证bug：7次write内容SHA完全相同，post在event27，后续相同内容write却使revision递增，造成不必要的交付失效与13次submit阻断。它不是controller SUBMIT。即使去掉虚假阻断，artifact中的签名/授权依旧不正确，不能据此称任务成功。

28条实际问题没有一条带7800，虽然Agent草稿写着7800。规则只能引用真实已读消息，不能把草稿计算冒充NPC确认。公开单价/座数可以作为可审计的公开计算来源，但本轮修复不硬编码7800、不定制task ID，也不声称已实现新的计算补全能力。

## 5. 已完成的最小协议2修复（零API）

- `phase0.py`：公开来源按稳定消息ID核验去重，不把不同请求下字面相同的“Approved”合并。来源保留回复绑定、请求原始上下文及哈希，明确请求不是确认；候选值去重并引用来源，新来源原文每收件人只传一次。冲突值和原始否定/批准资格保留，不将提及当grant；后续NPC完整对话保留先前已传原文，不反复塞整段历史。
- 同一公开事件仅在native receipts中完整表达；当前state保留尚未表达的tail并显式声明表示方式。function_call及对应output不删；control、实际send/read、普通工具事件与来源均可无损恢复，不以隐藏事件缩短模型输入。
- `runtime.py`：相同路径相同字节write仍记事件、消耗普通一步，但不增内容revision；真实字节变化仍增revision并须重新post。没有强制代交付或改任务答案。
- 新协议provider恢复显式阻断；旧authority/新root不能默认绕过本轮unknown。新scope必须先绑定全部378次累计调用、373 settled与5 unknown，再走单一原USD50授权路径。

同一已保存结构的**离线重编码**：Agent569996→145832 bytes，NPC241642→67319 bytes；27条已读回复的ID和原始内容全部保留，108个历史事件完整单份表示。**没有新的token usage、provider接受或研究收益证据。**来源引用索引仍会增长，不承诺所有费用严格线性。

44项相关离线回归通过：28轮长对话单份事件/不重引全部旧原文、冲突值与资格保留、同字批准不合并请求、公私隔离、草稿不冒充确认；7次相同write后仍可ordinary submit、真实变化仍需post；未知费用/单函数/预算门不放宽。源与审查证据分版本，旧数据不改分。

**偏差必须承认**：旧C/D虽然只用公开数据，但“每次整段重附”偏离预期公开值补全；加上桥接错误，旧六块不能作为忠实实现Phase0的终结论。A/B仍有虚拟环境/64步等论文兼容性限制，B/D又是可误判自然语言进度的路由参考，不是已认证完美oracle；同LLM NPC也会越条件披露或过度拒绝。不能把这些限制藏成训练收益/失败。

## 6. 预算可行性与下一次可执行恢复

六个完整块24episodes实际241 calls、USD1.23137025。若余695slot重复其均值，约需USD35.66；每26slot以一个本次**尚未完成**的USD2.625尾部替换普通slot，约USD104.46。不是CI或最坏保证，尾部还被截尾，六题不能代表全60。

真正重新启动统一协议2须完整720而非仅补695：相同完成均值情景约USD36.94，落在剩USD41.75内；相同“每26有一个截尾尾部”情景约USD108.22。**无法保证原50跑完**。这是基于旧实测的情景，不是修后费用预测；没有tokenizer或新usage，byte下降不能换称token/费用下降。

需要一次明确的**统一协议2恢复授权及累计账本绑定**，不是无目的再probe：先包含现5笔unknown与所有settled，不释放/重放旧请求；重新冻结同60×4×3四臂统一输入版本和执行顺序。原25条保留为旧版本诊断，不能补695条就拼成同协议720。以正式配对块兼作必要接口验收，无额外孤立付费probe；如果获准推进，则沿冻结顺序到完整覆盖或同帽/unknown安全门停止。不减步数、不裁受保护来源、不改门以凑预算。

当前到此停止：代码修复及离线验收已完成；没有恢复调用、训练、RL、GPU或终测。
