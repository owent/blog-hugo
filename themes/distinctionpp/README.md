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
    theme: base
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
| **PlantUML** | `![](file.puml)` / `.plantuml` | ` ```plantuml ` | `{{</* plantuml src="file.puml" */>}}` | `{{</* plantuml */>}}code{{</* /plantuml */>}}` |

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

### PlantUML build integration

The same `scripts/build-d2.py` command also renders PlantUML. Install Java 21+, Graphviz and PlantUML 1.2026.8, and set `PLANTUML_JAR` to the downloaded JAR. `JAVA_BINARY` optionally selects Java outside PATH. On Linux install a CJK font (CI uses `fonts-noto-cjk`) for Chinese labels. No PlantUML server or browser runtime is used.

Each diagram requires one `@startuml` / `@enduml` pair. `.puml` and `.plantuml` image references, `plantuml` code fences, and inline/file shortcodes share the D2 sizing and `alt` attributes. Relative `!include` paths use the source file's directory. The ALLOWLIST security profile permits local files within the repository; remote includes are disabled. Both renderers must succeed before generated assets are replaced. Generated PlantUML SVGs live in ignored `assets/plantuml-generated/`; their IDs are prefixed per occurrence. Rebuild after changing included files.

```bash
export PLANTUML_JAR=/path/to/plantuml-1.2026.8.jar
python scripts/build-d2.py --buildDrafts --renderToMemory
python scripts/test-plantuml.py -v
```

CI downloads the official release and checks SHA-256 `5e1ecfa8ecd32c90b03bbf3b1eb6f020943f98ab0fcf4032be31a0002ee2c462`. The default is the bundled high-contrast `plain` theme; use `!theme cerulean-outline` or another bundled theme in the diagram to override it. See [PlantUML themes](https://plantuml.com/theme) and [security profiles](https://plantuml.com/security).

### Diagram appearance

`layouts/partials/diagram-theme.html` holds the browser chart defaults: Mermaid `base` with blue/teal variables, ECharts' native theme object, Plotly's light layout template, and Chart.js font/text/grid defaults. Native per-diagram options retain priority. No additional theme package is fetched. Excalidraw and Draw.io preserve the source file's colors. D2 examples use `Cool Classics` (`theme-id: 4`) in their source; other D2 files retain their selected themes.

D2 `style.animated: true` and `style.stroke-dash: 3` produce moving dashed edges in the generated SVG. CSS disables these animations for `prefers-reduced-motion: reduce`. Theme comparisons, official references and all four PlantUML examples are in [2602.md](../../source/post/2026/2602.md).

### Layout and advertising

The palette follows the existing navy header (`#172437`), navigation (`#111c2c`) and cyan footer links (`#a9ced7`). The slate background uses a subtle diagonal texture and a bounded radial gradient, both in CSS. Surface, link, focus and quote colors are centralized in `static/css/_variables.scss`. Panels and cards use 8px corners; the table of contents and quotations use 6px; tags, pagination and card action links use 4px. Cards and reading panels use neutral off-white (`#ededed`), with slightly darker gray (`#e3e3e3`) for card footers and the table of contents. Against the solid reading background, body text (`#263548`) has about 10.6:1 contrast and summary text (`#526174`) about 5.4:1. The off-white surface has lower luminance than pure white; these contrast calculations follow [W3C's luminance and contrast guidance](https://www.w3.org/WAI/tips/designing/#provide-sufficient-contrast-between-foreground-and-background).

