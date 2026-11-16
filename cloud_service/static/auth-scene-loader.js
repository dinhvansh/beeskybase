(()=>{
 let scheduled=false,loaded=false;
 const media=matchMedia('(min-width:761px)');
 function start(){
  if(loaded||scheduled||!media.matches||!document.querySelector('.auth-scene'))return;
  scheduled=true;
  const load=()=>{
   scheduled=false;if(loaded||!media.matches||!document.querySelector('.auth-scene'))return;
   loaded=true;const script=document.createElement('script');script.src='/static/auth-scene.js?v=perf1';script.async=true;script.fetchPriority='low';
   script.onerror=()=>{loaded=false};document.head.append(script);
  };
  requestAnimationFrame(()=>{if('requestIdleCallback'in window)requestIdleCallback(load,{timeout:700});else setTimeout(load,100)});
 }
 new MutationObserver(start).observe(document.querySelector('#cloud-app'),{childList:true});
 media.addEventListener('change',start);start();
})();
