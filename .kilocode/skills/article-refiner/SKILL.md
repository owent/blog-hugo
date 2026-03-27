---
name: article-refiner
description: Refine, expand, polish, or review an existing technical share-style article / 润色 / 完善 / 改写 / 校对 this Hugo repo's Markdown posts. Use when improving structure, clarity, accuracy, tone, examples, front matter, publish readiness, or when Mermaid, Chart.js, Excalidraw, or Draw.io visuals should be added or fixed under source/post/. Do NOT use for writing articles from scratch — use article-writer instead.
compatibility: Works in .agents/skills, .claude/skills, .roo/skills, and .kilocode/skills. No extra dependencies.
allowed-tools: Read Grep Glob
metadata:
  audience: experienced-engineers
  default-language: zh-cn
  repo: blog-hugo
  version: 1.2.0
  last-updated: 2026-03-27
  trigger-phrases:
    - 润色文章
    - 完善草稿
    - refine article
    - polish post
---

# Article Refiner

在用户要"润色文章、完善草稿、改写段落、补全缺失部分、发布前校对、压缩废话、增强逻辑结构"时使用。

## Scope & Boundaries

**本 Skill 负责：**

- 修正事实错误、术语不一致
- 优化文章结构、标题表达
- 压缩冗余、过长的段落
- 补充边界条件、常见坑、验证方法
- 添加或修正图表
- 提升整体可读性和专业性

**本 Skill 不负责：**

- 从零创建新文章（使用 article-writer）
- 改变作者的核心论点和观点
- 编造新实验、新数据填补逻辑空洞
- 修改文件名、id、年份目录、稳定锚点

**优先级原则：**

- **P0（最高）**：事实错误、安全漏洞、严重术语错误
- **P1**：结构跳跃、标题含糊、长段落、重复表达
- **P2**：补充前提、边界条件、常见坑、验证方法
- **P3**：措辞润色、节奏优化、排版美化

## Input Requirements

开始润色前，请确保：

1. **完整阅读原文**：包括 front matter、正文、底部引用、脚注、图表引用、相邻资源文件名
2. **明确润色范围**：
   - 轻量润色（只改措辞、格式）
   - 结构性改写（调整章节顺序）
   - 补充缺失章节
3. **了解用户意图**：用户最在意改进哪些方面？

**如果原文有明显问题：**

- 先列出发现的问题清单
- 给出修订策略摘要
- 询问用户确认后再进行大幅度修改

## Workflow

### Step 1: 先完整读文，再决定改多少

- 阅读整篇文章，包括 front matter、底部引用、脚注、图表引用、相邻资源文件名
- 判断这是轻量润色、结构性改写，还是补充缺失章节
- **避免一上来大改特改**

### Step 2: 优先保留原作者意图

- 保留原文的核心观点、已明确给出的事实
- 保留仓库内链接、资源引用和已有章节职责
- **只有在以下情况才调整论点或事实表述**：
  - 用户明确要求
  - 已有表述明显错误、冲突、不清楚
  - 存在安全或事实风险

### Step 3: 按价值排序做改进

### P0 - 修正根本问题

- 事实不清或错误
- 术语不一致
- 安全漏洞提示

### P1 - 结构优化

- 结构跳跃、逻辑断层
- 标题含糊、不具体
- 段落过长（>4 行）
- 重复表达

### P2 - 内容增强

- 补充前提、边界条件
- 补充常见坑
- 补充验证方法
- 补充必要示例
- 当大段解释适合流程图、时序图、概念图或统计图时，补一个合适的图

### P3 - 精细打磨

- 措辞润色
- 节奏优化
- 排版美化

### Step 4: 保持 Hugo 友好和 diff 友好

- 保持合法 YAML front matter
- **不要擅自修改**：文章编号、文件名、年份目录、稳定 anchor、脚注标签、配套资源命名
- 如果只是改文，不要顺手重排所有章节或统一改写所有句子
- 尽量让 diff 集中于真正有改进的地方

### Step 5: 技术内容要更清楚，而不是更花哨

- 每节先给结论，再解释原因，再给例子
- 明确平台、版本、编译器、时间点、实验条件等前提
- 删除无助于理解的铺垫
- 保留真正能帮助读者落地的例子和权衡

