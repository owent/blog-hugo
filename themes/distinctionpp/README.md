# distinctionpp

Distinctionpp theme for [Hugo][1].

- [Preview](https://owent.net/)

## Installation

### Install

``` bash
git clone https://github.com/owent/hugo-theme-distinctionpp.git themes/distinctionpp
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
    css: //unpkg.com/bootstrap@latest/dist/css/bootstrap.min.css
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
  chartjs:
    js: //unpkg.com/chart.js@latest/dist/chart.umd.js
  mermaid:
    js: //unpkg.com/mermaid@latest/dist/mermaid.esm.min.mjs
    theme: default
  excalidraw:
    js: "https://esm.sh/@excalidraw/excalidraw"
    css: "https://cdn.jsdelivr.net/npm/excalidraw/dist/excalidraw.min.css"
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

services:
  # disqus:
  #   shortname: owent
  googleAnalytics:
    ID: "G-PQEY77BYG1"
```

All of them are enabled by default. You can edit them in `widget` setting.

## Article lists

Home, category and tag lists use a responsive grid with a light background and
white cards. Each card's content panel is 28rem high; titles show up to three lines.
Summaries retain paragraphs, headings, emphasis, links, lists and code formatting.
They are truncated to 480 characters with balanced HTML tags, then limited to
eight lines inside a clipped viewport with a fade at the bottom. This also bounds
summaries defined with `<!--more-->` or front matter. Interactive embeds are shown
only in the full article. Dates appear above the title; up to three tag links and
the read-more link stay aligned at the bottom. Full article styles are unchanged.

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
{{< mermaid id="ID" style="css styles for div" class="class of div" >}}
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

### echarts

See https://echarts.apache.org/ for more detail.

```
{{</* echarts id="ID" width="100%" max-width="720px" height="500px" style="css styles" class="class" extensions="gl" alt="text before rendered" */>}}
{
  "title": { "text": "Line Chart" },
  "xAxis": { "type": "category", "data": ["Mon", "Tue", "Wed"] },
  "yAxis": { "type": "value" },
  "series": [{ "type": "line", "data": [120, 200, 150] }]
}
{{</* /echarts */>}}
```

Use `extensions="gl"` to load the ECharts-GL extension for 3D charts.

### plotly

See https://plotly.com/javascript/ for more detail.

```
{{</* plotly id="ID" width="100%" max-width="720px" height="500px" style="css styles" class="class" extensions="gl3d" alt="text before rendered" */>}}
{
  "data": [{ "type": "scatter", "mode": "lines", "x": [1, 2, 3], "y": [2, 4, 3] }],
  "layout": { "title": "Line Chart" }
}
{{</* /plotly */>}}
```

Use `extensions="gl3d"` (or `cartesian`, `geo`, `gl2d`, `mapbox`, `finance`) to load a Plotly.js partial bundle. Plotly.js partial bundles redefine the global `Plotly` object and cannot be stacked; when a page mixes minimal charts with extended charts, the loader falls back to the full bundle.

## Diagram & Chart Extensions

This theme supports rendering diagrams and charts from various sources:

All diagram and chart renderers accept `width`, `height`, `max-width`, `max-height`, `class`, and `style`. ECharts and Plotly.js also accept `extensions` for optional bundles.

### Supported Formats

| Type | Image Syntax | Code Block | Shortcode (src) | Shortcode (inline) |
|------|-------------|------------|-----------------|-------------------|
| **Draw.io** | `![](file.drawio)` | ` ```drawio ` | `{{</* drawio src="file.drawio" */>}}` | `{{</* drawio */>}}XML{{</* /drawio */>}}` |
| **Mermaid** | `![](file.mermaid)` | ` ```mermaid ` | `{{</* mermaid src="file.mermaid" */>}}` | `{{</* mermaid */>}}code{{</* /mermaid */>}}` |
| **Excalidraw** | `![](file.excalidraw)` | ` ```excalidraw ` | `{{</* excalidraw src="file.excalidraw" */>}}` | `{{</* excalidraw */>}}JSON{{</* /excalidraw */>}}` |
| **Chart.js** | `![](file.chart.json)` | ` ```chart ` or ` ```chartjs ` | `{{</* chart src="file.chart.json" */>}}` | `{{</* chart */>}}JSON{{</* /chart */>}}` |
| **ECharts** | `![](file.echarts.json)` | ` ```echarts ` | `{{</* echarts src="file.echarts.json" */>}}` | `{{</* echarts */>}}JSON{{</* /echarts */>}}` |
| **Plotly.js** | `![](file.plotly.json)` | ` ```plotly ` | `{{</* plotly src="file.plotly.json" */>}}` | `{{</* plotly */>}}JSON{{</* /plotly */>}}` |
| **D2** | `![](file.d2)` | ` ```d2 ` | `{{</* d2 src="file.d2" */>}}` | `{{</* d2 */>}}code{{</* /d2 */>}}` |

### D2 build integration

D2 diagrams use the native [D2 CLI](https://d2lang.com/tour/install/) at build time. No D2 JavaScript or WASM is loaded by the reader. SVG is embedded inline to preserve links and tooltips. Each occurrence has its own ID salt, including repeated references to the same file. On narrow screens diagrams keep their intrinsic width and scroll horizontally so text remains readable.

In this repository, install Python 3.9+, Hugo, and D2 v0.9.0, then run:

```bash
python scripts/build-d2.py --buildDrafts --renderToMemory
python scripts/test-d2.py -v
```

`HUGO_BINARY` and `D2_BINARY` can point to executables outside PATH. The wrapper runs Hugo with a temporary `params.d2.collect` config overlay to publish diagram requests to a temporary directory, renders every request into ignored `assets/d2-generated/` resources, then runs the requested Hugo build. Stale generated SVGs are removed after a successful render; a failed render keeps the previous outputs untouched. Both passes use the requested Hugo environment. Hugo flags are forwarded to the final build. D2 errors and invalid SVG stop the build before the final Hugo invocation; partial D2 output is discarded. Direct Hugo builds report missing generated SVGs as errors.

Use local `src` paths relative to the article. Relative imports and images are resolved from the external D2 file's directory, or the article's directory for inline content. Set layout, theme, and padding in `vars.d2-config`. The wrapper exports only the root board. Remote icons still require network access during rendering. Re-run the wrapper after changing D2 sources, imports, or images, then use `hugo server` for preview; the wrapper is a one-shot build command.

The templates live in the theme, while `scripts/build-d2.py` is the repository's build adapter. Other sites using the theme must also install this adapter (and use their own deployment entrypoint). D2 accepts the common sizing and style attributes listed above, plus `alt` for code blocks and shortcodes. The image syntax uses its normal alt text.

### Configuration

Add the following to your `config.yaml`:

```yaml
params:
  chartjs:
    js: //unpkg.com/chart.js@latest/dist/chart.umd.js
  mermaid:
    js: //unpkg.com/mermaid@latest/dist/mermaid.esm.min.mjs
    theme: default
  excalidraw:
    js: "https://esm.sh/@excalidraw/excalidraw"
  drawio:
    js: "https://viewer.diagrams.net/js/viewer-static.min.js"
  echarts:
    # Default minimal bundle (all 2D charts, no 3D). Add extensions="gl" on a chart to load echarts-gl.
    js: "https://cdn.jsdelivr.net/npm/echarts/dist/echarts.min.js"
    extensions:
      gl: "https://cdn.jsdelivr.net/npm/echarts-gl/dist/echarts-gl.min.js"
      wordcloud: "https://cdn.jsdelivr.net/npm/echarts-wordcloud/dist/echarts-wordcloud.min.js"
      liquidfill: "https://cdn.jsdelivr.net/npm/echarts-liquidfill/dist/echarts-liquidfill.min.js"
  plotly:
    # Default minimal bundle (scatter/bar/pie). Declare extensions="gl3d" etc. to use a partial bundle.
    js: "https://cdn.jsdelivr.net/npm/plotly.js-basic-dist-min"
    # Full bundle used as fallback when minimal and extended charts are mixed on the same page.
    full: "https://cdn.jsdelivr.net/npm/plotly.js-dist-min"
    bundles:
      cartesian: "https://cdn.jsdelivr.net/npm/plotly.js-cartesian-dist-min"
      geo: "https://cdn.jsdelivr.net/npm/plotly.js-geo-dist-min"
      gl3d: "https://cdn.jsdelivr.net/npm/plotly.js-gl3d-dist-min"
      gl2d: "https://cdn.jsdelivr.net/npm/plotly.js-gl2d-dist-min"
      mapbox: "https://cdn.jsdelivr.net/npm/plotly.js-mapbox-dist-min"
      finance: "https://cdn.jsdelivr.net/npm/plotly.js-finance-dist-min"
```

### Examples

See [examples/diagram-demo.md](examples/diagram-demo.md) for a comprehensive demonstration of all diagram and chart rendering methods.

Example files included:
- `examples/2509-test-diagram.drawio` - Draw.io diagram
- `examples/2509-test-diagram.mermaid` - Mermaid diagram
- `examples/2509-test-diagram.excalidraw` - Excalidraw diagram
- `examples/2509-test-chart.chart.json` - Chart.js configuration
- `examples/2509-test-echarts-sin.echarts.json` - ECharts 2D function chart
- `examples/2509-test-echarts-3d.echarts.json` - ECharts 3D surface chart
- `examples/2509-test-plotly-sin.plotly.json` - Plotly.js 2D function chart
- `examples/2509-test-plotly-3d.plotly.json` - Plotly.js 3D surface chart

## Development

Generate css files:

```bash
sassc -t compressed -m auto static/css/style.scss static/css/style.css

sass -s compressed --source-map -c static/css/style.scss static/css/style.css
```

[1]: https://gohugo.io/
