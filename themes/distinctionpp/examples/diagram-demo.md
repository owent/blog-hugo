---
author: owent
categories:
  - Article
  - Blablabla
date: 2025-12-30 10:00:00
draft: true
id: 2509
tags: 
  - test
  - excalidraw
  - mermaid
  - drawio
  - chartjs
title: "Diagram & Chart Rendering Demo - Excalidraw, Mermaid, Draw.io, Chart.js"
description: "This is a comprehensive demo file showing all supported diagram and chart rendering methods in the distinctionpp theme."
---

# Diagram & Chart Rendering Demo

This page demonstrates all supported methods for rendering diagrams and charts:
- **Draw.io** - `.drawio` files
- **Mermaid** - `.mermaid` files
- **Excalidraw** - `.excalidraw` files  
- **Chart.js** - `.chart.json` files

Each format supports 4 usage methods:
1. Image syntax: `![](file.ext)`
2. Code block: ` ```language `
3. Shortcode with src: `{{</* type src="file" */>}}`
4. Shortcode inline: `{{</* type */>}}content{{</* /type */>}}`

---

## 1. Draw.io 测试

### 1.1 图片语法引用 .drawio 文件

下面是通过图片语法引用的 draw.io 图表：

![Draw.io 流程图](2509-test-diagram.drawio)

### 1.2 代码块方式（内嵌XML）

```drawio
<mxfile host="app.diagrams.net">
  <diagram name="Page-1" id="codeblock-test">
    <mxGraphModel dx="800" dy="400" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="827" pageHeight="1169">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        <mxCell id="2" value="代码块方式" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontSize=14;fontStyle=1" vertex="1" parent="1">
          <mxGeometry x="40" y="40" width="120" height="50" as="geometry" />
        </mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

### 1.3 Shortcode 引用外部文件

{{< drawio src="2509-test-diagram.drawio" >}}{{< /drawio >}}

### 1.4 Shortcode 内联方式

{{< drawio >}}
<mxfile host="app.diagrams.net">
  <diagram name="Page-1" id="shortcode-inline-test">
    <mxGraphModel dx="800" dy="400" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="827" pageHeight="1169">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        <mxCell id="2" value="Shortcode 内联" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;fontSize=14;fontStyle=1" vertex="1" parent="1">
          <mxGeometry x="40" y="40" width="120" height="50" as="geometry" />
        </mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
{{< /drawio >}}

---

## 2. Mermaid 图片语法测试

### 2.1 图片语法引用 .mermaid 文件

下面是通过图片语法引用的 mermaid 图表：

![流程图](2509-test-diagram.mermaid)

### 2.2 代码块方式

```mermaid
graph LR
    A[代码块方式] --> B{工作正常?}
    B -->|是| C[蓝色流程图]
    B -->|否| D[检查代码]
```

### 2.3 Shortcode 引用外部文件

{{< mermaid src="2509-test-diagram.mermaid" >}}{{< /mermaid >}}

### 2.4 Shortcode 内联方式

{{< mermaid >}}
graph TD
    A[Shortcode 内联] --> B[Mermaid 图表]
    B --> C{正常显示?}
    C -->|是| D[成功]
    C -->|否| E[检查]
{{< /mermaid >}}

---

## 3. Excalidraw 图片语法测试

### 3.1 图片语法引用 .excalidraw 文件

下面是通过图片语法引用的 excalidraw 图表：

![测试图表](2509-test-diagram.excalidraw)

### 3.2 Shortcode 引用外部文件

{{< excalidraw src="2509-test-diagram.excalidraw" >}}{{< /excalidraw >}}

### 3.3 Shortcode 内联方式

{{< excalidraw >}}
{
  "type": "excalidraw",
  "version": 2,
  "source": "https://excalidraw.com",
  "elements": [
    {
      "id": "shortcode-inline-rect",
      "type": "rectangle",
      "x": 100,
      "y": 100,
      "width": 180,
      "height": 80,
      "angle": 0,
      "strokeColor": "#2f9e44",
      "backgroundColor": "#b2f2bb",
      "fillStyle": "solid",
      "strokeWidth": 2,
      "roughness": 1,
      "opacity": 100,
      "seed": 11111,
      "version": 1,
      "versionNonce": 1
    },
    {
      "id": "shortcode-inline-text",
      "type": "text",
      "x": 115,
      "y": 125,
      "width": 150,
      "height": 30,
      "angle": 0,
      "strokeColor": "#1e1e1e",
      "backgroundColor": "transparent",
      "fillStyle": "solid",
      "strokeWidth": 1,
      "roughness": 1,
      "opacity": 100,
      "seed": 22222,
      "version": 1,
      "versionNonce": 1,
      "text": "Shortcode 内联",
      "fontSize": 18,
      "fontFamily": 1,
      "textAlign": "center",
      "verticalAlign": "middle"
    }
  ],
  "appState": {
    "viewBackgroundColor": "#ffffff"
  }
}
{{< /excalidraw >}}

