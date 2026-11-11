'use strict';
// Bridge the 3D view to the exact same rack/slot identity used by the 2D view.
let rackScene=null,rackSceneVersion=0;
let sceneKey='',sceneCamera=null,focusRackDevice=null;
const rackMoves=[];
const warehouseEngine=new WarehouseEngine(()=>layout.racks);
const machineGroups=new MachineGroups(()=>layout.devices);
let warehouseEffects=true;
let warehouseMode='inspect',warehouseSelectedRack=null,warehouseExpanded=false,warehouseOwnFullscreen=false;
function warehouseVisibleRacks(){return warehouseEngine.racks(currentSite()).filter(r=>layout.filter==='all'||r.id===layout.filter)}
function warehouseFloorControls(){
  const site=currentSite(),floor=warehouseEngine.floor(site),rs=warehouseEngine.racks(site);
  if(!rs.some(r=>r.id===warehouseSelectedRack))warehouseSelectedRack=rs[0]?.id||null;
  return `<div class="warehouse-floorbar"><label>Tầng xưởng<select id="warehouse-floor" aria-label="Tầng xưởng">${warehouseEngine.floors(site).map(f=>`<option value="${f.id}" ${f.id===floor.id?'selected':''}>${esc(f.name)} · ${warehouseEngine.racks(site,f.id).length} kệ</option>`).join('')}</select></label><button class="btn small" data-warehouse="add-floor">Thêm tầng</button><button class="btn small" data-warehouse="rename-floor">Đổi tên tầng</button><span class="muted">${floor.width} × ${floor.depth} ô lưới</span><button class="btn small" data-warehouse="delete-floor" ${rs.length||warehouseEngine.floors(site).length===1?'disabled':''}>Xóa tầng trống</button></div>`;
}
function warehouseTools(){
  const rs=warehouseEngine.racks(currentSite()),editing=warehouseMode==='racks';
  return `${warehouseFloorControls()}<div class="warehouse-tools"><div class="warehouse-mode" role="group" aria-label="Chế độ tương tác"><button class="btn small ${!layout.edit&&!editing?'primary':''}" data-warehouse="inspect" aria-pressed="${!layout.edit&&!editing}">Khám phá</button><button class="btn small ${layout.edit?'primary':''}" data-warehouse="machines" aria-pressed="${layout.edit}">Di chuyển máy</button><button class="btn small ${editing?'primary':''}" data-warehouse="racks" aria-pressed="${editing}">Bố trí kệ</button></div><div class="warehouse-tools-actions"><button class="btn small" data-warehouse="effects" aria-pressed="${warehouseEffects}">Hiệu ứng: ${warehouseEffects?'Bật':'Tắt'}</button><button class="btn small" data-action="rack-add">Thêm kệ</button><button class="btn small" data-warehouse="fullscreen" aria-pressed="${warehouseExpanded}">${warehouseExpanded?'Thu nhỏ':'Toàn màn hình'}</button></div></div>${`<div class="warehouse-rackbar"><label>Kệ đang chọn<select id="warehouse-rack" aria-label="Kệ đang chọn">${rs.map(r=>`<option value="${r.id}" ${r.id===warehouseSelectedRack?'selected':''}>${esc(r.name)}</option>`).join('')}</select></label><button class="btn small" data-warehouse="rack-position" ${rs.length?'':'disabled'}>Vị trí & tầng</button><button class="btn small" data-warehouse="rotate-left" ${rs.length?'':'disabled'}>↶ Xoay trái</button><button class="btn small" data-warehouse="rotate" ${rs.length?'':'disabled'}>↷ Xoay phải</button><button class="btn small" data-warehouse="undo" ${warehouseEngine.history.at(-1)?.site===currentSite()?'':'disabled'}>Hoàn tác kệ</button><span class="muted">${editing?'Kéo kệ trên sàn · R xoay · Esc hủy':'Chọn kệ để xoay · Bật Bố trí kệ để kéo'}</span></div>`}`;
}
const before3dReset=resetDemo;
resetDemo=function(){before3dReset();rackMoves.length=0;sceneCamera=null;focusRackDevice=null;warehouseEngine.sites.clear();warehouseEngine.history.length=0;machineGroups.groups=[];if(typeof machineGroupFilters!=='undefined')machineGroupFilters.clear();warehouseMode='inspect'};
function moveRackDevice(id,r,i){
  if(!r||r.site!==currentSite()||!Number.isInteger(i)||i<0||i>=r.slots.length)throw Error('Vị trí không hợp lệ.');
  if(r.slots[i])throw Error('Ô đã có máy. Hãy chọn ô trống.');
  if(!devicesFor(r.site).some(d=>d.id===id))throw Error('Máy không thuộc xưởng này.');
  const old=locationOf(id);
  rackMoves.push({id,site:r.site,from:old?{rack:old.rack.id,index:old.index}:null,to:{rack:r.id,index:i}});
  assign(r,i,id);layout.pending=null;clearDrag();render();
  toast('Đã chuyển máy đến '+position(r,i)+' · Bản duyệt, chưa lưu server.');
}
const before3dFarmView=farmsView;
farmsView=function(){
  let html=before3dFarmView();
  if(!html.includes('class="rack-boards"'))return html;
  const floorIds=new Set(warehouseEngine.racks(currentSite()).map(r=>r.id));
  html=html.replace(/<button data-rack-filter="([^"]+)"[^>]*>[\s\S]*?<\/button>/g,(all,id)=>id==='all'||floorIds.has(id)?all:'');
  html=html.replace('Đang xem 3D','Chuyển sang 2D').replace('Xem 3D','Xem xưởng 3D');
  if(layout.depth===false){html=html.replace('<div class="rack-toolbar">',warehouseFloorControls()+'<div class="rack-toolbar">');if(!warehouseEngine.racks(currentSite()).length)html=html.replace('<div class="rack-boards">','<div class="rack-boards"><div class="panel empty"><h2>Tầng này chưa có kệ</h2><p>Thêm kệ hoặc chuyển kệ từ tầng khác trong chế độ 3D.</p></div>');return html}
  const panel=`<section class="panel rack-world" aria-label="Sơ đồ xưởng 3D"><header class="rack-world-toolbar"><strong>Xưởng 3D</strong><div><button type="button" class="btn small" data-scene-view="hall">Toàn xưởng</button><button type="button" class="btn small" data-scene-view="overview">Cận kệ</button><button type="button" class="btn small" data-scene-view="front">Mặt trước</button><button type="button" class="btn small" data-scene-view="top">Từ trên</button><button type="button" class="btn small" data-undo-rack-move ${rackMoves.at(-1)?.site===currentSite()?'':'disabled'}>Hoàn tác</button></div></header><div id="rack-world-canvas" class="rack-world-canvas"><p class="rack-world-loading" role="status">Đang tải sơ đồ 3D…</p></div><div id="rack-world-status" class="rack-world-status" role="status" aria-live="polite">${layout.edit?'Kéo máy đến ô trống. Esc để hủy.':'Kéo nền để xoay · Cuộn để zoom · Bấm máy để xem chi tiết.'}</div><footer class="rack-world-footer"><span>${layout.edit?'Đang sắp xếp vị trí':'Bật “Sắp xếp vị trí” để kéo máy trong rack.'}</span><span>Coin/hash minh họa · Không phải thu nhập thực · Vị trí lưu trong phiên</span></footer></section>`;
  const enhanced=panel.replace('<div id="rack-world-canvas"',warehouseTools()+'<div id="rack-world-canvas"').replace('<p class="rack-world-loading"','<aside id="warehouse-hover" class="warehouse-hover" hidden></aside><p class="rack-world-loading"').replace('Bật “Sắp xếp vị trí” để kéo máy trong rack.','Chọn Di chuyển máy hoặc Bố trí kệ để chỉnh sơ đồ.');
  return html.replace('<div class="rack-boards">',enhanced+'<div class="rack-boards rack-2d-fallback">').replace('Kéo máy thả vào ô trống trên rack.','Kéo máy vào ô trống trong 3D hoặc bấm Chọn vị trí.');
};
const beforeWarehouseRackHtml=rackHtml;
rackHtml=function(r){return r.placement?.floorId===warehouseEngine.site(r.site).active?beforeWarehouseRackHtml(r):''};
function warehouseHover(data){
  const el=document.getElementById('warehouse-hover');if(!el)return;
  if(!data){el.hidden=true;return}
  const {r,i,d,x,y}=data,floor=warehouseEngine.floor(r.site,r.placement.floorId);
  el.innerHTML=`<header><strong>${esc(d.ip)}</strong><span class="pill ${d.offline?'neutral':d.temp>=85?'red':'neutral'}">${d.offline?'Mất kết nối':d.temp+'°C'}</span></header><p>${esc(d.model)}</p><dl><div><dt>Serial</dt><dd>${esc(d.serial)}</dd></div><div><dt>Tầng xưởng</dt><dd>${esc(floor.name)}</dd></div><div><dt>Vị trí</dt><dd>${esc(position(r,i))}</dd></div><div><dt>Trạng thái</dt><dd>${esc(layoutIssue(d)||'Hoạt động bình thường')}</dd></div></dl><small>Bấm máy để mở chi tiết · Dữ liệu mẫu</small>`;
  el.hidden=false;const host=el.parentElement;el.style.left=Math.max(8,Math.min(x+18,host.clientWidth-el.offsetWidth-8))+'px';el.style.top=Math.max(8,Math.min(y+18,host.clientHeight-el.offsetHeight-8))+'px';
}
function sceneStatus(message){const el=document.getElementById('rack-world-status');if(el)el.textContent=message}
const before3dRender=render;
render=function(){
  const requestedSite=location.hash.startsWith('#/farms')?new URLSearchParams(location.hash.split('?')[1]||'').get('farm'):null;
  if(requestedSite&&state.farms.some(f=>f.id===requestedSite)){layout.site=requestedSite;state.selected=requestedSite}
  warehouseEngine.sync(currentSite());
  if(layout.filter!=='all'&&!warehouseEngine.racks(currentSite()).some(r=>r.id===layout.filter))layout.filter='all';
  const key=currentSite()+':'+warehouseEngine.site(currentSite()).active+':'+layout.filter+':'+warehouseMode;
  if(rackScene&&sceneKey===key)sceneCamera=rackScene.cameraState();else if(sceneKey!==key)sceneCamera=null;
  sceneKey=key;
  const version=++rackSceneVersion;rackScene?.dispose();rackScene=null;
  before3dRender();
  if(warehouseExpanded){
    const panel=document.querySelector('#app .rack-world');
    if(panel){const overlay=warehouseOverlay();overlay.replaceChildren(panel)}else warehouseCloseFullscreen(false);
  }
  const host=document.getElementById('rack-world-canvas');if(!host)return;
  import('./rack-scene.js?v=faa1a25677').then(module=>{
    if(version!==rackSceneVersion||!host.isConnected)return;
    const style=getComputedStyle(document.documentElement),token=(name,fallback)=>style.getPropertyValue(name).trim()||fallback;
    const dark=document.documentElement.dataset.theme==='dark';
    const colors={bg:token('--bg',dark?'#101113':'#f6f7f9'),floor:token('--surface2',dark?'#23272e':'#e9edf2'),grid:token('--border','#b9c3cd'),brand:token('--brand','#facc15'),frame:token('--rack-frame','#53677e'),shelf:token('--rack-shelf','#b5c1ce'),fan:token('--rack-fan','#304052'),normal:token('--green','#16a34a'),warm:token('--amber','#d97706'),critical:token('--red','#dc2626'),offline:token('--muted','#64748b'),empty:token('--border','#cbd5e1'),selected:token('--info','#285fca'),text:token('--text','#18202e'),labelBg:token('--surface','#ffffff')};
    try{
      rackScene=module.mount(host,{colors,effects:()=>warehouseEffects,visualModel:d=>machineGroups.model(d),camera:sceneCamera,floor:warehouseEngine.floor(currentSite()),mode:()=>warehouseMode,selectedRack:()=>warehouseSelectedRack,selectRack:id=>{warehouseSelectedRack=id;const select=document.getElementById('warehouse-rack');if(select){select.value=id;select.dispatchEvent(new Event('change',{bubbles:true}))}},validateRack:(r,p)=>warehouseEngine.check(r,p),moveRack:(r,p)=>{try{warehouseEngine.move(r.id,p);warehouseSelectedRack=r.id;render();toast('Đã cập nhật bố trí '+r.name+' trong bản duyệt.')}catch(err){sceneStatus(err.message)}},hover:warehouseHover,query:()=>rackQuery().trim()||(typeof machineGroupFilterActive==='function'&&machineGroupFilterActive()?'group':''),matches:()=>typeof machineHighlightIds==='function'?machineHighlightIds():new Set(matchingRackDevices().map(({d})=>d.id)),racks:warehouseVisibleRacks,device:id=>layout.devices.find(d=>d.id===id),position,edit:()=>layout.edit&&warehouseMode!=='racks',pending:()=>layout.pending,dragged:()=>warehouseMode==='racks'?null:draggedDevice,status:sceneStatus,inspect:(r,i)=>layout.edit?editSlot(r,i):inspectSlot(r,i),move:(id,r,i)=>{try{moveRackDevice(id,r,i)}catch(err){sceneStatus(err.message)}}});
      if(focusRackDevice){rackScene.focusDevice(focusRackDevice);focusRackDevice=null}
      host.querySelector('.rack-world-loading')?.remove();
      if(!warehouseVisibleRacks().length){const note=document.createElement('p');note.className='warehouse-empty-floor';note.textContent='Tầng này chưa có kệ. Bấm Thêm kệ, hoặc chuyển kệ từ tầng khác qua Vị trí & tầng.';host.append(note)}
      if(warehouseMode==='racks')sceneStatus('Kéo kệ trên sàn · Bám lưới 0,5 · R xoay kệ · Esc hủy kéo.');
    }catch(error){
      host.innerHTML='<div class="rack-world-error"><strong>Không mở được đồ họa 3D</strong><p>Bạn vẫn có thể sắp xếp máy trên sơ đồ 2D.</p><button class="btn" data-action="layout-depth">Mở sơ đồ 2D</button></div>';
      sceneStatus('Chuyển sang 2D để tiếp tục.');console.error('Rack 3D:',error);
    }
  }).catch(error=>{if(version!==rackSceneVersion||!host.isConnected)return;host.innerHTML='<div class="rack-world-error">Không tải được sơ đồ. <button class="btn" data-action="layout-depth">Mở sơ đồ 2D</button></div>';console.error('Rack 3D:',error)});
};
document.addEventListener('click',e=>{
  const camera=e.target.closest('[data-scene-view]');if(camera){rackScene?.view(camera.dataset.sceneView);return}
  if(!e.target.closest('[data-undo-rack-move]'))return;
  const move=rackMoves.at(-1);if(!move||move.site!==currentSite())return;
  const target=layout.racks.find(r=>r.id===move.to.rack),source=move.from&&layout.racks.find(r=>r.id===move.from.rack);
  if(target?.slots[move.to.index]!==move.id||(move.from&&(!source||source.slots[move.from.index]))){toast('Vị trí đã thay đổi. Không thể hoàn tác bước này.');return}
  target.slots[move.to.index]=null;if(source)source.slots[move.from.index]=move.id;
  rackMoves.pop();render();toast('Đã hoàn tác di chuyển máy.');
});
new MutationObserver(()=>{if(document.getElementById('rack-world-canvas'))render()}).observe(document.documentElement,{attributes:true,attributeFilter:['data-theme']});
document.addEventListener('click',e=>{const result=e.target.closest('[data-find-rack-device]');if(result){focusRackDevice=result.dataset.findRackDevice;const r=locationOf(focusRackDevice)?.rack;if(r?.placement)warehouseEngine.select(r.site,r.placement.floorId)}},true);
document.addEventListener('input',e=>{if(e.target.id==='rack-device-query')rackScene?.highlight()});
document.addEventListener('click',e=>{if(e.target.closest('[data-action="rack-edit"],[data-place-device]'))warehouseMode='inspect'},true);
function warehouseOverlay(){document.getElementById('app').inert=true;let el=document.getElementById('warehouse-expanded');if(!el){el=document.createElement('div');el.id='warehouse-expanded';el.className='warehouse-expanded';el.setAttribute('role','region');el.setAttribute('aria-label','Xưởng 3D toàn màn hình');document.body.append(el)}return el}
function warehouseCloseFullscreen(redraw=true){warehouseExpanded=false;document.getElementById('app').inert=false;document.getElementById('warehouse-expanded')?.remove();if(warehouseOwnFullscreen&&document.fullscreenElement){warehouseOwnFullscreen=false;document.exitFullscreen().catch(()=>{})}if(redraw){render();document.querySelector('[data-warehouse=fullscreen]')?.focus()}}
async function warehouseFullscreen(){
  if(warehouseExpanded){warehouseCloseFullscreen();return}
  warehouseExpanded=true;warehouseOwnFullscreen=document.fullscreenElement===document.documentElement;warehouseOverlay();render();
  if(!document.fullscreenElement&&document.documentElement.requestFullscreen)try{await document.documentElement.requestFullscreen();warehouseOwnFullscreen=true}catch{warehouseOwnFullscreen=false}
  document.querySelector('[data-warehouse=fullscreen]')?.focus();
}
document.addEventListener('fullscreenchange',()=>{if(warehouseExpanded&&warehouseOwnFullscreen&&!document.fullscreenElement){warehouseOwnFullscreen=false;warehouseCloseFullscreen()}});
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&warehouseExpanded&&!document.fullscreenElement&&!document.querySelector('#modal[open]'))warehouseCloseFullscreen()});
function warehouseRackDialog(){
  const r=warehouseEngine.racks(currentSite()).find(r=>r.id===warehouseSelectedRack);if(!r)return;
  const p=r.placement;
  modal('Bố trí '+r.name,'Tọa độ theo ô lưới của bản duyệt. Máy trong kệ được giữ nguyên.',`<input type="hidden" name="rackId" value="${r.id}"><div class="field"><label for="warehouse-rack-floor">Tầng xưởng</label><select id="warehouse-rack-floor" name="floorId">${warehouseEngine.floors(r.site).map(f=>`<option value="${f.id}" ${f.id===p.floorId?'selected':''}>${esc(f.name)}</option>`).join('')}</select></div><div class="field-row"><div class="field"><label for="warehouse-x">Tọa độ X</label><input id="warehouse-x" name="x" type="number" step="0.5" value="${p.x}" required></div><div class="field"><label for="warehouse-z">Tọa độ Z</label><input id="warehouse-z" name="z" type="number" step="0.5" value="${p.z}" required></div></div><div class="field"><label for="warehouse-rotation">Góc xoay</label><select id="warehouse-rotation" name="rotation">${[0,90,180,270].map(v=>`<option value="${v}" ${v===p.rotation?'selected':''}>${v}°</option>`).join('')}</select></div><p class="muted">Kệ không được chồng lên nhau hoặc vượt khỏi sàn. Có thể hoàn tác sau khi lưu.</p>`,'warehouse-rack-form','Lưu bố trí');
}
document.addEventListener('change',e=>{
  if(e.target.id==='warehouse-floor'){warehouseEngine.select(currentSite(),e.target.value);layout.filter='all';layout.pending=null;warehouseSelectedRack=null;render()}
  if(e.target.id==='warehouse-rack'){warehouseSelectedRack=e.target.value;rackScene?.selectRack(warehouseSelectedRack)}
});
document.addEventListener('click',e=>{
  const action=e.target.closest('[data-warehouse]')?.dataset.warehouse;if(!action)return;
  const site=currentSite(),floor=warehouseEngine.floor(site);
  try{
    if(action==='effects'){warehouseEffects=!warehouseEffects;const button=e.target.closest('[data-warehouse]');button.setAttribute('aria-pressed',String(warehouseEffects));button.textContent='Hiệu ứng: '+(warehouseEffects?'Bật':'Tắt');rackScene?.setEffects(warehouseEffects);return}
    if(action==='fullscreen'){warehouseFullscreen();return}
    if(['inspect','machines','racks'].includes(action)){warehouseMode=action==='racks'?'racks':'inspect';layout.edit=action==='machines';layout.pending=null;clearDrag();render();if(action==='racks'){rackScene?.view('top');sceneStatus('Kéo kệ để đổi vị trí. R để xoay kệ đang chọn. Esc hủy kéo.')}return}
    if(action==='add-floor'){modal('Thêm tầng xưởng','Mỗi tầng có bố trí kệ riêng. Kích thước dùng ô lưới, chưa phải số đo thực tế.',`<div class="field"><label for="warehouse-floor-name">Tên tầng</label><input id="warehouse-floor-name" name="name" value="Tầng ${warehouseEngine.floors(site).length+1}" required maxlength="60"></div><div class="field-row"><div class="field"><label for="warehouse-width">Chiều ngang (ô lưới)</label><input id="warehouse-width" name="width" type="number" min="16" max="100" value="40" required></div><div class="field"><label for="warehouse-depth">Chiều sâu (ô lưới)</label><input id="warehouse-depth" name="depth" type="number" min="12" max="100" value="24" required></div></div>`,'warehouse-floor-form','Tạo tầng');return}
    if(action==='rename-floor'){modal('Đổi tên tầng','',`<input type="hidden" name="floorId" value="${floor.id}"><div class="field"><label for="warehouse-floor-name">Tên tầng</label><input id="warehouse-floor-name" name="name" value="${esc(floor.name)}" required maxlength="60"></div>`,'warehouse-floor-rename-form','Lưu tên');return}
    if(action==='delete-floor'){warehouseEngine.removeFloor(site,floor.id);warehouseSelectedRack=null;render();toast('Đã xóa tầng trống.');return}
    if(action==='rack-position'){warehouseRackDialog();return}
    if(action==='rotate'||action==='rotate-left'){const r=layout.racks.find(r=>r.id===warehouseSelectedRack);if(!r)return;warehouseEngine.move(r.id,{...r.placement,rotation:r.placement.rotation+(action==='rotate-left'?-90:90)});render();toast('Đã xoay '+r.name+' · '+r.placement.rotation+'°');return}
    if(action==='undo'){const r=warehouseEngine.undo(site);warehouseSelectedRack=r.id;layout.filter='all';render();toast('Đã hoàn tác bố trí kệ.');return}
  }catch(error){toast(error.message)}
});
document.addEventListener('submit',e=>{
  if(!['warehouse-floor-form','warehouse-floor-rename-form','warehouse-rack-form'].includes(e.target.id))return;
  e.preventDefault();const form=e.target,f=form.elements,site=currentSite();
  try{
    if(form.id==='warehouse-floor-form'){warehouseEngine.addFloor(site,f.namedItem('name').value,+f.width.value,+f.depth.value);layout.filter='all';warehouseSelectedRack=null}
    if(form.id==='warehouse-floor-rename-form')warehouseEngine.renameFloor(site,f.floorId.value,f.namedItem('name').value);
    if(form.id==='warehouse-rack-form'){const r=layout.racks.find(r=>r.id===f.rackId.value);if(!r||r.site!==site)throw Error('Kệ không thuộc xưởng này.');warehouseEngine.move(r.id,{floorId:f.floorId.value,x:+f.x.value,z:+f.z.value,rotation:+f.rotation.value});warehouseEngine.select(site,r.placement.floorId);layout.filter='all';warehouseSelectedRack=r.id}
    document.querySelector('#modal').close();render();toast('Đã cập nhật bố trí trong bản duyệt.');
  }catch(error){toast(error.message)}
});
// Validate space before the existing rack form adds an object to shared state.
document.addEventListener('submit',e=>{if(e.target.id!=='rack-form')return;const f=e.target.elements;try{warehouseEngine.space({id:'new-rack',site:currentSite(),cols:+f.cols.value,rows:+f.rows.value},warehouseEngine.site(currentSite()).active)}catch(error){e.preventDefault();e.stopImmediatePropagation();toast(error.message)}},true);
if(route==='farms')render();
