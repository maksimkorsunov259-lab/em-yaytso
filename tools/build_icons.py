"""Render standard icon sizes from the edited cutout; keep the supplied original archived.

The master was edited with image_gen to remove the exterior white canvas and shadow.
The renderer removes the outer 1% edge fringe and uses the family's rounded-square
mask. It does not generate new artwork. Apple Touch Icon gets an opaque cream
backing because iOS may render transparent pixels black.
"""
import base64,os
from pathlib import Path
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1]
source='data:image/png;base64,'+base64.b64encode((root/'assets/icon-rounded-master.png').read_bytes()).decode()
with sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH','/usr/bin/chromium'),args=['--no-sandbox'])
 page=browser.new_page()
 for size in [180,192,512]:
  result=page.evaluate('''async ({source,size})=>{const image=new Image();image.src=source;await image.decode();const canvas=document.createElement('canvas');canvas.width=canvas.height=size;const c=canvas.getContext('2d');if(size===180){c.fillStyle='#fff7e8';c.fillRect(0,0,size,size);}c.beginPath();c.roundRect(0,0,size,size,size*2/7);c.clip();c.imageSmoothingEnabled=true;c.imageSmoothingQuality='high';const dx=image.naturalWidth*.01,dy=image.naturalHeight*.01;c.drawImage(image,dx,dy,image.naturalWidth-2*dx,image.naturalHeight-2*dy,0,0,size,size);return canvas.toDataURL('image/png').split(',')[1];}''',{'source':source,'size':size})
  (root/f'assets/icon-rounded-{size}.png').write_bytes(base64.b64decode(result))
 browser.close()
print('Rounded-square icons: 180, 192, 512; uploaded original preserved')
