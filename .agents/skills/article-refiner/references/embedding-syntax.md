# Hugo 图表嵌入语法参考

本仓库使用 2 种嵌入方式：代码块内嵌和图片语法引用外部文件。

## 代码块内嵌（推荐用于简短图表）

````markdown
```mermaid
flowchart TD
    A[开始] --> B[处理]
```

```chart
{
  "type": "line",
  "data": { ... }
}
```

```drawio
<mxfile>...</mxfile>
```

```excalidraw
{
  "type": "excalidraw",
  ...
}
```
````

## 图片语法引用外部文件（推荐用于复杂/可复用图表）

```markdown
![流程图](2601-flow.mermaid)
![趋势图](2601-perf.chart.json)
![架构草图](2601-arch.excalidraw)
![部署图](2601-deploy.drawio)
```

## 默认优先级

1. **简短图表** → 代码块（`mermaid`、`chart`/`chartjs`、`drawio`、`excalidraw`）
2. **较长或可复用** → 拆成外部文件，用图片语法引用

> **不要**使用 Shortcode 方式（`{{< type src="..." >}}` 或 `{{< type >}}...{{< /type >}}`）。

## 资源命名规范

新增资源放在同一年目录下，与文章编号同前缀：

```
source/post/2025/
├── 2601.md              # 文章正文
├── 2601-flow.mermaid    # 流程图
├── 2601-arch.excalidraw # 架构图
└── 2601-perf.chart.json # 性能图表
```

## 图表说明要求

- 文件型图表的图片语法要写有意义的 alt 文本
- 正文中用 1-2 句说明"这张图帮读者看什么"

**示例：**

```markdown
![MPG 调度模型](2601-mpg-model.mermaid)
*图 1：MPG 调度模型。M 是操作系统线程，P 是逻辑处理器，G 是待执行任务。*
```
