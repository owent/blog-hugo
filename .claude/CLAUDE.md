# Claude Code bootstrap

> **版本**: 1.2.2  
> **更新日期**: 2026-03-27

## Quick Start

This repository uses [`/AGENTS.md`](../AGENTS.md) as the canonical project guide.
**Read `/AGENTS.md` before drafting or revising any article.**

## Available Skills

| Skill | Purpose | Trigger |
|-------|---------|---------|
| [`article-writer`](skills/article-writer/SKILL.md) | Draft new articles from scratch | "写篇文章", "起草博客" |
| [`article-refiner`](skills/article-refiner/SKILL.md) | Polish existing articles | "润色文章", "完善草稿" |

## Default Guidelines

1. **Language**: Simplified Chinese (unless user explicitly requests English or bilingual)
2. **Tone**: Pragmatic technical, experienced-engineer oriented
3. **Structure**: Problem → Constraints → Solution → Examples → Pitfalls → Summary
4. **Quality**: Always run through the quality checklist before finishing

## Key Constraints

- Do not change numeric filenames, `id`, or year directories
- Never invent benchmarks, issue links, or compatibility claims
- Mark uncertain facts with `> **待确认**: ...`
- Keep diffs minimal when editing
- If Mermaid is embedded inline, carefully review and validate the Mermaid syntax and rendering before finishing; prefer external `.mermaid` files for complex diagrams, and wrap HTML-like text such as `<...>` in quotes when keeping it inline

## Diagram Support

This repo supports embedding for:

- **Mermaid**: flowcharts, sequence diagrams (`*.mermaid`)
- **Chart.js**: data visualization (`*.chart.json`)
- **Excalidraw**: sketches (`*.excalidraw`)
- **Draw.io**: formal diagrams (`*.drawio`)

See [`/AGENTS.md`](../AGENTS.md) for detailed embedding conventions.

When Mermaid is embedded inline, carefully verify the syntax and rendering result before finishing. If inline text includes `<...>`-style placeholders, wrap them in quotes before validation.

## Maintenance

Skills in `.claude/skills/` are **synced from `.agents/skills/`**
(including `references/` subdirectories). Do not edit directly.

To update skills:

1. Edit `.agents/skills/<skill>/SKILL.md` or `references/`
2. Run `sync-skills.ps1` to sync
