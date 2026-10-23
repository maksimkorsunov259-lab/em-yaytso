"""Header selection preserves separate diaries, confirmation and pending saves."""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
APP=Path(__file__).resolve().parents[1].name
EGG=APP=='em-yaytso';current='state' if EGG else 'p';namefield='patientName' if EGG else 'name'
with sync_playwright() as pw:
 b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);c=b.new_context(viewport={'width':390,'height':844});page=c.new_page();errors=[];accept=[False];prompts=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 def dialog(d):prompts.append(d.message);d.accept() if accept[0] else d.dismiss()
 page.on('dialog',dialog);page.goto(os.environ.get('APP_URL','http://127.0.0.1:8055/'+APP+'/'));page.wait_for_function('!loading&&!pendingWrites')
 page.evaluate("""egg=>{const model=egg?EggModel:PrikormModel,a=collection.patients[0],b=model.patient('Миша <тест>','2020-10-01');a.name='Первый пациент';a.dob='2021-01-02';if(egg){a.reportQuestion='Вопрос первого';b.reportQuestion='Вопрос второго';}else{a.questions='Вопрос первого';b.questions='Вопрос второго';a.plan='План первого';b.plan='План второго';}collection.patients.push(b);render('today');}""",EGG);page.wait_for_function('!pendingWrites')
 ids=page.locator('#patient-select option').evaluate_all('(els)=>els.map(e=>e.value)');select=page.locator('#patient-select');assert len(ids)==2
 expect(select.locator('option').nth(1)).to_have_text('Миша <тест> · 1 октября 2020 г.');assert page.locator('#patient-select тест').count()==0
 for width in [320,390,1440]:
  page.set_viewport_size({'width':width,'height':844});page.evaluate('scrollTo(0,700)');select.select_option(ids[1]);page.wait_for_function('(id)=>collection.activePatientId===id&&!pendingWrites',arg=ids[1]);assert page.evaluate(current+'.'+('reportQuestion' if EGG else 'questions'))=='Вопрос второго';assert not page.evaluate('document.documentElement.scrollWidth>innerWidth');select.select_option(ids[0]);page.wait_for_function('(id)=>collection.activePatientId===id&&!pendingWrites',arg=ids[0])
 # Cancel leaves the selected patient and the draft unchanged.
 page.evaluate("render('profile')");page.locator('[name='+namefield+']').fill('Черновик');select.select_option(ids[1]);expect(select).to_have_value(ids[0]);expect(page.locator('[name='+namefield+']')).to_have_value('Черновик');assert page.evaluate('collection.activePatientId')==ids[0];assert prompts
 accept[0]=True;select.select_option(ids[1]);page.wait_for_function('(id)=>collection.activePatientId===id&&!pendingWrites',arg=ids[1]);assert page.evaluate('collection.patients[0].name')=='Первый пациент'
 # All queued writes complete before selection changes; a failed write blocks switching.
 page.evaluate("window.realWrite=DiaryStore.write;DiaryStore.write=s=>new Promise(resolve=>{window.finishWrite=()=>realWrite(s).then(resolve)});"+current+".name='Сохранённый второй';render('today')");page.wait_for_function('pendingWrites===1');select.select_option(ids[0]);expect(select).to_be_disabled();assert page.evaluate('collection.activePatientId')==ids[1];page.evaluate('finishWrite();DiaryStore.write=realWrite');page.wait_for_function('(id)=>collection.activePatientId===id&&!pendingWrites',arg=ids[0]);expect(select).to_be_enabled()
 page.evaluate('navigator.serviceWorker.ready');page.reload();page.wait_for_function('!loading&&!pendingWrites');assert page.evaluate('collection.activePatientId')==ids[0];expect(select.locator('option').nth(1)).to_contain_text('Сохранённый второй')
 c.set_offline(True);page.reload();page.wait_for_function('!loading&&!pendingWrites');select.select_option(ids[1]);page.wait_for_function('(id)=>collection.activePatientId===id&&!pendingWrites',arg=ids[1]);assert page.evaluate(current+'.'+('reportQuestion' if EGG else 'questions'))=='Вопрос второго'
 page.evaluate("DiaryStore.write=async()=>{throw Error('Test failure')};"+current+".name='Не сохранено';render('today')");page.wait_for_function('storageFailed');expect(select).to_be_disabled();assert page.evaluate('collection.activePatientId')==ids[1];assert not errors,errors;c.close();b.close()
print('PASS:',APP,'dropdown labels/escaping, 320/390/1440, patient isolation, cancel/confirm draft, pending writes, reload/offline and failed storage.')
