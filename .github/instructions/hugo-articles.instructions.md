---
name: "Hugo article authoring"
description: "Quick reference for writing or revising technical blog posts in this Hugo repository. Full guide in /AGENTS.md."
applyTo: "source/post/**/*.md"
---

# Hugo Article Quick Reference

**完整写作规范**：参见仓库根目录 `AGENTS.md`。

## Key Constraints

- 默认语言：简体中文（除非用户明确要求英文或双语）
- 不要修改已有文章的数字文件名、`id` 或年份目录
- 不要编造 benchmark、Issue 编号、兼容性声明
- 不确定的信息标注 `> **待确认**: ...`
- 编辑已有文章时保持 diff 最小化
- 默认采用自然、圆润、连贯的技术博客文风；避免生硬翻译腔、提纲改写感和明显的 AI 味

## Required Front Matter

```yaml
---
title: 文章标题
date: 2025-03-27T10:00:00+08:00
draft: true
type: post
tags: [golang, performance]
categories: [技术分享]
author: owent
---
```

## Writing Structure

```text
背景/问题 → 现象或约束 → 方案设计 → 关键示例 → 边界条件/坑点 → 总结
```

- 开头 1-3 段：问题、为什么值得读、读完能获得什么、不覆盖什么
- 每节：结论先行 → 原因 → 代码/图表
- 段落之间要有自然承接，像在写完整博文，而不是把提纲机械展开

## Diagrams

仅在降低理解成本时使用。选型速查：

| 工具              | 用途                       |
| ----------------- | -------------------------- |
| `mermaid`         | 流程、时序、状态、ER、甘特 |
| `chart`/`chartjs` | 数值对比、趋势、占比       |
| `excalidraw`      | 概念草图、白板式架构       |
| `drawio`          | 正式的架构/部署图          |

资源命名：`<文章编号>-<描述>.<ext>`（如 `2601-flow.mermaid`）

- 若使用 inline Mermaid（围栏代码块），必须逐行仔细核对并验证语法正确，确认可正确渲染后再交付
- 若图较长、可复用、包含较多 `<br/>` / 引号 / 注释，可优先拆成外部 `.mermaid` 文件并用图片语法引用
- 若 inline Mermaid 中需要保留 `<...>` 这类 HTML 风格文本，优先用引号包起来，再验证渲染结果

## Skills

| 任务         | Skill           |
| ------------ | --------------- |
| 写新文章     | article-writer  |
| 润色已有文章 | article-refiner |

## Guardrails

- 不编造引用来源、外链、Issue、实验数据
- 不确定时标注"待确认"
- 短段落、bullet list、显式前提
- 编辑时保持 diff 最小