### 3.4 代码块方式

```excalidraw
{
  "type": "excalidraw",
  "version": 2,
  "source": "https://excalidraw.com",
  "elements": [
    {
      "id": "codeblock-rect",
      "type": "rectangle",
      "x": 100,
      "y": 100,
      "width": 200,
      "height": 100,
      "angle": 0,
      "strokeColor": "#1971c2",
      "backgroundColor": "#a5d8ff",
      "fillStyle": "solid",
      "strokeWidth": 2,
      "roughness": 1,
      "opacity": 100,
      "seed": 54321,
      "version": 1,
      "versionNonce": 1
    },
    {
      "id": "codeblock-text",
      "type": "text",
      "x": 130,
      "y": 135,
      "width": 140,
      "height": 30,
      "angle": 0,
      "strokeColor": "#1e1e1e",
      "backgroundColor": "transparent",
      "fillStyle": "solid",
      "strokeWidth": 1,
      "roughness": 1,
      "opacity": 100,
      "seed": 65432,
      "version": 1,
      "versionNonce": 1,
      "text": "代码块方式",
      "fontSize": 20,
      "fontFamily": 1,
      "textAlign": "center",
      "verticalAlign": "middle"
    }
  ],
  "appState": {
    "viewBackgroundColor": "#ffffff"
  }
}
```

---

## 4. Chart.js 测试

### 4.1 图片语法引用 .chart.json 文件

下面是通过图片语法引用的 Chart.js 图表：

![销售图表](2509-test-chart.chart.json)

### 4.2 Shortcode 引用外部文件

{{< chart src="2509-test-chart.chart.json" >}}{{< /chart >}}

### 4.3 Shortcode 内联方式

{{< chart >}}
{
  "type": "doughnut",
  "data": {
    "labels": ["Red", "Blue", "Yellow"],
    "datasets": [{
      "data": [300, 50, 100],
      "backgroundColor": ["#FF6384", "#36A2EB", "#FFCE56"]
    }]
  },
  "options": {
    "responsive": true,
    "plugins": {
      "title": {
        "display": true,
        "text": "Shortcode 内联图表"
      }
    }
  }
}
{{< /chart >}}

### 4.4 代码块方式

```chart
{
  "type": "line",
  "data": {
    "labels": ["周一", "周二", "周三", "周四", "周五"],
    "datasets": [{
      "label": "访问量",
      "data": [65, 59, 80, 81, 56],
      "fill": false,
      "borderColor": "rgb(75, 192, 192)",
      "tension": 0.1
    }]
  },
  "options": {
    "responsive": true,
    "plugins": {
      "title": {
        "display": true,
        "text": "代码块方式图表 (chart)"
      }
    }
  }
}
```

### 4.5 代码块方式 (chartjs 语法)

```chartjs
{
  "type": "pie",
  "data": {
    "labels": ["Chrome", "Firefox", "Safari", "Edge"],
    "datasets": [{
      "data": [60, 20, 10, 10],
      "backgroundColor": ["#4285F4", "#FF7139", "#00D084", "#0078D7"]
    }]
  },
  "options": {
    "responsive": true,
    "plugins": {
      "title": {
        "display": true,
        "text": "代码块方式图表 (chartjs)"
      }
    }
  }
}
```

---

## 5. 测试结果

| 类型 | 图片语法 | 代码块方式 | Shortcode (内联) | Shortcode (src) |
|------|---------|-----------|-----------------|-----------------|
| Draw.io | ✓ `.drawio` | ✓ `drawio` | ✓ | ✓ |
| Mermaid | ✓ `.mermaid` | ✓ `mermaid` | ✓ | ✓ |
| Excalidraw | ✓ `.excalidraw` | ✓ `excalidraw` | ✓ | ✓ |
| Chart.js | ✓ `.chart.json` | ✓ `chart` / `chartjs` | ✓ | ✓ |

如果所有图表都能正常显示，说明功能正常工作！
