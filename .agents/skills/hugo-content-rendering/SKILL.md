---
name: hugo-content-rendering
description: 解释、诊断或修改 DistinctionPP 对文章内容的渲染，例如图片写法生成了代码、图表没有绘制、codeblock 片段不对或 banner 出现在错误页面。新写或润色文章由相应文章 Skill 处理。
---

# 文章内容渲染

- 解释功能或语法时，查[共享参考](../../../docs/hugo-content.md)的对应小节，并用原文、同目录资源或 2602 的实际调用核对。先区分作者要执行嵌入还是要在教程里展示语法。
- 排障时，从出问题的文章和页面入手。对图片查完整后缀和标题属性，对围栏查语言名，对 shortcode 查名称、命名参数和内部内容。沿对应的 [render hook](../../../themes/distinctionpp/layouts/_default/_markup) 或 [shortcode](../../../themes/distinctionpp/layouts/shortcodes) 找到实际处理参数的模板。
- 根据生成物缩小范围。代码片段核对源文件和起止行，横幅分别检查卡片和单篇输出，构建时 SVG 检查源文件与适配器，浏览器图表检查页面中的配置、资源请求和渲染结果。
- 修改主题扩展时，用原问题的调用方式复验。只有共用模板或加载器受影响时，才扩大到其他入口。支持范围发生变化时，同步[共享参考](../../../docs/hugo-content.md)及对应的主题用法说明。
