'use strict';
const placementFilters=new Map();
let draggedDevice=null;
function placementState(){const site=currentSite();if(!placementFilters.has(site))placementFilters.set(site,{query:'',model:'all',status:'all'});return placementFilters.get(site)}
function matchingUnplaced(){const f=placementState(),q=f.query.trim().toLocaleLowerCase('vi');return freeDevices(currentSite()).filter(d=>(!q||[d.ip,d.serial,d.model].some(v=>v.toLocaleLowerCase('vi').includes(q)))&&(f.model==='all'||d.model===f.model)&&(f.status==='all'||(f.status==='attention'?!!layoutIssue(d):!layoutIssue(d)))).sort((a,b)=>ipv4(a.ip)-ipv4(b.ip))}
function placementCards(){const ds=matchingUnplaced();return ds.length?ds.map(d=>`<div class="unplaced-device ${layout.pending===d.id?'selected':''}" draggable="true" data-drag-device="${d.id}" aria-label="Máy ${d.ip}, kéo vào ô trống hoặc bấm chọn vị trí"><div class="unplaced-top"><strong>${d.ip}</strong><span class="pill neutral">${d.offline?'Mất kết nối':d.temp+'°C'}</span></div><p>${esc(d.model)}</p><small>${esc(d.serial)}</small><button class="btn small full ${layout.pending===d.id?'primary':''}" data-place-device="${d.id}">${icon('pin')}${layout.pending===d.id?'Đang chọn vị trí…':'Chọn vị trí'}</button></div>`).join(''):`<div class="unplaced-empty"><strong>${freeDevices(currentSite()).length?'Không có máy phù hợp':'Đã xếp hết máy'}</strong><p>${freeDevices(currentSite()).length?'Thử đổi bộ lọc hoặc từ khóa.':'Máy mới phát hiện sẽ xuất hiện ở đây.'}</p></div>`}
const placementFarmView=farmsView;
// Both scopes use one search component, with one border and one focus ring.
function deviceSearchInput(id,label,value,placeholder){
  return `<div class="device-search-field"><label for="${id}">${label}</label><div class="device-search-control">${icon('search')}<input id="${id}" type="search" autocomplete="off" placeholder="${placeholder}" value="${esc(value)}"><button type="button" class="device-search-clear" data-clear-device-search="${id}" aria-label="Xóa ${label.toLocaleLowerCase('vi')}" ${value?'':'hidden'}>${icon('close')}</button></div></div>`;
}
const rackSearches=new Map();
function rackQuery(){return rackSearches.get(currentSite())||''}
function matchingRackDevices(){
  const query=rackQuery().trim().toLocaleLowerCase('vi');
  if(!query)return [];
  return devicesFor(currentSite()).flatMap(d=>{
    const p=locationOf(d.id);
    if(!p||p.rack.site!==currentSite())return [];
    const text=[d.ip,d.model,d.serial,p.rack.name,p.rack.zone].join(' ').toLocaleLowerCase('vi');
    return text.includes(query)?[{d,p}]:[];
  }).sort((a,b)=>ipv4(a.d.ip)-ipv4(b.d.ip));
}
function rackSearchResults(){
  if(!rackQuery().trim())return '';
  const matches=matchingRackDevices();
  return `<div class="rack-search-summary" role="status">${matches.length} máy trong rack phù hợp${matches.length>20?' · Hiển thị 20 kết quả đầu':''}</div>`+(matches.length?`<div class="rack-search-matches">${matches.slice(0,20).map(({d,p})=>`<button type="button" data-find-rack-device="${d.id}"><strong>${esc(d.ip)}</strong><span>${esc(position(p.rack,p.index))}</span><small>${esc(d.model)}</small>${icon('pin')}</button>`).join('')}</div>`:'<p class="rack-search-empty">Không tìm thấy máy đã xếp. Thử IP, model, serial hoặc tên rack khác.</p>');
}
function updateSearchClear(id){const input=document.getElementById(id),clear=document.querySelector(`[data-clear-device-search="${id}"]`);if(clear&&input)clear.hidden=!input.value}
function highlightRackMatches(){
  const active=!!rackQuery().trim(),ids=new Set(matchingRackDevices().map(({d})=>d.id));
  document.querySelectorAll('[data-rack-slot]').forEach(slot=>{
    const r=racksFor(currentSite()).find(r=>r.id===slot.dataset.rackSlot),id=r?.slots[+slot.dataset.slot];
    slot.classList.toggle('search-match',active&&ids.has(id));
    slot.classList.toggle('search-muted',active&&!ids.has(id));
  });
}
function refreshRackSearch(){
  const results=document.getElementById('rack-search-results');if(results)results.innerHTML=rackSearchResults();
  updateSearchClear('rack-device-query');highlightRackMatches();
}
farmsView=function(){
  let html=placementFarmView();
  if(!html.includes('class="unplaced-list"'))return html;
  const f=placementState(),models=[...new Set(devicesFor(currentSite()).map(d=>d.model))].sort();
  const controls=`<div class="placement-controls">${deviceSearchInput('placement-query','Tìm máy chưa xếp',f.query,'IP, model hoặc serial')}<div class="placement-filter-row"><select id="placement-model" aria-label="Lọc model máy chưa xếp"><option value="all">Tất cả model</option>${models.map(m=>`<option value="${esc(m)}" ${f.model===m?'selected':''}>${esc(m)}</option>`).join('')}</select><select id="placement-status" aria-label="Lọc trạng thái máy chưa xếp"><option value="all">Mọi trạng thái</option><option value="normal" ${f.status==='normal'?'selected':''}>Bình thường</option><option value="attention" ${f.status==='attention'?'selected':''}>Cần kiểm tra</option></select></div><div class="placement-results"><span id="placement-result-count" role="status">${matchingUnplaced().length} / ${freeDevices(currentSite()).length} máy</span><button class="btn small" data-action="placement-clear">Xóa lọc</button></div><small>Kéo máy thả vào ô trống trên rack.</small></div>`;
  html=html.replace(/<div class="unplaced-list">[\s\S]*?<\/div><\/div><div class="panel rule-card">/,controls+`<div class="unplaced-list">${placementCards()}</div></div><div class="panel rule-card">`);
  const search=`<section class="rack-device-search" aria-label="Tìm máy đã xếp trong xưởng">${deviceSearchInput('rack-device-query','Tìm máy trong rack',rackQuery(),'Tìm IP, model, serial hoặc tên rack')}<div id="rack-search-results">${rackSearchResults()}</div></section>`;
  html=html.replace('<div class="rack-toolbar">',search+'<div class="rack-toolbar">');
  return html;
};
// Reapply search markers after changes to rack tabs, names, or placement.
const placementRender=render;
render=function(){placementRender();if(route==='farms')highlightRackMatches()};
const placementRackHtml=rackHtml;
rackHtml=function(r){return placementRackHtml(r).replace(/data-rack-slot="([^"]+)" data-slot="(\d+)"/g,(all,id,i)=>all+(layout.edit&&r.slots[+i]?' draggable="true" data-drag-device="'+r.slots[+i]+'"':'' )).replace('<div class="rack-meta">',`<div class="rack-meta"><button class="btn small" data-rename-rack="${r.id}" aria-label="Đổi tên ${esc(r.name)}">${icon('settings')}Sửa rack</button>`)};
function refreshPlacement(){const list=document.querySelector('.unplaced-list');if(list)list.innerHTML=placementCards();const count=document.querySelector('#placement-result-count');if(count)count.textContent=`${matchingUnplaced().length} / ${freeDevices(currentSite()).length} máy`}
document.addEventListener('input',e=>{if(e.target.id==='placement-query'){placementState().query=e.target.value;refreshPlacement();updateSearchClear('placement-query')}else if(e.target.id==='rack-device-query'){rackSearches.set(currentSite(),e.target.value);refreshRackSearch()}});
document.addEventListener('change',e=>{if(e.target.id==='placement-model')placementState().model=e.target.value;else if(e.target.id==='placement-status')placementState().status=e.target.value;else return;refreshPlacement()});
document.addEventListener('click',e=>{
  const clear=e.target.closest('[data-clear-device-search]');
  if(clear){const id=clear.dataset.clearDeviceSearch,input=document.getElementById(id);if(input){input.value='';input.dispatchEvent(new Event('input',{bubbles:true}));input.focus()}return}
  const result=e.target.closest('[data-find-rack-device]');
  if(result){const p=locationOf(result.dataset.findRackDevice);if(!p||p.rack.site!==currentSite())return;layout.filter=p.rack.id;render();const slot=document.querySelector(`[data-rack-slot="${p.rack.id}"][data-slot="${p.index}"]`);if(slot){slot.scrollIntoView({block:'center',inline:'center',behavior:'instant'});slot.focus({preventScroll:true});slot.classList.add('search-located')}return}
  if(e.target.closest('[data-action="placement-clear"]')){placementFilters.delete(currentSite());render()}
  const target=e.target.closest('[data-rename-rack]');if(!target)return;const r=racksFor(currentSite()).find(r=>r.id===target.dataset.renameRack);if(!r)return;
  modal('Chỉnh sửa rack',esc(state.farms.find(f=>f.id===r.site)?.name),`<input type="hidden" name="rackId" value="${r.id}"><div class="field"><label for="edit-rack-name">Tên kệ / rack</label><input id="edit-rack-name" name="rackName" value="${esc(r.name)}" required maxlength="60"></div><div class="field"><label for="edit-rack-zone">Khu / dãy</label><input id="edit-rack-zone" name="zone" value="${esc(r.zone)}" maxlength="80"></div><small>Đổi tên không thay đổi vị trí máy trên rack.</small>`,'rename-rack-form','Lưu thay đổi');
});
document.addEventListener('submit',e=>{if(e.target.id!=='rename-rack-form')return;e.preventDefault();const f=e.target.elements,r=racksFor(currentSite()).find(r=>r.id===f.rackId.value),name=f.rackName.value.trim();if(!r||!name){toast('Nhập tên rack hợp lệ.');return}if(racksFor(r.site).some(other=>other.id!==r.id&&other.name.toLocaleLowerCase('vi')===name.toLocaleLowerCase('vi'))){toast('Tên rack đã có trong xưởng.');return}r.name=name;r.zone=f.zone.value.trim()||'Chưa đặt khu / dãy';$('#modal').close();render();toast('Đã cập nhật tên rack trong bản mẫu.')});
function clearDrag(){draggedDevice=null;document.querySelectorAll('.drag-source,.drop-ready,.drop-hover').forEach(el=>el.classList.remove('drag-source','drop-ready','drop-hover'))}
function dropTarget(target){const slot=target.closest('[data-rack-slot]');if(!slot||!draggedDevice)return null;const r=racksFor(currentSite()).find(r=>r.id===slot.dataset.rackSlot),i=+slot.dataset.slot;if(!r||!Number.isInteger(i)||i<0||i>=r.slots.length||r.slots[i]||!devicesFor(r.site).some(d=>d.id===draggedDevice))return null;return{slot,r,i}}
document.addEventListener('dragstart',e=>{const card=e.target.closest('[data-drag-device]');if(!card||!devicesFor(currentSite()).some(d=>d.id===card.dataset.dragDevice)||!!locationOf(card.dataset.dragDevice)&&!layout.edit)return;draggedDevice=card.dataset.dragDevice;e.dataTransfer.effectAllowed='move';e.dataTransfer.setData('application/x-beesky-device',draggedDevice);card.classList.add('drag-source');document.querySelectorAll('.rack-slot.vacant').forEach(el=>el.classList.add('drop-ready'))});
document.addEventListener('dragover',e=>{const t=dropTarget(e.target);if(t){e.preventDefault();e.dataTransfer.dropEffect='move';t.slot.classList.add('drop-hover')}});
document.addEventListener('dragleave',e=>{const slot=e.target.closest('[data-rack-slot]');if(slot&&!slot.contains(e.relatedTarget))slot.classList.remove('drop-hover')});
document.addEventListener('drop',e=>{const t=dropTarget(e.target);if(!t)return;e.preventDefault();if(e.dataTransfer.getData('application/x-beesky-device')!==draggedDevice){clearDrag();return}try{moveRackDevice(draggedDevice,t.r,t.i)}catch(err){clearDrag();toast(err.message)}});
document.addEventListener('dragend',clearDrag);
if(route==='farms')render();
