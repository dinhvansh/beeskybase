'use strict';
// Bridge the 3D view to the exact same rack/slot identity used by the 2D view.
let rackScene=null,rackSceneVersion=0;
let sceneKey='',sceneCamera=null,focusRackDevice=null;
const rackMoves=[];
const before3dReset=resetDemo;
resetDemo=function(){before3dReset();rackMoves.length=0;sceneCamera=null;focusRackDevice=null};
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
  html=html.replace('Đang xem 3D','Chuyển sang 2D').replace('Xem 3D','Xem xưởng 3D');
  if(layout.depth===false)return html;
  const panel=`<section class="panel rack-world" aria-label="Sơ đồ xưởng 3D"><header class="rack-world-toolbar"><strong>Xưởng 3D</strong><div><button type="button" class="btn small" data-scene-view="overview">Phối cảnh</button><button type="button" class="btn small" data-scene-view="front">Mặt trước</button><button type="button" class="btn small" data-scene-view="top">Từ trên</button><button type="button" class="btn small" data-undo-rack-move ${rackMoves.at(-1)?.site===currentSite()?'':'disabled'}>Hoàn tác</button></div></header><div id="rack-world-canvas" class="rack-world-canvas"><p class="rack-world-loading" role="status">Đang tải sơ đồ 3D…</p></div><div id="rack-world-status" class="rack-world-status" role="status" aria-live="polite">${layout.edit?'Kéo máy đến ô trống. Esc để hủy.':'Kéo nền để xoay · Cuộn để zoom · Bấm máy để xem chi tiết.'}</div><footer class="rack-world-footer"><span>${layout.edit?'Đang sắp xếp vị trí':'Bật “Sắp xếp vị trí” để kéo máy trong rack.'}</span><span>Dữ liệu mẫu · Vị trí chỉ lưu trong phiên</span></footer></section>`;
  return html.replace('<div class="rack-boards">',panel+'<div class="rack-boards rack-2d-fallback">').replace('Kéo máy thả vào ô trống trên rack.','Kéo máy vào ô trống trong 3D hoặc bấm Chọn vị trí.');
};
function sceneStatus(message){const el=document.getElementById('rack-world-status');if(el)el.textContent=message}
const before3dRender=render;
render=function(){
  const key=currentSite()+':'+layout.filter;
  if(rackScene&&sceneKey===key)sceneCamera=rackScene.cameraState();else if(sceneKey!==key)sceneCamera=null;
  sceneKey=key;
  const version=++rackSceneVersion;rackScene?.dispose();rackScene=null;
  before3dRender();
  const host=document.getElementById('rack-world-canvas');if(!host)return;
  import('./rack-scene.js?v=1').then(module=>{
    if(version!==rackSceneVersion||!host.isConnected)return;
    const style=getComputedStyle(document.documentElement),token=(name,fallback)=>style.getPropertyValue(name).trim()||fallback;
    const dark=document.documentElement.dataset.theme==='dark';
    const colors={bg:token('--bg',dark?'#101113':'#f6f7f9'),floor:token('--surface2',dark?'#23272e':'#e9edf2'),grid:token('--border','#b9c3cd'),brand:token('--brand','#facc15'),frame:token('--rack-frame','#53677e'),shelf:token('--rack-shelf','#b5c1ce'),fan:token('--rack-fan','#304052'),normal:token('--green','#16a34a'),warm:token('--amber','#d97706'),critical:token('--red','#dc2626'),offline:token('--muted','#64748b'),empty:token('--border','#cbd5e1'),selected:token('--info','#285fca'),text:token('--text','#18202e'),labelBg:token('--surface','#ffffff')};
    try{
      rackScene=module.mount(host,{colors,camera:sceneCamera,query:()=>rackQuery().trim(),matches:()=>new Set(matchingRackDevices().map(({d})=>d.id)),racks:()=>racksFor(currentSite()).filter(r=>layout.filter==='all'||r.id===layout.filter),device:id=>layout.devices.find(d=>d.id===id),position,edit:()=>layout.edit,pending:()=>layout.pending,dragged:()=>draggedDevice,status:sceneStatus,inspect:(r,i)=>layout.edit?editSlot(r,i):inspectSlot(r,i),move:(id,r,i)=>{try{moveRackDevice(id,r,i)}catch(err){sceneStatus(err.message)}}});
      if(focusRackDevice){rackScene.focusDevice(focusRackDevice);focusRackDevice=null}
      host.querySelector('.rack-world-loading')?.remove();
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
document.addEventListener('click',e=>{const result=e.target.closest('[data-find-rack-device]');if(result)focusRackDevice=result.dataset.findRackDevice},true);
document.addEventListener('input',e=>{if(e.target.id==='rack-device-query')rackScene?.highlight()});
if(route==='farms')render();
