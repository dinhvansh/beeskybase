/* BeeSky shell interactions. No API or device commands are issued here. */
(()=>{
 let collapsed=false;try{collapsed=localStorage.getItem('beesky-sidebar')==='collapsed'}catch{}
 const dialog=document.querySelector('#modal');
 function command(){
  modal('Tìm kiếm','Đi đến trang hoặc xem máy đào trong bản duyệt.', '<label class="field" for="command-query">Trang, IP hoặc model</label><input id="command-query" type="search" style="width:100%;padding:10px" autocomplete="off"><div class="command-results" id="command-results"></div>');
  const input=document.querySelector('#command-query'),results=document.querySelector('#command-results');
  function draw(){const q=input.value.trim().toLocaleLowerCase();const pages=[...navs,...management].map(([id,ic,name])=>({href:'#/'+id,name,ic,kind:'Trang'}));const machines=state.newAccount?[]:miners.map(m=>({href:'#/miners',name:m.ip+' · '+m.model,ic:'miner',kind:'Máy mẫu',ip:m.ip}));results.innerHTML=[...pages,...machines].filter(x=>x.name.toLocaleLowerCase().includes(q)).slice(0,16).map(x=>`<a href="${x.href}" ${x.ip?`data-command-miner="${esc(x.ip)}"`:''}>${icon(x.ic)}<span>${esc(x.name)}</span><small>${x.kind}</small></a>`).join('')||'<p class="empty">Không tìm thấy kết quả.</p>'}
  input.addEventListener('input',draw);draw();input.focus();results.addEventListener('click',e=>{const a=e.target.closest('a');if(!a)return;dialog.close();if(a.dataset.commandMiner){state.search=a.dataset.commandMiner;state.selected='all';state.filter='all';if(route==='miners')render()}});
 }
 document.addEventListener('keydown',e=>{if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='k'){e.preventDefault();command()}});
 document.addEventListener('click',e=>{const b=e.target.closest('[data-ui]');if(!b)return;if(b.dataset.ui==='sidebar'){if(innerWidth<768){document.querySelector('.shell')?.classList.toggle('menu-open')}else{collapsed=!collapsed;try{localStorage.setItem('beesky-sidebar',collapsed?'collapsed':'expanded')}catch{}sync()}}if(b.dataset.ui==='search')command();if(b.dataset.ui==='account')modal('Tài khoản','Bản duyệt giao diện · Các thay đổi chỉ tồn tại trong phiên này.',`<div class="command-results"><a href="#/security">${icon('shield')}Bảo mật</a><a href="#/settings">${icon('settings')}Cài đặt tổ chức</a><a href="#/login">${icon('logout')}Đăng nhập</a><a href="#/signup">${icon('users')}Đăng ký</a><a href="#/onboarding">${icon('farm')}Xem tài khoản mới</a></div>`)});
 dialog.addEventListener('click',e=>{if(e.target.closest('.command-results a'))dialog.close()});
 function sync(){const shell=document.querySelector('.shell');if(shell&&shell.classList.contains('nav-collapsed')!==collapsed)shell.classList.toggle('nav-collapsed',collapsed);document.querySelectorAll('.nav-item').forEach(a=>{if(!a.title){a.title=a.textContent.trim();a.setAttribute('aria-label',a.title)}})}
 new MutationObserver(sync).observe(document.querySelector('#app'),{childList:true,subtree:true});sync();
})();

document.addEventListener('click',event=>{const link=event.target.closest('a[href^="#/"]');if(!link||!ops.editing||link.hash===location.hash)return;event.preventDefault();const target=link.hash;modal('Rời trình thiết kế?','Bản chỉnh sửa chưa lưu sẽ bị bỏ.','<p>Bạn có thể quay lại và lưu bản nháp trước.</p><button type="button" class="btn danger" id="discard-and-navigate">Bỏ thay đổi và tiếp tục</button>');document.querySelector('#discard-and-navigate').addEventListener('click',()=>{ops.editing=null;document.querySelector('#modal').close();location.hash=target})},true);
window.addEventListener('beforeunload',event=>{if(ops.editing){event.preventDefault();event.returnValue=''}});
