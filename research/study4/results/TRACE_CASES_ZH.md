# 四组真实配对trace：控制器到底做了什么

只读既有16dev/32次执行及原教师数据；没有新增API、GPU推理或训练。cycle为0起算。
[阅读入口](../README.md) · [诊断](DIAGNOSIS_ZH.md) · [公开机器索引](evidence/trace_cases.json)

下列原trace名称是未公开原始archive中的来源标识，不是已上传文件链接；JSONL行号1起算，事件索引=行号−1。
本文是最终V2提取的公开节选，不是原字节；原trace SHA与本文自身SHA分别登记，见[证据说明](EVIDENCE_ZH.md)。
公开机器索引保留全部已有label概率、实际工具命令与事件引用，省略完整请求/响应转储和私有参考全库。
离线参考只为分析解释，**没有输入控制器**。

**概率口径**：SFT行中的p来自原trace完整label序列分数softmax，不是任务成功概率；
argmax选择的行为概率为1，不等于p(NO_ASK)。原生API动作概率未记录，不能伪造。
逐cycle原始绝对log-score未持久化；下列Δlog由log(p_top/p_runner-up)恢复，
只能恢复分差，不能恢复绝对值。已有单状态GPU工程probe的绝对值见[摘要](evidence/summary.json)。

## 客户邮件：该再问一次，却没有问

`m-low-customer-mailing`；选择理由：唯一原生ASK，能核实NPC实际回复及第二次授权缺口。

**公开指令**：As of 2026-11-05: Prepare the customer mailing request for the Q4 upgrade notice to enterprise accounts. Save /workspace/deliverable.json with segment_id, recipient_count, send_date, authorization_ref. Post a short summary and the file path in #engineering.

**初始可见/缺口**：公开mailer明确上季度SEG-Q3-ENT/420/APR-Q3；当前segment、count和批准号未读到。policy要求Sales Director提供当前segment并批准。

初始workspace已包含全部公共documents及directory，未read_file不代表没看到文档。

### 原生mini（无外置控制器）

原trace：`archive:study4_teacher87_eval_v6_native_mini_gpu_gate_v4_frozen_flags / teacher87-dev16-m-low-customer-mailing-native_mini-r1.trace.jsonl`
SHA256：`3a80efdd4e60ecf948c1b5dc3f0ae915f8daa1ad94d83216de8ad12f8d4b1564`（24行）。

legal actions（各cycle相同，直到停止）：`NO_ASK`, `ASK:Mark Johnson`, `ASK:Li Ming`, `ASK:Jessica Chen`, `ASK:Jessica Lee`。

| cycle / 决策行 | 决策前公开状态 | 实际动作、已有置信分差 | mini实际工具与参数节选 | 观察变化/停止 |
|---|---|---|---|---|
| 0 / L3 | 余8，history=0，phase=decision | ASK:Mark Johnson；原生概率/分数未知 | NATIVE: `{"tool":"ask_colleague","arguments":{"person_id":"Mark Johnson","question":"Please provide the current enterprise account segment ID and authorization reference to use for the Q4 upgrade notice customer mailing. We already have the send date 2026-11-12 and last quarter’s reference was SEG-Q3-ENT / APR-Q3, but I need the current …〔节选；此处为参数节选；结构化工具命令见公开索引〕`<br>SELF: `{"tool":"write_file","arguments":{"path":"/workspace/deliverable.json","content":"{\"segment_id\":\"SEG-Q4-ENT\",\"recipient_count\":455,\"send_date\":\"2026-11-12\",\"authorization_ref\":\"APR-Q3\"}"}}` | history 0→4；C=3；余7cycle |
| 1 / L13 | 余7，history=4，phase=decision；已有deliverable | NO_ASK；原生概率/分数未知 | NATIVE: `{"tool":"post_channel","arguments":{"channel":"#engineering","content":"Customer mailing request prepared and saved at /workspace/deliverable.json. Summary: enterprise Q4 upgrade notice with segment SEG-Q4-ENT, 455 recipients, send date 2026-11-12, authorization ref APR-Q3."}}` | history 4→5；C=3；余6cycle |
| 2 / L19 | 余6，history=5，phase=decision；已有deliverable | NO_ASK；原生概率/分数未知 | NATIVE: `{"tool":"submit","arguments":{"answer":"Completed: /workspace/deliverable.json saved with the customer mailing JSON. Posted summary to #engineering: enterprise Q4 upgrade notice, segment SEG-Q4-ENT, 455 recipients, send date 2026-11-12, authorization ref APR-Q3."}}` | history 5→6；C=3；submit终止 |

**原结果**：business_pass=False；T=0.75；R=0.6；C=3.0；workflow_business_success=False。 artifact=True，channel摘要=True，submit=True。

**实际NPC回复（L7）**：`{"recipient_count":455,"segment_id":"SEG-Q4-ENT"}`。
只有当前segment/count，没有批准号；mini写入的是新segment/count但旧APR-Q3。
离线私有参考确认：第二个record要求先拿到H1，再向Mark带SEG-Q4-ENT/455请求批准。
原生后续没有第二次ask，不能把一次正确求助说成完整解决授权链。

### mini + SFT87（argmax）

