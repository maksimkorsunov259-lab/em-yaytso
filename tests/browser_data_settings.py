"""Shared data/install UI and real backup lifecycle on isolated synthetic diaries."""
import os,json,tempfile
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
APP=os.environ.get('APP_NAME',Path(__file__).resolve().parents[1].name)
DY=APP=='dyshu-diary';MO=APP=='em-moloko';prefix='pf-' if DY else 'em-' if MO else ''
with sync_playwright() as pw,tempfile.TemporaryDirectory() as tmp:
 b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);c=b.new_context(viewport={'width':390,'height':844});p=c.new_page();errors=[];accept=[True];p.on('pageerror',lambda e:errors.append(str(e)));p.on('dialog',lambda d:d.accept() if accept[0] else d.dismiss())
 p.goto(os.environ.get('APP_URL','http://127.0.0.1:8055/'+APP+'/'))
 def ready():
  if DY:expect(p.locator('#pf-loading')).to_be_hidden();p.evaluate('DyshuUpdate.prepare()')
  elif not MO:p.wait_for_function('!loading&&!pendingWrites')
 def settings():
  ready()
  if DY:
   if not p.locator('#pf-data-panel').is_visible():p.locator('.pf-tabs [data-screen=settings]').click();p.locator('#pf-settings-panel [data-open-data]').click()
  elif MO:
   if not p.locator('[data-panel=settings]').is_visible():p.locator('.em-nav [data-view=more]').click();p.locator('[data-panel=more] [data-view=settings]').click()
  else:p.evaluate("render('settings')");ready()
  expect(p.locator('.family-data')).to_be_visible()
 def action(name):
  ids={'export':'backup' if DY else 'export','import-add':'import-add','import-replace':'import-confirm' if DY else 'import-apply','import-cancel':'import-cancel','delete-patient':'delete-patient','check-update':'check-update'}
  return p.locator('#'+prefix+ids[name]) if DY or MO else p.locator('.family-data [data-runtime='+name+']')
 def file(raw):p.locator('#'+prefix+('import' if DY else 'import-file')).set_input_files({'name':'backup.json','mimeType':'application/json','buffer':json.dumps(raw).encode()})
 def download():
  with p.expect_download() as dl:action('export').click()
  path=Path(tmp)/'copy.json';dl.value.save_as(path);return json.loads(path.read_text())
 def count(raw):return len(raw['profiles'] if DY else raw['patients'])
 settings();baseline=download();n=count(baseline)
 assert p.locator('[data-family-section]').evaluate_all('(els)=>els.map(e=>e.dataset.familySection)')==['device','install','update','backup']
 assert p.locator('[data-family-section=device] [data-family-delete-patient]').count()==1
 expect(p.locator('[data-family-section=device]')).to_contain_text('хранятся только на вашем устройстве')
 expect(p.locator('[data-family-install-android]')).to_contain_text('Chrome')
 expect(p.locator('[data-family-install-ios]')).to_contain_text('Safari')
 for w in [320,390,1440]:
  p.set_viewport_size({'width':w,'height':900});assert not p.evaluate('document.documentElement.scrollWidth>innerWidth'),(APP,w);p.screenshot(path='/tmp/data-'+APP+'-'+str(w)+'.png',full_page=True)
 file({'app':'wrong-app'});expect(action('import-add')).to_be_hidden();assert count(download())==n
 file(baseline);expect(action('import-add')).to_be_visible();action('import-cancel').click();expect(action('import-add')).to_be_hidden();assert count(download())==n
 file(baseline);expect(action('import-add')).to_be_visible();accept[0]=False;action('import-replace').click();assert count(download())==n;accept[0]=True
 action('import-add').click();settings();merged=download();assert count(merged)==2*n,(APP,merged)
 # Distinct patient identities; none of the pre-existing data is changed.
 if DY:
  for key in baseline['profiles']:assert merged['profiles'][key]==baseline['profiles'][key];assert merged['records'][key]==baseline['records'][key]
 else:
  assert len({x['id'] for x in merged['patients']})==2*n
  for old in baseline['patients']:assert next(x for x in merged['patients'] if x['id']==old['id'])==old
 # Delete a patient other than the active diary; selecting a target must not switch diaries.
 header=p.locator('#pf-profile' if DY else '#em-patient-select' if MO else '#patient-select')
 active=header.input_value();ids=list(merged['profiles']) if DY else [x['id'] for x in merged['patients']]
 target=next(id for id in ids if id!=active)
 p.locator('[data-family-delete-patient]').select_option(target);expect(header).to_have_value(active)
 accept[0]=False;action('delete-patient').click();assert count(download())==2*n;expect(p.locator('[data-family-delete-patient]')).to_have_value(target)
 accept[0]=True;action('delete-patient').click();settings();after=download();assert count(after)==2*n-1
 remaining=list(after['profiles']) if DY else [x['id'] for x in after['patients']]
 assert target not in remaining and active in remaining;expect(header).to_have_value(active)
 if DY:
  for key in remaining:assert after['profiles'][key]==merged['profiles'][key];assert after['records'][key]==merged['records'][key]
 else:
  for old in after['patients']:assert old==next(x for x in merged['patients'] if x['id']==old['id'])
 file(baseline);expect(action('import-replace')).to_be_visible();action('import-replace').click();settings();restored=download();assert count(restored)==n
 if DY:
  legacy=json.loads(json.dumps(baseline));legacy['version']=3;file(legacy);action('import-replace').click();settings();assert download()['records']==baseline['records']
 # Removing the active and last diary leaves a usable empty profile and preserves other patients.
 for _ in range(n):
  active=header.input_value();p.locator('[data-family-delete-patient]').select_option(active);action('delete-patient').click();settings()
 remaining=download();assert count(remaining)==1
 if DY:assert not any(remaining['records'].values())
 elif MO:assert not remaining['patients'][0]['diary']['records']
 else:assert not remaining['patients'][0]['records' if APP=='em-yaytso' else 'meals']
 file(baseline);expect(action('import-replace')).to_be_visible();action('import-replace').click();settings()
 # Check updates offline without deleting caches or records.
 p.evaluate('navigator.serviceWorker.ready');p.reload();ready();settings();c.set_offline(True);action('check-update').click();expect(p.locator('#'+prefix+'update-check-status')).to_contain_text('интернет');p.reload();ready();settings();assert count(download())==n
 assert not errors,errors;c.close();b.close()
print('PASS:',APP,'common four blocks and scoped patient selection, mobile/desktop, wrong-file rejection, cancel/merge/replace/delete with isolation, legacy backup and offline.')
