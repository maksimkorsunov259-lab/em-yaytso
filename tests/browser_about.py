"""About opens over the current diary, preserving unsaved input and return position."""
import os,tempfile
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
APP=Path(__file__).resolve().parents[1].name
URL=os.environ.get('APP_URL','http://127.0.0.1:8040/'+APP+'/')
with sync_playwright() as pw,tempfile.TemporaryDirectory() as tmp:
 c=pw.chromium.launch_persistent_context(tmp,executable_path=os.environ.get('CHROMIUM_PATH','/usr/bin/chromium'),headless=True,args=['--no-sandbox'],viewport={'width':390,'height':844})
 p=c.new_page();errors=[];prompts=[];accept=[False]
 p.on('pageerror',lambda e:errors.append(str(e)))
 def answer(d):
  prompts.append(d.type);d.accept() if accept[0] else d.dismiss()
 p.on('dialog',answer);p.goto(URL);p.wait_for_selector('.family-about',state='attached');p.evaluate('navigator.serviceWorker.ready')
 if APP=='dyshu-diary':
  p.locator('#pf-edit-profile').click();field=p.locator('#pf-patient-name');root='#pf-demo';trigger=p.locator('[data-open-about]').first
 elif APP=='em-moloko':
  p.locator('#em-profile-button').click();field=p.locator('#em-child-name');root='#em-demo';trigger=p.locator('[data-view=about]').first
 elif APP=='em-yaytso':
  p.wait_for_function('!loading');p.evaluate("render('profile')");field=p.locator('[name=patientName]');root='#em-demo';trigger=p.locator('[data-go=about]').first
 else:
  p.wait_for_function('!loading&&!pendingWrites');p.evaluate("render('profile')");field=p.locator('[name=name]');root='.device';trigger=p.locator('[data-go=about]').first
 field.fill('Несохранённое имя');dialog=p.locator('dialog.family-about');before=field.evaluate('(e)=>{e.dataset.aboutSentinel="keep";return e.value}')
 for width in [320,390,1440]:
  p.set_viewport_size({'width':width,'height':900});trigger.scroll_into_view_if_needed();position=p.evaluate('window.scrollY');trigger.click();expect(dialog).to_be_visible();assert dialog.evaluate('(d)=>d.matches(":modal")');assert not prompts,prompts
  assert field.get_attribute('data-about-sentinel')=='keep';assert field.input_value()==before
  assert not dialog.evaluate('(d)=>d.scrollWidth>d.clientWidth'),width
  assert dialog.get_attribute('aria-labelledby');assert dialog.locator('a[href*="taplink.cc"]').count()>0
  assert dialog.locator('a[href*="prodoctorov.ru"]').count()>0
  p.keyboard.press('Shift+Tab');assert dialog.evaluate('(d)=>d.contains(document.activeElement)')
  p.keyboard.press('Tab');expect(dialog.locator('[data-family-about-close]')).to_be_focused()
  for _ in range(12):
   p.keyboard.press('Tab');assert dialog.evaluate('(d)=>d.contains(document.activeElement)')
  p.keyboard.press('Escape');expect(dialog).not_to_be_visible();expect(trigger).to_be_focused();assert abs(p.evaluate('window.scrollY')-position)<3;assert field.input_value()==before
  trigger.click();expect(dialog).to_be_visible();assert dialog.evaluate('(d)=>d.scrollTop')==0
  dialog.locator('[data-family-about-close]').click();expect(dialog).not_to_be_visible();expect(trigger).to_be_focused();assert field.input_value()==before
 # Navigating from the overlay retains the existing unsaved-change confirmation.
 if APP!='dyshu-diary':
  trigger.click();destination=dialog.locator('[data-go=settings],[data-view=settings]');destination.click();expect(dialog).to_be_visible();assert prompts==['confirm'];assert field.input_value()==before
  accept[0]=True;destination.click();expect(dialog).not_to_be_visible();assert prompts==['confirm','confirm']
  if APP in ['em-prikorm','em-yaytso']:assert p.evaluate('view')=='settings'
  else:assert p.locator('[data-panel=settings]').is_visible()
  accept[0]=False
 # Reload the cached application offline and use About again.
 accept[0]=True;p.reload();p.wait_for_selector('.family-about',state='attached');p.evaluate('navigator.serviceWorker.ready');c.set_offline(True);p.reload();p.wait_for_selector('.family-about',state='attached')
 trigger=p.locator('[data-open-about],[data-view=about],[data-go=about]').first;trigger.click();expect(dialog).to_be_visible();assert dialog.locator('[data-family-about-close]').is_visible();assert p.evaluate("document.documentElement.style.overflow")=='hidden';dialog.locator('[data-family-about-close]').click();expect(dialog).not_to_be_visible();assert p.evaluate("document.documentElement.style.overflow")!='hidden'
 assert not errors,errors;c.close()
print('PASS:',APP,'About overlay: unsaved form identity/values, focus trap, Escape/button return, scroll restoration, links, cancelled/confirmed navigation, responsive widths and offline.')
