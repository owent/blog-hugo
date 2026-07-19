---
name: article-writer
description: Use this skill when drafting a new technical blog post in this Hugo repository, including requests to 写文章、起草博客、把笔记或调研整理成新稿, or create a new post's title, summary, front matter, structure, examples, and visuals. Do not use for localized edits, polishing, or factual repairs to an existing article; use article-refiner instead.
---

# Article Writer

## Outcome

产出一篇有事实依据、保留作者判断、符合仓库约定的新 Hugo 技术文章；材料不足时，产出可执行的大纲和信息缺口，不补写虚构内容。

## Workflow

1. 读取 `../../../AGENTS.md`，确认主题、读者、核心判断、已有材料、适用边界和交付位置。
2. 搜索同主题文章；需要校准语气时只抽样 2 至 3 篇相关旧文，避免重复背景或模仿固定口头禅。
3. 将事实、作者判断、待验证信息分开。易变结论使用当前一手来源；无法验证的关键内容标注缺口。
4. 根据材料建立章节，不强制套用固定模板。优先保留实测数据、代码、失败记录和取舍理由。
5. 写完内容后再判断是否需要图。需要嵌入细节时读取
   `references/embedding-syntax.md`，并按 `AGENTS.md` 选择图表类型。
6. 做事实复核和风格复核：检查模板化段落、重复总结、均匀小节、长免责声明，以及被写成中性报告的作者判断。
7. 按 `AGENTS.md` 运行 Hugo、Markdown、图表和 diff 验证；修复后再交付。

## Deliverable

- 用户指定目标文件时，直接写入该文件并保留编号和资源命名约束。
- 用户只要求草稿且未指定文件时，默认给出 3 个短标题候选、推荐标题、摘要、front matter 和正文。
- 只有图表能明显降低理解成本时，才附图表或资源建议。

## Guardrails

- 不编造作者经历、实验、数据、引用或观点，也不通过故意错字制造“人味”。
- 不把新文章写成新闻稿、产品说明、论文摘要或每节节奏相同的提纲扩写。
- 不代替用户做技术选型；给出依据、权衡和待确认项。
