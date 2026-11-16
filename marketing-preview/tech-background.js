(()=>{
  const bee=document.createElement('div');
  bee.className='ambient-bee';
  bee.setAttribute('aria-hidden','true');
  bee.innerHTML=`<div class="bee-glow"></div><svg viewBox="0 0 120 100" fill="none"><defs><linearGradient id="bee-gold" x1="27" y1="39" x2="60" y2="79" gradientUnits="userSpaceOnUse"><stop stop-color="#fff1ad"/><stop offset=".45" stop-color="#edc65a"/><stop offset="1" stop-color="#b68a31"/></linearGradient><linearGradient id="bee-dark" x1="61" y1="42" x2="80" y2="75" gradientUnits="userSpaceOnUse"><stop stop-color="#5e6257"/><stop offset="1" stop-color="#272f2b"/></linearGradient><linearGradient id="bee-glass" x1="45" y1="10" x2="60" y2="47" gradientUnits="userSpaceOnUse"><stop stop-color="white" stop-opacity=".95"/><stop offset="1" stop-color="#bedde3" stop-opacity=".5"/></linearGradient><clipPath id="bee-body"><ellipse cx="44" cy="60" rx="25" ry="19" transform="rotate(-12 44 60)"/></clipPath></defs><g class="bee-wing-back"><path d="M60 48 C44 35 47 8 61 13 C75 18 74 35 65 48" fill="url(#bee-glass)" stroke="#cfdee0"/></g><path d="M23 65 L12 69 L24 72" fill="#51594c"/><ellipse cx="44" cy="60" rx="25" ry="19" transform="rotate(-12 44 60)" fill="url(#bee-gold)"/><g clip-path="url(#bee-body)" stroke="url(#bee-dark)" stroke-width="9"><path d="M30 40 Q40 60 31 84 M49 37 Q62 58 52 82"/></g><ellipse cx="66" cy="55" rx="16" ry="18" fill="url(#bee-dark)"/><g class="bee-wing-front"><path d="M59 47 C39 43 27 19 39 14 C52 8 64 27 63 44" fill="url(#bee-glass)" stroke="#d4e4e7" stroke-width="1.2"/><path d="M42 21 Q52 30 58 42" stroke="white" stroke-opacity=".8"/></g><circle cx="82" cy="51" r="13" fill="url(#bee-dark)"/><path d="M82 39 Q82 30 88 29 M89 41 Q97 34 99 38" stroke="#646b5b" stroke-width="2" stroke-linecap="round"/><ellipse cx="87" cy="48" rx="3" ry="4" fill="#151e1d"/><circle cx="88" cy="46.5" r="1" fill="white"/><path d="M62 70 L66 78 L72 78 M73 68 L78 75 L83 73" stroke="#626a57" stroke-width="2" stroke-linecap="round"/><path d="M26 53 Q31 46 39 46" stroke="#fff4cb" stroke-width="2" stroke-linecap="round" opacity=".7"/></svg>`;
  document.body.append(bee);
  document.querySelectorAll('.portal-hero, #solutions, #products, #services, .split-hero, #toolkit, #scan, #start').forEach((section,index)=>{
    section.classList.add('tech-scene');
    const layer=document.createElement('div');
    layer.className='tech-background';
    layer.setAttribute('aria-hidden','true');
    layer.innerHTML=`<div class="tech-grid"></div><svg viewBox="0 0 1440 800" preserveAspectRatio="xMidYMid slice"><g class="tech-traces"><path d="M-40 190 H170 L235 255 H410 V360 H530"/><path d="M1480 520 H1260 L1195 455 H1080 V330 H950"/><path d="M80 840 V680 L160 600 H300"/><circle cx="410" cy="255" r="5"/><circle cx="1080" cy="455" r="5"/><circle cx="300" cy="600" r="4"/><circle cx="530" cy="360" r="4"/></g><g class="tech-signal"><path d="M-40 190 H170 L235 255 H410 V360 H530"/><path d="M1480 520 H1260 L1195 455 H1080 V330 H950"/></g><g class="tech-orbit"><circle cx="1280" cy="130" r="145"/><circle cx="1280" cy="130" r="175"/></g></svg>`;
    layer.style.setProperty('--tech-direction',index%2?-1:1);
    section.prepend(layer);
  });
  let pending=false;
  const media=matchMedia('(prefers-reduced-motion:reduce)');
  function update(){pending=false;document.documentElement.style.setProperty("--tech-viewport",`${document.documentElement.clientWidth}px`);const stopped=media.matches||document.body.classList.contains('still');document.querySelectorAll('.tech-scene').forEach(section=>{const r=section.getBoundingClientRect();if(r.bottom<0||r.top>innerHeight)return;const drift=stopped?0:Math.max(-65,Math.min(65,(r.top+r.height/2-innerHeight/2)*.12));section.style.setProperty('--tech-drift',`${drift}px`)});}
  function schedule(){if(!pending){pending=true;requestAnimationFrame(update)}}
  addEventListener('scroll',schedule,{passive:true});addEventListener('resize',schedule);media.addEventListener('change',schedule);new MutationObserver(schedule).observe(document.body,{attributes:true,attributeFilter:['class']});schedule();
})();



