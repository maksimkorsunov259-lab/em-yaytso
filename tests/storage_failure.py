"""Storage read failures must never overwrite existing data or export an empty replacement."""
import json,os,tempfile
from pathlib import Path
from playwright.sync_api import sync_playwright
url=os.environ.get('APP_URL','http://127.0.0.1:8028/em-yaytso/')
with sync_playwright() as pw:
 b=pw.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH','/usr/bin/chromium'),headless=True,args=['--no-sandbox'])
 c=b.new_context();p=c.new_page();p.add_init_script("Object.defineProperty(window,'indexedDB',{get(){throw new Error('Storage denied')}})")
 p.goto(url);p.wait_for_selector('#storage-error:not([hidden])')
 assert p.locator('#storage-error [data-runtime=export]').count()==0
 assert p.locator('a[href="tel:112"]').count()==1
 c.close()
 c=b.new_context(accept_downloads=True);p=c.new_page();p.goto(url);p.wait_for_function('typeof state!=="undefined"&&state&&!loading');p.wait_for_timeout(600)
 assert p.evaluate('canExport')
 p.evaluate("saveQueue.then(()=>DiaryStore.write({app:'em-yaytso',schemaVersion:999,original:'Keep original data'}))")
 p.reload();p.wait_for_selector('#storage-error:not([hidden])')
 with p.expect_download() as download:p.locator('#storage-error [data-runtime=export]').click()
 with tempfile.TemporaryDirectory() as directory:
  target=Path(directory)/'recovery.json';download.value.save_as(str(target));data=json.loads(target.read_text());assert data['schemaVersion']==999;assert data['original']=='Keep original data'
 print('PASS: unreadable storage is not overwritten; corrupt snapshot can be exported unchanged; emergency help remains accessible')
 b.close()
