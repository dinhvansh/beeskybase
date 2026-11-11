/* Apply before first paint; preference is independent of demo account data. */
(()=>{
 const key='beesky-color-theme',system=matchMedia('(prefers-color-scheme: dark)');
 let preference=null;
 try{const value=localStorage.getItem(key);if(['light','dark'].includes(value))preference=value}catch{}
 const sun='<circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1.5 1.5m11 11L19 19M5 19l1.5-1.5m11-11L19 5"/>';
 const moon='<path d="M20.7 13A9 9 0 0 1 11 3.3 9 9 0 1 0 20.7 13Z"/>';
 function syncButton(){
  if(!document.body)return;
  const target=document.querySelector('.top-actions')||document.querySelector('.auth-layout')||document.querySelector('.onboarding')||document.querySelector('.reviewbar nav');
  if(!target)return;
  let button=document.querySelector('[data-theme-toggle]');
  if(!button){button=document.createElement('button');button.type='button';button.className='icon-btn theme-toggle';button.dataset.themeToggle='';}
  if(button.parentElement!==target)target.prepend(button);
  const dark=document.documentElement.dataset.theme==='dark';
  const label=dark?'Chuyển sang giao diện sáng':'Chuyển sang giao diện tối';
  if(button.getAttribute('aria-label')!==label){button.setAttribute('aria-label',label);button.title=label;button.setAttribute('aria-pressed',String(dark));button.innerHTML=`<svg class="icon" viewBox="0 0 24 24" aria-hidden="true">${dark?sun:moon}</svg>`;}
 }
 function apply(theme){document.documentElement.dataset.theme=theme;document.documentElement.style.colorScheme=theme;document.dispatchEvent(new CustomEvent('beesky:theme',{detail:theme}));syncButton()}
 apply(preference||(system.matches?'dark':'light'));
 system.addEventListener('change',()=>{if(!preference)apply(system.matches?'dark':'light')});
 addEventListener('storage',event=>{if(event.key!==key)return;preference=['light','dark'].includes(event.newValue)?event.newValue:null;apply(preference||(system.matches?'dark':'light'))});
 document.addEventListener('click',event=>{if(!event.target.closest('[data-theme-toggle]'))return;preference=document.documentElement.dataset.theme==='dark'?'light':'dark';try{localStorage.setItem(key,preference)}catch{}apply(preference)});
 document.addEventListener('DOMContentLoaded',()=>{syncButton();new MutationObserver(syncButton).observe(document.querySelector('#app'),{childList:true,subtree:true})});
})();
