'use strict';
// One atomic snapshot with optimistic concurrency. Never overwrite another tab.
window.DiaryStore=(()=>{
 let db,revision=0;
 const open=()=>new Promise((resolve,reject)=>{
  const r=indexedDB.open('em-yaytso.diary.v1',1);
  r.onupgradeneeded=()=>r.result.createObjectStore('snapshots');
  r.onerror=()=>reject(r.error);r.onblocked=()=>reject(new Error('Закройте другие вкладки дневника и повторите.'));
  r.onsuccess=()=>{db=r.result;db.onversionchange=()=>db.close();resolve();};
 });
 async function read(){await open();return new Promise((resolve,reject)=>{const tx=db.transaction('snapshots','readonly'),r=tx.objectStore('snapshots').get('main');r.onerror=()=>reject(r.error);r.onsuccess=()=>{revision=r.result?.revision||0;resolve(r.result?.data||null);};});}
 function write(data){return new Promise((resolve,reject)=>{
  if(!db)return reject(new Error('Хранилище недоступно.'));
  const tx=db.transaction('snapshots','readwrite'),store=tx.objectStore('snapshots'),get=store.get('main');let conflict=false;
  get.onsuccess=()=>{if((get.result?.revision||0)!==revision){conflict=true;tx.abort();return;}store.put({revision:revision+1,data},'main');};
  tx.oncomplete=()=>{revision++;resolve();};tx.onabort=()=>reject(new Error(conflict?'Дневник изменён в другой вкладке. Скачайте копию несохранённых изменений и перезагрузите эту страницу.':(tx.error?.message||'Не удалось записать дневник.')));tx.onerror=()=>{};
 });}
 return {read,write};
})();
