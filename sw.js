const PREFIX='em-yaytso:'+new URL('./',self.location).pathname+':';
const CACHE=PREFIX+'5f0a69caf781';
const FILES=["./index.html", "./styles.css", "./app.css", "./family-ui.css", "./family-about.js", "./recipes.js", "./model.js", "./storage.js", "./app.js", "./runtime.js", "./manifest.webmanifest", "./assets/icon-original.png", "./assets/icon-rounded-180.png", "./assets/icon-rounded-192.png", "./assets/icon-rounded-512.png", "./assets/icon-rounded-master.png", "./assets/icon.svg", "./assets/image-177842a5a4de.png", "./assets/image-9bfbd99af1d3.png"];
self.addEventListener('install',event=>event.waitUntil((async()=>{const cache=await caches.open(CACHE);await cache.addAll(FILES.map(file=>new Request(new URL(file,self.location),{cache:'reload'})));})()));
self.addEventListener('activate',event=>event.waitUntil((async()=>{const keys=await caches.keys();await Promise.all(keys.filter(k=>k.startsWith(PREFIX)&&k!==CACHE).map(k=>caches.delete(k)));await self.clients.claim();})()));
self.addEventListener('message',event=>{if(event.data?.type==='ACTIVATE')self.skipWaiting();});
self.addEventListener('fetch',event=>{
 const url=new URL(event.request.url),base=new URL('./',self.location);
 if(event.request.method!=='GET'||url.origin!==base.origin||!url.pathname.startsWith(base.pathname))return;
 const relative=url.pathname.slice(base.pathname.length);
 if(!FILES.includes('./'+relative)&&relative!=='')return;
 event.respondWith((async()=>{const cache=await caches.open(CACHE);const key=new URL(relative===''?'./index.html':'./'+relative,self.location);const hit=await cache.match(key);return hit||fetch(event.request);})());
});