原trace：`archive:study4_teacher87_eval_v6_native_mini_gpu_gate_v4_frozen_flags / teacher87-dev16-m-low-customer-mailing-sft87-r1.trace.jsonl`
SHA256：`b9b85d31a5a4a7749f2303c5dc11fe2d69d35e1896db279b831aebd4af52d626`（50行）。

legal actions（各cycle相同，直到停止）：`NO_ASK`, `ASK:Mark Johnson`, `ASK:Li Ming`, `ASK:Jessica Chen`, `ASK:Jessica Lee`。

| cycle / 决策行 | 决策前公开状态 | 实际动作、已有置信分差 | mini实际工具与参数节选 | 观察变化/停止 |
|---|---|---|---|---|
| 0 / L3 | 余8，history=0，phase=decision | NO_ASK；p(NO)=0.7495，次高ASK:Mark Johnson=0.1717；Δp=0.5778，Δlog=1.4737 | SELF: `{"tool":"write_file","arguments":{"path":"/workspace/deliverable.json","content":"{\"segment_id\":\"SEG-Q3-ENT\",\"recipient_count\":420,\"send_date\":\"2026-11-12\",\"authorization_ref\":\"APR-Q3\"}"}}` | history 0→1；C=0；余7cycle |
| 1 / L9 | 余7，history=1，phase=decision；已有deliverable | NO_ASK；p(NO)=0.8761，次高ASK:Mark Johnson=0.0806；Δp=0.7955，Δlog=2.3856 | SELF: `{"tool":"post_channel","arguments":{"channel":"#engineering","content":"Prepared customer mailing deliverable for enterprise upgrade notice.\nFile: /workspace/deliverable.json"}}` | history 1→2；C=0；余6cycle |
| 2 / L15 | 余6，history=2，phase=decision；已有deliverable | NO_ASK；p(NO)=0.8702，次高ASK:Mark Johnson=0.0850；Δp=0.7852，Δlog=2.3265 | SELF: `{"tool":"write_file","arguments":{"path":"/workspace/deliverable.json","content":"{\"segment_id\":\"SEG-Q3-ENT\",\"recipient_count\":420,\"send_date\":\"2026-11-12\",\"authorization_ref\":\"APR-Q3\"}"}}` | history 2→3；C=0；余5cycle |
| 3 / L21 | 余5，history=3，phase=decision；已有deliverable | NO_ASK；p(NO)=0.8487，次高ASK:Mark Johnson=0.0964；Δp=0.7522，Δlog=2.1747 | SELF: `{"tool":"post_channel","arguments":{"channel":"#engineering","content":"Prepared customer mailing deliverable for enterprise upgrade notice.\nFile: /workspace/deliverable.json"}}` | history 3→4；C=0；余4cycle |
| 4 / L27 | 余4，history=4，phase=decision；已有deliverable | NO_ASK；p(NO)=0.7412，次高ASK:Mark Johnson=0.1653；Δp=0.5759，Δlog=1.5005 | SELF: `{"tool":"write_file","arguments":{"path":"/workspace/deliverable.json","content":"{\"segment_id\":\"SEG-Q3-ENT\",\"recipient_count\":420,\"send_date\":\"2026-11-12\",\"authorization_ref\":\"APR-Q3\"}"}}` | history 4→5；C=0；余3cycle |
| 5 / L33 | 余3，history=5，phase=decision；已有deliverable | NO_ASK；p(NO)=0.7476，次高ASK:Mark Johnson=0.1624；Δp=0.5852，Δlog=1.5267 | SELF: `{"tool":"write_file","arguments":{"path":"/workspace/deliverable.json","content":"{\"segment_id\":\"SEG-Q3-ENT\",\"recipient_count\":420,\"send_date\":\"2026-11-12\",\"authorization_ref\":\"APR-Q3\"}"}}` | history 5→6；C=0；余2cycle |
| 6 / L39 | 余2，history=6，phase=decision；已有deliverable | NO_ASK；p(NO)=0.8010，次高ASK:Mark Johnson=0.1338；Δp=0.6672，Δlog=1.7897 | SELF: `{"tool":"write_file","arguments":{"path":"/workspace/deliverable.json","content":"{\"segment_id\":\"SEG-Q4-ENT\",\"recipient_count\":420,\"send_date\":\"2026-11-12\",\"authorization_ref\":\"APR-Q3\"}"}}` | history 6→7；C=0；余1cycle |
| 7 / L45 | 余1，history=7，phase=decision；已有deliverable | NO_ASK；p(NO)=0.8270，次高ASK:Mark Johnson=0.1065；Δp=0.7206，Δlog=2.0499 | SELF: `{"tool":"post_channel","arguments":{"channel":"#engineering","content":"Prepared Q4 enterprise customer mailing deliverable.\nFile: /workspace/deliverable.json"}}` | history 7→8；C=0；8cycle截止，非submit |

**原结果**：business_pass=False；T=0.5；R=0.5；C=0.0；workflow_business_success=False。 artifact=True，channel摘要=True，submit=False。

**全部label概率**（完整精度在公开机器索引；此处四位小数）：

