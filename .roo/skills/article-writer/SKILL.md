---
name: article-writer
description: Draft or heavily rewrite a technical share-style blog post / 技术分享 / 技术文章 / 博客文章 for this Hugo repository. Use when the user wants a new article, wants notes turned into a post, needs title options, summary, front matter, outline, or wants Mermaid, Chart.js, Excalidraw, or Draw.io visuals added under source/post/. Do NOT use for polishing or minor edits to existing articles — use article-refiner instead.
compatibility: Works in .agents/skills, .claude/skills, .roo/skills, and .kilocode/skills. No extra dependencies.
allowed-tools: Read Grep Glob
metadata:
  audience: experienced-engineers
  default-language: zh-cn
  repo: blog-hugo
  version: 1.2.2
  last-updated: 2026-03-27
  trigger-phrases:
    - 写篇文章
    - 起草博客
    - write an article
    - draft a post
---

# Article Writer

在用户要"写新文章、根据笔记起草技术博客、补齐结构、生成标题/摘要/front matter、把零散材料整理成可发布草稿"时使用。

## Scope & Boundaries

**本 Skill 负责：**

- 从零创建文章结构和内容
- 生成 3 个标题候选 + 推荐标题 + 摘要
- 生成合法 YAML front matter
- 根据主题判断是否需要图表，并给出建议
- 将零散材料整理成完整草稿

**本 Skill 不负责：**

- 修改已有文章（使用 article-refiner）
- 修改已有文章的文件名、id、年份目录
- 执行代码验证或生成 benchmark 数据
- 代替作者做技术决策（只提供建议）

## Input Requirements

开始写作前，请确保有以下信息之一：

1. **明确主题**：要写的技术话题是什么
2. **目标读者**：初学者/中级工程师/专家
3. **核心结论**：读者读完应该获得什么
4. **素材来源**：文档链接、代码片段、实验数据、个人笔记

**如果信息不足：**

- 先输出信息缺口清单
- 提供大纲或章节建议
- 询问关键决策点

## Workflow

### Step 1: 明确任务边界

- 提炼主题、目标读者、核心结论、适用场景、限制条件
- **如果材料不足以支持明确结论，先输出缺口清单、大纲或需要补充的信息，不要硬编事实**

### Step 2: 结合仓库上下文写作

- 先读取 [`AGENTS.md`](../../../AGENTS.md)
- 如果是落库写作，检查目标目录 `source/post/<year>/` 的已有文章、资源命名和 front matter 风格
- 如有必要，对比 1-3 篇相近主题文章，复用术语粒度，避免重复铺陈已有背景

### Step 3: 先搭章节骨架，再展开正文

- 对这个仓库，优先使用这类结构：`背景/问题 -> 现象或约束 -> 方案设计/机制 -> 示例或实验 -> 适用条件与坑点 -> 总结`
- 开头前 1-3 段要交代问题、收益和边界，让读者快速判断是否值得继续读
- 每节先给 takeaway，再解释原因，再给例子、图或代码
- 默认文风应自然、圆润、连贯，像有经验的工程师在写给同行看的技术博客，而不是把提纲机械铺开

### Step 4: 输出有效的 Hugo Markdown

- 生成合法 YAML front matter
- 新文章默认可使用：`type: post`、`author: owent`，并给出克制且有检索价值的 `tags` / `categories`
- **不要擅自修改已有文章的数字文件名、`id`、年份目录或稳定资源名**

### Step 5: 主动判断是否需要图表

- 如果纯文字会迫使读者脑内模拟流程、状态、时序、拓扑、依赖关系或数据变化，就补一个图或图表
- 图要放在首次需要它的位置附近，而不是统一堆到章节末尾
- **如果使用 inline Mermaid（围栏代码块）**，必须逐行仔细核对语法并在交付前验证可正确渲染；不要只写完代码块就结束
- 如果 Mermaid 图较长、可复用、包含较多 `<br/>`、引号、复杂 note/message，可优先拆成外部 `.mermaid` 文件
- 如果 inline Mermaid 中必须保留 `<...>` 这类 HTML 风格文本，优先用引号包裹后再验证渲染结果

### Step 6: 补齐真正有价值的信息

- 写清前提：版本、平台、编译器、时间点、网络环境、实验条件
- 解释 trade-off，不只写 happy path
- 优先用短段落、列表、表格和必要图表降低阅读负担
- 即便使用列表，也要让段落前后有承接，避免整篇文章看起来像会议纪要、笔记拼接或 AI 自动扩写

