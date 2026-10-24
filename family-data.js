/* Shared presentation only: each app keeps its own storage, identity and actions. */
'use strict';
window.FamilyData={
 selectedPatient:()=>document.querySelector('[data-family-delete-patient]')?.value,
 standalone:()=>matchMedia('(display-mode: standalone)').matches||navigator.standalone===true,
 refresh(count,name,patients,activeId){
  const root=document.querySelector('.family-data');if(!root)return;
  if(count!==undefined)root.querySelector('[data-family-count]').textContent='Пациентов: '+count+'.';
  const select=root.querySelector('[data-family-delete-patient]');
  if(select&&patients){const selected=select.value;select.replaceChildren(...patients.map(p=>new Option(p.label,p.id)));select.value=patients.some(p=>p.id===selected)?selected:activeId;}
  root.querySelector('[data-family-install-help]').textContent=this.standalone()?'Приложение установлено.':'Дневником можно пользоваться в браузере или установить его на главный экран устройства. В Chrome и Edge на компьютере установка доступна через меню браузера, если он её поддерживает.';
  if(this.standalone())root.querySelectorAll('[id$="install"],[data-runtime="install"]').forEach(b=>b.hidden=true);
 },
 watchStorage(sourceSelector){const source=document.querySelector(sourceSelector);if(!source)return;const sync=()=>{const target=document.querySelector('[data-family-save]');if(target){const value=source.textContent.trim()||'Записи сохранены на этом устройстве.';if(target.textContent!==value)target.textContent=value;}};new MutationObserver(sync).observe(source,{childList:true,subtree:true,characterData:true});this.syncStorage=sync;sync();}
};
window.addEventListener('appinstalled',()=>FamilyData.refresh());
matchMedia('(display-mode: standalone)').addEventListener('change',()=>FamilyData.refresh());
