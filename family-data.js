/* Shared presentation only: each app keeps its own storage, identity and actions. */
'use strict';
window.FamilyData={
 standalone:()=>matchMedia('(display-mode: standalone)').matches||navigator.standalone===true,
 refresh(count,name){
  const root=document.querySelector('.family-data');if(!root)return;
  if(count!==undefined)root.querySelector('[data-family-count]').textContent='Пациентов: '+count+'.';
  if(name!==undefined)root.querySelector('[data-family-delete-name]').textContent=name;
  const ua=navigator.userAgent,ios=/iPhone|iPad|iPod/.test(ua)||navigator.platform==='MacIntel'&&navigator.maxTouchPoints>1;
  root.querySelector('[data-family-install-help]').textContent=this.standalone()?'Приложение установлено.':ios?'На iPhone или iPad откройте сайт в Safari → «Поделиться» → «На экран Домой».':/Android/.test(ua)?'На Android откройте сайт в Chrome → меню ⋮ → «Установить приложение» или «Добавить на главный экран».':'В Chrome или Edge откройте меню браузера и выберите установку приложения, если она доступна. Дневником можно пользоваться и в браузере.';
  if(this.standalone())root.querySelectorAll('[id$="install"],[data-runtime="install"]').forEach(b=>b.hidden=true);
 },
 watchStorage(sourceSelector){const source=document.querySelector(sourceSelector);if(!source)return;const sync=()=>{const target=document.querySelector('[data-family-save]');if(target){const value=source.textContent.trim()||'Записи сохранены на этом устройстве.';if(target.textContent!==value)target.textContent=value;}};new MutationObserver(sync).observe(source,{childList:true,subtree:true,characterData:true});this.syncStorage=sync;sync();}
};
window.addEventListener('appinstalled',()=>FamilyData.refresh());
matchMedia('(display-mode: standalone)').addEventListener('change',()=>FamilyData.refresh());
