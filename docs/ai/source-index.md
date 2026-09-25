# AI 提示词与写作实践来源索引

本文件保存提示词和 Skill 维护所需的外部依据，不作为默认写作提示加载。只记录当前可执行结论；来源语义或仓库用法变化时重新核验。

## Agent 指令与 Skills

| 来源 | 当前结论 | 重新核验触发条件 |
| --- | --- | --- |
| [Agent Skills Specification](https://agentskills.io/specification) | `name` 和 `description` 承担发现与触发；完整正文在触发后加载，详细资源按需读取。 | 修改 Skill 目录、front matter 或客户端兼容策略 |
| [Best practices for skill creators](https://agentskills.io/skill-creation/best-practices) | Skill 应来自真实任务、用户纠错和项目资料；只保留 Agent 容易做错的专业流程，并用执行结果删减无效规则。 | 新增 Skill、同类错误复发或 Skill 明显膨胀 |
| [Optimizing skill descriptions](https://agentskills.io/skill-creation/optimizing-descriptions) | 描述按用户意图写明适用场景和相邻边界；用正反触发样例评估，避免为个别关键词过拟合。 | Skill 误触发、漏触发或任务边界调整 |
| [Evaluating skill output quality](https://agentskills.io/skill-creation/evaluating-skills) | 将可客观验证的要求写成断言；语气和作者感仍需人工评审。规则增加但质量不升时，优先删减。 | 修改核心流程或收到新的质量反馈 |
| [Claude Code project memory](https://code.claude.com/docs/en/memory) | Claude 兼容入口使用 `@` 导入 `AGENTS.md`，避免复制全局规则；相对路径从导入文件所在目录解析。 | Claude Code 的加载位置或导入语法变化 |

## 去模板化写作

| 来源 | 当前结论 | 应用边界 |
| --- | --- | --- |
| [Claude prompting best practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) | 用清晰的正向要求描述目标格式和语气；少量相关且多样的示例比抽象形容词稳定；提示本身的格式会影响输出格式。 | 作者声音需要校准时，抽样相关旧文；不把整库文章塞入上下文 |
| [OpenAI Model Spec: appropriate style](https://model-spec.openai.com/) | 默认表达应清晰、直接、简洁，避免不增加信息的华丽措辞、夸张、套话和重复。 | 作为通用编辑原则，不覆盖作者有意保留的语气 |
| [Stylometric comparisons of human versus AI-generated creative writing](https://www.nature.com/articles/s41599-025-05986-3) | 受控语料中，同一模型输出比人类文本更容易形成均匀的风格簇；全文级节奏和结构重复值得检查。 | 研究对象主要是英文创意写作，不能据此判定单篇中文文章的作者身份 |
| [Delving into LLM-assisted writing in biomedical publications through excess vocabulary](https://pmc.ncbi.nlm.nih.gov/articles/PMC12219543/) | 大规模英文摘要出现一组 LLM 相关高频词变化，说明词汇模板会积累；单个词本身不是可靠证据。 | 只用于提醒检查密集套话，不建立中文禁词表，也不用于规避检测器 |

## 写作研究与编辑依据

下列资料于 2026-09-25 核对。日期栏记录发表或版本日期，阅读范围列说明实际证据边界；没有复现实验。
既有的供应商提示建议不能替代作者样本或实际改稿效果。研究结论只适用于其模型、语言和任务，不能直接推出通用中文禁词表。

| 来源、日期与状态 | 阅读范围与发现 | 在本仓库的用途及限制 |
| --- | --- | --- |
| [Google：Voice and tone](https://developers.google.com/style/tone)，页面更新 2026-05-27；[Microsoft：简明用词](https://learn.microsoft.com/en-us/style-guide/word-choice/use-simple-words-concise-sentences)，页面更新 2022-06-24 | 编辑指南正文：直接表达、删无效修饰、同一概念保持同一术语 | 作为技术说明的编辑基线，保留博客作者有意使用的语气 |
| [Do LLMs write like humans?](https://www.pnas.org/doi/10.1073/pnas.2422455122)，PNAS，2025-02-18 | 摘要与公开结果：受测指令模型偏好名词密集表达，文体适配存在差异 | 检查语法结构和文体，不能只替换词汇；主要是英语研究 |
| [Beemo](https://aclanthology.org/2025.naacl-long.357/)，NAACL，2025-04；[附录 B](https://aclanthology.org/2025.naacl-long.357.pdf) | 摘要和专家编辑指引：重复、生硬表达、语气、助手包装与事实都需要复核 | 借鉴检查项，不照搬数据制作时的修改比例 |
| [Human-LLM Coevolution](https://aclanthology.org/2025.findings-acl.657/)，ACL Findings，2025-07 | 摘要：部分被指出过度使用的词随后减少，其他词继续增加 | 高频信号会变化，不把固定词表当成作者鉴定工具 |
| [Can You Make It Sound Like You?](https://aclanthology.org/2026.acl-long.2030/)，ACL，2026-07 | 摘要：81 人研究中，后期编辑改善了风格相似性，但未完全恢复无辅助写作的特征 | 对照作者原稿和样本；“人工看过”或一句“保留声音”不能保证恢复个人风格 |
| [The shrinking landscape of linguistic diversity](https://pubmed.ncbi.nlm.nih.gov/42637911/)，Nature Human Behaviour，2026-08-24 | 作者摘要与[期刊简报](https://www.nature.com/articles/s41562-026-02549-7)：润色与风格差异缩小有关；未读取付费全文方法 | 审慎对待反复全文重写，不用随机句长或强加口语补偿 |
| [How LLMs Distort Our Written Language](https://arxiv.org/abs/2603.18161v2)，预印本 v2，2026-08-26 | 摘要：限定语法编辑仍可能引起意义变化 | 修改后比较事实与立场，不能只看文字是否顺畅；不把效果量外推到本站 |
| [Style as a Confound](https://arxiv.org/abs/2608.26710v1)，arXiv v1，2026-08-27 | 摘要：同样的专业编辑会让不同检测器评分向不同方向变化 | 检测评分不作为写作质量或作者身份的证明 |
| [AI Writers Have a Consistent Stylometric Footprint, but AI Editors Do Not](https://arxiv.org/abs/2608.27855v2)，arXiv v2，2026-09-22 | 摘要和版本记录：从零生成与修改人类原稿的文体特征不同 | 新写与润色分开评估；arXiv 作者填写的会议备注不等于已核验正式发表 |

词汇多样性、单篇语言复杂度和不同作者之间的风格差异是不同指标。比较研究前先确认其度量对象。
表中的编辑用途是可检验的建议，不代表本站规则已通过多模型实验或读者盲评。

## 更新与评估写作规则

更换主要写作模型、出现反复的改稿问题、增加语言或文体、重要来源修订时，重新核验。
也可每 3—6 个月复核；这是维护建议，不是研究结论。只维护影响实际写作的规则，不积累无关论文摘要。

1. 读取 `AGENTS.md`、相关 Skill、本索引和实际失败样例，确认要解决的是事实、语义、结构还是文风问题。
2. 从已有来源查新版本、勘误和后续研究，再检索近期原文及反例。可用 `LLM editing author voice semantic drift`、
   `AI generated versus AI edited text stylometry`、`中文 AI 润色 文体 同质化`，按当前年份和目标文体调整。
3. 记录链接、发表和版本日期、访问日期、阅读范围、语言、文体、模型、样本与限制。
   区分正式研究、预印本、编辑指南和社区经验；摘要不能代替方法核查，相关性不能改成因果。
4. 用代表性中文与英文文章、作者认可的旧文和失败样例比较新旧规则。加入准确术语、真实对比、必要警告等
   应保留的反例。新写固定材料，润色固定原稿；两类结果分开看，控制模型版本和可控制的生成设置。
5. 先查事实、语义和作者立场是否保留，再评理解效果、重复、语气及剩余人工修改量。
   有条件时隐藏输出版本请读者比较，并使用未参与调规则的样本复查；未做的评估明确记录。
   检测分数、句长或词频不替代这些检查，也不能用流畅度抵消事实退化。
6. 只合入有依据的最小修改，合并重复规则并保留例外。稳定规则写入 `AGENTS.md`；
   只有任务独有流程或触发边界改变才修改 Skill 并同步镜像，来源及限制留在本文件。
   验证 Markdown、引用、相对路径和 diff；规则效果变差时根据版本记录撤回对应修改。

每次更新在审阅记录中说明：触发问题、核对的来源与版本、规则增删原因、样本和评审方式、
实际结果、未执行检查及待复核问题。不要把调研历史和维护日期复制进常驻提示。
