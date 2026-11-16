import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const {chromium} = await import('playwright').catch(()=>import('/tmp/practica-qa/node_modules/playwright/index.mjs'));
const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const OUT=path.join(ROOT,'evidence');
const BASE=process.env.SITE_URL||'http://127.0.0.1:8008';
const allPages=JSON.parse(fs.readFileSync(path.join(OUT,'pages.json'),'utf8'));const pages=process.argv.length>2?allPages.filter(p=>process.argv.slice(2).includes(p.key)):allPages;
const browser=await chromium.launch({headless:true,...(fs.existsSync('/run/current-system/sw/bin/chromium')?{executablePath:'/run/current-system/sw/bin/chromium'}:{}),args:['--no-sandbox','--disable-dev-shm-usage']});
const previous=process.argv.length>2&&fs.existsSync(path.join(OUT,'browser-checks.json'))?JSON.parse(fs.readFileSync(path.join(OUT,'browser-checks.json'),'utf8')):{checks:[],failures:[]};const contexts=new Map();const checks=previous.checks.filter(r=>!pages.some(p=>p.key===r.page));const failures=previous.failures.filter(r=>!pages.some(p=>p.key===r.page));
for(const width of [375,1440])fs.mkdirSync(path.join(OUT,'screenshots',String(width)),{recursive:true});
async function context(role){
 if(contexts.has(role))return contexts.get(role);
 const c=await browser.newContext({deviceScaleFactor:1,locale:'ru-RU'});
 if(role){const r=await c.request.get(BASE+'/accounts/login/');const html=await r.text();const csrf=html.match(/name="csrfmiddlewaretoken" value="([^"]+)"/)[1];const result=await c.request.post(BASE+'/accounts/login/',{form:{username:role,password:'DemoTravel8!2026',csrfmiddlewaretoken:csrf},headers:{Referer:BASE+'/accounts/login/'}});if(!result.ok())throw Error('Login failed: '+role);}
 contexts.set(role,c);return c;
}
try{
 for(const row of pages){
  const c=await context(row.role);const page=await c.newPage();let errors=[];
  page.on('pageerror',error=>errors.push(error.message));
  page.on('console',message=>{if(message.type()==='error'&&!([403,404].includes(row.status)&&message.text().includes(String(row.status))))errors.push(message.text());});
  for(const width of [360,375,768,1024,1440]){
   errors=[];await page.setViewportSize({width,height:1000});
   const response=await page.goto(BASE+row.url,{waitUntil:'networkidle'});await page.evaluate(()=>document.fonts.ready);
   const layout=await page.evaluate(()=>{
    const visible=e=>{const r=e.getBoundingClientRect();return r.width>0&&r.height>0&&r.bottom>0&&getComputedStyle(e).visibility!=='hidden';};
    return {viewport:innerWidth,documentWidth:document.documentElement.scrollWidth,h1:document.querySelectorAll('h1').length,inlineStyles:document.querySelectorAll('[style]').length,brokenImages:[...document.images].filter(e=>e.complete&&!e.naturalWidth).map(e=>e.src),smallTargets:[...document.querySelectorAll('a,button,input:not([type=hidden]):not([type=checkbox]):not([type=radio]),select')].filter(visible).filter(e=>e.getBoundingClientRect().height<39.5).map(e=>({tag:e.tagName,text:e.textContent.trim().slice(0,60),height:e.getBoundingClientRect().height})),images:[...document.images].map(e=>({alt:e.getAttribute('alt'),width:e.getAttribute('width'),height:e.getAttribute('height')}))};
   });
   const result={page:row.key,width,status:response.status(),...layout,consoleErrors:[...errors]};checks.push(result);
   if(response.status()!==row.status||layout.documentWidth>width+1||layout.h1!==1||layout.inlineStyles||layout.brokenImages.length||errors.length||layout.smallTargets.length||layout.images.some(i=>i.alt===null||!i.width||!i.height))failures.push(result);
   if([375,1440].includes(width))await page.screenshot({path:path.join(OUT,'screenshots',String(width),row.key+'.png'),fullPage:true});
  }
  await page.close();console.log(JSON.stringify({checked:row.key}));
 }
 const interactions=[];
 const guest=await context(null);const page=await guest.newPage();await page.setViewportSize({width:375,height:900});
 await page.goto(BASE+'/',{waitUntil:'networkidle'});await page.locator('.burger').click();if(await page.locator('.burger').getAttribute('aria-expanded')!=='true')throw Error('Menu did not open');await page.keyboard.press('Escape');if(await page.locator('.burger').getAttribute('aria-expanded')!=='false')throw Error('Menu did not close');interactions.push({name:'mobile menu and Escape',passed:true});
 await page.goto(BASE+'/tours/',{waitUntil:'networkidle'});await page.evaluate(()=>window.__auditMarker='search');await page.locator('#id_q').fill('Алтай');await page.waitForFunction(()=>document.querySelector('#catalog-results').textContent.includes('Найдено маршрутов: 1'));
 if(await page.evaluate(()=>window.__auditMarker)!=='search')throw Error('Live search reloaded page');interactions.push({name:'live search without reload',passed:true});
 await page.goto(BASE+'/contacts/',{waitUntil:'networkidle'});await page.locator('#id_email').fill('wrong');await page.locator('#id_phone').fill('123');await page.getByRole('button',{name:'Отправить вопрос',exact:true}).click();
 if(!await page.locator('#id_email_client_error').innerText())throw Error('Email validation missing');if(!await page.locator('#id_phone_client_error').innerText())throw Error('Phone validation missing');interactions.push({name:'required, email and phone client validation',passed:true});
 const row=allPages.find(p=>p.key==='booking_new');const tourist=await context(row.role);const formPage=await tourist.newPage();await formPage.goto(BASE+row.url,{waitUntil:'networkidle'});await formPage.evaluate(()=>window.__auditMarker='quote');
 await formPage.locator('#id_tourists-0-full_name').fill('Иван Петров');await formPage.locator('#id_tourists-0-birth_date').fill('1990-01-01');await formPage.locator('#calculate').click();await formPage.waitForFunction(()=>document.querySelector('#quote-result').textContent.includes('Итого:'));
 const first=await formPage.locator('#quote-result').innerText();await formPage.locator('#add-tourist').click();await formPage.locator('#id_tourists-1-full_name').fill('Анна Петрова');await formPage.locator('#id_tourists-1-birth_date').fill('1992-01-01');await formPage.locator('#calculate').click();await formPage.waitForFunction(()=>document.querySelector('#quote-result').textContent.includes('Анна Петрова'));
 if(await formPage.evaluate(()=>window.__auditMarker)!=='quote')throw Error('Quote reloaded page');if(first===await formPage.locator('#quote-result').innerText())throw Error('Quote did not change');interactions.push({name:'add tourist and fetch price update without reload',passed:true});await formPage.close();await page.close();
 fs.writeFileSync(path.join(OUT,'browser-checks.json'),JSON.stringify({checks,failures,interactions,screenshots:allPages.length*2},null,2));
 console.log(JSON.stringify({checks:checks.length,failures:failures.map(r=>({page:r.page,width:r.width,overflow:r.documentWidth-r.width,targets:r.smallTargets,errors:r.consoleErrors,broken:r.brokenImages})),interactions}));
 if(failures.length)process.exitCode=1;
}finally{await browser.close();}
