---
name: article-refiner
description: Refine, expand, polish, or review an existing technical share-style article / 润色 / 完善 / 改写 / 校对 this Hugo repo's Markdown posts. Use when improving structure, clarity, accuracy, tone, examples, front matter, publish readiness, or when Mermaid, Chart.js, Excalidraw, or Draw.io visuals should be added or fixed under source/post/.
compatibility: Works as a repo-local skill in .agents/skills, .claude/skills, .roo/skills, and .kilocode/skills. No extra runtime dependencies are required.
metadata:
  audience: experienced-engineers
  default-language: zh-cn
  repo: blog-hugo
---

# Article Refiner

在用户要“润色文章、完善草稿、改写段落、补全缺失部分、发布前校对、压缩废话、增强逻辑结构”时使用。

## Workflow

1. **先完整读文，再决定改多少**
   - 阅读整篇文章，包括 front matter、底部引用、脚注、图表引用、相邻资源文件名。
   - 先判断这是轻量润色、结构性改写，还是补充缺失章节，避免一上来大改特改。
2. **优先保留原作者意图**
   - 保留原文的核心观点、已明确给出的事实、仓库内链接、资源引用和已有章节职责。
   - 只有在用户明确要求，或已有表述明显错误、冲突、不清楚时，才调整论点或事实表述。
3. **按价值排序做改进**
   - 先修正事实不清、术语不一致、结构跳跃、标题含糊、长段落、重复表达。
   - 再补前提、边界条件、常见坑、验证方法、必要示例。
   - 当一大段解释其实更适合流程图、时序图、概念图或统计图时，补一个合适的图，而不是继续堆字。
   - 最后才做措辞润色和节奏优化。
4. **保持 Hugo 友好和 diff 友好**
   - 保持合法 YAML front matter。
   - 不要擅自修改文章编号、文件名、年份目录、稳定 anchor、脚注标签或配套资源命名。
   - 如果只是改文，不要顺手重排所有章节或统一改写所有句子。
5. **技术内容要更清楚，而不是更花哨**
   - 每节先给结论，再解释原因，再给例子。
   - 明确平台、版本、编译器、时间点、实验条件等前提。
   - 删除无助于理解的铺垫，保留真正能帮助读者落地的例子和权衡。
6. **交付前核对**
   - front matter、标题层级、列表缩进、代码块、Mermaid/KaTeX 语法、引用链接是否完整。
   - 检查有没有新增的“看起来像真的”但实际上未经验证的说法。

## Diagram decisions

- 如果文章的难点在“理解关系”，优先考虑图；如果难点在“理解数值变化”，优先考虑图表。
- 选型规则：
  - **Mermaid**：流程、时序、状态、类、ER、甘特、象限等结构化关系。
  - **Chart.js**：数值对比、趋势、比例、分布。
  - **Excalidraw**：概念解释、白板式架构、需要更轻松叙事感的图。
  - **Draw.io**：更正式、元素更多、布局精确的架构/部署/网络图。
- 默认落地方式：短 Mermaid/Chart.js 用代码块；复杂或可复用内容拆外部文件；非平凡 Excalidraw/Draw.io 优先外部文件并在正文中用图片语法引用。
- 图表应该紧贴首次需要它的段落出现，并配有引导语或简短说明；不要把图和解释拆得太远。
- 对文件型图表，使用有意义的 alt 文本，并确保正文即使不看图也能读懂主结论。

## Supported embedding syntax

- **图片语法引用外部文件**
  - Mermaid：`![流程图](2604-example.mermaid)`
  - Chart.js：`![趋势图](2604-example.chart.json)`
  - Excalidraw：`![架构草图](2604-example.excalidraw)`
  - Draw.io：`![部署图](2604-example.drawio)`
- **代码块内嵌**
  - Mermaid：` ```mermaid `
  - Chart.js：` ```chart ` 或 ` ```chartjs `
  - Excalidraw：` ```excalidraw `，内容为 Excalidraw JSON
  - Draw.io：` ```drawio `，内容为 draw.io XML
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

## Default Output

如果用户只说“帮我润色/完善这篇文章”而未指定形式，优先给出：

1. 发现的问题清单（结构 / 事实 / 术语 / 节奏）
2. 修订策略摘要
3. 可直接替换的修订版本，或在仓库中直接完成改写

## Guardrails

- 不要为了“看起来更像 AI 在工作”而过度改写作者原文。
- 不要编造新实验、新引用、新数据去填补逻辑空洞；不确定时标注“待确认”。
- 如果原文已经有清晰结构，优先做局部增强，而不是推倒重来。
