/* Shared, non-destructive About overlay. The diary remains mounted underneath. */
'use strict';
window.FamilyAbout={create({root,dialog=null,trigger,build,activate,navigate}){
 const existing=Boolean(dialog);dialog=dialog||document.createElement('dialog');
 dialog.classList.add('family-about');if(!dialog.id)dialog.id='family-about';
 const oldButton=existing?dialog.querySelector('button'):null,oldHeading=existing?dialog.querySelector('h2'):null;
 const content=document.createElement('div');content.className='family-about-content';
 if(existing){oldButton?.remove();oldHeading?.remove();content.append(...dialog.childNodes);}
 const bar=document.createElement('div');bar.className='family-about-bar';
 const closeButton=oldButton||document.createElement('button');closeButton.type='button';closeButton.textContent='← Вернуться';closeButton.dataset.familyAboutClose='';closeButton.autofocus=true;
 const heading=oldHeading||document.createElement('h2');heading.id=heading.id||'family-about-title';heading.textContent='О приложении';
 bar.append(closeButton,heading);dialog.replaceChildren(bar,content);dialog.setAttribute('aria-labelledby',heading.id);
 if(!existing)root.append(dialog);
 let origin=null,scroll=null,restore=true,overflow='',generation=0;
 const api={get isOpen(){return dialog.open;},open(opener=document.activeElement){
  if(dialog.open)return;
  if(build){const node=build();content.replaceChildren(node);activate?.(content);}
  generation++;origin=opener;scroll={x:window.scrollX,y:window.scrollY};restore=true;overflow=document.documentElement.style.overflow;
  document.documentElement.style.overflow='hidden';dialog.showModal();dialog.scrollTop=0;closeButton.focus({preventScroll:true});
 },close(returnToOrigin=true){if(!dialog.open)return;restore=returnToOrigin;dialog.close();},dialog};
 dialog.addEventListener('keydown',event=>{
  if(event.key!=='Tab'||event.ctrlKey||event.metaKey||event.altKey)return;
  const items=[...dialog.querySelectorAll('button:not([disabled]),a[href],input:not([disabled]),select:not([disabled]),textarea:not([disabled]),summary,[tabindex]:not([tabindex="-1"])')].filter(el=>el.getClientRects().length&&!el.closest('[inert]'));
  const first=items[0],last=items.at(-1);
  if(event.shiftKey&&document.activeElement===first){event.preventDefault();last?.focus();}
  else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first?.focus();}
 });
 dialog.addEventListener('close',()=>{
  const token=generation,position=scroll,target=origin,shouldRestore=restore;
  document.documentElement.style.overflow=overflow;
  if(shouldRestore)requestAnimationFrame(()=>{if(token!==generation||dialog.open)return;target?.isConnected&&target.focus?.({preventScroll:true});if(position)window.scrollTo({left:position.x,top:position.y,behavior:'instant'});});
 });
 document.addEventListener('click',event=>{
  const button=event.target.closest('button');if(!button||button.disabled)return;
  if(button.matches(trigger)&&root.contains(button)){event.preventDefault();event.stopImmediatePropagation();api.open(button);return;}
  if(!dialog.contains(button))return;
  if(button.hasAttribute('data-family-about-close')){event.preventDefault();event.stopImmediatePropagation();api.close();return;}
  const destination=button.dataset.go||button.dataset.view;
  if(destination&&navigate){event.preventDefault();event.stopImmediatePropagation();navigate(destination);}
 },true);
 return api;
}};
