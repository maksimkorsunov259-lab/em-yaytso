from playwright.sync_api import sync_playwright
from pathlib import Path
import json
import os,tempfile
out=Path(tempfile.mkdtemp(prefix='em-yaytso-tests-'));out.mkdir(exist_ok=True)
with sync_playwright() as pw:
 b=pw.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH','/usr/bin/chromium'),headless=True,args=['--no-sandbox'])
 c=b.new_context(viewport={'width':390,'height':844},accept_downloads=True)
 p=c.new_page(); errors=[];p.on('pageerror',lambda e:errors.append(str(e)));p.on('dialog',lambda d:d.accept())
 p.goto(os.environ.get('APP_URL','http://127.0.0.1:8028/em-yaytso/'));p.wait_for_function('typeof state!=="undefined"&&state&&!loading');p.wait_for_timeout(700)
 def go(v):p.evaluate('(v)=>render(v)',v)
 def saved():
  p.evaluate('saveQueue'); assert p.locator('#storage-error').is_hidden(),p.locator('#storage-error').inner_text()
 def fill(n,v):p.locator('[name="'+n+'"]').fill(str(v))
 def sel(n,v):p.locator('[name="'+n+'"]').select_option(v)
 go('profile');fill('patientName','Аня');fill('dob','2023-01-15');p.locator('#patient-form button[type=submit]').click();saved()
 go('plan');sel('phenotype','delayed');fill('diagnosis','Назначение аллерголога');fill('age',3);sel('setting','home');sel('asthma','none');p.locator('[name=clinicianConfirmed]').check()
 fill('protocol','Назначение от 18.10.2026');sel('stage','2')
 for rid in ['EL-22','EL-21']:
  p.locator('[name=allowed][value='+rid+']').check();fill('start-'+rid,'¼ полной порции');fill('schedule-'+rid,'По письменному назначению врача')
 for n,v in {'goal':'Полная порция с повторным наблюдением','start':'2026-10-01','frequency':'По назначению','minDays':0,'fullRequired':2,'immediateHours':0,'delayedHours':0,'restart':'Связаться с врачом','contact':'План помощи от врача'}.items():fill(n,v)
 p.locator('#plan-form > label input[type=checkbox]').check();p.locator('#plan-form button[type=submit]').click();saved()
 print('PLAN',p.evaluate('view'),p.locator('#screen').inner_text()[:50]);assert p.evaluate('view')=='chooseRecipe'
 p.locator('[data-choose-recipe=EL-22]').click();p.locator('[name=confirmStart]').check();p.locator('#recipe-choice-form button[type=submit]').click();saved()
 assert p.evaluate('state.plan.recipeId')=='EL-22'
 p.locator('[data-daily=well]').check();saved();p.reload();p.wait_for_function('typeof state!=="undefined"&&state&&!loading');assert p.evaluate('state.daily.well')
 go('today');p.screenshot(path=str(out/'today.png'),full_page=True)
 # Complete a full portion; stay on the current course and do not auto advance.
 go('entry');p.locator('[data-fraction="1/1"]').click();p.locator('[name=recipeMatch]').check();p.locator('[name=immediateDone]').check();p.locator('[name=delayedDone]').check();sel('symptom','none');p.locator('#entry-form button[type=submit]').click();saved()
 assert p.evaluate('state.records.length')==1;assert p.evaluate('progressInfo().full')==1;assert not p.evaluate('progressInfo().ready')
 old=p.evaluate('structuredClone(state.records[0])')
 # Recipe switch cannot carry full portions or alter historical snapshots.
 go('chooseRecipe');p.locator('[data-choose-recipe=EL-21]').click();p.locator('[name=confirmStart]').check();p.locator('#recipe-choice-form button[type=submit]').click();saved()
 assert p.evaluate('progressInfo().full')==0;assert p.evaluate('state.records[0]')==old
 go('entry');p.locator('[data-fraction="1/4"]').click();sel('symptom','symptom');fill('onset','Через 20 минут');fill('note','Сыпь');p.locator('#entry-form button[type=submit]').click();saved();assert p.evaluate('state.paused')
 go('chooseRecipe');assert p.locator('[data-choose-recipe=EL-22]').is_disabled()
 # Separate patient with empty plan and no inherited reaction pause.
 go('patients');p.locator('[data-go=newPatient]').click();fill('patientName','Боря');fill('dob','2024-03-04');p.locator('#patient-form button[type=submit]').click();saved();assert p.evaluate('state.records.length')==0;assert not p.evaluate('state.paused');assert not p.evaluate('state.assigned')
 go('entry');sel('kind','skip');fill('note','Поездка');p.locator('#entry-form button[type=submit]').click();saved();assert p.evaluate('state.records.length')==1
 go('patients');p.screenshot(path=str(out/'patients.png'),full_page=True);p.locator('[data-patient]:not([disabled])').click();saved();assert p.evaluate('state.name')=='Аня';assert p.evaluate('state.paused');assert p.evaluate('state.records.length')==2
 # Resume only through documented clinical review, restarting the course.
 go('clinicalReview');fill('reviewClinician','Аллерголог');fill('reviewNote','Осмотр проведён, условия возобновления согласованы');sel('reviewDecision','resume');sel('restartRecipe','EL-22');fill('restartStart','По назначению врача');fill('restartSchedule','По письменному плану');p.locator('[name=reviewConfirmed]').check();p.locator('#clinical-review-form button[type=submit]').click();saved();assert not p.evaluate('state.paused');assert p.evaluate('state.clinicalReviews.length')==1;assert p.evaluate('progressInfo().full')==0
 go('settings')
 with p.expect_download() as d:p.locator('[data-runtime=export]').click()
 d.value.save_as(str(out/'test-backup.json')); data=json.loads((out/'test-backup.json').read_text());assert len(data['patients'])==2
 p.locator('#import-file').set_input_files(str(out/'test-backup.json'));p.wait_for_selector('[data-runtime=import-add]');p.locator('[data-runtime=import-add]').click();saved();assert p.evaluate('collection.patients.length')==4
 # Full restore replaces collection after explicit confirmation.
 go('settings');p.locator('#import-file').set_input_files(str(out/'test-backup.json'));p.wait_for_selector('[data-runtime=import-replace]');p.locator('[data-runtime=import-replace]').click();saved();assert p.evaluate('collection.patients.length')==2
 # Reject another application's backup and malformed clinical data without mutation.
 go('settings');before=p.evaluate('JSON.stringify(collection)');bad=json.loads(json.dumps(data));bad['patients'][0]['records'][0]['context']['metrics']['measuredProteinMg']=9999
 p.locator('#import-file').set_input_files({'name':'bad.json','mimeType':'application/json','buffer':json.dumps(bad).encode()});p.wait_for_timeout(100);assert p.locator('#import-error').inner_text();assert p.evaluate('JSON.stringify(collection)')==before
 # Persisted patient/date identity and offline operation.
 p.reload();p.wait_for_function('typeof state!=="undefined"&&state&&!loading');saved();assert p.evaluate('collection.patients.length')==2
 p.wait_for_function('navigator.serviceWorker.controller!==null');c.set_offline(True);p.reload();p.wait_for_function('typeof state!=="undefined"&&state&&!loading');go('recipes');assert p.locator('#screen').inner_text().find('РЕЦЕПТЫ')>=0;go('help');assert p.locator('a[href="tel:112"]').count()==1;c.set_offline(False)
 # Concurrent tabs: stale tab must stop, never overwrite the newer save.
 q=c.new_page();q.goto(os.environ.get('APP_URL','http://127.0.0.1:8028/em-yaytso/'));q.wait_for_function('typeof state!=="undefined"&&state&&!loading')
 go('profile');fill('patientName','Аня (обновлено)');p.locator('#patient-form button[type=submit]').click();saved()
 q.evaluate("state.name='Устаревшая вкладка';render('today')");q.evaluate('saveQueue');assert q.locator('#storage-error').is_visible();assert 'другой вкладке' in q.locator('#storage-error').inner_text();q.close()
 assert not errors,errors
 print('PASS: profiles, persisted plan, recipe selection/switch, full portions, reactions/review, backups, invalid import, offline, concurrency; no JS errors')
 b.close()
