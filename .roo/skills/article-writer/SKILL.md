---
name: article-writer
description: Draft or heavily rewrite a technical share-style blog post / 技术分享 / 技术文章 / 博客文章 for this Hugo repository. Use when the user wants a new article, wants notes turned into a post, needs title options, summary, front matter, outline, or wants Mermaid, Chart.js, Excalidraw, or Draw.io visuals added under source/post/.
compatibility: Works as a repo-local skill in .agents/skills, .claude/skills, .roo/skills, and .kilocode/skills. No extra runtime dependencies are required.
metadata:
  audience: experienced-engineers
  default-language: zh-cn
  repo: blog-hugo
---

# Article Writer

在用户要“写新文章、根据笔记起草技术博客、补齐结构、生成标题/摘要/front matter、把零散材料整理成可发布草稿”时使用。

## Workflow

1. **先明确任务边界**
   - 提炼主题、目标读者、核心结论、适用场景、限制条件和希望保留的素材。
   - 如果材料不足以支持明确结论，先输出缺口清单、大纲或需要补充的信息，不要硬编事实。
2. **结合仓库上下文写作**
   - 先读取 `AGENTS.md`。
   - 如果是落库写作，检查目标目录 `source/post/<year>/` 的已有文章、资源命名和 front matter 风格。
   - 如有必要，对比 1-3 篇相近主题文章，复用术语粒度，避免重复铺陈已有背景。
3. **先搭章节骨架，再展开正文**
   - 对这个仓库，优先使用这类结构：`背景/问题 -> 现象或约束 -> 方案设计/机制 -> 示例或实验 -> 适用条件与坑点 -> 总结`。
   - 开头前 1-3 段要交代问题、收益和边界，让读者快速判断是否值得继续读。
   - 每节先给 takeaway，再解释原因，再给例子、图或代码。
4. **输出有效的 Hugo Markdown**
   - 生成合法 YAML front matter。
   - 新文章默认可使用：`type: post`、`author: owent`，并给出克制且有检索价值的 `tags` / `categories`。
   - 不要擅自修改已有文章的数字文件名、`id`、年份目录或稳定资源名。
5. **主动判断是否需要图表**
   - 如果纯文字会迫使读者脑内模拟流程、状态、时序、拓扑、依赖关系或数据变化，就补一个图或图表。
   - 图要放在首次需要它的位置附近，而不是统一堆到章节末尾。
6. **补齐真正有价值的信息**
   - 写清前提：版本、平台、编译器、时间点、网络环境、实验条件。
   - 解释 trade-off，不只写 happy path。
   - 优先用短段落、列表、表格和必要图表降低阅读负担。
7. **交付前自审**
   - 标题具体、不标题党；摘要忠实反映正文。
   - 术语一致，段落不过长，列表和代码块清晰。
   - 不编造 benchmark、Issue、引用、版本结论或用户未提供的事实。

## Diagram decisions

- 仅在图表能显著降低理解成本时使用，不加装饰性图片。
- 选型规则：
  - **Mermaid**：流程图、时序图、状态图、类图、ER 图、甘特图、象限图、简单文本驱动架构图。
  - **Chart.js**：带数值的对比、趋势、占比、分布、混合折线/柱状图。
  - **Excalidraw**：概念草图、白板式架构、角色/组件关系、帮助建立心智模型的解释型图示。
  - **Draw.io**：更正式、更规整、更稠密的架构图、部署图、网络拓扑图。
- 默认落地方式：
  1. 简短 **Mermaid / Chart.js**：优先代码块（`mermaid`、`chart`、`chartjs`）。
  2. 较长或可复用 **Mermaid / Chart.js**：优先外部 `*.mermaid` / `*.chart.json` 文件。
  3. 非平凡 **Excalidraw / Draw.io**：优先外部 `*.excalidraw` / `*.drawio` 文件，并在正文中用图片语法引用。
  4. Shortcode `src` / inline 均支持，但默认不要优先选，除非它明显更干净。
- 外部资源命名与文章编号保持同前缀，例如 `2604-*.mermaid`、`2604-*.drawio`、`2604-*.excalidraw`、`2604-*.chart.json`。
- 文件型图表在图片语法里要写有意义的 alt 文本；正文里也要用 1-2 句点明“这张图要帮助读者看什么”。
- 如果图表只是重复正文，没有新增理解价值，就删掉它。

## Supported embedding syntax

这个仓库里，四类图表都支持“外部文件”和“内嵌内容”两大类写法；默认优先选可维护性更好的那一种。

- **图片语法引用外部文件**
  - Mermaid：`![流程图](2604-example.mermaid)`
  - Chart.js：`![趋势图](2604-example.chart.json)`
  - Excalidraw：`![架构草图](2604-example.excalidraw)`
  - Draw.io：`![部署图](2604-example.drawio)`
- **代码块内嵌**
  - Mermaid：使用 ` ```mermaid ` 代码块
  - Chart.js：使用 ` ```chart ` 或 ` ```chartjs ` 代码块
  - Excalidraw：使用 ` ```excalidraw ` 代码块，内容是 Excalidraw JSON
  - Draw.io：使用 ` ```drawio ` 代码块，内容是 draw.io XML
- **Shortcode 引用外部文件**
  - Mermaid：`{{< mermaid src="2604-example.mermaid" >}}{{< /mermaid >}}`
  - Chart.js：`{{< chart src="2604-example.chart.json" >}}{{< /chart >}}`
  - Excalidraw：`{{< excalidraw src="2604-example.excalidraw" >}}{{< /excalidraw >}}`
  - Draw.io：`{{< drawio src="2604-example.drawio" >}}{{< /drawio >}}`
- **Shortcode 内联**
  - Mermaid：`{{< mermaid >}}...{{< /mermaid >}}`
  - Chart.js：`{{< chart >}}...{{< /chart >}}`
  - Excalidraw：`{{< excalidraw >}}...{{< /excalidraw >}}`
  - Draw.io：`{{< drawio >}}...{{< /drawio >}}`

默认优先级：短 Mermaid/Chart.js 用代码块；复杂 Mermaid/Chart.js 用外部文件；非平凡 Excalidraw/Draw.io 用外部文件；shortcode 只在它明显比图片语法或代码块更自然时使用。

## Default Output

如果用户要求“起草一篇新文”但没有指定输出格式，优先提供：

1. 3 个标题候选
2. 1 个推荐标题 + 简短摘要
3. front matter 草稿
4. 正文 Hugo Markdown
5. 如确有必要，再补配图/图表建议与建议文件名

## Self-check

- 标题和 H2/H3 是否足够描述性，能让读者快速扫描？
- 开头是否说清问题、收益和边界？
- 长段解释里，是否有本应改成列表、表格、时序图、流程图或统计图的内容？
- 每个图表是否放在需要它的位置，并真正减少了读者的脑内模拟成本？

## Guardrails

- 不要编造引用来源、外链、Issue、实验数据或兼容性结论。
- 结论依赖前提时，必须把前提写出来。
- 不确定时，明确标注“待确认”，并说明还需要验证什么。
- 如果是在现有文件上继续写，优先延续原文结构和语气，而不是整篇推翻重写。
