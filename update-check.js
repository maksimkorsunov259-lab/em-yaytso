/* Shared by the diary and the independent update page. No diary storage access. */
'use strict';
window.AppUpdates={
 waitForInstall(registration,timeout=20000){
  const worker=registration.installing;
  if(!worker)return Promise.resolve();
  return new Promise((resolve,reject)=>{
   let timer;
   const finish=error=>{clearTimeout(timer);worker.removeEventListener('statechange',check);error?reject(error):resolve();};
   const check=()=>{if(worker.state==='installed'||worker.state==='activated')finish();else if(worker.state==='redundant')finish(new Error('Не удалось загрузить все файлы обновления. Повторите проверку с интернетом.'));};
   worker.addEventListener('statechange',check);
   timer=setTimeout(()=>finish(new Error('Загрузка обновления не завершилась. Проверьте подключение и повторите попытку.')),timeout);check();
  });
 },
 async check(registration){try{await registration.update();}catch{throw new Error('Не удалось получить обновление с сайта. Проверьте подключение и повторите попытку.');}await this.waitForInstall(registration);return Boolean(registration.waiting);}
};
