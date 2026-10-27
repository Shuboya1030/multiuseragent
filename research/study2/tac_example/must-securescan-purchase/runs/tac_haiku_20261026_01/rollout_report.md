# 真实 TAC rollout 报告

## 结果

执行与三次同事对话均使用Haiku5.5。真实TAC服务、自定义API执行端、官方Sotopia NPC；不是OpenHands浏览器基线。原评分2/3，流程和交付通过，artifact的controls同义字符串被严格比较拒绝。

## 可复查步骤

|轮次（从1起）|动作|目标|结果|
|---|---|---|---|
|1|list_documents||成功|
|2|read_document|securescan_quote.md|成功|
|3|read_document|procurement_policy.md|成功|
|4|read_document|directory_R1.md|成功|
|5|read_document|trial_estimate.md|成功|
|6|send_message|Wang Fang|成功|
|7|read_messages|Wang Fang|读取 1 条真实NPC消息|
|8|send_message|Liu Qiang|成功|
|9|read_messages|Liu Qiang|读取 1 条真实NPC消息|
|10|send_message|David Wong|成功|
|11|read_messages|David Wong|读取 1 条真实NPC消息|
|12|write_purchase_request||成功|
|13|post_summary||成功|
|14|finish||成功|

## 三次真实同事回复

### Wang Fang

服务器消息ID：`KgzsRdZGiSSSRqvdm`；时间：`2026-10-26T23:33:38.598Z`。

Hi, thanks for following up. Here are the current AI Team allocation fields:

- Seats: 24
- Budget code: AI-OPS-26
- Data class: source-code-confidential
- Revision: AI-Q4-07

So the 24-seat figure should replace the archived 18-seat trial number. I can't approve the purchase or any risk sign-off on my end, so you'll need to get that from whoever owns the purchase approval. Let me know if you need anything else for the request.

### Liu Qiang

服务器消息ID：`RN7SZKNgbdikgPW9y`；时间：`2026-10-26T23:33:46.493Z`。

Hi, I've checked your request and it includes all five required items: AI-Q4-07, 24 seats, source-code-confidential, EU-only processing, and zero-retention. The cross-team review for this allocation is SR-2648, with a security review disposition of conditional-pass. The conditions are EU-only processing and zero-retention, so the deployment has to meet both. This covers the security/quality review only. It doesn't approve the USD 11,520 spend under AI-OPS-26, so that still needs to go through the budget owner.

### David Wong

服务器消息ID：`9emkzJB86dceCZuxP`；时间：`2026-10-26T23:33:53.038Z`。

Hi, I've reviewed the request for the 12-month SecureScan Pro purchase: 24 seats, USD 11,520 total, budget AI-OPS-26, and security review SR-2648 with EU-only processing and zero-retention controls. Your request covers the purchase details I need, so I'm approving it. Authorization ID: PO-26-1048, approved by David Wong. Please keep the quote validity date of 2026-11-15 in mind when you proceed.

## 最终业务答案

```json
{
  "vendor": "SecureScan Pro",
  "seats": 24,
  "total_cost_usd": 11520,
  "budget_code": "AI-OPS-26",
  "requirements_revision": "AI-Q4-07",
  "security_review": "conditional-pass",
  "review_id": "SR-2648",
  "controls": [
    "EU-only processing",
    "zero-retention"
  ],
  "approved_by": "David Wong",
  "authorization_id": "PO-26-1048"
}

```

## 审计与结论边界

共 14 次执行模型调用、3 次同事模型调用；估计总费用 $0.0077938，非账单。执行阶段约 28.85 秒，部署时间不包含在内。

服务器消息ID与Agent读取内容一致；三次读取都发生在下一依赖请求前，最终授权也在写文件之前。仅观察到了正确请求路径；不存在证据证明所有错误请求都会被NPC正确拒绝。

本例证明新任务可以在真实TAC服务与LLM同事链路中完成，未证明它适合直接作为正式研究任务。三个干扰者均未被联系，不能估计干扰强度；单次成功不用于设定难度目标。

原始输入哈希见input_manifest；原评分见tac_evaluation；事后格式解释见format_diagnosis；完整请求响应见api_io与npc_api_io；详细工具结果见trace。
