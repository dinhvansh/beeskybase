(()=>{
 const flowHero=document.querySelector('body[data-page="flow"] .document-visual');
 if(flowHero)flowHero.outerHTML='<figure class="flow-real-hero"><img src="assets/flowdocker-dashboard-studio-v1.png" alt="Minh họa 3D FlowDocker từ giao diện tổng quan thực tế" width="1672" height="941"><figcaption>Giao diện minh họa từ sản phẩm FlowDocker</figcaption></figure>';
 const nav=document.querySelector('header nav');if(!nav)return;
 nav.setAttribute('aria-label','Điều hướng chính');
 const menu=document.createElement('details');menu.className='products-menu';
 menu.innerHTML=`<summary>Sản phẩm <svg width="12" height="12" viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="m4 6 4 4 4-4" stroke="currentColor" stroke-width="1.5"/></svg></summary><div class="products-submenu"><span class="products-menu-title">SẢN PHẨM CỦA BEESKY</span><a href="/flowdocker"><span class="product-menu-icon">F</span><span><strong>FlowDocker</strong><small>Quy trình, phê duyệt & ký PDF</small></span><b aria-hidden="true">↗</b></a><a href="/mine"><span class="product-menu-icon">M</span><span><strong>BeeSky Mine</strong><small>Bộ công cụ quản lý xưởng đào</small></span><b aria-hidden="true">↗</b></a><a href="https://api.beeskybase.com/"><span class="product-menu-icon">AI</span><span><strong>BeeSkyBase AI</strong><small>Kết nối mô hình & quản lý API</small></span><b aria-hidden="true">↗</b></a></div>`;
 const old=nav.querySelector('a[href="#products"]');if(old)old.replaceWith(menu);else nav.insertBefore(menu,nav.children[1]||null);
 document.addEventListener('click',e=>{if(!menu.contains(e.target))menu.open=false});
 document.addEventListener('keydown',e=>{if(e.key==='Escape'&&menu.open){menu.open=false;menu.querySelector('summary').focus()}});
 menu.querySelectorAll('a').forEach(a=>a.addEventListener('click',()=>{menu.open=false}));
})();
