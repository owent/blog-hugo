OWenT.Articles
======

All contents are also published on https://owent.net

About Me
------
See [About](source/about/index.md)

Notice
------
Some old articles are written by staticeditor and now in gitbook. Anything that only supported by stackeditor will be unavailable.(Such as \[TOC\] is used to generate a content table before and is unavailabled now). Those symbols are not removed in gitbook and only have a little effect on layout.

```bash
# We use Graphviz to generate graph and use OptiPNG to make png files smaller,
# install
choco install --yes Graphviz OptiPNG
pacman -S mingw-w64-x86_64-graphviz mingw-w64-x86_64-optipng
sudo apt install -y graphviz optipng
sudo yum install -y graphviz optipng

# run
dot -Tpng -O 1807-02.dot 
optipng -o6 1807-02.dot.png
```

{% include "./LICENSE.md" %}

## Plugins for hexo
+ hexo-renderer-dot
+ hexo-generator-feed
+ hexo-generator-i18n
+ hexo-generator-index
+ hexo-generator-search
+ hexo-generator-seo-friendly-sitemap
+ hexo-generator-sitemap
+ hexo-generator-tag
+ hexo-generator-type
+ hexo-pagination
+ hexo-migrator-wordpress
+ hexo-filter-highlight
+ hexo-renderer-markdown-it
+ hexo-math

## Search Engine Support
+ Google
  + https://cse.google.com
  + URL: //google.com/search
  + 搜索词参数: q=搜索内容
  + 站内限制参数: sitesearch=域名
+ Bing 
  + https://blogs.msdn.microsoft.com/zxue/2009/07/31/adding-microsoft-bing-to-your-web-site/
  + URL: //www.bing.com/search
  + 搜索词参数: q=搜索内容
  + 站内限制参数: q1=site:域名
+ DuckDuckGo
  + https://duckduckgo.com/search_box
  + http://patdryburgh.com/blog/adding-a-custom-duckduckgo-search-bar-to-your-site/
  + http://duckduckgo.com/params.html
  + URL: //duckduckgo.com/
  + 搜索词参数: q=搜索内容
  + 站内限制参数: sites=域名
+ Baidu
  + http://zhanzhang.baidu.com/guide/index
  + http://zn.baidu.com/cse/wiki/index?category_id=25
  + URL: //zhannei.baidu.com/cse/site
  + 搜索词参数: query=搜索内容
  + 站内限制参数: cc=域名
+ Sogou
  + http://fuwu.sogou.com/daima/code.html
  + URL: //www.sogou.com/web
  + 搜索词参数: query=搜索内容
  + 站内限制参数: insite=域名

## Plugins for gitbook
+ [toc](https://plugins.gitbook.com/plugin/toc)
+ [mathjax](https://plugins.gitbook.com/plugin/mathjax)

### Tex/Latex and [MathJax][1] and [KaTex][2]

### Online [MathJax][1] Editor
1. https://zohooo.github.io/jaxedit/
2. http://zh.numberempire.com/texequationeditor/equationeditor.php

### Supported LaTeX/Tex commands on [MathJax][1] or [KaTex][2]
1. https://docs.mathjax.org/en/latest/tex.html#supported-latex-commands
2. http://www.onemathematicalcat.org/MathJaxDocumentation/TeXSyntax.htm
3. https://khan.github.io/KaTeX/function-support.html

[1]: https://www.mathjax.org/
[2]: https://github.com/Khan/KaTeX