| cycle | NO_ASK | ASK:Mark Johnson | ASK:Li Ming | ASK:Jessica Chen | ASK:Jessica Lee |
|---|---|---|---|---|---|
| 0 | 0.7495 | 0.1717 | 0.0266 | 0.0463 | 0.0059 |
| 1 | 0.8761 | 0.0806 | 0.0094 | 0.0307 | 0.0032 |
| 2 | 0.8702 | 0.0850 | 0.0111 | 0.0301 | 0.0037 |
| 3 | 0.8487 | 0.0964 | 0.0107 | 0.0410 | 0.0032 |
| 4 | 0.7412 | 0.1653 | 0.0208 | 0.0667 | 0.0060 |
| 5 | 0.7476 | 0.1624 | 0.0194 | 0.0651 | 0.0055 |
| 6 | 0.8010 | 0.1338 | 0.0155 | 0.0456 | 0.0041 |
| 7 | 0.8270 | 0.1065 | 0.0149 | 0.0468 | 0.0048 |

**原教师实际动作，不是oracle**：c0:ASK:Mark Johnson → c1:ASK:Mark Johnson → c2:NO_ASK → c3:NO_ASK → c4:NO_ASK。
原教师结果T=1.0、business_pass=True；教师trace路径/hash和训练MODEL_INPUTS行号见JSON索引。

## 演示数据：不求助本来可以，问题出在不停止

`o-low-demo-dataset`；选择理由：Optional合法旧版可用，隔离求助决策与工具/submit循环。

**公开指令**：As of 2026-11-05: Prepare the sales demo setup for search relevance. Save /workspace/deliverable.json with dataset_id, document_count, refreshed_on. Post a short summary and the file path in #engineering.

**初始可见/缺口**：公开旧DS-DEMO-2合法可用；更新版只提升质量，不问人本身不构成业务错误。应避免重复发同一摘要，并按当前桥接协议submit。

初始workspace已包含全部公共documents及directory，未read_file不代表没看到文档。

### 原生mini（无外置控制器）

原trace：`archive:study4_teacher87_eval_v6_native_mini_gpu_gate_v4_frozen_flags / teacher87-dev16-o-low-demo-dataset-native_mini-r1.trace.jsonl`
SHA256：`7e589ceceb74ecb58653b6cbc2b48bf3566b0a746f3e2c171d881fbf1ccdab3e`（20行）。

legal actions（各cycle相同，直到停止）：`NO_ASK`, `ASK:Emily Zhou`, `ASK:Priya Sharma`, `ASK:Zhang Wei`, `ASK:David Wong`, `ASK:Mark Johnson`, `ASK:Jessica Lee`, `ASK:Sarah Johnson`, `ASK:Li Ming`。

| cycle / 决策行 | 决策前公开状态 | 实际动作、已有置信分差 | mini实际工具与参数节选 | 观察变化/停止 |
|---|---|---|---|---|
| 0 / L3 | 余8，history=0，phase=decision | NO_ASK；原生概率/分数未知 | NATIVE: `{"tool":"write_file","arguments":{"path":"/workspace/deliverable.json","content":"{\"dataset_id\":\"DS-DEMO-2\",\"document_count\":420000,\"refreshed_on\":\"2025-12-01\"}"}}` | history 0→1；C=0；余7cycle |
| 1 / L9 | 余7，history=1，phase=decision；已有deliverable | NO_ASK；原生概率/分数未知 | NATIVE: `{"tool":"post_channel","arguments":{"channel":"#engineering","content":"Prepared sales demo search-relevance deliverable at /workspace/deliverable.json with dataset_id DS-DEMO-2, document_count 420000, refreshed_on 2025-12-01."}}` | history 1→2；C=0；余6cycle |
| 2 / L15 | 余6，history=2，phase=decision；已有deliverable | NO_ASK；原生概率/分数未知 | NATIVE: `{"tool":"submit","arguments":{"answer":"Done. Deliverable saved at /workspace/deliverable.json and summary posted to #engineering."}}` | history 2→3；C=0；submit终止 |

**原结果**：business_pass=True；T=0.5；R=0.5；C=0.0；workflow_business_success=True。 artifact=True，channel摘要=True，submit=True。

### mini + SFT87（argmax）

原trace：`archive:study4_teacher87_eval_v6_native_mini_gpu_gate_v4_frozen_flags / teacher87-dev16-o-low-demo-dataset-sft87-r1.trace.jsonl`
SHA256：`71ac6e02842e41cee6b523ee689ef8e214220ab15a24753557d7bc83ba752511`（50行）。

legal actions（各cycle相同，直到停止）：`NO_ASK`, `ASK:Emily Zhou`, `ASK:Priya Sharma`, `ASK:Zhang Wei`, `ASK:David Wong`, `ASK:Mark Johnson`, `ASK:Jessica Lee`, `ASK:Sarah Johnson`, `ASK:Li Ming`。

