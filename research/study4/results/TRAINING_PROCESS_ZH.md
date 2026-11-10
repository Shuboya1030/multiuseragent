# 训练过程与成果：完成行为模仿，不等于学会有效求助

[返回阅读入口](../README.md) · [评测结果](TEACHER87_NATIVE_MINI_DEV16_RESULTS_ZH.md) · [失败诊断](DIAGNOSIS_ZH.md)

## 当前模型与实验范围

**原定3 epochs / 87个更新及最终评估均已完成。按原dev NLL规则选择step87。**
这是GPT-only实际教师动作的监督模仿SFT，不是三教师都完成，不是任务回报优化或已成功的joint RL。
只更新控制器LoRA，执行器和NPC不训练。

控制器输入为公开任务、完整可见历史、已读回复、公共同事角色/知识/权限/价格及合法动作mask。
未读私有事实、gold和evaluator反馈不进入输入。输出只有NO_ASK或ASK(person)：
NO_ASK允许固定执行器执行一个普通工具动作；ASK让执行器写问题、发送、读取NPC回复，再执行一个普通动作。
发送和读取分别记事件，已读消息进入后续公开状态；控制器不自行写交付物或最终答案。

## 数据从哪里来

| 项目 | 实际范围 |
|---|---|
| 教师 | GPT-only；没有把尚未采集的其他模型算进来 |
| 轨迹 | 59条完整bounded rollout＋1条历史HTTP429 partial |
| 决策 | 292条合法、可重建动作：291来自完整轨迹，1来自partial |
| 动作分布 | NO_ASK 243；ASK 49 |
| train | 44题、230决策：192 NO / 38 ASK |
| dev | 16题、62决策：51 NO / 11 ASK |
| 标签含义 | 教师当时实际合法行为，不是已认证最优/正确的when+whom |

没有按成功、回报或语义复核结果筛选。partial只保留真实已完成决策，没有补造terminal reward。
教师train任务结果为20成功、23失败、1 partial；dev为9成功、7失败。
这些数字本身说明“合法教师标签”不能冒充oracle。
行为概率未知；292条不能直接当作满足随机采集条件的offline RL数据。

split seed98117；同任务、可验证workflow/pair与所用authored-family不跨split。
Must按结构家族、Optional按authored domain分组。60题同属一个17人组织，且都有此前R1暴露：
这只是same-org held-family探索性模型选择，非未见组织/密封终测。16dev此后又用于评测和诊断。

## 模型、目标与实际运行配置

| 参数 | 固定配置 |
|---|---|
| 底座 | `Qwen/Qwen2.5-1.5B-Instruct` |
| model/tokenizer revision | `989aa7980e4cf806f80c7fef2b1adb7bc71aa306` |
| LoRA | rank8、alpha8、dropout0，q_proj / v_proj |
| 精度/attention | FP32 / eager；gradient checkpointing、suffix-only logits、逐label重算 |
| 上下文 | 4352；全量真实tokenizer审计，无截断、无筛短样本 |
| optimizer | AdamW，lr1e-5、weight_decay0，clip norm1 |
| batch / epoch | 每批8个决策串行梯度累积，末批6；每epoch全230条、29步，共87步 |
| 随机性 | 训练seed98118；固定epoch顺序由seed98119与决策ID绑定 |
| loss | 完整action JSON＋EOS的token log-prob求和，再对合法labels做categorical CE；每决策等权 |
| checkpoint选择 | 初始及每epoch固定全量train/dev评估；最低dev NLL，平局较早 |

损失没有使用rollout的T、R或C反传；没有价值模型。公开Qwen输入含候选T−.15C，
原评测R的联系权重是.05，两者不同；教师标准请求没有额外这个数值objective。
Qwen训练/推理字段一致，但不能据此认定教师对该精确目标最优。
新奖励未签署，不能以事后改lambda重新宣布收益。

### 实际容量门

| 范围 | 决策数 | >2048 tokens | p50 | p95 | 最大tokens |
|---|---:|---:|---:|---:|---:|
| 全部 | 292 | 132 | 1953 | 3422.35 | 4159 |
| train | 230 | 114 | 2041.5 | 3546.6 | 4159 |
| dev | 62 | 18 | 1741.5 | 2903.6 | 3177 |

使用同Qwen chat template与完整候选label＋EOS实测，不用GPT usage估算。
4096不足，独立4352配置覆盖4159最大状态，未修改底座原生位置上限。
免费Colab Tesla T4实际最长状态17-label forward/backward通过、非零有限梯度；
peak reserved 10,882,121,728 bytes，诊断本身optimizer steps=0。
这只是训练前fit门，不与87个真实更新混算。

原环境核心版本为torch2.11.0+cu130、transformers5.22.0、peft0.21.2、
accelerate1.15.0、numpy2.4.6；torchao移除。
恢复时NumPy/Transformers经已核官方来源构建及后续备份wheel恢复；
不声称与最早wheel二进制完全相同，须通过下述实际数值/状态门。

