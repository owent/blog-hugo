---
name: article-refiner
description: Use this skill when reviewing or changing an existing Hugo technical post, including requests to 润色、完善、扩写、改写、校对、事实核查 or prepare it for publication by fixing structure, examples, front matter, links, or visuals. Do not use when the intended result is a new article created from scratch; use article-writer instead.
---

# Article Refiner

## Outcome

在不改写作者核心立场的前提下，修正已有文章的事实、结构、术语、示例和表达，并完成与改动范围相称的发布验证。

## Workflow

1. 读取 `../../../AGENTS.md` 和目标文章全文，包括 front matter、引用、脚注及关联资源。
2. 先列出真正需要处理的问题，按事实与术语、论证与结构、前提与验证、措辞与节奏排序。
3. 对易变或可疑结论查当前一手来源。区分事实错误、作者判断和仍需确认的信息，不用更圆滑的措辞掩盖不确定性。
4. 保持 diff 克制：保留作者观点、第一人称、关键数据、资源名和章节职责；只处理影响可信度、理解或语气的问题。
5. 用户指出“AI 味”时，先扫描全文同类模式，再调整段落和章节节奏。不要把某些词当作禁词，也不要机械注入口语、短句或句长变化。
6. 图表需要新增或修复时读取 `references/embedding-syntax.md`；只保留确实帮助理解的图，并验证实际渲染。
7. 完成事实复核和风格复核，再按 `AGENTS.md` 运行 Hugo、Markdown、图表和 diff 验证。

## Deliverable

- 用户要求修改仓库中的文章时，直接完成文件修改；最终说明重要修复、保留边界和验证结果。
- 用户只要求审阅时，按严重程度报告可定位的问题，不把个人风格偏好冒充事实错误。

## Guardrails

- 不改文件名、年份目录、`id`、稳定锚点或作者核心立场，除非用户明确要求。
- 不删除支撑结论的原始数据，不补写虚构经历、引语、实验或引用。
- 不为“更完整”重写整篇，不把有判断、有情绪的工程复盘磨成均匀的中性说明。