| cycle / 决策行 | 决策前公开状态 | 实际动作、已有置信分差 | mini实际工具与参数节选 | 观察变化/停止 |
|---|---|---|---|---|
| 0 / L3 | 余8，history=0，phase=decision | NO_ASK；p(NO)=0.7146，次高ASK:Emily Zhou=0.1841；Δp=0.5305，Δlog=1.3561 | SELF: `{"tool":"write_file","arguments":{"path":"/workspace/deliverable.json","content":"{\"dataset_id\":\"DS-DEMO-2\",\"document_count\":420000,\"refreshed_on\":\"2025-12-01\"}"}}` | history 0→1；C=0；余7cycle |
| 1 / L9 | 余7，history=1，phase=decision；已有deliverable | NO_ASK；p(NO)=0.7888，次高ASK:Emily Zhou=0.1393；Δp=0.6495，Δlog=1.7341 | SELF: `{"tool":"post_channel","arguments":{"channel":"#engineering","content":"Saved deliverable for sales demo setup: /workspace/deliverable.json"}}` | history 1→2；C=0；余6cycle |
| 2 / L15 | 余6，history=2，phase=decision；已有deliverable | NO_ASK；p(NO)=0.8640，次高ASK:Emily Zhou=0.0890；Δp=0.7749，Δlog=2.2724 | SELF: `{"tool":"post_channel","arguments":{"channel":"#engineering","content":"Saved deliverable for sales demo setup: /workspace/deliverable.json"}}` | history 2→3；C=0；余5cycle |
| 3 / L21 | 余5，history=3，phase=decision；已有deliverable | NO_ASK；p(NO)=0.9158，次高ASK:Emily Zhou=0.0576；Δp=0.8582，Δlog=2.7661 | SELF: `{"tool":"post_channel","arguments":{"channel":"#engineering","content":"Saved deliverable for sales demo setup: /workspace/deliverable.json"}}` | history 3→4；C=0；余4cycle |
| 4 / L27 | 余4，history=4，phase=decision；已有deliverable | NO_ASK；p(NO)=0.8628，次高ASK:Emily Zhou=0.0979；Δp=0.7649，Δlog=2.1760 | SELF: `{"tool":"post_channel","arguments":{"channel":"#engineering","content":"Saved deliverable for sales demo setup: /workspace/deliverable.json"}}` | history 4→5；C=0；余3cycle |
| 5 / L33 | 余3，history=5，phase=decision；已有deliverable | NO_ASK；p(NO)=0.8349，次高ASK:Emily Zhou=0.1183；Δp=0.7165，Δlog=1.9540 | SELF: `{"tool":"post_channel","arguments":{"channel":"#engineering","content":"Saved deliverable for sales demo setup: /workspace/deliverable.json"}}` | history 5→6；C=0；余2cycle |
| 6 / L39 | 余2，history=6，phase=decision；已有deliverable | NO_ASK；p(NO)=0.8256，次高ASK:Emily Zhou=0.1254；Δp=0.7002，Δlog=1.8845 | SELF: `{"tool":"post_channel","arguments":{"channel":"#engineering","content":"Saved deliverable for sales demo setup: /workspace/deliverable.json"}}` | history 6→7；C=0；余1cycle |
| 7 / L45 | 余1，history=7，phase=decision；已有deliverable | NO_ASK；p(NO)=0.8269，次高ASK:Emily Zhou=0.1212；Δp=0.7057，Δlog=1.9206 | SELF: `{"tool":"post_channel","arguments":{"channel":"#engineering","content":"Saved deliverable for sales demo setup: /workspace/deliverable.json"}}` | history 7→8；C=0；8cycle截止，非submit |

**原结果**：business_pass=True；T=0.5；R=0.5；C=0.0；workflow_business_success=False。 artifact=True，channel摘要=True，submit=False。

**全部label概率**（完整精度在公开机器索引；此处四位小数）：

| cycle | NO_ASK | ASK:Emily Zhou | ASK:Priya Sharma | ASK:Zhang Wei | ASK:David Wong | ASK:Mark Johnson | ASK:Jessica Lee | ASK:Sarah Johnson | ASK:Li Ming |
|---|---|---|---|---|---|---|---|---|---|
| 0 | 0.7146 | 0.1841 | 0.0314 | 0.0081 | 0.0095 | 0.0061 | 0.0140 | 0.0171 | 0.0151 |
| 1 | 0.7888 | 0.1393 | 0.0219 | 0.0068 | 0.0085 | 0.0049 | 0.0124 | 0.0104 | 0.0071 |
| 2 | 0.8640 | 0.0890 | 0.0116 | 0.0049 | 0.0066 | 0.0037 | 0.0075 | 0.0067 | 0.0060 |
| 3 | 0.9158 | 0.0576 | 0.0059 | 0.0026 | 0.0039 | 0.0023 | 0.0039 | 0.0043 | 0.0035 |
| 4 | 0.8628 | 0.0979 | 0.0087 | 0.0032 | 0.0058 | 0.0028 | 0.0073 | 0.0070 | 0.0043 |
| 5 | 0.8349 | 0.1183 | 0.0095 | 0.0044 | 0.0064 | 0.0036 | 0.0100 | 0.0077 | 0.0052 |
| 6 | 0.8256 | 0.1254 | 0.0104 | 0.0045 | 0.0060 | 0.0036 | 0.0113 | 0.0074 | 0.0059 |
| 7 | 0.8269 | 0.1212 | 0.0127 | 0.0063 | 0.0064 | 0.0036 | 0.0091 | 0.0080 | 0.0058 |

**原教师实际动作，不是oracle**：c0:NO_ASK → c1:NO_ASK → c2:NO_ASK。
原教师结果T=0.5、business_pass=True；教师trace路径/hash和训练MODEL_INPUTS行号见JSON索引。

## 政策引用：明确过时的信息被直接复用

`m-low-policy-citation`；选择理由：单跳、公开角色线索清晰，不需要多级授权也未求助。

