"""Sticky patient/navigation stack, including an update appearing mid-scroll."""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
APP=os.environ.get('APP_NAME',Path(__file__).resolve().parents[1].name)
URL=os.environ.get('APP_URL','http://127.0.0.1:8055/'+APP+'/')
config={
 'dyshu-diary':('.pf-patient-switch','.pf-tabs','#pf-update-banner','#pf-patients','[data-screen=guide]'),
 'em-moloko':('.em-patient-switch','.em-nav','#em-update-bar','[data-view=patients]','[data-view=more]'),
 'em-yaytso':('.patient-bar','.em-nav','#update-banner','[data-go=patients]','[data-go=more]'),
 'em-prikorm':('.patient','.nav','#update-banner','[data-go=patients]','[data-go=more]'),
}
with sync_playwright() as pw:
 b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 c=b.new_context(viewport={'width':390,'height':844});p=c.new_page();errors=[]
 p.on('pageerror',lambda e:errors.append(str(e)));p.on('dialog',lambda d:d.dismiss());p.goto(URL)
 if APP=='dyshu-diary':expect(p.locator('#pf-loading')).to_be_hidden();p.evaluate('DyshuUpdate.prepare()')
 elif APP in ['em-yaytso','em-prikorm']:p.wait_for_function('!loading&&!pendingWrites')
 patient,nav,banner,patients,guide=config[APP];stack=p.locator('.family-topbar');patient=p.locator(patient);nav=p.locator(nav);banner=p.locator(banner)
 nav.locator(guide).click();p.evaluate('navigator.serviceWorker.ready');p.wait_for_timeout(500)
 def clickable(el):
  assert el.evaluate('e=>{const r=e.getBoundingClientRect();return e.contains(document.elementFromPoint(r.x+r.width/2,r.y+r.height/2))}'),(el,p.viewport_size,el.evaluate('e=>{const r=e.getBoundingClientRect();return [r.toJSON(),e.hidden,getComputedStyle(e).display,document.elementFromPoint(r.x+r.width/2,r.y+r.height/2)?.outerHTML]}'))
 for width,height in [(320,640),(390,844),(1440,900),(844,390)]:
  p.set_viewport_size({'width':width,'height':height})
  for visible in [False,True,False]:
   p.evaluate('scrollTo(0,700)')
   if APP in ['em-yaytso','em-prikorm']:p.evaluate('(v)=>{reloadReady=v;refreshUpdateUI()}',visible)
   banner.evaluate('(e,v)=>{e.hidden=!v;e.querySelector("button").hidden=!v}',visible)
   for y in [1100,450]:
    p.evaluate('(y)=>scrollTo(0,y)',y);p.wait_for_timeout(100)
    s=stack.bounding_box();pa=patient.bounding_box();n=nav.bounding_box()
    assert abs(s['y'])<2,(APP,width,s)
    assert n['y']>=pa['y']+pa['height']-1,(pa,n)
    assert n['y']+n['height']<height,(APP,width,n)
    assert not p.evaluate('document.documentElement.scrollWidth>innerWidth'),(APP,width)
    clickable(stack.locator(patients));clickable(nav.locator(guide))
    if visible:
     u=banner.bounding_box();assert abs(u['y'])<2;assert pa['y']>=u['y']+u['height']-1
     clickable(banner.locator('button'))
  p.screenshot(path='/tmp/sticky-'+APP+'-'+str(width)+'.png')
 # Patient action remains functional while scrolled.
 stack.locator(patients).click()
 if APP=='dyshu-diary':expect(p.locator('#pf-patients-panel')).to_be_visible()
 elif APP=='em-moloko':expect(p.locator('[data-panel=patients]')).to_be_visible()
 else:assert p.evaluate('view')=='patients'
 nav.locator(guide).click();banner.evaluate('e=>e.hidden=false')
 p.locator('[data-go=about], [data-view=about], [data-open-about]').first.click()
 expect(p.locator('dialog.family-about[open]')).to_be_visible();clickable(p.locator('dialog.family-about[open] [data-family-about-close]'));p.locator('dialog.family-about[open] [data-family-about-close]').click()
 p.emulate_media(media='print');expect(stack).to_be_hidden();p.emulate_media(media='screen')
 assert not errors,errors;c.close();b.close()
print('PASS:',APP,'patient/navigation/update stack, scroll both ways, 320/390/1440/landscape, clickable controls, overlay stacking and print.')