### Step 6: 质量检查（交付前必做）

按 [`AGENTS.md`](../../../AGENTS.md) "交付质量检查清单" 逐项确认。特别注意：

- 核心观点是否与原文一致（除非用户要求修改）
- 新补充的事实是否经过验证或有"待确认"标注
- 内部链接和资源引用是否完整
- front matter 仍然合法
- 图表紧贴首次需要它的段落，有 alt 文本和说明

## Diagram Decisions

是否添加/修改图表的判断标准：

- 难点在"理解关系" → 图；难点在"理解数值变化" → 图表
- 图表紧贴首次需要它的段落，配有引导语或简短说明
- 修改已有图表时，保留原图核心结构，只优化表达
- 图表只是重复正文、没有新增理解价值时，删除它

选型规则和嵌入语法详见 [`AGENTS.md`](../../../AGENTS.md) "图表使用指南" 和 [`references/embedding-syntax.md`](references/embedding-syntax.md)。

## Default Output Format

如果用户只说"帮我润色/完善这篇文章"而未指定形式，**必须**按以下顺序提供：

1. **发现的问题清单**（分类：结构 / 事实 / 术语 / 节奏）
2. **修订策略摘要**（哪些改、哪些不改、为什么）
3. **可直接替换的修订版本**，或在仓库中直接完成改写

### 问题清单格式示例

```markdown
## 发现的问题

### P0 - 需要修正

- [ ] 第 3 段提到的 Go 1.18 特性在 1.17 中不存在，需要标注版本要求
- [ ] "性能提升 50%"缺乏实验环境说明，需要补充或标注待验证

### P1 - 建议优化

- [ ] 第 2 节段落过长（6 行），建议拆成 bullet points
- [ ] "解决方案"标题过于笼统，建议改为"基于 Channel 的并发控制方案"

### P2 - 可以补充

- [ ] 缺少适用场景说明（什么时候用这个方案？）
- [ ] 缺少常见坑点（有什么陷阱？）
- [ ] 建议添加 MPG 调度器示意图

### P3 - 精细打磨

- [ ] 第 5 段"因此"出现 3 次，建议换用词
```

## Error Handling

- **事实错误**：P0 标注 → 确定的直接修正，不确定的标注"待确认"
- **与已有文章冲突**：列出冲突点 → 给出协调建议（引用已有文章、说明差异）
- **信息不足**：不凭猜测修改 → 在问题清单中标注 → 询问用户确认或标注"待确认"

## Example

### 轻量润色：长段落 → 结构化输出

输入：一段冗长、缺乏结构的"解决方案"描述
输出：

1. 问题清单（P1：段落过长、标题笼统）
2. 修订策略（标题改为具体方案名、拆 bullet points、补代码示例、修正术语大小写）
3. 修订后的 Markdown（标题更具体、列表化要点、附代码片段）

## Guardrails

### 禁止行为

- **不要为了"看起来更像 AI 在工作"而过度改写作者原文**
- 不要编造新实验、新引用、新数据去填补逻辑空洞
- 不要改变作者的核心观点（除非用户明确要求）
- 不要擅自修改文件名、id、年份目录、锚点
- 不要删除作者有意保留的内容（即使你觉得冗余）

### 必须遵守

- 如果原文已经有清晰结构，优先做局部增强，而不是推倒重来
- 不确定的信息标注"待确认"
- 保留用户提供的原始素材
- 让 diff 尽可能小，只改真正需要改的地方

## Self-Check Questions

交付前问自己：

1. 我是否保留了作者的核心观点？
2. 有没有新增的"看起来像真的"但实际上未经验证的说法？
3. 修改后的 diff 是否集中在真正有改进的地方？
4. 图表是否真正增加了理解价值（而不是重复正文）？
5. 如果我是作者，会认可这些修改吗？

## Maintenance

**主副本**：`.agents/skills/article-refiner/`（含 `SKILL.md` 和 `references/`）

**同步策略**：

- 本目录是主副本，所有修改在此进行
- `.claude/skills/`、`.kilocode/skills/`、`.roo/skills/` 下的副本通过 `sync-skills.ps1` 同步
- 修改后需检查 compatibility 字段是否仍然准确