**公开指令**：As of 2026-11-05: Prepare the compliance checklist entry citing the remote-work policy. Save /workspace/deliverable.json with policy, version, effective_date, url_slug. Post a short summary and the file path in #engineering.

**初始可见/缺口**：checklist明确从去年复制；wiki-policy说明Documentation Engineer维护发布版本。未向Priya核实现行版本。

初始workspace已包含全部公共documents及directory，未read_file不代表没看到文档。

### 原生mini（无外置控制器）

原trace：`archive:study4_teacher87_eval_v6_native_mini_gpu_gate_v4_frozen_flags / teacher87-dev16-m-low-policy-citation-native_mini-r1.trace.jsonl`
SHA256：`7ccc86e144fe4bd498d315cd67c94602b94d02b4e60bb1f7e7d303cc2cdf14fa`（20行）。

legal actions（各cycle相同，直到停止）：`NO_ASK`, `ASK:Alex Turner`, `ASK:Sophia Rodriguez`, `ASK:Emily Zhou`, `ASK:Jessica Chen`, `ASK:Emma Lewis`, `ASK:Priya Sharma`, `ASK:Jessica Lee`, `ASK:Huang Jie`。

| cycle / 决策行 | 决策前公开状态 | 实际动作、已有置信分差 | mini实际工具与参数节选 | 观察变化/停止 |
|---|---|---|---|---|
| 0 / L3 | 余8，history=0，phase=decision | NO_ASK；原生概率/分数未知 | NATIVE: `{"tool":"write_file","arguments":{"path":"/workspace/deliverable.json","content":"{\"policy\":\"remote-work\",\"version\":\"v3.1\",\"effective_date\":\"2026-01-01\",\"url_slug\":\"remote-work-v3\"}"}}` | history 0→1；C=0；余7cycle |
| 1 / L9 | 余7，history=1，phase=decision；已有deliverable | NO_ASK；原生概率/分数未知 | NATIVE: `{"tool":"post_channel","arguments":{"channel":"#engineering","content":"Compliance checklist entry ready: /workspace/deliverable.json"}}` | history 1→2；C=0；余6cycle |
| 2 / L15 | 余6，history=2，phase=decision；已有deliverable | NO_ASK；原生概率/分数未知 | NATIVE: `{"tool":"submit","arguments":{"answer":"{\"policy\":\"remote-work\",\"version\":\"v3.1\",\"effective_date\":\"2026-01-01\",\"url_slug\":\"remote-work-v3\"}"}}` | history 2→3；C=0；submit终止 |

**原结果**：business_pass=False；T=0.25；R=0.25；C=0.0；workflow_business_success=False。 artifact=True，channel摘要=True，submit=True。

### mini + SFT87（argmax）

原trace：`archive:study4_teacher87_eval_v6_native_mini_gpu_gate_v4_frozen_flags / teacher87-dev16-m-low-policy-citation-sft87-r1.trace.jsonl`
SHA256：`7ff2b8fe1bc8a5327c384f88b1d507328a9d37e09494a1f144ca3870e59f9993`（50行）。

legal actions（各cycle相同，直到停止）：`NO_ASK`, `ASK:Alex Turner`, `ASK:Sophia Rodriguez`, `ASK:Emily Zhou`, `ASK:Jessica Chen`, `ASK:Emma Lewis`, `ASK:Priya Sharma`, `ASK:Jessica Lee`, `ASK:Huang Jie`。

