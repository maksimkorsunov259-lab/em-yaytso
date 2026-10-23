/* Shared, non-destructive About overlay. The diary remains mounted underneath. */
'use strict';
const familyScrollLocks=new Set();let familyScrollOverflow='';
window.FamilyAbout={layout({name,tagline,icon,description,details='',dataDetails='',actions='',author,rightsExtra}){
 // All HTML arguments are application-owned copy, never diary input.
 const body=document.createElement('div');body.className='family-about-layout';
 body.innerHTML=`<div class="family-about-brand"><img width="72" height="72" alt=""><div><strong class="family-about-name"></strong><p class="family-about-tagline"></p></div></div><section class="family-about-section" data-about-section="purpose"><h3>Чем помогает приложение</h3>${description}<p class="family-about-note">Приложение не проходило независимую клиническую валидацию.</p>${details}</section><section class="family-about-section" data-about-section="storage"><h3>Дневник на вашем устройстве</h3><p>Без регистрации и облачной синхронизации. Записи не передаются автору приложения.</p>${dataDetails}${actions?'<div class="family-about-actions">'+actions+'</div>':''}</section><section class="family-about-section" data-about-section="rights"><h3>Авторские права</h3><p class="family-about-note">© 2026 Коршунов Максим Александрович. Все права защищены.</p><p class="family-about-note">Уведомление относится к материалам приложения, права на которые принадлежат Коршунову Максиму Александровичу. Их копирование и распространение допускаются с разрешения правообладателя, кроме случаев, предусмотренных законом.</p><p class="family-about-note"></p></section>`;
 body.querySelector('.family-about-brand img').src=icon;body.querySelector('.family-about-brand img').alt='Иконка '+name;
 body.querySelector('.family-about-name').textContent=name;body.querySelector('.family-about-tagline').textContent=tagline;
 body.querySelector('[data-about-section="rights"] p:last-child').textContent=rightsExtra||'Права на сторонние материалы, включая клинические рекомендации, публикации и рецепты, принадлежат соответствующим правообладателям. Ссылки на источники не означают одобрения приложения профессиональными обществами.';
 if(author){const copy=author.cloneNode(true);for(const node of [copy,...copy.querySelectorAll('[class]')])for(const cls of [...node.classList])if(/^(em|pf)-(author|support)/.test(cls)){node.classList.remove(cls);node.classList.add(cls.replace(/^(em|pf)-/,'family-'));}for(const [oldClass,newClass] of [['em-note','family-author-note'],['em-small','family-author-small'],['em-eyebrow','family-author-eyebrow']])for(const node of copy.querySelectorAll('.'+oldClass)){node.classList.remove(oldClass);node.classList.add(newClass);}copy.className='family-about-section family-author';copy.dataset.aboutSection='author';body.append(copy);}
 return body;
},
create({root,dialog=null,trigger,build,activate,navigate,id='family-about',title='О приложении',returnLabel}){
 const existing=Boolean(dialog);dialog=dialog||document.createElement('dialog');
 dialog.classList.add('family-about');if(!dialog.id)dialog.id=id;
 const oldButton=existing?dialog.querySelector('button'):null,oldHeading=existing?dialog.querySelector('h2'):null;
 const content=document.createElement('div');content.className='family-about-content';
 if(existing){oldButton?.remove();oldHeading?.remove();content.append(...dialog.childNodes);}
 const bar=document.createElement('div');bar.className='family-about-bar';
 const closeButton=oldButton||document.createElement('button');closeButton.type='button';closeButton.textContent='← Вернуться';closeButton.dataset.familyAboutClose='';closeButton.autofocus=true;
 const heading=oldHeading||document.createElement('h2');heading.id=heading.id||(id+'-title');heading.textContent=title;
 bar.append(heading,closeButton);dialog.replaceChildren(bar,content);dialog.setAttribute('aria-labelledby',heading.id);
 if(!existing)root.append(dialog);
 let origin=null,scroll=null,restore=true,overflow='',generation=0;
 const api={get isOpen(){return dialog.open;},open(opener=document.activeElement){
  if(dialog.open)return;
  closeButton.textContent=returnLabel?returnLabel(dialog):'← Вернуться';
  if(build){const node=build();content.replaceChildren(node);activate?.(content);}
  generation++;origin=opener;scroll={x:window.scrollX,y:window.scrollY};restore=true;overflow=document.documentElement.style.overflow;if(!familyScrollLocks.size)familyScrollOverflow=overflow;familyScrollLocks.add(dialog);
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
  familyScrollLocks.delete(dialog);document.documentElement.style.overflow=familyScrollLocks.size?'hidden':familyScrollOverflow;
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
