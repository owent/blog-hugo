# distinctionpp

Distinctionpp theme for [Hugo][1].

- [Preview](https://owent.net/)

## Installation

### Install

``` bash
git clone -b master https://github.com/owent/hugo-theme-distinctionpp.git themes/distinctionpp
```

**Distinctionpp requires Hugo 1.5 and above.**

### Enable

Modify `theme` setting in `config.yaml` to `distinctionpp`.

### Update

``` bash
cd themes/distinctionpp
git pull
```

## Configuration

```yml

params:
  description: "Chanllege Everything"
  author: "OWenT"
  githubuser: "owent"
  sitesource: "https://github.com/owent/hugo-theme-distinctionpp"
  favicon: /favicon.ico
  css: ["css/syntax.css"] # additional css file related to baseURL
  ugly: ".html"
  search:
    url: //www.bing.com/search
    keywork: q
    sitename: q1
    siteprefix: "site:"
  bootstrap:
    js: //unpkg.com/bootstrap@latest/dist/js/bootstrap.min.js
    css: //unpkg.com/bootstrap@latest/dist/css/bootstrap.min.css
    popper:
      js: //unpkg.com/@popperjs/core@latest/dist/umd/popper.min.js
  highlightjs:
    style: "vs2015"      # style name
    langs: ['capnproto', 'cmake', 'd', 'dos', 'erlang', 'go', 'less', 'lua', 'php', 'powershell', 'protobuf', 'profile', 'typescript', 'vim']
    selector: 'pre>code'
    version: 'latest'
    url:
      js: //unpkg.com/@highlightjs/cdn-assets@%VERSION%/highlight.min.js
      style: //unpkg.com/@highlightjs/cdn-assets@%VERSION%/styles/%STYLE%.min.css
      lang: //unpkg.com/@highlightjs/cdn-assets@%VERSION%/languages/%LANG%.min.js
    options:              # options of highlight.js see http://highlightjs.readthedocs.io/en/latest/api.html#configure-options
      tabReplace: '    '
      useBR: false
      #classPrefix: 'hljs-'
      languages: {}   # language alias
  katex:
    js: //unpkg.com/katex@latest/dist/katex.min.js
    css: //unpkg.com/katex@latest/dist/katex.min.css
    autorender: //unpkg.com/katex@latest/dist/contrib/auto-render.min.js
  # mathjax:
  #   js: //cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js
  #   js: //unpkg.com/mathjax@3/es5/tex-mml-chtml.js
  jquery:
    js: //unpkg.com/jquery@latest/dist/jquery.slim.min.js
    migrate: //unpkg.com/jquery-migrate@latest/dist/jquery-migrate.min.js
  chartjs:
    js: //unpkg.com/chart.js@latest/dist/chart.min.js
  mermaid:
    js: //unpkg.com/mermaid@latest/dist/mermaid.min.js
  styleimport:
    delay: 200
    urls: ['https://fonts.googleapis.com/css?family=Noto+Sans+SC:400,700&subset=chinese-simplified,japanese', 'https://fonts.googleapis.com/css?family=Roboto+Mono:400,400i,500,500i&subset=latin-ext', 'https://fonts.googleapis.com/css?family=Roboto:400,400i,500,500i&subset=latin-ext']
  utteranc:
    repo: "owent/blog-website"
    issue_term: "pathname"
    theme: "github-dark"

menu:
  main:
    - Name: "Home"
      Weight: 1
      Identifier: "home"
      URL: "/"
    - Name: "Archives"
      Weight: 2
      Identifier: "archives"
      URL: "/archives.html"
    - Name: "About"
      Weight: 3
      Identifier: "about"
      URL: "/about.html"

author:
    name: "OWenT"
    email: "admin@owent.net"

taxonomies:
  tag: "tags"
  category: "categories"

DisqusShortname: owent
googleAnalytics: "UA-19298704-1"
```

All of them are enabled by default. You can edit them in `widget` setting.

## shortcodes

### chart

See http://www.chartjs.org for more detail

```
{{< chart id="ID" style="css styles canvas" class="class of canvas" alt="text before rended" >}}
// json options of [chartjs](http://www.chartjs.org), for example
{
  "type": "bar",
  "data": {
  "labels": [ "A", "B", "C" ],
  "datasets": [
    {
    "label": "bar chart",
    "data": [ 1, 2, 3 ],
    "backgroundColor": [
      "rgba(255, 99, 132, 0.2)",
      "rgba(54, 162, 235, 0.2)",
      "rgba(255, 206, 86, 0.2)"
    ],
    "borderColor": [
      "rgba(255,99,132,1)",
      "rgba(54, 162, 235, 1)",
      "rgba(255, 206, 86, 1)"
    ],
    "borderWidth": 1
    }
  ]
  },
  "options": {}
}
{{< /chart >}}
```

### diagram - mermaid

See https://mermaidjs.github.io/

```
{{< mermaid id="ID" style="css styles for div" class="class of div" options="" >}}
sequenceDiagram
Alice ->> Bob: Hello Bob, how are you?
Bob-->>John: How about you John?
Bob--x Alice: I am good thanks!
Bob-x John: I am good thanks!
Note right of John: Bob thinks a long<br/>long time, so long<br/>that the text does<br/>not fit on a row.
Bob-->Alice: Checking with John...
alt either this
Alice->>John: Yes
else or this
Alice->>John: No
else or this will happen
Alice->John: Maybe
end
par this happens in parallel
Alice -->> Bob: Parallel message 1
and
Alice -->> John: Parallel message 2
end
{{< /mermaid >}}
```

## Development

Generate css files:

```bash
sassc -t compressed -m auto static/css/style.scss static/css/style.css

sass -s compressed --source-map -c static/css/style.scss static/css/style.css
```

[1]: https://gohugo.io/