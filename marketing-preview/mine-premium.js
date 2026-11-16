(()=>{
const ecosystem=document.querySelector('.mine-ecosystem');
const art=document.createElement('div');art.className='mine-hero-art mine-live-hero';
art.innerHTML=`<div class="mine-live-stage" role="img" aria-label="Model máy gió S19 Pro và máy nước S21 Hydro trên kệ 3D"><p class="mine-model-fallback" hidden>Không tải được model. Thử tải lại trang nhé.</p></div><a class="mine-glass-panel mine-scanner-panel" href="#scan"><span class="mine-panel-top"><i></i> SCANNER</span><strong>Đã tìm thấy.</strong><div class="mine-device-line"><b>S19 Pro</b><small>192.168.1.21</small><em>Online</em></div><div class="mine-device-line"><b>S21 Hydro</b><small>192.168.1.22</small><em>Online</em></div><span class="mine-panel-bottom">LAN → nhận diện thiết bị</span></a><a class="mine-glass-panel mine-cloud-panel" href="https://mine.beeskybase.com/#/login"><span class="mine-panel-top"><i></i> CLOUD</span><strong>Cả xưởng. Trong tầm mắt.</strong><div class="mine-cloud-metrics"><div><b>18<small>/18</small></b><span>Máy kết nối</span></div><div><b>3</b><span>Kệ đang chạy</span></div></div><svg viewBox="0 0 180 40" aria-hidden="true"><path d="M0 32 L20 28 L40 30 L60 17 L80 22 L100 10 L120 15 L140 7 L160 12 L180 3"/></svg></a><span class="mine-agent-tag"><i></i> AGENT · KẾT NỐI TẠI XƯỞNG</span><span class="mine-art-caption">S19 Pro · S21 Hydro <small>Model 3D & số liệu minh họa</small></span>`;ecosystem.prepend(art);
document.querySelector('.eco-top').remove();
document.querySelector('.opening h1').innerHTML='Từng máy.<br>Cả xưởng.<br>Cùng một nơi.';
document.querySelector('.opening .lead').textContent='Quét tìm miner. Kết nối dữ liệu. Nhìn rõ không gian, điện và bảo trì trên cùng hệ thống.';
document.querySelector('.opening .pill').textContent='Thử quét miner';document.querySelector('.opening .pill').href='#scan';
document.querySelectorAll('.toolkit-grid article').forEach((card,i)=>{card.insertAdjacentHTML('afterbegin',`<div class="mine-tool-icon" aria-hidden="true">${['⌕','⇄','☁','✧'][i]}</div><span class="mine-tool-number">0${i+1}</span>`);});
document.querySelector('.closing .kicker').textContent='BEESKY MINE / BẮT ĐẦU TỪ XƯỞNG CỦA BẠN';document.querySelector('.closing h2').innerHTML='Kết nối thiết bị.<br>Nắm rõ vận hành.';
const storySection=document.querySelector('#story');storySection.classList.add('mine-chapters');
const firstChapter=storySection.querySelector('.sticky-story');firstChapter.classList.add('mine-chapter');
firstChapter.querySelector('.story-controls').hidden=true;
panels.slice(1).forEach((panel,index)=>{
 const chapter=document.createElement('div');chapter.className='mine-chapter mine-chapter-'+(index+2);
 chapter.innerHTML=`<div class="story-title"><p class="kicker">${panel.chapter}</p><h2>${panel.title}</h2><p>${panel.copy}</p></div><div class="screen"><div class="screen-top"><b>BeeSky Mine</b><span>${panel.name}</span><small>MINH HỌA</small></div><div class="chapter-content">${panel.html}</div></div>`;
 storySection.append(chapter);
});
const targets=[...document.querySelectorAll('.opening,.mine-hero-art,.toolkit-section>h2,.toolkit-grid article,.scan-intro,.scan-demo,.device-support h2,#start>h2,.closing h2')];
const media=matchMedia('(prefers-reduced-motion:reduce)');let pending=false;
function update(){pending=false;const stop=media.matches||document.body.classList.contains('still');targets.forEach((el,i)=>{const r=el.getBoundingClientRect();if(!stop&&(r.bottom< -150||r.top>innerHeight+150))return;const previous=parseFloat(el.style.getPropertyValue('--mine-drift'))||0;const p=Math.max(-1,Math.min(1,(r.top-previous+r.height/2-innerHeight/2)/innerHeight));const speed=el.classList.contains('mine-hero-art')?1:el.classList.contains('scan-demo')?.65:i%2?.3:-.35;el.style.setProperty('--mine-drift',stop?'0px':`${p*speed*(innerWidth<701?45:145)}px`);});}
targets.forEach(e=>e.classList.add('mine-depth'));function schedule(){if(!pending){pending=true;requestAnimationFrame(update)}}addEventListener('scroll',schedule,{passive:true});addEventListener('resize',schedule);media.addEventListener('change',schedule);new MutationObserver(schedule).observe(document.body,{attributes:true,attributeFilter:['class']});schedule();
})();


