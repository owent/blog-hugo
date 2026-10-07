// NODE_PATH=<directory containing playwright> node scripts/test-registration.cjs
// Route the same built HTML to different browser origins; no DNS or live site requests.
const {chromium, firefox, webkit} = require('playwright');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const site = path.resolve(process.env.BLOG_TEST_SITE || '_agent_tmp/after-design');
const html = fs.readFileSync(path.join(site, 'index.html'), 'utf8');
const script = fs.readFileSync(path.join(site, 'js/site-registration.js'), 'utf8');
const stylesheet = fs.readFileSync(path.join(site, 'css/style.css'), 'utf8');
const bootstrap = path.resolve(process.env.BOOTSTRAP_CSS || '_agent_tmp/browser/bootstrap.css');
const cases = [
  ['http://localhost:1313/', true], ['http://preview.localhost:8080/', true],
  ['https://x-ha.com/', true], ['https://blog.x-ha.com/', true],
  ['https://a.b.x-ha.com/', true], ['https://r-ci.com/', true],
  ['https://blog.r-ci.com/', true], ['https://BLOG.X-HA.COM:8443/', true],
  ['https://x-ha.com./', true], ['https://owent.net/', false],
  ['https://badx-ha.com/', false], ['https://x-ha.com.evil.test/', false],
  ['https://notr-ci.com/', false], ['https://r-ci.com.evil.test/', false],
  ['https://notlocalhost/', false], ['http://127.0.0.1:1313/', false],
  ['http://[::1]:1313/', false], ['https://example.test/?domain=x-ha.com', false],
  ['https://example.test/#localhost', false]
];
async function routePage(page, source) {
  await page.route('**/*', route => {
    if (route.request().resourceType() === 'document') return route.fulfill({body:source,contentType:'text/html'});
    const pathname = new URL(route.request().url()).pathname;
    if (pathname === '/js/site-registration.js') return route.fulfill({body:script,contentType:'text/javascript'});
    if (pathname.endsWith('/bootstrap.min.css')) return route.fulfill({path:bootstrap,contentType:'text/css'});
    if (pathname.endsWith('/css/style.css')) return route.fulfill({body:stylesheet,contentType:'text/css'});
    return route.abort();
  });
}
(async () => {
  for (const [name, type] of Object.entries({chromium, firefox, webkit})) {
    const browser = await type.launch({headless:true});
    try {
      const page = await browser.newPage();
      await routePage(page, html);
      for (const [url, visible] of cases) {
        await page.goto(url, {waitUntil:'load'});
        assert.equal(await page.locator('#site-registration').isVisible(), visible, `${name}: ${url}`);
      }
      await page.goto('https://x-ha.com/', {waitUntil:'load'});
      for (const width of [320, 390, 768, 1440, 3840]) {
        await page.setViewportSize({width,height:800});
        const footer = await page.locator('#footer').evaluate(el => {
          const license = el.querySelector('.footer-license').getBoundingClientRect();
          const credit = el.querySelector('.footer-credit').getBoundingClientRect();
          return {width:el.clientWidth,scroll:el.scrollWidth,lineGap:Math.abs(license.top+license.bottom-credit.top-credit.bottom)};
        });
        assert.ok(footer.scroll<=footer.width+1, `${name}: registration overflows footer at ${width}px`);
        assert.ok(footer.lineGap<3, `${name}: license wraps with registration at ${width}px`);
      }
      // Exact-only entries must not grant access to subdomains.
      const exact = await browser.newPage();
      const exactHtml = html.replace('data-domains="[]"', 'data-domains="[&quot;preview.example.test&quot;]"');
      await routePage(exact, exactHtml);
      await exact.goto('https://preview.example.test/', {waitUntil:'load'});
      assert.ok(await exact.locator('#site-registration').isVisible());
      await exact.goto('https://sub.preview.example.test/', {waitUntil:'load'});
      assert.equal(await exact.locator('#site-registration').isVisible(), false);
      // Empty/invalid allowlists are fail-closed, even on a normally allowed host.
      for (const value of ['[]','invalid-json','null','[null]']) {
        await page.goto('https://x-ha.com/', {waitUntil:'load'});
        await page.locator('#site-registration').evaluate((el, input) => {
          el.dataset.domains = '[]'; el.dataset.domainSuffixes = input;
        }, value);
        await page.addScriptTag({content:script});
        assert.equal(await page.locator('#site-registration').isVisible(), false);
      }
      const offline = await browser.newContext({javaScriptEnabled:false});
      const noJS = await offline.newPage();
      await routePage(noJS, html);
      await noJS.goto('https://x-ha.com/', {waitUntil:'load'});
      assert.equal(await noJS.locator('#site-registration').isVisible(), false);
      await offline.close();
      console.log(`${name}: ${cases.length + 7} registration checks passed`);
    } finally { await browser.close(); }
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