### Step 7: 质量检查（交付前必做）

按 [`AGENTS.md`](../../../AGENTS.md) "交付质量检查清单" 逐项确认
（Content Quality / Technical Accuracy / Hugo Compliance /
Readability / Editorial）。

## Diagram Decisions

仅在图表能显著降低理解成本时使用。选型规则和落地方式详见 [`AGENTS.md`](../../../AGENTS.md) "图表使用指南"。嵌入语法详见 [`references/embedding-syntax.md`](references/embedding-syntax.md)。

**速查：** Mermaid → 流程/时序/状态；Chart.js → 数值对比/趋势；
Excalidraw → 概念草图；Draw.io → 正式架构图。短内容用代码块，
复杂内容拆外部文件。**inline Mermaid 必须仔细核对并验证语法/渲染结果。**

## Default Output Format

如果用户要求"起草一篇新文"但没有指定输出格式，**必须**按以下顺序提供：

1. **3 个标题候选**（不同侧重点）
2. **1 个推荐标题** + 简短理由
3. **摘要**（100-150 字）
4. **Front matter 草稿**（YAML 格式）
5. **正文 Hugo Markdown**（章节骨架 + 关键段落）
6. **配图/图表建议**（如确有必要，含建议文件名）

## Error Handling

### 信息不足时

**不要**强行生成内容。应该：

1. 列出信息缺口清单
2. 提供可能的写作方向
3. 询问用户需要补充哪些信息

**示例回复：**

```text
根据现有材料，以下信息需要补充：
1. 目标读者是谁？（初学者/中级/专家）
2. 核心结论是什么？（读者应该获得什么）
3. 有代码示例或实验数据吗？
4. 适用场景和限制条件是什么？

在获得这些信息前，我可以提供：
- 文章大纲建议
- 可能的章节结构
- 相关参考资料（如有）
```

### 发现冲突时

如果主题与仓库已有文章有重叠：

1. 引用已有文章链接
2. 说明本文与已有文章的区别
3. 建议补充而非重复

### 技术细节不确定时

**必须**显式标注：

```markdown
> **待确认**：该特性在 v1.18 中的行为可能与 v1.17 不同，需要验证。
```

## Example

**用户说"写篇关于 Go 并发模型的文章"→ 输出结构：**

1. 3 个标题候选（不同侧重点）
2. 推荐标题 + 理由：`Go 并发模型详解：Goroutine、Channel 与 Select 的协作机制`
3. 摘要（100-150 字）
4. Front matter 草稿（type: post, tags: [golang, concurrency, goroutine, channel]）
5. 正文大纲：问题背景 → MPG 调度器原理 → Channel 通信 → Select 多路复用 → 适用条件与坑点 → 总结
6. 图表建议：`2601-mpg-model.mermaid`（调度器架构图）

## Guardrails

### 禁止行为

- 不要编造引用来源、外链、Issue、实验数据或兼容性结论
- 不要代替用户做技术选型决策
- 不要在信息不足时强行生成完整文章
- 不要擅自修改已有文章的文件名、id、年份目录

### 必须遵守

- 结论依赖前提时，必须把前提写出来
- 不确定时，明确标注"待确认"，并说明还需要验证什么
- 保留用户提供的原始素材和核心观点
- 如果发现与仓库已有文章冲突，必须引用并说明差异

## Self-Check Questions

交付前问自己：

1. 标题和 H2/H3 是否足够描述性，能让读者快速扫描？
2. 开头是否说清问题、收益和边界？
3. 长段解释里，是否有本应改成列表、表格、时序图、流程图或统计图的内容？
4. 每个图表是否放在需要它的位置，并真正减少了读者的脑内模拟成本？
5. 若使用 inline Mermaid，我是否已经仔细核对并验证语法与渲染结果，且对 `<...>` 这类文本采用了引号包裹等安全写法？
6. 有没有新增的"看起来像真的"但实际上未经验证的说法？
7. 如果我是读者，看完这篇文章能做出技术决策吗？

## Maintenance

**主副本**：`.agents/skills/article-writer/`（含 `SKILL.md` 和 `references/`）

**同步策略**：

- 本目录是主副本，所有修改在此进行
- `.claude/skills/`、`.kilocode/skills/`、`.roo/skills/` 下的副本通过 `sync-skills.ps1` 同步
- 修改后需检查 compatibility 字段是否仍然准确
