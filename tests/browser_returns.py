"""Return captions follow the actual source route, including nested information pages."""
import os,tempfile
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
APP=Path(__file__).resolve().parents[1].name
URL=os.environ.get('APP_URL','http://127.0.0.1:8055/'+APP+'/')
with sync_playwright() as pw,tempfile.TemporaryDirectory() as tmp:
 c=pw.chromium.launch_persistent_context(tmp,executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'],viewport={'width':390,'height':844});p=c.new_page();errors=[];accept=[False];prompts=[]
 p.on('pageerror',lambda e:errors.append(str(e)))
 def answer(d):
  prompts.append(d.type);d.accept() if accept[0] else d.dismiss()
 p.on('dialog',answer);p.goto(URL);p.wait_for_function('!loading&&!pendingWrites')
 def render(view):p.evaluate('(v)=>render(v)',view)
 def back(target,label):
  button=p.locator('#screen button.back').first;expect(button).to_contain_text(label);assert button.get_attribute('data-go')==target;button.click();assert p.evaluate('view')==target
 guide='readiness' if APP=='em-prikorm' else 'guide'
 render('today');render(guide);back('today','Сегодня')
 render('more');p.locator('#screen [data-go="'+guide+'"]').click();back('more','Памятка')
 if APP=='em-prikorm':
  render('foods');p.locator('#screen [data-food]').first.click();back('foods','Продукты')
  render('today');p.evaluate("selectedFood='egg';render('food')");back('today','Сегодня')
  render('diary');p.locator('#screen [data-go=report]').click();back('diary','Дневник')
  render('today');p.locator('[data-action=choking-help]').first.click();expect(p.locator('#triage-dialog [data-action=close-triage]')).to_have_text('← Сегодня');p.locator('[data-action=close-triage]').click()
 else:
  render('more');p.locator('#screen [data-go=recipes]').click();p.locator('#screen [data-recipe]').first.click();back('recipes','Рецепты и продукты');back('more','Памятка')
  render('today');render('recipe');back('today','Сегодня')
  render('recipes');p.locator('#screen [data-go=doctorTable]').click();back('recipes','Рецепты и продукты')
  render('diary');render('report');back('diary','Дневник')
 render('diary');render('profile');field=p.locator('[name=name]' if APP=='em-prikorm' else '[name=patientName]');field.fill('Черновик');p.locator('#screen .back').first.click();assert p.evaluate('view')=='profile';expect(field).to_have_value('Черновик');assert prompts
 for width in [320,390,1440]:
  p.set_viewport_size({'width':width,'height':900})
  for overlay,trigger in [('family-about','about'),('family-help','help')]:
   p.locator('[data-go="'+trigger+'"]').first.click();dialog=p.locator('#'+overlay);expect(dialog).to_be_visible();expect(dialog.locator('[data-family-about-close]')).to_have_text('← Профиль');assert not dialog.evaluate('d=>d.scrollWidth>d.clientWidth');dialog.locator('[data-family-about-close]').click();expect(field).to_have_value('Черновик')
 accept[0]=True;back('diary','Дневник')
 p.wait_for_function('!pendingWrites');p.evaluate('navigator.serviceWorker.ready');p.reload();p.wait_for_function('!loading');c.set_offline(True);p.reload();p.wait_for_function('!loading');render('today');render(guide);back('today','Сегодня');assert not errors,errors;c.close()
print('PASS:',APP,'contextual and nested returns, concise captions, unsaved-form guard, overlay drafts, responsive/offline.')
