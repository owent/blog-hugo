---
name: "Hugo article authoring"
description: "Path-scoped entry point for Hugo posts; the canonical rules are in /AGENTS.md."
applyTo: "source/post/**/*.md"
---

# Hugo 文章入口

完整规则以仓库根目录 `AGENTS.md` 为准。

- 新写文章使用 `article-writer`；修改已有文章使用 `article-refiner`。
- 不改已有文章的数字文件名、年份目录、`id` 或稳定锚点。
- 保留 front matter、引用、脚注、资源名、作者立场和支撑结论的数据。
- 不编造 benchmark、Issue、兼容性声明、引用或用户经历；易变事实先查当前一手来源。
- 所有围栏代码块标注语言。修改图表时验证渲染，修改文章后验证 Hugo 构建。
- 处理“AI 味”时检查全文重复结构和模板化表达，不做词语黑名单替换，不伪造错字或经历。
