# blog-hugo Agent Skills

[仓库指南](../../AGENTS.md)管理全局规则。[博客功能与内容语法](../../docs/hugo-content.md)维护当前主题的入口、真实示例和验证方法，文章与主题任务都可按需查阅。

| 任务举例 | 使用入口 |
| --- | --- |
| 把实验笔记写成新文章，引用现有脚本 | [article-writer](article-writer/SKILL.md) |
| 润色已有文章，保留折叠目录、公式和外部代码片段 | [article-refiner](article-refiner/SKILL.md) |
| 查明 JSON 为什么显示成代码、修复 shortcode 或排查页面图表空白 | [hugo-content-rendering](hugo-content-rendering/SKILL.md) |
| 调整首页配色或修改部署参数 | 按仓库指南查主题 SCSS 或部署脚本 |

修改本目录的 Skill 主副本后，按仓库指南运行规范校验和 `sync-skills.ps1`，并核对 Claude 镜像。
