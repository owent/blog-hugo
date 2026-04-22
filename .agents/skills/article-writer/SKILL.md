---
name: article-writer
description: Draft or heavily rewrite a technical share-style blog post / 技术分享 / 技术文章 / 博客文章 for this Hugo repository. Use when the user wants a new article, wants notes turned into a post, needs title options, summary, front matter, outline, or wants Mermaid, Chart.js, Excalidraw, or Draw.io visuals added under source/post/. Do NOT use for polishing or minor edits to existing articles — use article-refiner instead.
compatibility: Works in .agents/skills for GitHub Copilot, Kilo Code, Roo Code, and OpenCode; sync to .claude/skills for Claude Code compatibility. No extra dependencies.
allowed-tools: Read Grep Glob
metadata:
  audience: experienced-engineers
  default-language: zh-cn
  repo: blog-hugo
  version: 1.2.5
  last-updated: 2026-04-23
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
- 读者看完这篇，能据此做出判断或行动吗？

## Maintenance

主副本位于 `.agents/skills/article-writer/`；Kilo Code、Roo Code、OpenCode 和 GitHub Copilot 直接复用 `.agents/skills/`，仅在需要兼容 Claude Code 时同步到 `.claude/skills/`。
