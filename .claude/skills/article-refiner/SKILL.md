---
name: article-refiner
description: Refine, expand, polish, or review an existing technical share-style article / 润色 / 完善 / 改写 / 校对 this Hugo repo's Markdown posts. Use when improving structure, clarity, accuracy, tone, examples, front matter, publish readiness, or when Mermaid, Chart.js, Excalidraw, or Draw.io visuals should be added or fixed under source/post/. Do NOT use for writing articles from scratch — use article-writer instead.
compatibility: Works in .agents/skills for GitHub Copilot, Kilo Code, Roo Code, and OpenCode; sync to .claude/skills for Claude Code compatibility. No extra dependencies.
allowed-tools: Read Grep Glob
metadata:
  audience: experienced-engineers
  default-language: zh-cn
  repo: blog-hugo
  version: 1.2.5
  last-updated: 2026-04-23
  trigger-phrases:
    - 润色文章
    - 完善草稿
    - refine article
    - polish post
---

# Article Refiner

在用户要"润色文章、完善草稿、改写段落、补全缺失部分、发布前校对、压缩废话、增强逻辑结构"时使用。

## Canonical References

- **通用写作规范、质量清单、图表规则、front matter 约束**：统一以 [`AGENTS.md`](../../../AGENTS.md) 为准，不在本 Skill 中重复展开
- **图表嵌入语法**：见 [`references/embedding-syntax.md`](references/embedding-syntax.md)
- 本 Skill 只保留“润色旧文”真正独有的工作流和判断标准

## Scope & Boundaries

**本 Skill 负责：**

- 修正事实错误、术语不一致和明显歧义
- 优化结构、标题、转场、段落节奏
- 补齐缺失的前提、边界、坑点和验证信息
- 在需要时建议补图或修图
- 把文章润到更像作者本人在复盘，而不是在写说明稿

**本 Skill 不负责：**

- 从零创建新文章（使用 article-writer）
- 改写作者核心立场
- 编造实验、数据、引用或结论
- 修改文件名、`id`、年份目录、稳定锚点

## Workflow

1. **先完整读文**：至少覆盖 front matter、正文、引用、脚注、配套资源名，再判断是轻量润色、结构改写还是补充缺口
2. **先保留原意**：默认保留原文的核心观点、资源引用、章节职责；只在错误、冲突、不清楚或用户明确要求时调整
3. **按优先级改**：P0 事实/术语错误；P1 结构跳跃、标题含糊、长段和重复；P2 补前提、边界、坑点、验证方法；P3 打磨措辞和节奏
4. **语气优先像作者本人**：能保留第一人称时尽量保留，不要把明确的个人判断、体感、犹豫点、取舍理由抹平成中性摘要
5. **保持 diff 克制**：不要顺手重写整篇；优先修改真正影响可读性、可信度和作者感的部分

## Tone Calibration

润色旧文时，优先把它写成“有经验的工程师在复盘自己真实测试或实践”，而不是：

- 公文或发布说明
- 媒体评测摘要
- 过于均匀的 AI 中性总结

尤其注意：

- 开头不只要交代范围，还要让读者感受到作者为什么写、为什么亲自去测
- 转场少用“本文将… / 基于以上… / 作为基线…”这类官话
- 总结别只重复前文，应保留作者最终判断和“想帮读者少踩什么坑”的落点

## Default Deliverable

如果用户只说“帮我润色/完善这篇文章”，默认输出或落库顺序应为：

1. 发现的问题清单（结构 / 事实 / 术语 / 节奏）
2. 修订策略摘要（哪些改、哪些不改、为什么）
3. 可直接替换的修订版本，或在仓库中直接完成修改

## Quick Self-Check

- 核心观点还在吗？
- 有没有把作者原本有价值的判断磨没？
- 这版读起来像作者本人在复盘，还是像整理过的说明稿？
- 这次修改是否集中在真正有改进价值的地方？

## Maintenance

主副本位于 `.agents/skills/article-refiner/`；Kilo Code、Roo Code、OpenCode 和 GitHub Copilot 直接复用 `.agents/skills/`，仅在需要兼容 Claude Code 时同步到 `.claude/skills/`。