| cycle / 决策行 | 决策前公开状态 | 实际动作、已有置信分差 | mini实际工具与参数节选 | 观察变化/停止 |
|---|---|---|---|---|
| 0 / L3 | 余8，history=0，phase=decision | NO_ASK；p(NO)=0.8257，次高ASK:Alex Turner=0.0344；Δp=0.7913，Δlog=3.1779 | SELF: `{"tool":"write_file","arguments":{"path":"/workspace/deliverable.json","content":"{\"policy\":\"remote-work\",\"version\":\"v3.1\",\"effective_date\":\"2026-01-01\",\"url_slug\":\"remote-work-v3\"}"}}` | history 0→1；C=0；余7cycle |
| 1 / L9 | 余7，history=1，phase=decision；已有deliverable | NO_ASK；p(NO)=0.8688，次高ASK:Alex Turner=0.0313；Δp=0.8375，Δlog=3.3230 | SELF: `{"tool":"post_channel","arguments":{"channel":"#engineering","content":"Compliance checklist entry saved: remote-work policy v3.1 (effective 2026-01-01, slug remote-work-v3). File: /workspace/deliverable.json"}}` | history 1→2；C=0；余6cycle |
| 2 / L15 | 余6，history=2，phase=decision；已有deliverable | NO_ASK；p(NO)=0.9044，次高ASK:Alex Turner=0.0228；Δp=0.8815，Δlog=3.6787 | SELF: `{"tool":"post_channel","arguments":{"channel":"#engineering","content":"Compliance checklist entry saved: remote-work policy v3.1 (effective 2026-01-01, slug remote-work-v3). File: /workspace/deliverable.json"}}` | history 2→3；C=0；余5cycle |
| 3 / L21 | 余5，history=3，phase=decision；已有deliverable | NO_ASK；p(NO)=0.9246，次高ASK:Alex Turner=0.0194；Δp=0.9052，Δlog=3.8659 | SELF: `{"tool":"post_channel","arguments":{"channel":"#engineering","content":"Compliance checklist entry saved: remote-work policy v3.1 (effective 2026-01-01, slug remote-work-v3). File: /workspace/deliverable.json"}}` | history 3→4；C=0；余4cycle |
| 4 / L27 | 余4，history=4，phase=decision；已有deliverable | NO_ASK；p(NO)=0.8948，次高ASK:Alex Turner=0.0235；Δp=0.8712，Δlog=3.6387 | SELF: `{"tool":"post_channel","arguments":{"channel":"#engineering","content":"Compliance checklist entry saved: remote-work policy v3.1 (effective 2026-01-01, slug remote-work-v3). File: /workspace/deliverable.json"}}` | history 4→5；C=0；余3cycle |
| 5 / L33 | 余3，history=5，phase=decision；已有deliverable | NO_ASK；p(NO)=0.9100，次高ASK:Alex Turner=0.0240；Δp=0.8860，Δlog=3.6353 | SELF: `{"tool":"post_channel","arguments":{"channel":"#engineering","content":"Compliance checklist entry saved: remote-work policy v3.1 (effective 2026-01-01, slug remote-work-v3). File: /workspace/deliverable.json"}}` | history 5→6；C=0；余2cycle |
| 6 / L39 | 余2，history=6，phase=decision；已有deliverable | NO_ASK；p(NO)=0.8661，次高ASK:Alex Turner=0.0330；Δp=0.8331，Δlog=3.2661 | SELF: `{"tool":"post_channel","arguments":{"channel":"#engineering","content":"Compliance checklist entry saved: remote-work policy v3.1 (effective 2026-01-01, slug remote-work-v3). File: /workspace/deliverable.json"}}` | history 6→7；C=0；余1cycle |
| 7 / L45 | 余1，history=7，phase=decision；已有deliverable | NO_ASK；p(NO)=0.9107，次高ASK:Alex Turner=0.0193；Δp=0.8914，Δlog=3.8567 | SELF: `{"tool":"post_channel","arguments":{"channel":"#engineering","content":"Compliance checklist entry saved: remote-work policy v3.1 (effective 2026-01-01, slug remote-work-v3). File: /workspace/deliverable.json"}}` | history 7→8；C=0；8cycle截止，非submit |

**原结果**：business_pass=False；T=0.25；R=0.25；C=0.0；workflow_business_success=False。 artifact=True，channel摘要=True，submit=False。

**全部label概率**（完整精度在公开机器索引；此处四位小数）：

| cycle | NO_ASK | ASK:Alex Turner | ASK:Sophia Rodriguez | ASK:Emily Zhou | ASK:Jessica Chen | ASK:Emma Lewis | ASK:Priya Sharma | ASK:Jessica Lee | ASK:Huang Jie |
|---|---|---|---|---|---|---|---|---|---|
| 0 | 0.8257 | 0.0344 | 0.0217 | 0.0244 | 0.0335 | 0.0015 | 0.0208 | 0.0068 | 0.0312 |
| 1 | 0.8688 | 0.0313 | 0.0161 | 0.0203 | 0.0200 | 0.0013 | 0.0171 | 0.0044 | 0.0207 |
| 2 | 0.9044 | 0.0228 | 0.0115 | 0.0159 | 0.0161 | 0.0006 | 0.0121 | 0.0028 | 0.0138 |
| 3 | 0.9246 | 0.0194 | 0.0070 | 0.0111 | 0.0128 | 0.0005 | 0.0088 | 0.0026 | 0.0133 |
| 4 | 0.8948 | 0.0235 | 0.0127 | 0.0151 | 0.0202 | 0.0007 | 0.0131 | 0.0040 | 0.0160 |
| 5 | 0.9100 | 0.0240 | 0.0110 | 0.0138 | 0.0165 | 0.0005 | 0.0092 | 0.0029 | 0.0121 |
| 6 | 0.8661 | 0.0330 | 0.0175 | 0.0142 | 0.0201 | 0.0008 | 0.0203 | 0.0050 | 0.0230 |
| 7 | 0.9107 | 0.0193 | 0.0123 | 0.0093 | 0.0186 | 0.0006 | 0.0098 | 0.0039 | 0.0155 |

**原教师实际动作，不是oracle**：c0:ASK:Priya Sharma → c1:NO_ASK → c2:NO_ASK。
原教师结果T=0.75、business_pass=False；教师trace路径/hash和训练MODEL_INPUTS行号见JSON索引。

## 采购：旧配额导致金额和权限路径都错

`m-medium-research-purchase`；选择理由：两跳依赖和金额阈值，与简单资料更新不同；教师自身也未走完流程。

**公开指令**：Prepare the twelve-month VectorBench order for project Pine as of 2026-11-02. Save /workspace/deliverable.json with seats, total_usd, allocation_revision, budget_code and release_reference. Post its path and a brief order summary in #engineering.

**初始可见/缺口**：公开worksheet是旧规划、provisional非正式release；当前席位/revision/budget未取得，不能确定金额或沿用旧release。公开policy有USD10000权限阈值。

初始workspace已包含全部公共documents及directory，未read_file不代表没看到文档。

### 原生mini（无外置控制器）

