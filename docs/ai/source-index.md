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

## 仓库落地原则

- 用作者已有文章、真实改稿记录和用户纠错校准写作规则，外部研究只提供可检验的补充假设。
- 分开执行事实复核与风格复核，避免为了语气自然牺牲技术准确性。
- 检查全文的重复结构、均匀节奏和空泛转场；不要用词语黑名单或机械句长扰动代替编辑判断。
- 不通过故意错误、伪造经历或 AI 检测规避来制造“人味”。
