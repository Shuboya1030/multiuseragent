# 原生单函数协议 v1

版本：`study4-native-single-function-v1`。这是四臂共同的线协议改变，
不回写旧文本JSON请求、分数或账本，也不把旧slot当作新协议已完成episode。

## 契约

固定 `gpt-5.4-mini-2026-03-17` 支持函数调用。按2026-11-12读取的
[官方function calling指南](https://developers.openai.com/api/docs/guides/function-calling)，
`tool_choice="required"` 要求一个或多个，`parallel_tool_calls=false` 限制零或一个；
联合使用，并对每个函数 `strict=true`、所有字段required、禁止额外字段。
仍在本地精确要求**一个可执行function_call**，不截取多个动作的第一条。
reasoning与assistant output_text只作非可执行metadata；拒绝refusal、未知/托管tool输出、
零/多个function_call、未知函数、错误参数。静态检查不能证明provider实际接受。

普通函数仍仅 `read_file/write_file/list_files/post_channel/submit`，
沿用现有参数与虚拟环境；SELF仍一步。控制返回 `choose_help`，
问题构造返回 `compose_help_request`，均强制单函数，不写任务答案、不执行普通工具。
所有四臂使用相同普通prompt/schema、模型、公开任务/完整历史/工具权限。
只有已冻结的特权when/whom与what辅助差异，不能称为已训练控制器收益。

函数结果用原生call_id关联：
普通动作应用后记录真实公开event；ASK前的proposal明确标成未执行并丢弃，
拒绝submit则标成未执行；控制决策/问题构造只标成已记录/已构造而非已发消息。
规则NPC回复仍通过实际send/read自动交付，再生成下一普通动作，不新增读回复SELF门。
reasoning/非动作metadata与完整公开状态保留；不发gold/DAG/未读值/评分。
本地48slot脚本回放仅验接口、ASK生命周期、来源与调用关联，不是真实mini收益。

## 费用与恢复

新增 `provider_model_maximum_bound` version2，允许本地自定义strict函数，
明确不是收费builtin、web、code、MCP或compaction。
函数定义计input，包含在固定模型272000input最大值内；
完整128000output最大值与标准价格再加10%给每call USD.858 reserve。
实际wire output上限1024未变，usage合法结算后释放差额。
这不是含税、汇兑或私人账户附加费的全账单保证。
来源及支持域见 [版本化证据](configs/native_function_contract_v1.json)。

四笔旧unknown USD3.432和十笔settled上界USD.013762650必须逐字节保留，
继续累计同一个原USD50帽，不另开50、不重新解释原usage或释放未知。
新版冻结五个旧run的文件指纹、源码commit、用户来源、runtime/价格/模型/scorer、
唯一输出根与请求；互斥保护旧run。预验最多一条且不应用工具、不计episode。
仅成功合法settle后加入该预验为第六个已冻结history，再启动原48slot fresh批次。
任何新unknown、无法安全恢复或余额不足即停，无retry/GET/旧episode工具重放。
脚本重复启动被拒绝；不宣称跨崩溃工具exactly-once。

实际执行与结果将另存版本化报告；本协议文档本身不代表真实preflight通过、
48episode完成、训练开始或headroom存在。
