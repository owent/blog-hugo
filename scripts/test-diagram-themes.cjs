// Install playwright, mermaid, echarts, echarts-gl, chart.js, plotly.js-dist-min locally.
// Exercises generated page scripts with real npm libraries; blocks advertising/CDNs.
const {chromium} = require('playwright');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const site=path.resolve(process.env.BLOG_TEST_SITE || '_agent_tmp/after-design');
const modules=path.resolve(process.env.BLOG_TEST_MODULES || '_agent_tmp/browser/node_modules');
const bootstrap=path.resolve(process.env.BOOTSTRAP_CSS || '_agent_tmp/browser/bootstrap.css');
const output=path.resolve('_agent_tmp/layout-results');
fs.mkdirSync(output,{recursive:true});
(async()=>{
 const browser=await chromium.launch({headless:true,args:['--enable-unsafe-swiftshader']});
 try {
  const page=await browser.newPage({viewport:{width:1440,height:1000}});
  const errors=[];
  page.on('console',msg=>{if(msg.type()==='error'&&/parse (echarts|plotly)|mermaid|chart JSON/.test(msg.text()))errors.push(msg.text());});
  await page.route('**/*', async route=>{
   const url=new URL(route.request().url());
   let file;
   if(url.href==='https://esm.sh/mermaid') return route.fulfill({body:'export {default} from "https://owent.net/__vendor/mermaid/dist/mermaid.esm.min.mjs";',contentType:'text/javascript'});
   if(url.pathname.startsWith('/__vendor/')) file=path.join(modules,url.pathname.slice('/__vendor/'.length));
   else if(url.pathname.includes('/npm/echarts-gl/')) file=path.join(modules,'echarts-gl/dist/echarts-gl.min.js');
   else if(url.pathname.includes('/npm/echarts/')) file=path.join(modules,'echarts/dist/echarts.min.js');
   else if(url.pathname.includes('/npm/chart.js')) file=path.join(modules,'chart.js/dist/chart.umd.js');
   else if(url.pathname.includes('/npm/plotly.js')) file=path.join(modules,'plotly.js-dist-min/plotly.min.js');
   else if(url.pathname.endsWith('/bootstrap.min.css')) file=bootstrap;
   else if(url.hostname==='owent.net') file=path.join(site,decodeURIComponent(url.pathname));
   if(!file||!fs.existsSync(file)||!fs.statSync(file).isFile()) return route.abort();
   const ext=path.extname(file);
   return route.fulfill({path:file,contentType:({'.js':'text/javascript','.mjs':'text/javascript','.css':'text/css','.html':'text/html','.json':'application/json'})[ext]||'application/octet-stream',headers:{'Access-Control-Allow-Origin':'*'}});
  });
  await page.goto('https://owent.net/2026/2602.html',{waitUntil:'load'});
  await page.waitForFunction(()=>document.querySelectorAll('.mermaid[data-processed="true"]').length===4 && Object.keys(Chart.instances).length===5 && [...document.querySelectorAll('.echarts-chart')].every(e=>echarts.getInstanceByDom(e)) && [...document.querySelectorAll('.plotly-chart')].every(e=>e._fullLayout),{},{timeout:60000});
  const result=await page.evaluate(()=>({
   versions:{echarts:echarts.version,chart:Chart.version,plotly:Plotly.version},
   mermaid:document.querySelectorAll('.mermaid[data-processed="true"]').length,
   echarts:[...document.querySelectorAll('.echarts-chart')].map(e=>echarts.getInstanceByDom(e).getOption().color),
   plotly:[...document.querySelectorAll('.plotly-chart')].map(e=>e._fullLayout.colorway),
   titles:[...document.querySelectorAll('.plotly-chart')].map(e=>e._fullLayout.title.text),
   axes:[...document.querySelectorAll('.plotly-chart')].filter(e=>e._fullLayout.xaxis).map(e=>[e._fullLayout.xaxis.title.text,e._fullLayout.yaxis.title.text]),
   chart:Object.values(Chart.instances).map(c=>({font:c.options.font.family,border:c.data.datasets[0].borderColor})),
   svgIds:[...document.querySelectorAll('.plantuml-container [id],.d2-container [id]')].map(e=>e.id)
  }));
  assert.equal(result.echarts.length,5);assert.equal(result.plotly.length,5);
  assert.ok(result.echarts.every(c=>c[0]==='#267a93'));
  assert.ok(result.plotly.every(c=>c[0]==='#267a93'));
  assert.ok(result.titles.every(t=>t&& !t.includes('Click to enter')),'missing Plotly title');
  assert.ok(result.axes.every(a=>a[0]==='x'&&a[1]==='y'),'missing axis labels');
  assert.ok(await page.locator('.plotly-chart').evaluateAll(nodes=>nodes.every(n=>[...n.childNodes].every(c=>c.nodeType!==Node.TEXT_NODE||!c.textContent.trim()))),'Plotly placeholder consumes chart height');
  assert.ok(result.chart.some(c=>c.border==='rgb(75, 192, 192)'),'explicit dataset color was changed');
  assert.equal(new Set(result.svgIds).size,result.svgIds.length);
  assert.deepEqual(errors,[]);
  for(const width of [320,390,768,1440]) {
   await page.setViewportSize({width,height:1000});
   await page.waitForTimeout(250);
   assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1), `rendered charts overflow at ${width}`);
  }
  await page.setViewportSize({width:1100,height:900});
  for(const [label,selector] of [['mermaid','.mermaid-container'],['d2','.d2-container'],['plantuml','.plantuml-container'],['echarts','.echarts-container'],['plotly','.plotly-container'],['chart','.chartjs-container']]) {
   await page.locator(selector).first().screenshot({path:path.join(output,`theme-${label}.png`)});
  }
  fs.writeFileSync(path.join(output,'diagram-themes.json'),JSON.stringify(result,null,2));
  console.log(JSON.stringify({versions:result.versions,mermaid:result.mermaid,echarts:result.echarts.length,plotly:result.plotly.length,chart:result.chart.length,svgIds:result.svgIds.length}));
 } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
