---
name: "Hugo article authoring"
description: "Write or revise technical blog posts for this Hugo repository."
applyTo: "source/post/**/*.md"
---

# Hugo article authoring

- Keep YAML front matter valid and stable.
- Do not change the numeric filename, `id`, or year directory unless the user explicitly asks.
- Default to simplified Chinese and a pragmatic technical tone.
- Prefer concrete titles over slogan-like titles.
- In the first 1-3 paragraphs, explain the problem, why it matters, what the reader will gain, and what the article does not try to cover.
- A good default flow for this repo is: `背景/问题 -> 现象或约束 -> 方案设计 -> 关键示例 -> 边界条件/坑点 -> 总结`.
- Lead each section with the takeaway, then explain evidence, then show code, data, or diagrams only if they improve understanding.
- Use clear, descriptive headings and short paragraphs; prefer lists or tables over dense blocks when showing steps, comparisons, or decision rules.
- When editing existing posts, preserve the author's main观点, repo-local link labels, and neighboring asset filenames.
- If a process, state transition, call sequence, topology, or data trend would be easier to understand visually, add a diagram or chart near the paragraph it clarifies.
- Choose diagram types deliberately:
  - `mermaid`: flow, sequence, state, class, ER, gantt, quadrant, simple text-first architecture.
  - `chart` / `chartjs`: numeric comparisons, trends, proportions, distributions.
  - `excalidraw`: conceptual or whiteboard-style architecture and mental-model diagrams.
  - `drawio`: precise, denser, or more formal architecture / deployment / network diagrams.
- This repo supports 4 embedding modes for Mermaid, Chart.js, Excalidraw, and Draw.io: image syntax with external files, fenced code blocks, shortcode with `src`, and inline shortcode blocks.
- Use the correct syntax names when embedding:
  - Mermaid: image `*.mermaid`, fenced code block `mermaid`, shortcode `mermaid`
  - Chart.js: image `*.chart.json`, fenced code block `chart` or `chartjs`, shortcode `chart`
  - Excalidraw: image `*.excalidraw`, fenced code block `excalidraw`, shortcode `excalidraw`
  - Draw.io: image `*.drawio`, fenced code block `drawio`, shortcode `drawio`
- Prefer renderable, maintainable defaults:
  - short Mermaid / Chart.js -> fenced code blocks;
  - long or reusable Mermaid / Chart.js -> external `*.mermaid` / `*.chart.json` files;
  - non-trivial Excalidraw / Draw.io -> external `*.excalidraw` / `*.drawio` files, usually referenced with image syntax.
- Shortcode `src` and inline shortcode modes are supported, but do not use them by default unless they are clearly the cleanest option.
- If you add or modify diagrams, keep them renderable and store them beside the article with matching prefixes such as `2604-*.mermaid`, `2604-*.drawio`, `2604-*.excalidraw`, or `2604-*.chart.json`.
- Use meaningful alt text for file-based diagrams and explain the diagram's core idea in surrounding text; do not rely on the visual alone.
- Prefer short paragraphs, useful bullet lists, and explicit assumptions for versions, platforms, and time-sensitive claims.
- Never invent benchmarks, compatibility claims, issue links, release versions, or quotations.
- If source material is incomplete, mark uncertain statements explicitly and say what still needs verification.
