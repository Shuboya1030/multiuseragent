# 持久预算与HTTP执行前门：本地故障验收

2026-11-11。**持久reserve/恢复/互斥与HTTP适配已实际本地验证；真实模型调用仍blocked。**
本次只有临时测试账本、mock provider及本机loopback HTTP；
记录的一次完整验收产生4次HTTP请求，不是开发排错及发布复核的累计本地请求数。
真实模型服务/API支出/GPU作业均0，未读key、未创建正式paid ledger。
当前[待签配置](../configs/durable_preflight_pending.json)仍为`budget_cap_USD=null`，
provider token/framing proof为`UNPROVED`，不是默认填USD55/70的授权。

## 实测范围

| 门 | 本地证据 | 仍不代表 |
|---|---|---|
| 授权先于网络 | 无金额/记录不匹配/过期/错误root/runtime时，文件创建及DNS/socket前阻断 | 用户已批准新预算 |
| commit-before-send | 第二个SQLite连接在provider/HTTP入口读到已提交的sending+reservation | 已发送真实付费请求 |
| 崩溃重启 | 真实子进程在4个检查点直接退出；重开检查持久状态 | VM断电/磁盘硬件可靠性已认证 |
| 同批排他 | 活进程持锁时第二进程无法打开该批账本 | 跨主机分布式锁 |
| 成功恢复 | settled结果及SHA原子保存；同call ID+同请求恢复缓存不再发送 | 环境普通工具也已做到exactly-once |
| 失败保守占帽 | timeout、缺usage、超额、模型漂移、parse/重复JSON/非法动作等unknown整笔保留并停 | 失败可自动退款/修复/重试 |
| HTTP边界 | literal loopback；无代理/重定向/重试/授权header；字节上限、1秒deadline故障验证 | provider服务端schema/TLS/DNS/真实usage已验收 |
| 针对性测试 | 新18项＋此前64项，共82项通过 | 模型或任务收益证明 |

实际机器证据：[DURABLE_PREFLIGHT_CHECK.json](DURABLE_PREFLIGHT_CHECK.json)。
之前9fixture及24脚本适配报告仍精确复现；它们不转化为新训练或ceiling收益。

## 崩溃发生在哪里，恢复后做什么

| 强制退出点 | mock provider实际发送次数 | 重启状态 | 下一调用 |
|---|---:|---|---|
| reserve提交后 | 0 | unknown，仍占原最大费用 | 阻断，不猜测“肯定没收费”而重发 |
| sending提交后、HTTP前 | 0 | unknown，仍占帽 | 阻断 |
| provider返回后、settle前 | 1 | unknown，仍占帽 | 阻断，不能盲重发 |
| settle提交后、调用方拿结果前 | 1 | settled，结果hash可核 | 同ID同请求返回缓存，新增发送0 |

复用旧独立ledger的SQLite WAL/FULL、Decimal、先reserve后发送与unknown保守语义，
**没有复用旧数据库、USD30或任何旧授权**，也未沿用旧“UTF8字节+4096 framing”作为已证明上界。
新代码不重建已有账本，metadata绑定run、完整plan、授权记录与canonical storage root哈希。
锁文件保留，OS锁随进程退出释放，避免删除锁文件引起双持有竞态。
源码/runtime绑定采用UTF8 LF规范化指纹，防止Git换行转换产生伪版本差异。

同call ID不同请求、配置/价格/模型/runtime漂移或缓存hash不匹配都拒绝。
异常记录类型、response hash/长度及白名单类型化usage/status诊断（不冒充settlement），
不把含潜在凭据的异常正文/HTTP header或任意raw错误正文写进账本。
成功结果缓存用于恢复；临时DB、原请求、raw错误body和授权记录不随报告发布。
unknown没有自动清账/自动retry入口；需要另行核实，不能更换call ID绕开批次停止。

## token上界：哪里可证明，哪里不能

本机可发现generic `tokenizers`，但没有已核验的该OpenAI模型tokenizer；
未下载词表、安装依赖或调用token计数服务。

本地mock明确定义“序列化UTF8 body每字节计1 token、无隐藏framing”，
于是`input_bound=len(body)`对该**本地环境**可证明，Unicode/转义/等号边界有单元测试。
这不推出真实provider同样计数。即使byte-level tokenizer的可见文本满足每token至少消费1字节，
未知的角色、JSON schema或服务端隐藏framing仍可能增加tokens，不能假设固定4096一定够。

因此provider分支当前无有效proof实现：即使提供一个格式匹配的模拟“已批准”记录，
也会在建账本/网络前抛`BudgetBlocked`。不会把字符数/除4/经验余量冒充硬帽。
计费价格仍绑定[原官方来源](https://developers.openai.com/api/docs/pricing)与2026-11-11读取日期、
固定model候选、输入.75/输出4.50每百万及候选10%附加费；本轮未重新验证账户地区或新价格。

真实调用还需可审查的模型tokenizer＋framing上界，或供应商支持的安全总计数契约；
取得方法涉及网络/下载时另获授权。只有据此算出的reserve、完整request/usage与独立上限一致，
才可打开真实执行。现有USD55/70表仍是8000/1024假设下的**方案估算**，不是已验收实付硬帽。

## HTTP与恢复的剩余边界

`HTTPTransport`使用标准库单次POST，不读取环境变量，不使用系统代理，不跟随3xx，
构造连接前必须消费由持锁账本发出的真实一次性permit。
本地测试包括redirect、超大响应、延迟响应及调用前真实持久行检查。
socket deadline在loopback验证；真实provider DNS/TLS/服务端schema从未调用，
不能把静态strict JSON/模型名匹配当实际服务接受。

settle只有在完整响应、usage与应用输出都通过后发生；解析失败即使可能带usage，
也保留最大unknown并停，宁可占帽，不返回成功形状或自动补发。
成功缓存可以避免同一逻辑call重复付费，但**tool应用/episode状态的端到端恢复还需独立事务绑定**；
不得在恢复时盲目再post/submit。现代码不是已恢复的48episode付费runner。

## 停在真实门，不继续空转

当前检查点内的无付费工程已完成。剩余动作是取得独立范围/金额批准、解决provider token proof与
真实接口小门，训练另需Colab登录/实际GPU与阶段授权。
没有因此启动SFT/RL、重新运行旧32评测、扩大任务集或循环mock直到“赢”。
最终收益仍要固定mini/同接口native自主ASK对照，在另封存的新任务/组织上报告任务成功与固定新R，
并列交付/submit/联系安全/API成本/unknown及题或组织层级配对不确定性；旧60不是终测。

[当前发布字节指纹](DURABLE_PUBLICATION_MANIFEST.json) ·
[前一本地适配报告](LOCAL_ADAPTER_STAGE_ZH.md)