Inline links use saturated blue (`#0755b5`, about 6:1 against the solid reading background), persistent underlines, thicker underlines on hover, slate blue visited links and a blue outline with a light cyan keyboard focus background. Underlines follow [W3C's guidance on cues beyond color](https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html) and the [GOV.UK link pattern](https://design-system.service.gov.uk/styles/links/). Card headings use a neutral gray surface (`#e9e9e9`), dark titles and metadata (`#43566a`), with a thin divider below the heading area. Article title bands use a separate neutral gray surface (`#e7e7e7`). Content and heading backgrounds, grain and highlights have equal RGB channels, keeping blue accents concentrated in text, links and navigation. Quotations have a separate, flat gray background (`#dedede`) and a slightly darker inline-code background (`#d3d3d3`). They retain blue-gray text (`#35495c`, about 6.9:1), a 3px blue-gray left border and normal article link states, without a surrounding frame. Card tags and summary code backgrounds also use neutral grays. The separation of surfaces and restrained accents follows [Carbon's color layering guidance](https://www.carbondesignsystem.com/building-blocks/foundations/color/overview).

Reading panels and title surfaces use static [CSS background layers](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/background-image) rather than additional elements or image assets. Card headings combine fine matte grain with a broad light-to-shadow transition, without stripes. Article title bands add finer, lower-contrast grain over a diffuse top highlight and a faint vertical shade; the main prose retains its quiet dot texture. Heading and reading grain use neutral graphite, with the existing dot sizes, spacing and opacity preserved. Texture lists, repeat sizes and grain colors live in `static/css/_variables.scss`. The article title band extends to the panel edges while its text keeps the body's inset and existing distance from navigation. No texture covers text, links, diagrams or advertisements. Forced-colors mode disables the gradients. Contrast checks account for the darkest and lightest texture colors, rather than checking only the solid fallback color.

The homepage starts directly with cards, 16px below navigation on small screens and 20px on desktop. RSS has a single navigation entry; there is no separate list heading. Every card uses the same heading surface and one uniform 1px outer border, without a top accent stripe or shadow. The inner clipping radius is 1px smaller than the outer radius so the two curves align. Hover and keyboard focus change the border color without adding another outline around the card. Cards retain the same height and grid width. No hero block, carousel or extra JavaScript is added. Advertising containers inserted directly into the article layout clear the directory and use the full width. In-body ad containers use their own block formatting context to fit beside the directory, then use the full width below it.

Homepage and taxonomy lists use the available viewport width, with 32px gutters on desktop and additional card columns as space allows. At the default font size, 1920/2560/3840px viewports fit 4/6/9 columns. The Archives overview and reading panels also use the available width. Reading panels start 12px below navigation on small screens and 16px at 768px and wider; their top inner padding is 16–24px, with no extra panel top margin. On reading pages at 1200px and wider, the expanded table of contents uses a [right float](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/float), with an 18rem minimum and a 32% cap relative to the inner article layout. The percentage cap takes priority over the minimum when space is limited. Longer headings wrap at the cap. All desktop directory entries remain in normal document scrolling, without a height limit or sticky positioning. Prose wraps around the directory's height with a 2rem horizontal gap, then resumes the full width below it. Collapsing the native `details` leaves a compact summary button floating on the right on all screen sizes, with a 1rem horizontal gap. Text wraps only alongside the button and resumes the full width below it. A `flow-root` article layout contains the float; quotes and in-body ads establish their own block formatting contexts so their backgrounds do not overlap the directory. The directory collapses by default on smaller screens, where its open list remains limited to 60vh with a thin scrollbar and a [stable scrollbar gutter](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/scrollbar-gutter). Wide code, tables, math and offline SVG diagrams scroll within their own containers. The footer keeps the license badge (or its alt text when unavailable), year and author on one line; other footer links wrap as groups.

### Registration by hostname

Use `params.beian` instead of placing registration HTML in `params.content.footer.right`:

```yaml
params:
  beian:
    text: "沪ICP备2022003252号"
    url: "https://beian.miit.gov.cn/"
    domains: []
    domain_suffixes: [localhost, x-ha.com, r-ci.com]
```

`domains` matches exact hostnames only. `domain_suffixes` matches each listed hostname and its subdomains: `x-ha.com` and `blog.x-ha.com` match, while `badx-ha.com` and `x-ha.com.example.org` do not. Use bare hostnames without protocols, ports, paths or wildcards. Matching ignores case and a trailing DNS dot. `localhost` does not match `127.0.0.1` or `::1`; list those under `domains` separately if needed (use `[::1]` for the IPv6 hostname).

`static/js/site-registration.js` uses the browser's [`location.hostname`](https://developer.mozilla.org/en-US/docs/Web/API/Location/hostname), independent of Hugo's `baseURL`, so a single build works on several domains. Registration starts hidden and stays hidden for unmatched hosts, invalid configuration or disabled JavaScript. Omit `beian.text` to omit the element and script altogether.

### Advertising

Manual advertising is bounded by the templates: one unit after an article/page, and `params.ads.archive.feed` after cards 6 and 12 (at most two per list page). Old ad position keys are accepted as fallbacks, in the order in `partials/ads/slot.html`; only the first configured unit is used. Navigation advertising is independent (`params.ads.menu`, disabled in this repository). `noad: true` suppresses manual units and the AdSense loader. Keep one responsive unit per configuration value, with `data-full-width-responsive="false"` when its width must follow the content column.

Ad wrappers keep their natural height. Only units explicitly marked `unfilled` are collapsed; filled creatives are neither cropped nor inspected. [Google's responsive ad guidance](https://support.google.com/adsense/answer/9183363?hl=en) governs custom unit sizes.

Auto ads count, spacing, overlays and excluded areas are controlled in the [AdSense console](https://support.google.com/adsense/answer/9261307?hl=en-GB). When enabled, exclude `.archive-article`, `.toc`, navigation and diagram containers; reduce in-page ad load and disable formats that obstruct reading. These settings cannot be confirmed or applied from this repository. The grid accepts an inserted full-row ad, but cannot guarantee arbitrary server-selected placement inside cards. The browser tests use simulated creatives; they do not validate live inventory or account settings.

### Browser checks

Install Playwright and the chart libraries in a separate local directory (or make them available with `NODE_PATH`). Build with `--destination _agent_tmp/after-design`. The scripts default to `_agent_tmp/browser/node_modules` and a local copy of Bootstrap CSS at `_agent_tmp/browser/bootstrap.css`; `BLOG_TEST_SITE`, `BLOG_TEST_MODULES` and `BOOTSTRAP_CSS` can override the relevant paths.

```bash
npm install --prefix _agent_tmp/browser --no-save playwright mermaid echarts echarts-gl chart.js plotly.js-dist-min
npx --prefix _agent_tmp/browser playwright install chromium firefox webkit
curl -fL https://cdn.jsdelivr.net/npm/bootstrap/dist/css/bootstrap.min.css -o _agent_tmp/browser/bootstrap.css
NODE_PATH="$PWD/_agent_tmp/browser/node_modules" node scripts/test-layout.cjs
NODE_PATH="$PWD/_agent_tmp/browser/node_modules" node scripts/test-registration.cjs
NODE_PATH="$PWD/_agent_tmp/browser/node_modules" node scripts/test-diagram-themes.cjs
```

Layout tests use Chromium, Firefox and WebKit at 15 viewport sizes across 320–3840px, including a landscape phone viewport. They check homepage/Archives/tag list/article/About (225 browser/page/viewport combinations), wide-screen cards, footer alignment, responsive ad insertion, card overlap, unfilled units, D2 animation and reduced motion. Another 120 directory fixtures cover short, long and unbroken headings, the width cap, desktop font enlargement, text wrapping beside the directory, full-width text after it ends or collapses, normal page scrolling and directly inserted advertisements. Registration tests route the built HTML to different browser origins and check allowed hosts, rejected lookalikes, exact-only entries, invalid configuration, disabled JavaScript and narrow footer layout with registration visible. The chart test uses actual npm libraries and the generated page's initialization scripts; external advertising requests are blocked in these tests. Screenshots and measurements are written under `_agent_tmp/layout-results/` (`BLOG_TEST_OUTPUT` can override the layout output directory). These are desktop browser viewport tests, not physical-device or live-ad acceptance tests.

### Configuration

Add the following to your `config.yaml`:

```yaml
params:
  chartjs:
    js: //unpkg.com/chart.js@latest/dist/chart.umd.js
  mermaid:
    js: //unpkg.com/mermaid@latest/dist/mermaid.esm.min.mjs
    theme: base
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