原trace：`archive:study4_teacher87_eval_v6_native_mini_gpu_gate_v4_frozen_flags / teacher87-dev16-m-medium-research-purchase-native_mini-r1.trace.jsonl`
SHA256：`2652ab31e7fa2ac64726ea0c5eb6922aa9be0a3c273e98cfa993085e8eb2f545`（20行）。

legal actions（各cycle相同，直到停止）：`NO_ASK`, `ASK:Jessica Lee`, `ASK:Priya Sharma`, `ASK:Zhang Wei`, `ASK:Huang Jie`, `ASK:David Wong`, `ASK:Emily Zhou`, `ASK:Mike Chen`, `ASK:Wang Fang`。

| cycle / 决策行 | 决策前公开状态 | 实际动作、已有置信分差 | mini实际工具与参数节选 | 观察变化/停止 |
|---|---|---|---|---|
| 0 / L3 | 余8，history=0，phase=decision | NO_ASK；原生概率/分数未知 | NATIVE: `{"tool":"write_file","arguments":{"path":"/workspace/deliverable.json","content":"{\"seats\":16,\"total_usd\":9600,\"allocation_revision\":\"AI-26-A\",\"budget_code\":\"P-01\",\"release_reference\":\"VB-PLAN-16\"}"}}` | history 0→1；C=0；余7cycle |
| 1 / L9 | 余7，history=1，phase=decision；已有deliverable | NO_ASK；原生概率/分数未知 | NATIVE: `{"tool":"post_channel","arguments":{"channel":"#engineering","content":"Prepared VectorBench order for Pine: 16 seats, USD 9,600 total, allocation revision AI-26-A, budget code P-01, release reference VB-PLAN-16. Deliverable saved at /workspace/deliverable.json."}}` | history 1→2；C=0；余6cycle |
| 2 / L15 | 余6，history=2，phase=decision；已有deliverable | NO_ASK；原生概率/分数未知 | NATIVE: `{"tool":"submit","arguments":{"answer":"Completed: /workspace/deliverable.json saved with seats=16, total_usd=9600, allocation_revision=AI-26-A, budget_code=P-01, release_reference=VB-PLAN-16. Posted summary to #engineering."}}` | history 2→3；C=0；submit终止 |

**原结果**：business_pass=False；T=0.0；R=0.0；C=0.0；workflow_business_success=False。 artifact=True，channel摘要=True，submit=True。

### mini + SFT87（argmax）

原trace：`archive:study4_teacher87_eval_v6_native_mini_gpu_gate_v4_frozen_flags / teacher87-dev16-m-medium-research-purchase-sft87-r1.trace.jsonl`
SHA256：`8949e6a7fcca48d1d416b64fd1b8cbf5479e6cb4b0d8bda3b6a8773460710632`（50行）。

legal actions（各cycle相同，直到停止）：`NO_ASK`, `ASK:Jessica Lee`, `ASK:Priya Sharma`, `ASK:Zhang Wei`, `ASK:Huang Jie`, `ASK:David Wong`, `ASK:Emily Zhou`, `ASK:Mike Chen`, `ASK:Wang Fang`。

