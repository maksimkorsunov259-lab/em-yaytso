"""Real worker replacement preserves saved diaries and unfinished forms in other tabs."""
import functools,http.server,os,shutil,subprocess,tempfile,threading
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1]
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
def ready(p,url):
 p.goto(url);p.wait_for_function('!loading&&!pendingWrites&&!!registration?.active');assert not p.evaluate('storageFailed')
def deploy(root,version):
 f=root/'app.js';f.write_text(f.read_text()+f'\nwindow.updateTestBuild={version};\n')
 subprocess.run(['python',str(root/'tools/build_sw.py')],check=True,stdout=subprocess.DEVNULL)
with tempfile.TemporaryDirectory() as tmp,sync_playwright() as pw:
 app=Path(tmp)/'em-yaytso';shutil.copytree(ROOT,app,ignore=shutil.ignore_patterns('.git','__pycache__'))
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=tmp));threading.Thread(target=server.serve_forever,daemon=True).start();url=f'http://127.0.0.1:{server.server_port}/em-yaytso/'
 browser=pw.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH','/usr/bin/chromium'),args=['--no-sandbox']);c=browser.new_context();p=c.new_page();errors=[];p.on('pageerror',lambda e:errors.append(str(e)));p.on('dialog',lambda d:d.accept());ready(p,url)
 assert p.locator('#update-banner').is_hidden()
 q=c.new_page();q.on('pageerror',lambda e:errors.append(str(e)));q.on('dialog',lambda d:d.accept());ready(q,url);q.evaluate("render('profile')");q.locator('[name=patientName]').fill('Черновик')
 p.evaluate("render('settings')");deploy(app,1);p.evaluate('registration.update()');p.wait_for_function('!!registration.waiting');expect(p.locator('#update-banner')).to_be_visible();expect(p.locator('#screen [data-runtime=update]')).to_be_visible()
 # Receiving an update must not close About or reset its underlying form.
 p.locator('[data-go=about]').click();expect(p.locator('dialog.family-about:not(#family-help)')).to_be_visible();p.locator('#family-about [data-family-about-close]').click()
 # Unfinished inputs block activation.
 p.evaluate("render('profile')");p.locator('[name=patientName]').fill('Не сохранено');p.locator('#update-banner button').click();assert not p.evaluate('updateRequested');assert p.locator('[name=patientName]').input_value()=='Не сохранено'
 p.evaluate("render('today')")
 # Wait for a real pending write before activating the waiting worker.
 p.evaluate("window.realWrite=DiaryStore.write;DiaryStore.write=s=>new Promise(resolve=>{window.finishWrite=()=>realWrite(s).then(resolve)});state.name='Сохранённый пациент';render('today')");p.wait_for_function('pendingWrites===1');p.locator('#update-banner button').click();p.wait_for_function('updatePreparing');assert not p.evaluate('window.updateTestBuild');p.evaluate('finishWrite()');p.wait_for_function('window.updateTestBuild===1&&!loading');assert p.evaluate('state.name')=='Сохранённый пациент'
 q.wait_for_function('reloadReady');assert not q.evaluate('window.updateTestBuild');assert q.locator('[name=patientName]').input_value()=='Черновик';q.locator('#update-banner button').click();assert q.evaluate('formDirty');q.evaluate("render('today')");q.locator('#update-banner button').click();q.wait_for_function('window.updateTestBuild===1&&!loading');assert q.evaluate('state.name')=='Сохранённый пациент'
 # A failed pending write blocks an update, keeping recovery accessible.
 deploy(app,2);p.evaluate('registration.update()');p.wait_for_function('!!registration.waiting');p.evaluate("DiaryStore.write=()=>new Promise((resolve,reject)=>{window.failWrite=()=>reject(new Error('QuotaExceededError'))});state.name='Несохранённое изменение';render('today')");p.wait_for_function('pendingWrites===1');p.locator('#update-banner button').click();p.wait_for_function('updatePreparing');p.evaluate('failWrite()');p.wait_for_function('storageFailed&&!updatePreparing');assert p.evaluate('window.updateTestBuild')==1;assert not p.evaluate('updateRequested');expect(p.locator('#storage-error [data-runtime=export]')).to_be_visible()
 c.set_offline(True);q.reload();q.wait_for_function('!loading');assert q.evaluate('state.name')=='Сохранённый пациент';q.locator('[data-go=about]').click();expect(q.locator('dialog.family-about:not(#family-help)')).to_be_visible()
 assert not errors,errors;browser.close();server.shutdown()
print('PASS: update detection, automatic refresh of update controls, draft and queued-write protection, failed-write recovery, other-tab preservation, About after update, offline saved patient.')