## 训练指标：完成3 epochs，但并未证明收敛或任务能力

| checkpoint | Train NLL | Dev NLL | Train动作accuracy | Dev动作accuracy |
|---|---:|---:|---:|---:|
| 初始 / step0 | 3.546926 | 3.365714 | 2.1739% | 8.0645% |
| epoch1 / step29 | 2.544743 | 2.388990 | 4.7826% | 12.9032% |
| epoch2 / step58 | 1.444949 | 1.314781 | 55.6522% | 45.1613% |
| epoch3 / step87（选中） | 0.954693 | 0.799960 | 83.4783% | 82.2581% |
| 永远NO_ASK的accuracy | — | — | **83.4783%** | **82.2581%** |

NLL下降说明模仿目标改善，不能等同于任务utility提升。
最终accuracy恰等多数类baseline；未持久保存全部62条teacher-state预测，
不能仅据相等accuracy断言它们全部NO。现存rollout的精确匹配状态诊断见[缺陷报告](DIAGNOSIS_ZH.md)。

## 中断与恢复：按已持久确认的更新继续，不重放已接收步骤

| 阶段 | 事实与恢复依据 |
|---|---|
| 初次训练至22 | 逐步将adapter/optimizer/RNG/cursor/config/data/split绑定传回持久保存；VM丢失不补计inflight |
| 从22恢复 | 保留失败构建日志，定位NumPy bundled Meson误用；修复后核固定环境/base及checkpoint21/batch22 NLL完全一致，再恢复22状态，下一步23 |
| 至43后再中断 | epoch1/step29评估已完成；44仅start不计accepted；恢复checkpoint42/43数值与状态门，下一步44 |
| 至64后再中断 | epoch2/step58评估已完成；65仅start不计accepted；新VM恢复同两备份wheel/固定base，再核batch64 NLL完全一致及64全状态，下一步65 |
| 最终87 | 完成所有原定更新和epoch3全量评估，按同一规则选87；没有重置数据、改LR或重复计数 |

checkpoint的adapter、optimizer、CPU/CUDA RNG、policy score和cursor都须通过恢复门；
只有接收端fsync/hash/确认后的更新才算durable。模型启动、fit或日志中的start不算完成。
这些恢复不是新增独立训练实验，也不证明整个环境bitwise相同。

## 模型与数据指纹

| 对象 | SHA256 |
|---|---|
| 底座safetensors，3,087,467,144 bytes | `dd924a11b4c220f385b51ffa522daea7c9f3d850e31b162bb5661df483c6d3ee` |
| selected87原checkpoint文件，17,697,737 bytes | `846fef7fdfc19fde8a6d9cb7a75fff7d3dd8023036c1b357e99f2f8d73161a91` |
| checkpoint内部canonical digest | `9c8700e6b68cc4914b8a0f1484efa6485a02aa7047af942b338ca2ff96e5656b` |
| 数据canonical digest | `ad78840aa4878a84544c10b185be31bddc9c15c9b9e97d2128e9c7deefa11518` |
| split canonical digest | `05e14584f5c7549cffb32ca9d6c5d2daddb7407bbafea155d586f08377010d2b` |
| 训练config canonical digest | `0b69f05a5b0941c3e43d8bad1d9bba1e32fbcd177f97640bcbfd783786374e69` |

完整且区分“文件字节SHA”和“canonical对象digest”的登记见[小型摘要](evidence/summary.json)；
指纹不是已上传模型/数据的替代品。未上传checkpoint、原始教师请求和完整数据，
读者目前可复核公开表格/摘录一致性，但**不能只靠本目录重跑训练或独立重算全部结果**。
范围及获取边界见[证据说明](EVIDENCE_ZH.md)。

## 此前工程探索与当前87模型分开

| 较早分支 | 已完成/停止边界 | 不能推出的结论 |
|---|---|---|
| native-v2 filtered SFT | 39条eligible轨迹、15次更新；原4条dev的既定规则选step10 | 不等于当前292决策/87步数据或模型 |
| native-v2 Joint / learned Sequential原型 | 分别accepted4 / 2步；固定下一批ESS低于原门而停，未放宽保护 | 不是三种完整训练/公平优越性比较 |
| 旧SFT10真实三dev题检查 | 0/3业务pass，均T0；实际抽样6次NO，但总ASK概率约88.54%–92.57%，与重复seed路径有关 | 不能和本轮argmax全NO混称同一概率collapse |

这些是此前不同数据、选择规则和抽样协议的工程记录，未并入当前16对结果；
不把旧三题失败、R1历史或小样本IS估计当新原生mini基线。
原始证据仍保留，此次不发布完整早期运行包。当前可确认的是SFT87训练完成且任务收益未显示，
研究目标中的完整joint/学习型两阶段/同底座prompt比较仍未完成。