| cycle / 决策行 | 决策前公开状态 | 实际动作、已有置信分差 | mini实际工具与参数节选 | 观察变化/停止 |
|---|---|---|---|---|
| 0 / L3 | 余8，history=0，phase=decision | NO_ASK；p(NO)=0.8579，次高ASK:Jessica Lee=0.0438；Δp=0.8141，Δlog=2.9756 | SELF: `{"tool":"write_file","arguments":{"path":"/workspace/deliverable.json","content":"{\"seats\":16,\"total_usd\":9600,\"allocation_revision\":\"AI-26-A\",\"budget_code\":\"P-01\",\"release_reference\":\"VB-PLAN-16\"}"}}` | history 0→1；C=0；余7cycle |
| 1 / L9 | 余7，history=1，phase=decision；已有deliverable | NO_ASK；p(NO)=0.8235，次高ASK:Emily Zhou=0.0498；Δp=0.7737，Δlog=2.8058 | SELF: `{"tool":"post_channel","arguments":{"channel":"#engineering","content":"Prepared VectorBench order for Pine and saved the deliverable at /workspace/deliverable.json. Summary: 16 seats, USD 9,600 total, allocation revision AI-26-A, budget code P-01, release reference VB-PLAN-16."}}` | history 1→2；C=0；余6cycle |
| 2 / L15 | 余6，history=2，phase=decision；已有deliverable | NO_ASK；p(NO)=0.8724，次高ASK:Jessica Lee=0.0389；Δp=0.8336，Δlog=3.1110 | SELF: `{"tool":"post_channel","arguments":{"channel":"#engineering","content":"Prepared the VectorBench order for Pine and saved it at /workspace/deliverable.json. Summary: 16 seats, USD 9,600 total, allocation revision AI-26-A, budget code P-01, release reference VB-PLAN-16."}}` | history 2→3；C=0；余5cycle |
| 3 / L21 | 余5，history=3，phase=decision；已有deliverable | NO_ASK；p(NO)=0.8495，次高ASK:Jessica Lee=0.0565；Δp=0.7930，Δlog=2.7101 | SELF: `{"tool":"post_channel","arguments":{"channel":"#engineering","content":"Prepared the VectorBench order for Pine and saved it at /workspace/deliverable.json. Summary: 16 seats, USD 9,600 total, allocation revision AI-26-A, budget code P-01, release reference VB-PLAN-16."}}` | history 3→4；C=0；余4cycle |
| 4 / L27 | 余4，history=4，phase=decision；已有deliverable | NO_ASK；p(NO)=0.7694，次高ASK:Jessica Lee=0.0928；Δp=0.6767，Δlog=2.1157 | SELF: `{"tool":"post_channel","arguments":{"channel":"#engineering","content":"Prepared the VectorBench order for Pine and saved it at /workspace/deliverable.json. Summary: 16 seats, USD 9,600 total, allocation revision AI-26-A, budget code P-01, release reference VB-PLAN-16."}}` | history 4→5；C=0；余3cycle |
| 5 / L33 | 余3，history=5，phase=decision；已有deliverable | NO_ASK；p(NO)=0.8327，次高ASK:Jessica Lee=0.0619；Δp=0.7708，Δlog=2.5996 | SELF: `{"tool":"post_channel","arguments":{"channel":"#engineering","content":"Prepared the VectorBench order for Pine and saved it at /workspace/deliverable.json. Summary: 16 seats, USD 9,600 total, allocation revision AI-26-A, budget code P-01, release reference VB-PLAN-16."}}` | history 5→6；C=0；余2cycle |
| 6 / L39 | 余2，history=6，phase=decision；已有deliverable | NO_ASK；p(NO)=0.8819，次高ASK:Jessica Lee=0.0370；Δp=0.8449，Δlog=3.1718 | SELF: `{"tool":"post_channel","arguments":{"channel":"#engineering","content":"Prepared the VectorBench order for Pine and saved it at /workspace/deliverable.json. Summary: 16 seats, USD 9,600 total, allocation revision AI-26-A, budget code P-01, release reference VB-PLAN-16."}}` | history 6→7；C=0；余1cycle |
| 7 / L45 | 余1，history=7，phase=decision；已有deliverable | NO_ASK；p(NO)=0.8831，次高ASK:Jessica Lee=0.0370；Δp=0.8460，Δlog=3.1712 | SELF: `{"tool":"post_channel","arguments":{"channel":"#engineering","content":"Prepared the VectorBench order for Pine and saved it at /workspace/deliverable.json. Summary: 16 seats, USD 9,600 total, allocation revision AI-26-A, budget code P-01, release reference VB-PLAN-16."}}` | history 7→8；C=0；8cycle截止，非submit |

**原结果**：business_pass=False；T=0.0；R=0.0；C=0.0；workflow_business_success=False。 artifact=True，channel摘要=True，submit=False。

**全部label概率**（完整精度在公开机器索引；此处四位小数）：

| cycle | NO_ASK | ASK:Jessica Lee | ASK:Priya Sharma | ASK:Zhang Wei | ASK:Huang Jie | ASK:David Wong | ASK:Emily Zhou | ASK:Mike Chen | ASK:Wang Fang |
|---|---|---|---|---|---|---|---|---|---|
| 0 | 0.8579 | 0.0438 | 0.0139 | 0.0139 | 0.0166 | 0.0083 | 0.0340 | 0.0010 | 0.0107 |
| 1 | 0.8235 | 0.0477 | 0.0162 | 0.0192 | 0.0167 | 0.0115 | 0.0498 | 0.0017 | 0.0137 |
| 2 | 0.8724 | 0.0389 | 0.0107 | 0.0135 | 0.0130 | 0.0077 | 0.0345 | 0.0012 | 0.0080 |
| 3 | 0.8495 | 0.0565 | 0.0105 | 0.0163 | 0.0129 | 0.0074 | 0.0362 | 0.0010 | 0.0097 |
| 4 | 0.7694 | 0.0928 | 0.0224 | 0.0205 | 0.0247 | 0.0085 | 0.0468 | 0.0012 | 0.0136 |
| 5 | 0.8327 | 0.0619 | 0.0156 | 0.0179 | 0.0233 | 0.0063 | 0.0321 | 0.0008 | 0.0095 |
| 6 | 0.8819 | 0.0370 | 0.0107 | 0.0132 | 0.0169 | 0.0051 | 0.0264 | 0.0007 | 0.0082 |
| 7 | 0.8831 | 0.0370 | 0.0097 | 0.0116 | 0.0197 | 0.0044 | 0.0258 | 0.0006 | 0.0081 |

**原教师实际动作，不是oracle**：c0:ASK:Wang Fang → c1:NO_ASK → c2:NO_ASK。
原教师结果T=0.8、business_pass=False；教师trace路径/hash和训练MODEL_INPUTS行号见JSON索引。

## 阅读这些案例时不能作的推断

1. NO_ASK只放行一个普通工具，不会强迫mini发channel；重复发channel由mini实际选择。
2. 控制器动作集中只有NO_ASK/ASK(person)，没有SUBMIT；它不能直接让任务结束。
3. NATIVE和SELF同一mini/snapshot，但模式、phase及工具schema呈现不同；尚无接口匹配消融，不能断言循环全由adapter造成。
4. “完整交付”中的submit是桥接协议要求；上述原任务正文只明确artifact/channel，内容pass与协议终止必须分别看。
5. private事实仅用于本次离线解释，不能把它们作为将来控制器输入或据此重调已看的最终测试。
