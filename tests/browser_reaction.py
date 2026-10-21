"""Reaction help remains available without discarding an unfinished diary form."""
import os, tempfile
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
APP=Path(__file__).resolve().parents[1].name
URL=os.environ.get('APP_URL','http://127.0.0.1:8040/'+APP+'/')
with sync_playwright() as pw, tempfile.TemporaryDirectory() as tmp:
 c=pw.chromium.launch_persistent_context(tmp,executable_path=os.environ.get('CHROMIUM_PATH','/usr/bin/chromium'),headless=True,args=['--no-sandbox'],viewport={'width':390,'height':844})
 p=c.new_page(); errors=[]; prompts=[]; accept=[False]
 p.on('pageerror',lambda e:errors.append(str(e)))
 def answer(d):
  prompts.append(d.type)
  d.accept() if accept[0] else d.dismiss()
 p.on('dialog',answer);p.goto(URL);p.wait_for_selector('#family-help',state='attached');p.evaluate('navigator.serviceWorker.ready')
 if APP=='em-moloko':
  p.locator('#em-profile-button').click();field=p.locator('#em-child-name');trigger=p.locator('[data-view=help]').first
 elif APP=='em-yaytso':
  p.wait_for_function('!loading');p.evaluate("render('profile')");field=p.locator('[name=patientName]');trigger=p.locator('[data-go=help]').first
 else:
  p.wait_for_function('!loading&&!pendingWrites');p.evaluate("render('profile')");field=p.locator('[name=name]');trigger=p.locator('[data-go=help]').first
 field.fill('Не сохранено');field.evaluate('(e)=>e.dataset.sentinel="keep"');dialog=p.locator('#family-help')
 for width in [320,390,1440]:
  p.set_viewport_size({'width':width,'height':900});trigger.scroll_into_view_if_needed();position=p.evaluate('scrollY');trigger.click();expect(dialog).to_be_visible()
  assert dialog.evaluate('(d)=>d.matches(":modal")');assert not prompts,prompts
  assert field.input_value()=='Не сохранено' and field.get_attribute('data-sentinel')=='keep'
  expect(dialog.locator('#family-help-title')).to_have_text('Если появилась реакция')
  assert dialog.locator('a[href="tel:112"]').count()>0
  assert dialog.locator('a[href*="taplink.cc"]').count()>0
  assert not dialog.evaluate('(d)=>d.scrollWidth>d.clientWidth'),width
  p.keyboard.press('Escape');expect(dialog).not_to_be_visible();expect(trigger).to_be_focused()
  assert abs(p.evaluate('scrollY')-position)<3
  trigger.click();dialog.locator('[data-family-about-close]').click();expect(dialog).not_to_be_visible();expect(trigger).to_be_focused()
  assert field.input_value()=='Не сохранено'
 trigger.click();destination=dialog.locator('[data-go=diary],[data-view=diary]').first;destination.click();expect(dialog).to_be_visible()
 assert prompts==['confirm'] and field.input_value()=='Не сохранено'
 accept[0]=True;destination.click();expect(dialog).not_to_be_visible();assert prompts==['confirm','confirm']
 if APP=='em-prikorm':
  trigger.click();dialog.locator('[data-go=symptom]').click();expect(dialog).not_to_be_visible();assert p.evaluate('view')=='symptom'
  p.locator('[name=note]').fill('Наблюдение');trigger.click();dialog.locator('[data-go=symptom]').click();assert p.locator('[name=note]').input_value()=='Наблюдение'
 # Fresh offline launch still exposes the emergency instructions.
 p.reload();p.wait_for_selector('#family-help',state='attached');p.evaluate('navigator.serviceWorker.ready');c.set_offline(True);p.reload();p.wait_for_selector('#family-help',state='attached')
 p.locator('[data-view=help],[data-go=help]').first.click();expect(dialog).to_be_visible();assert dialog.locator('a[href="tel:112"]').count()>0
 dialog.locator('[data-family-about-close]').click();expect(dialog).not_to_be_visible();p.wait_for_function('document.documentElement.style.overflow!=="hidden"')
 assert not errors,errors;c.close()
print('PASS:',APP,'reaction overlay, emergency links, draft identity, responsive widths, return/focus/scroll, navigation guards and offline help.')
