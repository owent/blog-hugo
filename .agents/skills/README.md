# Agent Skills 配置说明

## 概述

本目录包含针对 blog-hugo 仓库的 AI Agent Skills 配置，用于指导不同
AI 工具（Claude Code、KiloCode、Roo、OpenCode 等）在撰写和润色技术博客
文章时的行为。

## 文件结构

```text
.agents/skills/
├── README.md                 # 本文件
├── article-writer/
│   └── SKILL.md             # 起草新文章的 Skill
└── article-refiner/
    └── SKILL.md             # 润色已有文章的 Skill
```

## Skill 列表

### article-writer

**用途**：从零创建技术博客文章

**触发条件**：

- 用户说"写篇关于 XXX 的文章"
- 将笔记整理成博客草稿
- 生成标题/摘要/front matter
- 添加图表到文章

**核心能力**：

- 生成 3 个标题候选 + 推荐
- 生成合法 YAML front matter
- 创建结构化正文
- 建议合适的图表

**文件**：[`article-writer/SKILL.md`](article-writer/SKILL.md)

### article-refiner

**用途**：润色、完善已有文章

**触发条件**：

- 用户说"润色这篇文章"
- 修正事实错误
- 优化结构和表达
- 发布前校对

**核心能力**：

- 按优先级分类改进（P0-P3）
- 保留作者核心观点
- 补充边界条件和坑点
- 优化图表

**文件**：[`article-refiner/SKILL.md`](article-refiner/SKILL.md)

## 使用方式

### 对于 AI Agent

各 AI Agent 工具会自动加载对应目录下的 `.md` 文件作为技能提示。文件位置：

| 工具 | Skill 目录 |
|------|-----------|
| Claude Code | `.claude/skills/` |
| KiloCode | `.kilocode/skills/` |
| Roo Code | `.roo/skills/` |
| OpenCode | `.agents/skills/` |
| VS Code Copilot | `.github/instructions/` |

### 对于用户

在与 AI 对话时，可以直接引用 skill：

```text
使用 article-writer 帮我写篇关于 Go 并发模型的文章
```

或让 AI 自动选择：

```text
请帮我完善这篇草稿
```

AI 会根据任务类型自动选择合适的 skill。

## 修改流程

**重要**：本目录（`.agents/skills/`）是所有 Skill 的**主副本**。

### 修改步骤

1. **编辑主副本**：修改 `.agents/skills/` 下的文件
2. **同步到其他目录**：运行同步脚本

```powershell
# 在仓库根目录执行
.\sync-skills.ps1
```

1. **验证同步结果**：脚本会自动检查所有文件的哈希值

### 注意事项

- 不要直接修改 `.claude/skills/`、`.kilocode/skills/`、`.roo/skills/` 下的文件
- 这些目录的文件是通过脚本从 `.agents/skills/` 同步的
- 修改后务必更新 front matter 中的 `version` 和 `last-updated` 字段

## 配置一致性

所有 Agent 目录下的 Skill 文件必须保持完全一致。验证命令：

```powershell
# 验证 article-writer
Get-FileHash .agents\skills\article-writer\SKILL.md,
             .claude\skills\article-writer\SKILL.md,
             .kilocode\skills\article-writer\SKILL.md,
             .roo\skills\article-writer\SKILL.md

# 验证 article-refiner
Get-FileHash .agents\skills\article-refiner\SKILL.md,
             .claude\skills\article-refiner\SKILL.md,
             .kilocode\skills\article-refiner\SKILL.md,
             .roo\skills\article-refiner\SKILL.md
```

## 与其他配置的关系

```text
AGENTS.md (项目主指南)
    ├── 被 .claude/CLAUDE.md 引用
    ├── 被 .github/instructions/hugo-articles.instructions.md 引用
    └── 被各 Skill 引用

.agents/skills/
    ├── article-writer/SKILL.md (引用 AGENTS.md)
    └── article-refiner/SKILL.md (引用 AGENTS.md)

sync-skills.ps1 (同步脚本)
    └── 将 .agents/skills/ 同步到各 Agent 目录
```

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0.0 | 2024 | 初始版本 |
| 1.1.0 | 2025-03-27 | 增加质量检查清单、错误处理指引、明确 Skill 边界、添加使用示例 |

## 维护者

- 主维护：owent
- 修改前请阅读 [AGENTS.md](../../AGENTS.md)
