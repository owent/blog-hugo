// Install playwright and katex locally, or set NODE_PATH to their node_modules directory.
// Builds into _agent_tmp; all browser resources are local and external requests are blocked.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {spawnSync} = require('node:child_process');
const {chromium} = require('playwright');

const root = path.resolve(__dirname, '..');
fs.mkdirSync(path.join(root, '_agent_tmp'), {recursive: true});
const output = fs.mkdtempSync(path.join(root, '_agent_tmp/math-test-'));
const site = path.join(output, 'site');
const fixture = path.join(output, 'fixture');
const katexDist = path.dirname(require.resolve('katex'));
const normalize = text => text.replace(/\r\n/g, '\n').trim();
const article = fs.readFileSync(path.join(root, 'source/post/2026/2612.md'), 'utf8');
const formulas = [...article.matchAll(/^> ```math\r?\n([\s\S]*?)^> ```\r?$/gm)]
  .map(match => normalize(match[1].replace(/^> ?/gm, '')));
assert.equal(formulas.length, 6, '2612 must retain its six quoted display formulas');

function build(args) {
  const result = spawnSync('hugo', args, {cwd: root, encoding: 'utf8'});
  if (result.error) throw result.error;
  assert.equal(result.status, 0, result.stdout + result.stderr);
}
function write(relative, text) {
  const filename = path.join(fixture, relative);
  fs.mkdirSync(path.dirname(filename), {recursive: true});
  fs.writeFileSync(filename, text);
}
build(['--buildDrafts', '--baseURL', 'https://math.test/', '--destination', site]);
const articleHtml = fs.readFileSync(path.join(site, '2026/2612.html'), 'utf8');
// Exercise the actual generated KaTeX setup, including delimiters and ignored tags.
const mathScripts = articleHtml.match(/<script\b[^>]*>[\s\S]*?<\/script>/g)
  .filter(script => /katex\/dist\/|renderMathInElement/.test(script)).join('\n');
assert.ok(mathScripts.includes('renderMathInElement'), 'generated KaTeX setup is missing');
// Keep the article layout and math scripts; unrelated CDN scripts are outside this test.
const articleMathHtml = articleHtml.replace(/<script\b[^>]*>[\s\S]*?<\/script>/g,
  script => /katex\/dist\/|renderMathInElement/.test(script) ? script : '');
const fence = (prefix, tex) => [prefix + '```math', ...tex.split('\n').map(line => prefix + line), prefix + '```'].join('\n');
const cases = [
  {prefix: '', tex: String.raw`x<y,\quad i>j`},
  {prefix: '> ', tex: String.raw`\begin{aligned}
x&=y\\
&>0
\end{aligned}`},
  {prefix: '> > ', tex: String.raw`\begin{pmatrix}
0&0\\
a&0
\end{pmatrix}`},
  // A leading > is a real TeX comparison, even inside a quote nested in a list.
  {prefix: '  > ', tex: '>0', before: '- list item\n\n'},
  {prefix: '> ', tex: String.raw`\text{<span>}\quad a<b\quad c>d`},
];
const content = cases.map(item => (item.before || '') + fence(item.prefix, item.tex)).join('\n\n');
const literal = '> $$\nx>y\n$$';
write('hugo.json', JSON.stringify({
  baseURL: 'https://math.test/', uglyURLs: true,
  markup: {goldmark: {extensions: {passthrough: {
    enable: true, delimiters: {block: [['$$', '$$'], ['\\[', '\\]']], inline: [['$', '$'], ['\\(', '\\)']]},
  }}}},
}));
write('content/probe.md', '---\ntitle: Math regression\ndate: 2020-01-01\n---\n\n' + content +
  '\n\nInline $a>b$ and $a < b$.\n\n$$x>y$$\n\n```text\n' + literal + '\n```\n');
write('layouts/_default/single.html', '<!doctype html><html><head><meta charset="utf-8"></head><body>{{ .Content }}' + mathScripts + '</body></html>');
write('layouts/_default/_markup/render-codeblock-math.html', fs.readFileSync(path.join(root, 'themes/distinctionpp/layouts/_default/_markup/render-codeblock-math.html'), 'utf8'));
build(['--source', fixture]);

(async () => {
  const browser = await chromium.launch({headless: true});
  try {
    const page = await browser.newPage({viewport: {width: 1440, height: 1000}});
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.route('**/*', route => {
      const url = new URL(route.request().url());
      if (url.hostname === 'math.test' && url.pathname === '/2026/2612.html') {
        return route.fulfill({body: articleMathHtml, contentType: 'text/html'});
      }
      let file;
      const katexPath = url.pathname.match(/\/npm\/katex(?:@[^/]+)?\/dist\/(.+)$/);
      if (katexPath) file = path.join(katexDist, katexPath[1]);
      else if (url.pathname.endsWith('/bootstrap.min.css')) file = path.join(root, '_agent_tmp/browser/bootstrap.css');
      else if (url.hostname === 'math.test') file = url.pathname === '/probe.html'
        ? path.join(fixture, 'public/probe.html') : path.join(site, url.pathname);
      if (!file || !fs.existsSync(file) || !fs.statSync(file).isFile()) return route.abort();
      return route.fulfill({path: file});
    });
    await page.goto('https://math.test/probe.html', {waitUntil: 'load'});
    assert.deepEqual(await page.locator('.math-block annotation[encoding="application/x-tex"]').allTextContents(), cases.map(item => '\n' + item.tex + '\n'));
    assert.equal(await page.locator('.math-block .katex-display').count(), cases.length);
    assert.equal(await page.locator('blockquote blockquote .math-block').count(), 1);
    assert.equal(await page.locator('li blockquote .math-block').count(), 1);
    assert.equal(normalize(await page.locator('pre code').textContent()), literal, 'literal code was interpreted as math');
    assert.equal(await page.locator('.katex-error').count(), 0);
    assert.equal(await page.locator('p .katex').count(), 2, 'existing inline math stopped rendering');
    assert.equal(await page.locator('.katex-display').count(), cases.length + 1, 'existing $$ math stopped rendering');

    await page.goto('https://math.test/2026/2612.html', {waitUntil: 'load'});
    assert.ok(await page.evaluate(() => [...document.styleSheets].some(sheet => sheet.href?.endsWith('/css/style.css') && sheet.cssRules.length)), 'theme stylesheet did not load');
    assert.equal(await page.locator('.math-block .katex-display').count(), 6);
    assert.equal(await page.locator('blockquote .math-block').count(), 6);
    assert.deepEqual((await page.locator('.math-block annotation[encoding="application/x-tex"]').allTextContents()).map(normalize), formulas);
    assert.equal(await page.locator('.katex-error').count(), 0, 'article contains a KaTeX error');
    const quote = page.locator('blockquote').filter({hasText: '将主对角线及以上的元素设为 0'});
    for (const width of [1440, 390]) {
      await page.setViewportSize({width, height: 1000});
      await page.evaluate(() => document.fonts.ready);
      // Offscreen math uses content-visibility:auto; let visible formulas finish layout.
      await quote.scrollIntoViewIfNeeded();
      await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
      assert.ok(await quote.locator('.katex-display').evaluateAll(elements => elements.every(element => element.getBoundingClientRect().height > 0)));
      await quote.screenshot({path: path.join(output, `blockquote-${width}.png`)});
    }
    assert.deepEqual(errors, [], 'browser script errors');
    console.log(`PASS: six article formulas; nested quotes/lists; literal comparisons; HTML escaping; existing math and code.\nScreenshots: ${output}`);
  } finally {
    await browser.close();
  }
})().catch(error => {console.error(error); process.exitCode = 1;});
