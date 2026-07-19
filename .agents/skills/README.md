# blog-hugo Agent Skills

`.agents/skills/` 是仓库 Skill 主副本。全局项目约束和写作基线只放在
[AGENTS.md](../../AGENTS.md)；Skill 只保留任务独有流程。

## Skills

| Skill | 使用场景 | 不适用场景 |
| --- | --- | --- |
| [article-writer](article-writer/SKILL.md) | 新写文章、把笔记整理成新稿、生成新稿的标题和 front matter | 局部修改已有文章 |
| [article-refiner](article-refiner/SKILL.md) | 润色、扩写、校对、事实修复或发布前检查已有文章 | 从零创建新文章 |

快速分流：

- “把这些笔记写成一篇新博客” → `article-writer`
- “润色 `2610.md`，顺便修正事实错误” → `article-refiner`
- “给现有文章补一张图” → `article-refiner`
- “修改主题 SCSS”或“解释 Hugo 配置” → 不触发文章 Skill

## Layout

~~~text
.agents/skills/
├── README.md
├── article-writer/
│   ├── SKILL.md
│   └── references/embedding-syntax.md
└── article-refiner/
    ├── SKILL.md
    └── references/embedding-syntax.md
~~~

`references/embedding-syntax.md` 仅在任务涉及图表嵌入时读取，不默认加载。

## Maintenance

1. 只编辑 `.agents/skills/` 主副本，不直接编辑 `.claude/skills/`。
2. `description` 写清用户意图、适用场景和相邻 Skill 边界；正文只保留任务独有流程、易错点和验收差异。
3. 删除版本历史、维护日期、重复的全局写作规则和 Agent 可从仓库直接推断的内容。
4. 使用可用的 Agent Skills 校验器检查目录名、`name`、`description` 和 YAML。
5. 在仓库根目录运行 `sync-skills.ps1`，再检查哈希和 `git diff --check`。

外部规范与调研依据见 [docs/ai/source-index.md](../../docs/ai/source-index.md)。
