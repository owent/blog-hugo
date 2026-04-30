---
name: article-writer
description: Draft or heavily rewrite a technical share-style blog post / 技术分享 / 技术文章 / 博客文章 for this Hugo repository. Use when the user wants a new article, wants notes turned into a post, needs title options, summary, front matter, outline, or wants Mermaid, Chart.js, Excalidraw, or Draw.io visuals added under source/post/. Do NOT use for polishing or minor edits to existing articles — use article-refiner instead.
compatibility: Works in .agents/skills for GitHub Copilot, Kilo Code, Roo Code, and OpenCode; sync to .claude/skills for Claude Code compatibility. No extra dependencies.
allowed-tools: Read Grep Glob
metadata:
  audience: experienced-engineers
  default-language: zh-cn
  repo: blog-hugo
  version: 1.2.9
  last-updated: 2026-04-30
  trigger-phrases:
    - 写篇文章
    - 起草博客
    - write an article
    - draft a post
---

# Article Writer

在用户要"写新文章、根据笔记起草技术博客、补齐结构、生成标题/摘要/front matter、把零散材料整理成可发布草稿"时使用。

## Canonical References

- **通用写作规范、质量清单、图表规则、front matter 约束**：统一以 [`AGENTS.md`](../../../AGENTS.md) 为准，不在本 Skill 中重复展开
- **图表嵌入语法**：见 [`references/embedding-syntax.md`](references/embedding-syntax.md)
- 本 Skill 只保留“从零起草新文章”真正独有的工作流和输出要求

## Scope & Boundaries

**本 Skill 负责：**

- 从零创建文章结构和正文草稿
- 生成标题候选、推荐标题、摘要和 front matter 草稿
- 根据主题判断是否需要图表，并给出建议
- 把零散材料整理成可发布草稿
- 在新文里主动写出作者感，而不是默认写成中性说明文

**本 Skill 不负责：**

- 修改已有文章（使用 article-refiner）
- 修改已有文章的文件名、`id`、年份目录
- 编造 benchmark、实验结果或外部结论
- 代替作者做技术选型决策

## Workflow

1. **先定边界**：提炼主题、目标读者、核心结论、适用场景和限制条件；如果信息不足，先列缺口，不要硬编
2. **先读仓库语境**：读取 [`AGENTS.md`](../../../AGENTS.md)，必要时检查目标年份目录和相近文章，避免术语粒度、资源命名和背景铺陈跑偏
3. **先搭骨架再展开**：优先按“背景/问题 → 约束 → 方案/机制 → 示例/实验 → 适用条件与坑点 → 总结”组织
4. **主动写出作者感**：如果题材包含实测、踩坑、体验对比、选型判断、额度或性能权衡，优先保留第一人称和个人判断，不要自动写成客观报告
5. **再决定是否要图**：只有在图表能显著降低理解成本时再补图，具体规则回看 `AGENTS.md`

## Tone Calibration

新文默认要写成“有经验的工程师在给同行做真实分享/复盘”，而不是：

- 新闻导语式开头
- 产品说明或发布稿
- 只有客观陈述、没有作者视角的中性摘要

尤其注意：

- 开头不只交代范围，还要让读者知道作者为什么关心这个问题、为什么值得写
- 转场优先自然博客口吻，少用“本文聚焦… / 基于以上分析… / 作为基线…”
- 少用声明式自证和机械铺垫，例如“这不是…而是…”、“先把边界说清楚”、“读完本文你会…”；真实博客通常会更快进入作者正在关心的问题
- 辅助项目、测试样本、工具背景只写到支撑主题所需的程度，不要把无关工程目的和模块细节展开成主线
- 标题保持简洁，优先短标题、名词短语或简洁判断，避免完整句子式长标题
- 需要分析数据时，优先写严重程度、量级、趋势和作者判断；如果原始表格、成本、耗时、数量、占比是文章核心证据，应尽量保留完整数据，不要只剩抽象总结
- 数据很多时，可以用“结论先行 + 明细表保留”的结构；不要因为追求短文而删掉支撑结论的量化记录
- 作者偏好直接、带个人体感和工程风险判断的表达，不喜欢过度中立、过度圆润、过度解释的 AI 腔
- 少写自我声明式句子，例如“我关心的不是…而是…”、“这些数字不是用来…”；真实文章可以直接给数据、给判断
- 如果作者在实测类文章里给出主观猜测、负面评价或口语化风险表达，优先保留；不要全部改成书面化的“风险提示”或乐观结论
- 原因相近的分析不要拆太散。上下文、长链路、幻觉、退化如果本质是同一个判断，可以合在一节里写
- 结尾可以更直接，允许保留“不能全信”“重要代码要人工 Review”“业务 GG”这类作者式落点，不要自动改成公文式总结
- 少用“锁住语义”“守住约束”“关键不变量”“收敛用法”这类书面化抽象词；优先写成“测到产品逻辑”“记得不能错的要求”“哪些地方绝对不能错”“别放开了随便用”
- 技术分享类文章结尾可以用“欢迎有兴趣的小伙伴们互相交流探讨。”作为轻量互动收尾；不要改成过于正式的“欢迎讨论指正”
- 总结不只重申结论，还应给出作者最后的判断、边界和落点

## Default Deliverable

如果用户要求“起草一篇新文”但没有指定格式，默认输出顺序应为：

1. 3 个标题候选
2. 1 个推荐标题 + 简短理由
3. 摘要
4. front matter 草稿
5. 正文 Hugo Markdown
6. 确有必要时再补图表建议

## Quick Self-Check

- 这篇读起来像真人作者在分享经验，还是像 AI 在整理材料？
- 开头、转场和结尾里，能感受到作者为什么写、怎么判断、想帮读者解决什么问题吗？
- 有没有把本来应该有“人味”的题材写成了中性报告？
- 有没有过多声明、过多解释、过多铺垫，或者把无关背景写成正文重点？
- 标题是不是太像一句完整的 AI 总结？能不能改短？
- 如果文章依赖测试或实测数据，关键表格和数值是否完整保留？
- 是否保留了作者自己的判断、怀疑和口语化风险感，而不是写成无情绪的客观报告？
- 是否把同一原因拆成了多个机械小节？能否合并？
- 是否出现“锁住、守住、不变量、收敛、语义”等偏书面抽象词？能否换成更直接、更像作者本人说话的表达？
- 读者看完这篇，能据此做出判断或行动吗？

## Maintenance

主副本位于 `.agents/skills/article-writer/`；Kilo Code、Roo Code、OpenCode 和 GitHub Copilot 直接复用 `.agents/skills/`，仅在需要兼容 Claude Code 时同步到 `.claude/skills/`。
