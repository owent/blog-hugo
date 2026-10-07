// npm install --no-save playwright (or set NODE_PATH); build into BLOG_TEST_SITE first.
// Uses synthetic creatives, blocks live advertising and external scripts.
const {chromium, firefox, webkit} = require('playwright');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const site = path.resolve(process.env.BLOG_TEST_SITE || '_agent_tmp/after-design');
const bootstrap = path.resolve(process.env.BOOTSTRAP_CSS || '_agent_tmp/browser/bootstrap.css');
const output = path.resolve(process.env.BLOG_TEST_OUTPUT || '_agent_tmp/layout-results');
fs.mkdirSync(output, {recursive:true});
const sizes = [[320,640],[360,800],[390,844],[568,320],[576,800],[768,1024],[820,1180],[1024,768],[1199,900],[1200,900],[1440,1000],[1920,1080],[2560,1440],[3440,1440],[3840,2160]];
const pages = ['/', '/archives/', '/tags/hugo.html', '/2026/2602.html', '/about/'];
const mime = {'.html':'text/html','.css':'text/css','.js':'text/javascript','.png':'image/png','.svg':'image/svg+xml','.jpg':'image/jpeg','.woff2':'font/woff2'};
const luminance=color=>color.match(/[\d.]+/g).slice(0,3).map(v=>Number(v)/255)
 .map(v=>v<=0.04045?v/12.92:((v+0.055)/1.055)**2.4)
 .reduce((sum,v,i)=>sum+v*[0.2126,0.7152,0.0722][i],0);
