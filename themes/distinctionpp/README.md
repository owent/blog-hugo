# distinctionpp

Distinctionpp theme for [Hugo][1].

- [Preview](https://owent.net/)

## Installation

### Install

``` bash
$ git clone -b master https://github.com/owt5008137/hugo-theme-distinctionpp.git themes/distinctionpp
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
  githubuser: "owt5008137"
  sitesource: "https://github.com/owt5008137/hugo-theme-distinctionpp"
  favicon: /favicon.ico
  css: ["css/syntax.css"] # additional css file related to baseURL
  ugly: ".html"
  search:
    url: //www.bing.com/search
    keywork: q
    sitename: q1
    siteprefix: "site:"
  bootstrap:
    js: //cdnjs.cloudflare.com/ajax/libs/twitter-bootstrap/4.1.3/js/bootstrap.min.js
    css: //cdnjs.cloudflare.com/ajax/libs/twitter-bootstrap/4.1.3/css/bootstrap.min.css
    popper:
      js: //cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.4/umd/popper.min.js
  highlightjs:
    style: "vs2015"      # style name
    langs: ['capnproto', 'cmake', 'd', 'dos', 'erlang', 'go', 'less', 'lua', 'php', 'powershell', 'protobuf', 'profile', 'typescript', 'vim']
    selector: 'pre>code'
    version: '9.13.1'
    url:                  # 
      js: //cdnjs.cloudflare.com/ajax/libs/highlight.js/%VERSION%/highlight.min.js
      style: //cdnjs.cloudflare.com/ajax/libs/highlight.js/%VERSION%/styles/%STYLE%.min.css
      lang: //cdnjs.cloudflare.com/ajax/libs/highlight.js/%VERSION%/languages/%LANG%.min.js
    options:              # options of highlight.js see http://highlightjs.readthedocs.io/en/latest/api.html#configure-options
      tabReplace: '    '
      useBR: false
      #classPrefix: 'hljs-'
      languages: {}   # language alias
  katex:
    js: //cdnjs.cloudflare.com/ajax/libs/KaTeX/0.10.0/katex.min.js
    css: //cdnjs.cloudflare.com/ajax/libs/KaTeX/0.10.0/katex.min.css
    autorender: //cdnjs.cloudflare.com/ajax/libs/KaTeX/0.10.0/contrib/auto-render.min.js
  mathjax:
    # js: //cdn.bootcss.com/mathjax/2.7.4/MathJax.js?config=TeX-AMS-MML_HTMLorMML
    # js: //cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.4/MathJax.js?config=TeX-AMS-MML_HTMLorMML
  jquery:
    js: //cdnjs.cloudflare.com/ajax/libs/jquery/3.3.1/jquery.slim.min.js
    migrate: //cdnjs.cloudflare.com/ajax/libs/jquery-migrate/3.0.1/jquery-migrate.min.js
  chartjs:
    js: //cdnjs.cloudflare.com/ajax/libs/Chart.js/2.7.2/Chart.min.js
  mermaid:
    js: //cdnjs.cloudflare.com/ajax/libs/mermaid/8.0.0-rc.8/mermaid.min.js
  styleimport:
    delay: 200
    urls: ['https://fonts.googleapis.com/css?family=Noto+Sans+SC:400,700&subset=chinese-simplified,japanese', 'https://fonts.googleapis.com/css?family=Roboto+Mono:400,400i,500,500i&subset=latin-ext', 'https://fonts.googleapis.com/css?family=Roboto:400,400i,500,500i&subset=latin-ext']

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
sassc -t compressed -m static/css/style.scss static/css/style.css
```

[1]: https://gohugo.io/