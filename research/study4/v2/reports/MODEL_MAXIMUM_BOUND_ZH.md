# 模型最大token费用上界：v2.1有界修正

2026-11-11。**已核官方来源并解除本版本“必须先有精确tokenizer”的技术费用上界阻塞；
独立预算仍未批准，不启动pilot。** 本轮0模型请求、0支出、0key读取、0正式账本、0GPU/安装下载。

## 为什么成立

[官方模型页](https://developers.openai.com/api/docs/models/gpt-5.4-mini)固定snapshot
`gpt-5.4-mini-2026-03-17`：context 400000、maximum input 272000、maximum output 128000。
[官方standard价格](https://developers.openai.com/api/docs/pricing)为输入USD.75/M、输出USD4.50/M，
regional uplift为10%。忽略缓存折扣，完整模型最大输入＋最大输出保守预留：

`(272000 × .75 + 128000 × 4.50) / 1000000 × 1.10 = USD .858000 / call`

对支持域内的一次有效推理，角色/schema/隐藏framing输入也须包含在模型最大input内；
不需要知道该prompt的精确token数，也不再猜额外4096。这个界不是“prompt一定装得下”的证明。
请求超长而被拒绝/没有usage时仍保留unknown，不自动重发，不静默截断。

官方Responses文档另明确`max_output_tokens`包括可见输出和reasoning tokens。
现wire仍请求1024，但本轮**不采用更紧1024费用bound**，预留仍用完整128000；
避免把“发送的output限制”“业务响应合法性限制”和“保守费用reservation”混成一个数。
settle验证实际usage后按实际tokens的保守单价结算/释放差额，.858不是每次实付。

## 严格支持域，而非一切账单保证

- 固定snapshot、直接Responses、`service_tier="default"`（官方定义standard），reasoning none。
- 两条显式text消息；不含image/audio/file、conversation/previous_response或扩展cache-write配置。
- `tools=[]`、`context_management=null`；无provider搜索、容器、文件存储、MCP或compaction额外调用。
- 非后台/非stream、store false、truncation disabled；其他顶层参数与模式漂移在reserve/transport前拒绝。
- 返回的实际tier也必须为default，usage/model/应用输出仍严格验证；异常unknown、全额占帽、整批停止。

**普通Agent工具未被禁用。** read/write/post/submit等仍由原普通JSON动作schema生成并在环境执行，
不是provider内置tools；三种请求的公开input/prompt与旧本地请求一致，只新增版本化计费envelope。
控制/提问/执行的下一次模型调用仍须分别reserve，不允许一次HTTP内产生未计费的额外模型工作。

这是所读价格和支持域下的模型推理费用上界，不覆盖税费、汇率、未核实账户合同加价、
未来涨价或供应商不按所请求standard域处理的情形。官方提醒actual tier可能与请求不同；
若返回非default则拒绝正常settlement并保留unknown，不能据此追溯保证收费没发生/自动退款。
实际账户收费域仍需执行前核对；没有声称供应商包含所有税费的绝对账单保证。

[来源证据](../configs/provider_model_maximum_bound_v1.json)包含官方URL、UTC获取时间、
原markdown字节数/SHA及事实摘要。完整官方原文只私下留存；hash不是摘要hash，也不是不可变价格SLA。
此次官方网页读取不是模型服务probe。

## 实现与真实本地验收

[provider_bound.py](../provider_bound.py)提供固定模型上界；[admission.py](../admission.py)
在v2 plan中绑定来源/runtime/价格，限制上述支持域；
[mini_request.py](../mini_request.py)增加`build_provider_request`，不改旧本地回放payload。
[durable.py](../durable.py)将reservation output单独设128000，wire/合法usage上限仍1024。

新增[6项针对性测试](../test_provider_bound.py)，与之前82项共88项通过：
完整.858先持久化再mock发送、实际mock usage settle后释放、缓存恢复0重发；
剩余.857999第一call拒绝，.858完成一小call后不足下次reserve仍拒绝，1.00可完成两次小call；
缺usage/实际tier漂移/超界在重启后保持.858 unknown、不换ID重发；
不支持模式在任何reserve/transport前拒绝；
provider的真实pending配置在文件/DNS/socket前被预算门拒绝。
测试只用临时LOCAL_TEST账本/mock及原loopback测试，不创建provider正式账本。

[机器验收](MODEL_MAXIMUM_BOUND_CHECK.json) · [本次发布指纹](MODEL_MAXIMUM_PUBLICATION_MANIFEST.json)

## 剩余门与预算解释

新[pending配置](../configs/durable_preflight_pending.json)仍为`budget_cap_USD=null`、episodes空，
没有用户授权记录；USD55/70仍只是未获批准的方案。
settle释放差额能让小usage调用连续执行，但必须在每次发送前保有.858可预留余额；
**不能承诺48episode在55内完成**。若4608次都取完整上界，总额为USD3953.664，
实际cap会更早挡住后续调用，不能为了跑满自动加帽或重试。
旧8000/1024预算表仅是有条件方案估算，不是本模型最大bound的全集费用保证。

真实schema接受/实际usage尚未实测，tool/episode端到端exactly-once事务恢复也未证明；
Colab登录/实际GPU及新训练另待资源与阶段授权。保留旧SFT87/32评测和所有历史报告，
不因解除这一个技术门启动付费实验。
