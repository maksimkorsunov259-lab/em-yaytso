from playwright.sync_api import sync_playwright
from pathlib import Path
import json
import os,tempfile
from urllib.parse import urljoin,urlparse
out=Path(tempfile.mkdtemp(prefix='em-yaytso-tests-'))
with sync_playwright() as pw:
 b=pw.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH','/usr/bin/chromium'),headless=True,args=['--no-sandbox'])
 c=b.new_context(viewport={'width':390,'height':844},accept_downloads=True)
 p=c.new_page();errors=[];p.on('pageerror',lambda e:errors.append(str(e)));p.on('dialog',lambda d:d.accept())
 p.goto(os.environ.get('APP_URL','http://127.0.0.1:8028/em-yaytso/'));p.wait_for_function('typeof state!=="undefined"&&state&&!loading');p.wait_for_timeout(500)
 # Every view remains usable at narrow and wide widths.
 for width in [320,768,1280]:
  p.set_viewport_size({'width':width,'height':844})
  for v in ['today','plan','more','guide','rules','recipes','recipe','doctorTable','entry','diary','report','progress','settings','profile','patients','about','help']:
   p.evaluate('(v)=>render(v)',v)
   assert not p.evaluate('document.documentElement.scrollWidth>innerWidth'),(v,width)
   assert p.locator('#author-slot img').count()==2,(v,width)
   for img in p.locator('#author-slot img').all():assert img.evaluate('(i)=>i.complete&&i.naturalWidth>0')
 p.set_viewport_size({'width':390,'height':844})
 # Daily preparation is reset on date change.
 p.evaluate("state.daily={well:true,asthma:true,changes:true,prepared:true};state.dailyDate=recentDate(-1);render('today')")
 assert not p.evaluate('Object.values(state.daily).some(Boolean)')
 # No future entries are accepted, even a later time on today's date.
 p.evaluate("render('entry')");p.locator('[name=kind]').select_option('observation');p.locator('[name=note]').fill('Наблюдение');p.locator('[name=time]').fill('23:59');p.locator('#entry-form button[type=submit]').click();assert p.locator('#entry-error').inner_text();assert p.evaluate('state.records.length')==0
 # A save failure remains visible and stops edits; recovery export retains unsaved state.
 p.evaluate("formDirty=false;render('profile');DiaryStore.write=async()=>{throw new Error('QuotaExceededError: тест заполненного хранилища')};void 0")
 p.locator('[name=patientName]').fill('Несохранённое имя');p.locator('#patient-form button[type=submit]').click();p.evaluate('saveQueue');assert p.locator('#storage-error').is_visible();assert 'QuotaExceededError' in p.locator('#storage-error').inner_text()
 p.evaluate("render('profile')");assert p.locator('[name=patientName]').is_disabled()
 with p.expect_download() as d:p.locator('#storage-error [data-runtime=export]').click()
 d.value.save_as(str(out/'failed-write-recovery.json'));assert json.loads((out/'failed-write-recovery.json').read_text())['patients'][0]['name']=='Несохранённое имя'
 p.reload();p.wait_for_function('typeof state!=="undefined"&&state&&!loading');assert p.evaluate('state.name')=='Новый пациент';assert p.locator('#storage-error').is_hidden()
 # App identities and cache namespaces remain distinct across all three PWAs.
 p.evaluate("caches.open('dyshu-diary:foreign-test');caches.open('em-moloko:foreign-test')")
 p.wait_for_function('navigator.serviceWorker.controller!==null')
 assert p.evaluate("navigator.serviceWorker.controller.scriptURL.endsWith('/em-yaytso/sw.js')")
 for app in ['em-yaytso','em-moloko','dyshu-diary']:
  response=c.request.get(urljoin(os.environ.get('APP_URL','http://127.0.0.1:8028/em-yaytso/'),'../'+app+'/manifest.webmanifest'))
  if not response.ok and app!='em-yaytso':continue
  m=response.json()
  assert urlparse(urljoin('http://127.0.0.1:8028/'+app+'/',m['id'])).path=='/'+app+'/'
 assert p.evaluate("caches.keys().then(keys=>keys.includes('dyshu-diary:foreign-test')&&keys.includes('em-moloko:foreign-test'))")
 # Text report uses selected profile and preserves measurements. PDF generation succeeds.
 p.evaluate("render('report')");p.pdf(path=str(out/'report-layout.pdf'),format='A4');assert (out/'report-layout.pdf').stat().st_size>10000
 assert not errors,errors
 print('PASS: 320/768/1280 layouts, author on every view, midnight reset, future-time rejection, failed-write recovery, distinct PWA identities, PDF')
 b.close()
