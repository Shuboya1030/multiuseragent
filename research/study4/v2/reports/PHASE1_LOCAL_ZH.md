# Study4 v2第一阶段实际报告：本地门通过，真实ceiling尚未运行

2026-11-11。[设计v1.1](../DESIGN_v1_1_ZH.md) · [代码与复跑](../README.md) ·
[下一授权门/预算](../CEILING_PILOT_ZH.md)

## 结果与范围

**已实际实现共享接口并完成零付费验收，不是只写设计。**
但本报告的executor是deterministic公共fixture mock、NPC是本地规则，
没有mini调用、GPU模型推理或真实benchmark评分；不能称修好了mini、Phase2完成或研究收益成立。

| 已运行检查 | 实际结果 | 能支持什么 |
|---|---|---|
| 新协议针对性tests | 24/24通过 | 本地行为、消息、来源、拒绝、提交与上下文/预算合同 |
| 旧HelpRuntime/native Agent定向regression | 12/12通过；合计36 tests | 未改变旧接口与行为的相关回归 |
| 9个手写fixture参考路径 | 9/9内容＋release＋用户交付＋bridge submit proof完成 | 特权DAG参考与mock组合能走通小环境 |
| 同9fixture always-SELF | 9/9公共交付/submit；只有2/9内容有效 | 能终止不代表信息/授权/业务正确；2个合法Optional baseline |
| 参考路径公开状态/标签兼容 | 33组兼容，其中2组不是唯一标签 | 只对被审计状态保留多解，没有硬造唯一人 |
| 故意同公开状态/不同私有最优联系人 | 1组明确unidentifiable，shared labels为空 | 不可辨识样本不得成为唯一可学习标签 |

来源：[实际机器报告](LOCAL_ACCEPTANCE.json)。9个fixture包括single、info→approval、
parallel→join、referral、delegation、阈值6000/12000两侧、Optional高成本baseline/低成本improve。
不称它们已通过原benchmark任务质量验收、不算生成5000题，也不是原60的回放。
Optional高成本fixture的20单位联系是故意的数值压力例，不是原TribalBench按seniority的3/2/1价格；
两种Optional路径仅检验冻结目标下baseline/improve的显式选择，未证明全局最优。

参考路径共34普通动作、15次联系、49次**mock callback**。
它们不是49次API。always-SELF的27次普通动作也没有API费用。
actual API=0、GPU jobs=0、training updates=0；没有读取key、连接Colab、
启动receiver/付费ledger或使用历史预算。

## 实际实现

- 普通工具schema、prompt和public progress只有一套；A/B/C/D给相同状态时ordinary payload逐字段相同。
- ASK发送绑定request ID→自动读实际reply→再执行恰好一普通步；refusal不输出grant。
  读已交付消息幂等，改稳定ID或无实际outgoing的reply不能入公共memory。
- 两跳部分回复、漏context被拒再补、并行与金额authority检查可跑通；
  what只选已获value IDs，问题不保留key=value时停止，不静默补写。
- 以reply的message/person保存值来源，冲突版本保留；金额由公开公式和已读seat值计算，
  source_value_ids可追溯，不能冒充NPC授权。
- 信息齐、但artifact/post尚未齐时SUBMIT记submission_blocked，未结束；SELF本来可submit。
  rewrite后旧channel revision不再满足交付门；重复post保留历史。
  错内容即使write/post/submit都完成，fixture checker仍false，公共progress不会暴露业务分。
- private snapshot提供纯本地受控继续执行基础、绑定/hash与恢复验收；
  与部署观察分开，不是已跑的付费分支数据集或完整训练checkpoint。
- key-point reason基础涵盖start、reply、write/submit proposal和每4步；
  真实proposal缓存/去重/费用admission driver未实现，不隐藏这一差距。
- context_view保护reply/value来源/summary/task，登记被剔除普通event；
  protected本身超限明确ContextOverflow。当前counter mock，不宣称Qwen真实6k门通过。

当前规则请求使用**公开intent前缀＋结构化key=value引用**，才能确定性检查所带值。
这是一项显式新接口约束；还没证明mini会稳定遵守，也没实现自由NL同义intent/事实抽取。
保持intent/引用的失败会停止而非自动“修好请求”；付费pilot前应单独验收。

## Scorer发现与未通过的正式评分门

只读实核TribalBench commit`4260bdc626548f59042f318cdf0566490e91b9d5`源码，
版本`tribalbench-1.0`，SHA256
`e6b47e4a251bdc44d2fbfe389e12b81273e6472092958fe04e33297f28a33e78`。
源码R是`T−.05*max(0,C−C_star)−.3*Nauth−.1*max(0,Nwaste−Nauth)`，
Optional C_star=0；与设计文字还存在auth/waste去重等细节差异。
已记录[固定绑定](../configs/scorer_binding.json)，没有执行远端scorer/其他primary checkout。

本地`local-fixture-proof-v1`不计算同名TribalBench R；正式scorer文件取得、
执行接线、固定版本/evidence binding与未知语义复核仍**blocked/未验收**。
不能把这个门用自写同名scorer或mock成绩替代。
旧SFT87 R、模型、32episode及所有历史分数未改。

## 阶段决策

**通过**：本阶段共享本地协议/小fixture基础/必要可辨识检查。
**仍未通过**：真实mini接口稳定性、真实四臂ceiling、原60规则NPC迁移、
官方scorer执行、真实6k模型上下文、5000题/新org split、三头模型可拟合/任务收益。
没有把旧设计“mock20 gold paths/真实alwaysSELF≥90%”改成已实测：
本次是9个明确手写fixture，真实mini门依然没跑。

下一步先签署[6题×4臂×2=48episode方案](../CEILING_PILOT_ZH.md)：
rule NPC建议独立USD55帽；如明确选择LLM NPC则USD70帽。
这是按24步、每步最多4/5调用（包括ASK失效proposal的ordinary刷新）、
8000输入/1024输出token与实际普通价格的保守建议，
不是已授权支出、也不是“48次调用”。预算/地域价格变化先重报。
旧USD30剩额不延用。没有因为本地成功就越门训练或采集。

## 保存与复核

代码、设计、配置、实际报告在本研究分支`research/study4/v2/`，
旧源码保持不动。本次文件fingerprint见[独立manifest](PUBLICATION_MANIFEST.json)；
Git LF发布字节与Windows CRLF checkout字节可能不同。
原64结果/trace、checkpoint87和已关闭账本SHA另作只读保全检查，不随本次上传原件。
报告附件是本文和[LOCAL_ACCEPTANCE.json](LOCAL_ACCEPTANCE.json)，
均可公开，无凭据、个人路径或大checkpoint。
