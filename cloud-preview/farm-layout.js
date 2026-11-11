'use strict';
// Farm-first layout navigation. All measurements remain explicitly sample data.
function layoutIssue(d){return d.offline?'Mất kết nối':d.temp>=85?'Nhiệt độ cao':d.issue||''}
function enrichLayout(){
  state.farms.forEach(f=>{
    const ds=devicesFor(f.id);
    ds.forEach(d=>{d.offline=false;d.temp=Math.min(d.temp,74);d.issue=''});
    ds.slice(0,f.issues).forEach((d,i)=>{if(i===0)d.temp=86;else if(i===1)d.offline=true;else d.issue=i===2?'Thiếu chip':'Giảm hashrate'});
  });
}
enrichLayout();
const farmReset=resetDemo;
resetDemo=function(){farmReset();enrichLayout()};
function layoutLink(site,issues=false){return '#/farms?farm='+encodeURIComponent(site)+(issues?'&attention=1':'')}
function farmLayoutCard(f){
  const ds=devicesFor(f.id),issues=ds.filter(d=>layoutIssue(d)).length,rs=racksFor(f.id);
  return `<article class="panel farm-layout-card"><a class="farm-layout-open" href="${layoutLink(f.id)}"><div class="site-card-top"><span class="site-avatar">${icon('farm')}</span><span class="pill neutral">${rs.length} rack</span></div><h2>${esc(f.name)}</h2><p class="muted">${esc(f.location)}</p><div class="farm-layout-metrics"><strong>${ds.length}<small> máy</small></strong><span>${ds.length-freeDevices(f.id).length} đã xếp vị trí</span></div><div class="farm-layout-mini" aria-hidden="true">${(rs.length?rs:[null]).map(r=>`<span>${Array.from({length:12},(_,i)=>'<i></i>').join('')}<b>${esc(r?.name||'Chưa có rack')}</b></span>`).join('')}</div><div class="farm-layout-cta">Xem sơ đồ & nhiệt độ ${icon('arrow')}</div></a><footer>${issues?`<a class="farm-issue-link" href="${layoutLink(f.id,true)}">${icon('warning')} ${issues} cần kiểm tra ${icon('arrow')}</a>`:'<span class="muted">Không có máy cần kiểm tra</span>'}</footer></article>`;
}
const rackDetailView=heatmapView;
farmsView=function(){
  const params=new URLSearchParams(location.hash.split('?')[1]||''),site=params.get('farm');
  if(!site||!state.farms.some(f=>f.id===site)){
    return head('','Trại của tôi','',button('Thêm trại','add-farm',true))+`<div class="farm-layout-grid">${state.farms.map(farmLayoutCard).join('')}</div>`+(state.farms.length?'':emptyData('Chưa có trại','Tạo trại trước khi bố trí rack.'));
  }
  layout.site=site;state.selected=site;
  const f=state.farms.find(f=>f.id===site),issues=devicesFor(site).filter(d=>layoutIssue(d)),attention=params.get('attention')==='1';
  let html=rackDetailView();
  html=html.replace(/<div class="page-head">[\s\S]*?<\/div><\/div>/,head('',esc(f.name),'',button('Thêm rack','rack-add',true)));
  const controls=`<div class="farm-layout-context"><a class="btn small" href="#/farms">← Trại của tôi</a><nav class="rack-tabs" aria-label="Tình trạng máy"><a class="btn small ${attention?'':'primary'}" href="${layoutLink(site)}">Tất cả máy</a><a class="btn small ${attention?'primary':''}" href="${layoutLink(site,true)}">${issues.length} cần kiểm tra</a></nav><button class="btn small" data-action="layout-depth" aria-pressed="${layout.depth!==false}">${layout.depth!==false?'Đang xem 3D':'Xem 3D'}</button></div>`;
  const list=attention?`<section class="panel farm-issue-panel"><div class="panel-head"><h2>${issues.length} máy cần kiểm tra</h2><span class="muted">${esc(f.name)}</span></div><div class="farm-issue-list">${issues.map(d=>{const p=locationOf(d.id);return `<button class="farm-issue-row" data-inspect-device="${d.id}"><strong>${d.ip}</strong><span>${esc(layoutIssue(d))}</span><span>${p?esc(position(p.rack,p.index)):'Chưa xếp vị trí'}</span>${icon('chevron')}</button>`}).join('')||'<p class="unplaced-empty">Không có máy cần kiểm tra.</p>'}</div></section>`:'';
  html=html.replace('<div class="toolbar">',controls+list+'<div class="toolbar">');
  // Highlight issue locations while keeping their physical context visible.
  if(attention)html=html.replace(/class="rack-slot ([^"]*)"([^>]*data-rack-slot="([^"]+)" data-slot="(\d+)"[^>]*)/g,(all,classes,attrs,id,index)=>{const r=layout.racks.find(r=>r.id===id),d=layout.devices.find(d=>d.id===r?.slots[+index]);return `class="rack-slot ${classes} ${d&&layoutIssue(d)?'needs-check':'context-slot'}"${attrs}`});
  return `<div class="farm-detail ${layout.depth!==false?'depth-view':''}">${html}</div>`;
};
// Farm cards throughout the application enter the same physical layout.
const previousFarmCard=farmCard;
farmCard=function(f){return previousFarmCard(f).replace('href="#/miners"',`href="${layoutLink(f.id)}"`).replace(`<em>${f.issues} cần kiểm tra</em>`,`<a class="farm-issue-link" href="${layoutLink(f.id,true)}">${f.issues} cần kiểm tra ${icon('arrow')}</a>`)};
document.addEventListener('click',e=>{
  if(e.target.closest('[data-action="layout-depth"]')){layout.depth=layout.depth===false;render()}
  const target=e.target.closest('[data-inspect-device]');if(target){const d=layout.devices.find(d=>d.id===target.dataset.inspectDevice),p=locationOf(d.id);if(p)inspectSlot(p.rack,p.index);else modal(d.ip,'Chưa xếp vị trí',`<p>${esc(layoutIssue(d))}</p><p>${esc(d.model)}</p>`) }
});
const previousInspectSlot=inspectSlot;
inspectSlot=function(r,i){previousInspectSlot(r,i);const d=layout.devices.find(d=>d.id===r.slots[i]);if(d){const body=document.querySelector('#modal .detail-hero');if(body)body.insertAdjacentHTML('beforeend',`<p class="slot-condition">${esc(layoutIssue(d)||'Hoạt động bình thường')}</p>`)} };
document.addEventListener('change',e=>{if(e.target.id==='layout-site'){layout.pending=null;layout.edit=false;location.hash=layoutLink(e.target.value)}});
const thermalNav=navs.findIndex(n=>n[0]==='heatmap');
if(thermalNav>=0)navs.splice(thermalNav,1);
heatmapView=function(){location.replace('#/farms'+(location.hash.includes('?')?'?'+location.hash.split('?')[1]:''));return ''};
if(route==='heatmap'||route==='farms'||route==='overview')render();