const contrast=(a,b)=>{const values=[luminance(a),luminance(b)].sort((x,y)=>y-x);return (values[0]+0.05)/(values[1]+0.05);};
// Bound each gradient layer by its lightest/darkest stop before compositing layers.
const surfaceContrast=(textColor,background,image='none')=>{
 const base=background.match(/[\d.]+/g).slice(0,3).map(Number);
 const layers=[];
 let depth=0,start=0;
 for(let i=0;i<image.length;i++){
  if(image[i]==='(')depth++;
  else if(image[i]===')')depth--;
  else if(image[i]===','&&depth===0){layers.push(image.slice(start,i));start=i+1;}
 }
 layers.push(image.slice(start));
 const bounds=[Math.min,Math.max].map(extreme=>[...layers].reverse().reduce((pixels,layer)=>{
  const stops=[...layer.matchAll(/rgba?\(([^)]+)\)/g)].map(match=>match[1].match(/[\d.]+/g).map(Number));
  return pixels.map((value,i)=>extreme(value,...stops.map(stop=>{
   const alpha=stop[3]??1;
   return value*(1-alpha)+stop[i]*alpha;
  })));
 },base));
 return Math.min(...bounds.map(rgb=>contrast(textColor,`rgb(${rgb.join(',')})`)));
};
async function checkAdaptiveToc(page, browserName) {
 await page.goto('https://owent.net/2026/2602.html',{waitUntil:'load'});
 await page.locator('.article-layout').evaluate(layout=>{
  const entry=layout.querySelector('.article-entry');
  for(const position of ['before','after']) {
   const p=document.createElement('p');p.dataset.tocProbe=position;
   p.textContent='这段正文用于检查目录结束或收起之后是否恢复完整的阅读宽度。'.repeat(24);
   if(position==='before')entry.prepend(p);else entry.append(p);
  }
  const ad=document.createElement('div');ad.className='google-auto-placed';
  ad.innerHTML='<iframe title="Simulated direct-layout ad" style="display:block;width:728px;height:90px;border:0" srcdoc="<body>广告布局测试</body>"></iframe>';
  layout.append(ad);
 });
 const widths=[2560,3840,1440,1200,1199,390];
 const fixtures={short:'概述',medium:'1.2 图片语法引用 .excalidraw 外部图表文件',
  long:'较长的章节标题需要完整显示，并在目录宽度上限内换行。'.repeat(5),unbroken:'UnbrokenHeading'.repeat(25)};
 const results=[];
 for(const width of widths)for(const fontSize of width>=1200?[16,32]:[16]) {
  await page.setViewportSize({width,height:900});
  await page.evaluate(size=>document.documentElement.style.setProperty('font-size',`${size}px`,'important'),fontSize);
  await page.locator('.toc').evaluate(toc=>toc.open=innerWidth>=1200);
  await page.waitForFunction(()=>document.querySelector('.toc').open===(innerWidth>=1200));
  for(const [fixture,label]of Object.entries(fixtures)) {
   await page.locator('.toc').evaluate(toc=>toc.open=true);
   await page.locator('.toc nav').evaluate((nav,label)=>{
    nav.innerHTML='<ul><li><a href="#toc-test-first"></a><ul><li><a href="#toc-test-nested"></a></li></ul></li><li><a href="#toc-test-last">最后一节</a></li></ul>';
    nav.querySelectorAll('a:not([href="#toc-test-last"])').forEach(a=>a.textContent=label);
   },label);
   const measure=await page.evaluate(()=>{
    const toc=document.querySelector('.toc'),nav=toc.querySelector('nav'),layout=toc.parentElement,entry=layout.querySelector('.article-entry');
    const t=toc.getBoundingClientRect(),l=layout.getBoundingClientRect(),e=entry.getBoundingClientRect(),ad=layout.querySelector('.google-auto-placed').getBoundingClientRect();
    const lineRects=position=>{
     const range=document.createRange();range.selectNodeContents(entry.querySelector(`[data-toc-probe="${position}"]`));
     return [...range.getClientRects()];
    };
    const first=lineRects('before')[0],last=lineRects('after');
    return {tocWidth:t.width,layoutWidth:l.width,layoutRight:l.right,entryWidth:e.width,tocLeft:t.left,
     firstRight:first.right,firstTop:first.top,lastRight:Math.max(...last.map(r=>r.right)),lastTop:last[0].top,
     adTop:ad.top,entryBottom:e.bottom,tocBottom:t.bottom,
     overflow:document.documentElement.scrollWidth-innerWidth,navWidth:nav.clientWidth,navScrollWidth:nav.scrollWidth,
     navHeight:nav.clientHeight,navScrollHeight:nav.scrollHeight,firstLines:nav.querySelector('a').getClientRects().length};
   });
   const context=`${browserName} ${width}px ${fontSize}px ${fixture}`;
   assert.ok(measure.overflow<=1,`${context}: directory causes page overflow`);
   assert.ok(measure.navScrollWidth<=measure.navWidth+1,`${context}: directory scrolls horizontally`);
   assert.ok(measure.adTop>=Math.max(measure.entryBottom,measure.tocBottom)-1,`${context}: injected ad does not occupy its own row`);
   if(width>=1200) {
    assert.ok(measure.tocWidth<=measure.layoutWidth*.32+1,`${context}: directory exceeds 32% of the reading layout`);
    assert.ok(Math.abs(measure.entryWidth-measure.layoutWidth)<2,`${context}: directory reserves a permanent side column`);
    assert.ok(measure.firstRight<=measure.tocLeft+1,`${context}: body text overlaps the expanded directory`);
    assert.ok(measure.lastTop>=measure.tocBottom,`${context}: end-of-body probe is not below the directory`);
    assert.ok(measure.lastRight>=measure.layoutRight-2*fontSize,`${context}: body remains narrow after the directory ends`);
    if(width>=2560&&fixture==='medium')assert.equal(measure.firstLines,1,`${context}: ordinary long heading still wraps on a wide screen`);
   }
   if(fixture==='short')assert.ok(measure.navScrollHeight<=measure.navHeight+1,`${context}: a short directory has an unnecessary scrollbar`);
   await page.locator('.toc nav a').last().scrollIntoViewIfNeeded();
   assert.ok(await page.locator('.toc nav').evaluate(nav=>{
    const n=nav.getBoundingClientRect(),a=[...nav.querySelectorAll('a')].at(-1).getBoundingClientRect();
    return a.top>=n.top-1&&a.bottom<=n.bottom+1;
   }),`${context}: final directory entry is inaccessible`);
   if(width>=1200) {
    assert.equal(await page.locator('.toc nav').evaluate(nav=>nav.scrollTop),0,`${context}: desktop directory is still internally scrolled`);
    await page.evaluate(()=>{
     const t=document.querySelector('.toc').getBoundingClientRect();
     scrollTo({top:scrollY+t.bottom+80,behavior:'instant'});
    });
    assert.ok(await page.locator('.toc').evaluate(toc=>toc.getBoundingClientRect().bottom<0),`${context}: directory continues sticking to the viewport`);
   }
   await page.locator('.toc summary').click();
   const collapsed=await page.evaluate(()=>{
    const toc=document.querySelector('.toc'),entry=document.querySelector('.article-entry');
    const range=document.createRange();range.selectNodeContents(entry.querySelector('[data-toc-probe="before"]'));
    const t=toc.getBoundingClientRect(),lines=[...range.getClientRects()];
    return {open:toc.open,width:t.width,right:t.right,
     bodyRight:Math.max(...lines.filter(r=>r.top>=t.bottom).map(r=>r.right))};
   });
   assert.equal(collapsed.open,false,`${context}: directory does not collapse`);
   assert.ok(collapsed.width<measure.tocWidth*.6,`${context}: collapsed directory retains a wide empty box`);
   assert.ok(Math.abs(collapsed.right-measure.layoutRight)<2,`${context}: collapsed directory does not stay on the right`);
   assert.ok(collapsed.bodyRight>=measure.layoutRight-2*fontSize,`${context}: collapsed directory still squeezes body text below the button`);
   results.push({width,fontSize,fixture,...measure});
  }
 }
 for(const fontSize of [16,32]) {
  const short=results.find(r=>r.width===2560&&r.fontSize===fontSize&&r.fixture==='short');
  const medium=results.find(r=>r.width===2560&&r.fontSize===fontSize&&r.fixture==='medium');
  const long=results.find(r=>r.width===2560&&r.fontSize===fontSize&&r.fixture==='long');
  assert.ok(short.tocWidth>=250,`${browserName}: short directory is excessively narrow`);
  assert.ok(medium.tocWidth>short.tocWidth+40,`${browserName}: directory does not expand with heading length`);
  assert.ok(long.tocWidth>medium.tocWidth,`${browserName}: longer headings do not receive more space`);
 }
 await page.evaluate(()=>document.documentElement.style.removeProperty('font-size'));
 console.log(`${browserName}: ${results.length} adaptive directory and flow checks passed`);
}
(async()=>{
 const results=[];
 for(const [name,type] of Object.entries({chromium,firefox,webkit})) {
  const browser = await type.launch({headless:true});
  try {
   const page=await browser.newPage();
   await page.route('**/*', async route=>{
    const url=new URL(route.request().url());
    if(url.pathname.endsWith('/bootstrap.min.css')) return route.fulfill({path:bootstrap,contentType:'text/css'});
    if(url.hostname!=='owent.net') return route.abort();
    let file=path.join(site,decodeURIComponent(url.pathname));
    if(url.pathname.endsWith('/')) file=path.join(file,'index.html');
    if(!file.startsWith(site+path.sep)||!fs.existsSync(file)||!fs.statSync(file).isFile()) return route.abort();
    return route.fulfill({path:file,contentType:mime[path.extname(file)]||'application/octet-stream'});
   });
   await checkAdaptiveToc(page,name);
   for(const url of pages) {
    await page.goto('https://owent.net'+url,{waitUntil:'load'});
    await page.evaluate(()=>document.fonts.ready);
    const archive=await page.locator('#index-content, #archive-content').count()>0;
    const label=url==='/'?'home':url.includes('archives')?'archives':url.includes('tags')?'tags':url.includes('2602')?'article':'about';
    if(label==='home') {
     assert.equal(await page.locator('.archive-heading').count(),0,'home still has a heading row');
     assert.equal(await page.locator('a[href$="index.xml"]').count(),1,'home has duplicate RSS links');
     assert.equal(await page.locator('#main-nav #nav-rss-link').count(),1,'navigation RSS link missing');
     const cards=await page.locator('.archive-article').evaluateAll(nodes=>nodes.map(el=>{
      const outer=getComputedStyle(el),inner=getComputedStyle(el.querySelector('.archive-article-inner'));
      const heading=getComputedStyle(el.querySelector('.archive-card-heading'));
      return {background:heading.backgroundColor,image:heading.backgroundImage,title:getComputedStyle(el.querySelector('.article-title')).color,
       category:getComputedStyle(el.querySelector('.archive-card-category')).color,
       date:getComputedStyle(el.querySelector('.archive-card-meta')).color,shadow:outer.boxShadow,
       borders:[outer.borderTopWidth,outer.borderRightWidth,outer.borderBottomWidth,outer.borderLeftWidth],
       innerBorder:inner.borderTopWidth,outerRadius:parseFloat(outer.borderTopLeftRadius),innerRadius:parseFloat(inner.borderTopLeftRadius)};
     }));
     assert.equal(new Set(cards.map(card=>card.background)).size,1,'first card has a different heading background');
     assert.equal(new Set(cards.map(card=>card.image)).size,1,'first card has a different heading texture');
     for(const card of cards) {
      assert.equal(card.shadow,'none','card has a shadow around its border');
      assert.deepEqual(card.borders,['1px','1px','1px','1px'],'card does not have a single uniform border');
      assert.equal(card.innerBorder,'0px','inner card adds another border');
      assert.equal(card.innerRadius,card.outerRadius-1,'nested card curves do not align');
      assert.ok(surfaceContrast(card.title,card.background,card.image)>=4.5,'card title contrast too low');
      assert.ok(surfaceContrast(card.date,card.background,card.image)>=4.5,'card date contrast too low');
      assert.ok(surfaceContrast(card.category,card.background,card.image)>=4.5,`card category contrast too low: ${card.category} on ${card.background}, ${card.image}`);
     }
    }
    if(label==='about') {
     const colors=await page.evaluate(()=>{
      const link=getComputedStyle(document.querySelector('.article-entry a'));
      const quote=getComputedStyle(document.querySelector('.article-entry blockquote'));
      const sample=document.createElement('div');
      sample.innerHTML='<a href="/__layout-quote">Quote link</a><strong>Emphasis</strong><h3>Heading</h3><code>code</code>';
      document.querySelector('.article-entry blockquote').append(sample);
      const nested=[...sample.children].map(el=>getComputedStyle(el).color);
      sample.remove();
      const panel=getComputedStyle(document.querySelector('.reading-panel'));
      const title=getComputedStyle(document.querySelector('.reading-panel .article-header'));
      return {link:link.color,underline:link.textDecorationLine,panel:panel.backgroundColor,panelImage:panel.backgroundImage,
       title:getComputedStyle(document.querySelector('.reading-panel .article-header a')).color,titleBackground:title.backgroundColor,titleImage:title.backgroundImage,
       quote:quote.color,quoteBackground:quote.backgroundColor,quoteBorder:quote.borderLeftColor,nested};
     });
     assert.ok(surfaceContrast(colors.link,colors.panel,colors.panelImage)>=4.5,'body link contrast too low');
     assert.ok(surfaceContrast(colors.title,colors.titleBackground,colors.titleImage)>=4.5,'article title contrast too low');
     assert.ok(colors.underline.includes('underline'),'body links lost their non-color cue');
     assert.ok(contrast(colors.quote,colors.quoteBackground)>=4.5,'quote text contrast too low');
     assert.ok(contrast(colors.quoteBorder,colors.quoteBackground)>=3,'quote border is too faint');
     for(const color of colors.nested) assert.ok(contrast(color,colors.quoteBackground)>=4.5,'text inside quote has low contrast');
    }
    if(name==='chromium'&&['home','article'].includes(label)&&process.env.BLOG_SCREENSHOTS!=='0') {
     await page.setViewportSize({width:2560,height:1200});
     await page.screenshot({path:path.join(output,`${label}-clean.png`)});
    }
    const slots=await page.locator('.ads-container').count();
    assert.ok(slots <= (archive?2:1), `${name} ${url}: too many manual slots: ${slots}`);
    if(process.env.BLOG_EXPECT_MANUAL==='1') assert.equal(slots,archive?Math.min(2,Math.floor(await page.locator('.archive-article').count()/6)):url.includes('2602')?1:0,'manual slot count/noad regression');
    assert.equal(await page.locator('.archive-article .ads-container, .toc .ads-container').count(),0);
    // Fill manual units (or an equivalent slot if this build has ads disabled).
    await page.evaluate(isArchive=>{
     const cards=document.querySelectorAll('.archive-article');
     if(!document.querySelector('.ads-container')) {
      const slot=document.createElement('aside');slot.className='ads-container';
      if(isArchive) (cards[5]||cards[cards.length-1]).after(slot);
      else (document.querySelector('.article-entry')||document.querySelector('.article-panel')).after(slot);
     }
     for(const slot of document.querySelectorAll('.ads-container')) slot.innerHTML='<ins class="adsbygoogle" data-ad-status="filled" style="display:block;width:100%"><iframe title="Simulated advertisement" style="display:block;border:0;margin:auto" srcdoc="<body style=&quot;margin:0;background:#e2e8f0;display:grid;place-items:center;height:100vh;font:16px sans-serif;color:#334155&quot;>广告布局测试</body>"></iframe></ins>';
     // Simulate an Auto ads block inserted into a grid, not inside a fixed card.
     const auto=document.createElement('div');auto.className='google-auto-placed';
     auto.innerHTML='<iframe title="Simulated auto ad" style="display:block;margin:auto;border:0" srcdoc="<body style=&quot;background:#e2e8f0&quot;>Auto ads 布局测试</body>"></iframe>';
     if(isArchive) (cards[2]||cards[cards.length-1]).after(auto);
     else if(document.querySelector('.article-entry p')) document.querySelector('.article-entry p').after(auto);
     else document.querySelector('.archive-widgets').append(auto);
    },archive);
    for(const [width,height] of sizes) {
     await page.setViewportSize({width,height});
     // Wait for the media-query change handler before measuring or capturing.
     await page.waitForFunction(()=>{
      const toc=document.querySelector('details.toc');
      return !toc||toc.open===(innerWidth>=1200);
     });
     await page.evaluate(()=>{
      for(const frame of document.querySelectorAll('.ads-container iframe,.google-auto-placed iframe')) {
       const available=frame.parentElement.getBoundingClientRect().width;
       frame.style.width=(available>=728?728:available>=468?468:Math.min(300,available))+'px';
       frame.style.height=(innerWidth<576?250:90)+'px';
      }
     });
     const measure=await page.evaluate(()=>{
      const rect=e=>{const r=e.getBoundingClientRect();return {left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width,height:r.height};};
      const reading=document.querySelector('.reading-panel > .article-panel-inner');
      const readingStyle=reading&&getComputedStyle(reading);
      return {viewport:innerWidth,scroll:document.documentElement.scrollWidth,
       cards:[...document.querySelectorAll('.archive-article')].map(rect),
       ads:[...document.querySelectorAll('.ads-container,.google-auto-placed')].map(rect),
       entry:document.querySelector('.article-entry')?rect(document.querySelector('.article-entry')):null,
       readingWidth:reading?reading.clientWidth-parseFloat(readingStyle.paddingLeft)-parseFloat(readingStyle.paddingRight):null,
       toc:document.querySelector('.toc')?rect(document.querySelector('.toc')):null,
       main:rect(document.querySelector('#main-content')),
       columns:document.querySelector('#index-content, #archive-content')?getComputedStyle(document.querySelector('#index-content, #archive-content')).gridTemplateColumns.split(' ').length:null,
       license:rect(document.querySelector('.footer-license')),
       credit:rect(document.querySelector('.footer-credit')),
       panel:getComputedStyle(document.querySelector('.article-panel')).backgroundColor,
       radius:parseFloat(getComputedStyle(document.querySelector('.article-panel')).borderTopLeftRadius),
       listTop:document.querySelector('#index-content')?document.querySelector('#index-content').getBoundingClientRect().top-document.querySelector('#header').getBoundingClientRect().bottom:null,
       readingTop:reading?reading.parentElement.getBoundingClientRect().top-document.querySelector('#header').getBoundingClientRect().bottom:null,
       titleTop:reading?reading.querySelector('.article-header h1').getBoundingClientRect().top-document.querySelector('#header').getBoundingClientRect().bottom:null,
       background:getComputedStyle(document.querySelector('#main')).backgroundColor};
     });
     assert.ok(measure.scroll<=width+1, `${name} ${url} ${width}: overflow ${measure.scroll}`);
     if((archive||label==='archives')&&width>=1920) {
      assert.ok(measure.main.width>=width-66,`${name} ${url}: wide list remains capped`);
      if(archive) assert.ok(measure.columns>=Math.floor((width-64+20)/404),'wide screen is not adding columns');
     }
     assert.ok(Math.abs((measure.license.top+measure.license.bottom)-(measure.credit.top+measure.credit.bottom))<3,'license and author are on different lines');
     assert.notEqual(measure.panel,'rgb(255, 255, 255)','panel is still pure white');
     assert.ok(measure.radius>=6&&measure.radius<=8,'panel corners should be moderately rounded');
     if(label==='home') assert.ok(measure.listTop<=21,'home starts too far below navigation');
     if(measure.entry) {
      // Subtracting viewport coordinates after scrolling can introduce fractional-pixel error.
      assert.ok(measure.readingTop<=16.1,`${name} ${url} ${width}: reading panel gap ${measure.readingTop}`);
      assert.ok(measure.titleTop<=41.1,`${name} ${url} ${width}: article title gap ${measure.titleTop}`);
     }
     for(const ad of measure.ads) {
      assert.ok(ad.left>=-1&&ad.right<=width+1, `${name} ${width}: ad outside viewport`);
      for(const card of measure.cards) assert.ok(ad.right<=card.left+1||ad.left>=card.right-1||ad.bottom<=card.top+1||ad.top>=card.bottom-1, 'ad overlaps card');
     }
     if(measure.entry) assert.ok(measure.entry.width>=Math.min(270,width-50),`${name} ${url} ${width}: reading column squeezed (${measure.entry.width}px)`);
     if(measure.entry&&width>=1200) {
      assert.ok(measure.main.width>=width-66,`${name} ${url} ${width}: reading panel remains capped`);
      assert.ok(Math.abs(measure.entry.width-measure.readingWidth)<2,`${name} ${url} ${width}: article does not fill available width`);
     }
     if(process.env.BLOG_SCREENSHOTS!=='0'&&[390,1440].includes(width)) {
      await page.screenshot({path:path.join(output,`${name}-${label}-${width}.png`)});
      if(label==='about') await page.locator('#footer').screenshot({path:path.join(output,`${name}-footer-${width}.png`)});
     }
     results.push({browser:name,url,width,height,...measure});
    }
    await page.locator('.ads-container ins').evaluateAll(nodes=>nodes.forEach(n=>n.dataset.adStatus='unfilled'));
    assert.ok(await page.locator('.ads-container').evaluateAll(nodes=>nodes.every(n=>n.getBoundingClientRect().height===0)), 'unfilled slot did not collapse');
   }
   await page.goto('https://owent.net/2026/2602.html',{waitUntil:'load'});
   assert.equal(await page.locator('.plantuml-container svg').count(),4);
   // WebKit may suspend SVG animation outside the viewport.
   await page.locator('.d2-container').first().scrollIntoViewIfNeeded();
   const animations=await page.locator('.d2-container *').evaluateAll(nodes=>nodes.filter(n=>getComputedStyle(n).animationName!=='none').map(n=>({tag:n.tagName,offset:getComputedStyle(n).strokeDashoffset})));
   assert.ok(animations.length>0,'D2 has no animated edges');
   await page.waitForFunction(before=>[...document.querySelectorAll('.d2-container *')]
    .filter(n=>getComputedStyle(n).animationName!=='none')
    .some((n,i)=>getComputedStyle(n).strokeDashoffset!==before[i].offset),animations,{timeout:5000,polling:100});
   await page.emulateMedia({reducedMotion:'reduce'});
   assert.equal(await page.locator('.d2-container *').evaluateAll(nodes=>nodes.filter(n=>getComputedStyle(n).animationName!=='none').length),0,'reduced motion ignored');
   await page.setViewportSize({width:390,height:844});
   await page.waitForFunction(()=>!document.querySelector('details.toc').open);
   await page.locator('.toc summary').click();
   assert.ok(await page.locator('.toc').evaluate(e=>e.open),'mobile TOC cannot open');
   const offline=await browser.newContext({javaScriptEnabled:false});
   const noJS=await offline.newPage();
   await noJS.route('**/*',r=>r.abort());
   await noJS.setContent(fs.readFileSync(path.join(site,'2026/2602.html'),'utf8'));
   assert.equal(await noJS.locator('.plantuml-container > svg,.d2-container > svg').count(),8);
   await offline.close();
   console.log(`${name}: ${sizes.length*pages.length} viewport/page checks passed`);
  } finally {await browser.close();}
 }
 fs.writeFileSync(path.join(output,'results.json'),JSON.stringify(results,null,2));
})().catch(e=>{console.error(e);process.exitCode=1;});
