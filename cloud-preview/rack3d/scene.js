import * as T from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {miningEffects} from './mining-effects.js';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';

const minerTemplates=new Map();
function minerTemplate(kind,base="assets/models/"){
  const key=base+kind;if(!minerTemplates.has(key)){
    const url=base+(kind==='hydro'?'s21-hydro.glb?v=5':'s19-pro-air.glb?v=5');
    const promise=new GLTFLoader().loadAsync(url).then(gltf=>{gltf.scene.traverse(o=>{if(o.geometry)o.geometry.userData.minerShared=true;for(const mat of Array.isArray(o.material)?o.material:[o.material])if(mat)for(const value of Object.values(mat))if(value?.isTexture)value.userData.minerShared=true});return gltf.scene}).catch(error=>{minerTemplates.delete(key);throw error});
    minerTemplates.set(key,promise);
  }
  return minerTemplates.get(key);
}

// Render only when the camera, size or selection changes. Data stays in the host.
export function mount(host,api){
  const scene=new T.Scene(),c=api.colors;
  scene.background=new T.Color(c.bg);
  const renderer=new T.WebGLRenderer({antialias:true});
  renderer.setPixelRatio(Math.min(devicePixelRatio,2));
  renderer.shadowMap.enabled=true;renderer.shadowMap.autoUpdate=false;renderer.shadowMap.type=T.PCFSoftShadowMap;renderer.toneMapping=T.ACESFilmicToneMapping;renderer.toneMappingExposure=1.15;
  host.prepend(renderer.domElement);
  const canvas=renderer.domElement;
  canvas.tabIndex=0;canvas.setAttribute('aria-label','Xưởng 3D: kéo nền để xoay, cuộn để zoom. Dùng sơ đồ 2D để thao tác bằng bàn phím.');
  const camera=new T.PerspectiveCamera(42,1,.1,500);
  const controls=new OrbitControls(camera,canvas);
  controls.maxPolarAngle=Math.PI*.49;controls.minDistance=3;controls.maxDistance=120;
  scene.add(new T.HemisphereLight(0xffffff,0x657080,2.4));
  const light=new T.DirectionalLight(0xffffff,3);light.position.set(5,16,8);light.castShadow=true;light.shadow.mapSize.set(2048,2048);Object.assign(light.shadow.camera,{left:-26,right:26,top:20,bottom:-20,far:65});light.shadow.bias=-.001;scene.add(light);
  const fill=new T.DirectionalLight(0xd9ecff,1.8);fill.position.set(-12,8,-8);scene.add(fill);
  const rackLabels=[],wallSigns=[];
  const slots=[],groups=[],rackMeshes=[],ray=new T.Raycaster(),pointer=new T.Vector2();
  const modelLoads=[];let loadedModels=0;
  const frameMat=new T.MeshStandardMaterial({color:c.frame,roughness:.65,metalness:.35});
  const shelfMat=new T.MeshStandardMaterial({color:c.shelf,roughness:.8});
  const fanMat=new T.MeshStandardMaterial({color:c.fan,roughness:.9});
  const box=new T.BoxGeometry(1,1,1),fanGeo=new T.CylinderGeometry(.28,.28,.025,12),hubGeo=new T.CylinderGeometry(.095,.095,.03,10);
  function block(group,x,y,z,w,h,d,mat){const m=new T.Mesh(box,mat);m.position.set(x,y,z);m.scale.set(w,h,d);m.receiveShadow=true;m.castShadow=h>.15;group.add(m);return m}
  function label(text,x,y,z,width,parent=scene){
    const el=document.createElement('canvas');el.width=512;el.height=96;
    const ctx=el.getContext('2d');ctx.fillStyle=c.labelBg;ctx.fillRect(0,0,512,96);
    ctx.fillStyle=c.text;ctx.font='600 48px Inter, Arial';ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillText(text,256,48,488);
    const texture=new T.CanvasTexture(el);texture.colorSpace=T.SRGBColorSpace;
    const s=new T.Sprite(new T.SpriteMaterial({map:texture,depthTest:true}));s.position.set(x,y,z);s.scale.set(width,width/5.33,1);parent.add(s);
  }
  const racks=api.racks(),columns=Math.min(3,racks.length||1);
  const floorStep=Math.max(9,...racks.map(r=>r.rows*1.12+4));
  const displayFloors=api.allFloors?api.floors:[api.floor];
  const floorY=id=>api.allFloors?Math.max(0,displayFloors.findIndex(f=>f.id===id))*floorStep:0;
  const totalHeight=(displayFloors.length-1)*floorStep+6;controls.maxDistance=Math.max(120,totalHeight*5);
  const span=Math.max(8,...racks.map(r=>r.cols*1.18+1)),height=Math.max(5,...racks.map(r=>r.rows*1.12+1));
  racks.forEach((r,n)=>{
    const w=r.cols*1.18+.35,h=r.rows*1.12+.45,g=new T.Group();
    g.position.set(r.placement.x,floorY(r.placement.floorId),r.placement.z);g.rotation.y=-r.placement.rotation*Math.PI/180;g.userData.r=r;groups.push(g);scene.add(g);
    for(const x of [-w/2,w/2])for(const z of [-.6,.6])block(g,x,h/2,z,.13,h,.13,frameMat);
    for(let row=0;row<=r.rows;row++)block(g,0,row*1.12+.15,0,w+.1,.1,1.4,shelfMat);
    for(let row=0;row<r.rows;row++)for(let col=0;col<r.cols;col++){
      const i=row*r.cols+col,d=api.device(r.slots[i]);
      const color=d?(d.maintenanceState&&d.maintenanceState!=='active'?c.critical:d.offline?c.offline:d.temp>=85?c.critical:d.temp>=75?c.warm:c.normal):c.empty;
      const mat=new T.MeshStandardMaterial({color,roughness:.6,metalness:d ? .2 : 0,transparent:true,opacity:d?1:.3});
      const m=block(g,(col-(r.cols-1)/2)*1.18,(r.rows-row-.5)*1.12+.2,.08,1,.86,1.1,mat);
      m.userData={r,i,d,original:color};slots.push(m);
      if(d){
        const fan=new T.Mesh(fanGeo,fanMat);fan.rotation.x=Math.PI/2;fan.position.set(0,0,.515);m.add(fan);const hub=new T.Mesh(hubGeo,frameMat);hub.rotation.x=Math.PI/2;hub.position.set(0,0,.54);m.add(hub);
        const kind=api.visualModel(d);
        if(kind==='air'||kind==='hydro')modelLoads.push(()=>minerTemplate(kind,api.modelBase).then(template=>{
          if(disposed)return;
          m.remove(fan,hub);
          const clone=template.clone(true),holder=new T.Group();
          holder.scale.set(1/m.scale.x,1/m.scale.y,1/m.scale.z);
          const materials=[];
          clone.traverse(o=>{if(o.isMesh){o.material=(Array.isArray(o.material)?o.material:[o.material]).map(mat=>{const owned=mat.clone();owned.transparent=true;o.castShadow=true;o.receiveShadow=true;materials.push(owned);return owned});if(o.material.length===1)o.material=o.material[0]}});
          holder.add(clone);m.add(holder);m.userData.hasModel=true;m.userData.modelMaterials=materials;
          const strip=new T.Mesh(box,new T.MeshBasicMaterial({color}));strip.position.set(0,.45,.53);strip.scale.set(.85,.035,.03);m.add(strip);
          loadedModels++;host.dataset.loadedModels=String(loadedModels);reset();draw();
        }).catch(()=>{if(!disposed)api.status('Không tải được model '+(kind==='hydro'?'máy nước':'máy gió')+'. Vẫn có thể dùng sơ đồ và sắp xếp vị trí.')}));
      }
    }
    g.traverse(o=>{if(o.isMesh){o.userData.rackGroup=g;rackMeshes.push(o)}});

  });
  const floorWidth=Math.max(...displayFloors.map(f=>f.width)),floorDepth=Math.max(...displayFloors.map(f=>f.depth));
  if(api.allFloors)displayFloors.forEach((floor,index)=>{
    const level=floorY(floor.id);
    if(index){const slabMat=new T.MeshBasicMaterial({color:c.selected,transparent:true,opacity:.08,depthWrite:false,side:T.DoubleSide});const slab=block(scene,0,level-.12,0,floor.width,.12,floor.depth,slabMat);slab.castShadow=false;slab.receiveShadow=false}
    const rim=new T.LineLoop(new T.BufferGeometry().setFromPoints([new T.Vector3(-floor.width/2,level, -floor.depth/2),new T.Vector3(floor.width/2,level,-floor.depth/2),new T.Vector3(floor.width/2,level,floor.depth/2),new T.Vector3(-floor.width/2,level,floor.depth/2)]),new T.LineBasicMaterial({color:c.selected}));scene.add(rim);

  });
  block(scene,0,-.08,0,floorWidth,.12,floorDepth,new T.MeshStandardMaterial({color:c.floor,roughness:1}));
  // Open front and roof: architecture frames the layout without hiding machines.
  const wallMat=new T.MeshStandardMaterial({color:c.shelf,roughness:.85});
  const trimMat=new T.MeshStandardMaterial({color:c.frame,roughness:.55,metalness:.5});
  const hydroMat=new T.MeshStandardMaterial({color:c.selected,roughness:.45,metalness:.25});
  const supplyMat=new T.MeshStandardMaterial({color:c.normal,roughness:.45,metalness:.25});
  const lampMat=new T.MeshBasicMaterial({color:0xfff4dc});
  const hallHeight=Math.max(height+2,8),back=-floorDepth/2;
  function wallSign(title,subtitle,x,y,width,rackId){
    const image=document.createElement('canvas');image.width=1024;image.height=256;
    const ctx=image.getContext('2d');ctx.fillStyle=c.labelBg;ctx.fillRect(0,0,1024,256);
    ctx.fillStyle=c.brand;ctx.fillRect(0,0,16,256);ctx.strokeStyle=c.frame;ctx.lineWidth=8;ctx.strokeRect(4,4,1016,248);
    ctx.fillStyle=c.text;ctx.textAlign='center';ctx.textBaseline='middle';ctx.font='700 76px Arial';ctx.fillText(title,520,subtitle?94:128,950);
    if(subtitle){ctx.font='36px Arial';ctx.fillText(subtitle,520,188,940)}
    const texture=new T.CanvasTexture(image);texture.colorSpace=T.SRGBColorSpace;
    const plaque=new T.Mesh(new T.PlaneGeometry(width,width/4),new T.MeshBasicMaterial({map:texture,toneMapped:false}));
    plaque.position.set(x,y,back+.38);scene.add(plaque);
    if(rackId){plaque.userData.rackId=rackId;wallSigns.push(plaque);rackLabels.push({plaque,rackId})}
    return plaque;
  }
  for(const floor of displayFloors){
    const level=floorY(floor.id),floorRacks=racks.filter(r=>r.placement.floorId===floor.id).sort((a,b)=>a.placement.x-b.placement.x);
    if(level)block(scene,0,level+hallHeight/2,back,floorWidth,hallHeight,.18,wallMat);
    const boardWidth=Math.min(6,(floorWidth-4)/Math.max(1,floorRacks.length)-.4);
    floorRacks.forEach((rack,index)=>{
      const x=(index-(floorRacks.length-1)/2)*Math.min(10,(floorWidth-4)/Math.max(1,floorRacks.length));
      wallSign(rack.name+' · '+rack.slots.filter(Boolean).length+'/'+rack.slots.length,floor.name+' · '+rack.zone,x,level+height+.7,boardWidth,rack.id);
    });
    if(api.allFloors)wallSign(floor.name,'',-floorWidth/2+3.5,level+hallHeight-.6,4);
  }

  block(scene,0,hallHeight/2,back,floorWidth,hallHeight,.18,wallMat);
  block(scene,-floorWidth/2,hallHeight/2,0,.18,hallHeight,floorDepth,wallMat);
  // Wall panels, steel columns and overhead service beams.
  for(let x=-floorWidth/2+2;x<floorWidth/2;x+=4){
    block(scene,x,hallHeight/2,back+.12,.08,hallHeight,.08,trimMat);
    block(scene,x,hallHeight-.25,back+.5,.12,.22,1,trimMat);
    block(scene,x,hallHeight-.45,back+.7,1.8,.06,.32,lampMat);

  }
  for(const z of [back,floorDepth/2])for(const x of [-floorWidth/2,floorWidth/2])block(scene,x,hallHeight/2,z,.22,hallHeight,.22,trimMat);
  block(scene,0,hallHeight,back,floorWidth,.2,.25,trimMat);block(scene,-floorWidth/2,hallHeight,0,.25,.2,floorDepth,trimMat);
  // A perimeter cooling skid is illustrative, independent of manually assigned groups.
  const skid=new T.Group();skid.position.set(floorWidth/2-3,0,back+2);scene.add(skid);
  block(skid,0,.2,0,3.6,.3,1.8,trimMat);
  block(skid,0,1,0,3.2,1.3,1.5,wallMat);
  for(const x of [-.85,.85]){
    const fan=new T.Mesh(new T.CylinderGeometry(.52,.52,.1,24),fanMat);fan.position.set(x,1.7,0);skid.add(fan);
    for(let i=0;i<4;i++){const blade=block(skid,x,1.77,0,.8,.025,.1,trimMat);blade.rotation.y=i*Math.PI/4;}
  }
  label('BỘ TẢN · MINH HỌA',0,2.4,0,3.5,skid);
  for(const [offset,material] of [[0,hydroMat],[.25,supplyMat]]){
    block(scene,0,2.2+offset,back+.4,floorWidth-4,.09,.09,material);
    block(scene,floorWidth/2-3,1.3,back+.45,.09,1.8,.09,material);
  }
  // Ventilation bank and power cabinet on the rear wall.
  for(let x=-floorWidth/2+3;x<-floorWidth/2+11;x+=2.5){
    block(scene,x,3,back+.18,1.8,1.8,.25,trimMat);
    const vent=new T.Mesh(new T.CylinderGeometry(.68,.68,.12,20),fanMat);vent.rotation.x=Math.PI/2;vent.position.set(x,3,back+.36);scene.add(vent);
    for(let v=-.5;v<=.5;v+=.25)block(scene,x,3+v,back+.45,1.3,.035,.04,wallMat);
  }
  block(scene,-floorWidth/2+1,1.1,back+3,1.2,2.2,.8,trimMat);
  const brandSign=wallSign('BEESKY · MINING WORKSHOP','',0,height+1,8);brandSign.rotation.y=Math.PI/2;brandSign.position.set(-floorWidth/2+.25,height+1,0);
  const safetyMat=new T.MeshBasicMaterial({color:c.brand});
  // Mark the perimeter service route; the central floor stays free for rack layout.
  for(const z of [-floorDepth/2+3,floorDepth/2-3]){
    block(scene,0,.012,z,floorWidth-4,.02,.055,safetyMat);
    for(let x=-floorWidth/2+2;x<floorWidth/2-2;x+=2)block(scene,x,.014,z+.5,.7,.02,.07,safetyMat);
  }
  const grid=new T.GridHelper(floorWidth,Math.ceil(floorWidth),c.grid,c.grid);grid.scale.z=floorDepth/floorWidth;grid.position.y=.001;grid.material.transparent=true;grid.material.opacity=.22;scene.add(grid);
  const extent=new T.Box3();groups.forEach(g=>extent.expandByObject(g));
  const center=extent.isEmpty()?new T.Vector3(0,1.5,0):extent.getCenter(new T.Vector3());if(!api.allFloors)center.y=height*.4;
  const size=extent.isEmpty()?new T.Vector3(20,5,12):extent.getSize(new T.Vector3());
  const selection=new T.BoxHelper(new T.Object3D(),c.selected);selection.visible=false;scene.add(selection);
  function selectRack(id){const g=groups.find(g=>g.userData.r.id===id);selection.visible=!!g;if(g)selection.setFromObject(g);draw()}
  function updateRackLabels(){
    for(const {plaque,rackId} of rackLabels)plaque.material.color.set(rackId===api.selectedRack()?0xffffff:0xd9dfe6);
  }
  function focusRack(id){
    const group=groups.find(g=>g.userData.r.id===id);if(!group)return;
    const target=new T.Box3().setFromObject(group).getCenter(new T.Vector3());
    controls.target.copy(target);camera.position.copy(target).add(new T.Vector3(4,4,12));controls.update();selectRack(id);draw();
  }
  function draw(){renderer.shadowMap.needsUpdate=true;renderer.render(scene,camera);updateRackLabels()}
  function view(mode='hall'){
    if(mode==='hall'){controls.target.set(0,api.allFloors?totalHeight/2:1.5,0);const dist=Math.max(floorWidth*1.05,floorDepth*1.5,totalHeight*1.4)*Math.max(1,1.25/camera.aspect);camera.position.set(dist*.58,dist*.65+(api.allFloors?totalHeight/2:0),dist*.85);controls.update();draw();return}
    controls.target.copy(center);const dist=Math.max(12,size.x*.95,size.z*.95,size.y*1.5,height*2)*Math.max(1,1.6/camera.aspect);
    if(mode==='front')camera.position.set(center.x,center.y,center.z+dist);
    else if(mode==='top')camera.position.set(center.x,dist*1.2,center.z+.01);
    else camera.position.set(center.x+dist*.35,height+dist*.26,center.z+dist*.8);
    controls.update();draw();
  }
  controls.addEventListener('change',draw);
  function resize(){const w=host.clientWidth,h=host.clientHeight,old=camera.aspect;renderer.setSize(w,h);camera.aspect=w/Math.max(h,1);camera.updateProjectionMatrix();if(Math.abs(old-camera.aspect)>.3)view();else draw()}
  const observer=new ResizeObserver(resize);observer.observe(host);
  let down=null,drag=null,rackDrag=null,disposed=false;
  function aim(e){const rect=canvas.getBoundingClientRect();pointer.set((e.clientX-rect.left)/rect.width*2-1,-(e.clientY-rect.top)/rect.height*2+1);ray.setFromCamera(pointer,camera)}
  function hit(e){aim(e);return ray.intersectObjects(slots,false)[0]?.object}
  function hitRack(e){aim(e);return ray.intersectObjects(rackMeshes,false)[0]?.object.userData.rackGroup}
  const groundPlane=new T.Plane(new T.Vector3(0,1,0),0);
  function ground(e){aim(e);return ray.ray.intersectPlane(groundPlane,new T.Vector3())}
  function reset(){const ids=api.matches();slots.forEach(m=>{const dim=api.query()&&!ids.has(m.userData.d?.id);m.material.emissive.set(ids.has(m.userData.d?.id)?c.selected:0x000000);m.material.opacity=dim ? .12 : m.userData.hasModel ? .045 : m.userData.d ? 1 : .3;for(const material of m.userData.modelMaterials||[])material.opacity=dim ? .15 : 1})}
  function describe(m){if(m){const {r,i,d}=m.userData;api.status((d?d.ip+' · '+(d.offline?'Mất kết nối':d.temp+'°C'):'Ô trống')+' · '+api.position(r,i))}}
  function start(e){if(e.button!==0)return;const m=hit(e);down={x:e.clientX,y:e.clientY,m};if(api.mode()==='racks'){const g=hitRack(e),p=ground(e);if(g&&p){api.selectRack(g.userData.r.id);selectRack(g.userData.r.id);rackDrag={g,old:g.position.clone(),offset:p.sub(g.position),next:null,error:'',moved:false};controls.enabled=false;canvas.setPointerCapture(e.pointerId);canvas.focus({preventScroll:true})}}else if(api.edit()&&m?.userData.d){controls.enabled=false;canvas.setPointerCapture(e.pointerId)}}
  function move(e){
    if(rackDrag){const p=ground(e);if(p&&Math.hypot(e.clientX-down.x,e.clientY-down.y)>6){const {g}=rackDrag;const next={...g.userData.r.placement,x:Math.round((p.x-rackDrag.offset.x)*2)/2,z:Math.round((p.z-rackDrag.offset.z)*2)/2};rackDrag.next=next;rackDrag.error=api.validateRack(g.userData.r,next);rackDrag.moved=true;g.position.set(next.x,0,next.z);selection.setFromObject(g);selection.material.color.set(rackDrag.error?c.critical:c.selected);api.status(rackDrag.error||g.userData.r.name+' · X '+next.x+' · Z '+next.z+' · Thả để lưu vị trí');canvas.style.cursor='grabbing';api.hover(null);draw()}return}
    const m=hit(e);if(down&&api.edit()&&down.m?.userData.d&&Math.hypot(e.clientX-down.x,e.clientY-down.y)>6){drag=down.m;canvas.style.cursor='grabbing'}reset();if(drag){api.hover(null);drag.material.emissive.set(c.selected);if(m&&m!==drag){m.material.emissive.set(m.userData.d?c.critical:c.selected);api.status(m.userData.d?'Ô đã có máy. Chọn ô trống.':'Thả để chuyển '+drag.userData.d.ip+' → '+api.position(m.userData.r,m.userData.i))}}else{canvas.style.cursor=api.mode()==='racks'&&hitRack(e)?'grab':api.edit()&&m?.userData.d?'grab':m?'pointer':'default';if(m){m.material.emissive.set(c.selected);describe(m)}const rect=canvas.getBoundingClientRect();api.hover(m?.userData.d?{...m.userData,x:e.clientX-rect.left,y:e.clientY-rect.top}:null)}draw()
  }
  function end(e){aim(e);const sign=ray.intersectObjects(wallSigns,false)[0]?.object;if(sign&&down&&api.mode()==='inspect'&&!api.edit()&&Math.hypot(e.clientX-down.x,e.clientY-down.y)<6){controls.enabled=true;down=null;api.selectRack(sign.userData.rackId);focusRack(sign.userData.rackId);return}const m=hit(e),wasDrag=drag;controls.enabled=true;if(canvas.hasPointerCapture(e.pointerId))canvas.releasePointerCapture(e.pointerId);if(rackDrag){const data=rackDrag;rackDrag=null;data.g.position.copy(data.old);if(data.moved&&data.next){if(data.error)api.status(data.error+' Vị trí cũ được giữ nguyên.');else api.moveRack(data.g.userData.r,data.next)}down=null;selection.material.color.set(c.selected);if(!disposed){selectRack(api.selectedRack());draw()}return}if(api.mode()==='racks'){down=null;return}if(drag&&m&&m!==drag){if(m.userData.d)api.status('Ô đã có máy. Vị trí cũ được giữ nguyên.');else api.move(drag.userData.d.id,m.userData.r,m.userData.i)}else if(down&&!wasDrag&&Math.hypot(e.clientX-down.x,e.clientY-down.y)<6&&m){if(api.pending()&&!m.userData.d)api.move(api.pending(),m.userData.r,m.userData.i);else api.inspect(m.userData.r,m.userData.i)}down=null;drag=null;reset();if(!disposed)draw()}
  function cancel(){if(rackDrag){rackDrag.g.position.copy(rackDrag.old);rackDrag=null;selection.material.color.set(c.selected);selectRack(api.selectedRack())}down=null;drag=null;controls.enabled=true;reset();api.hover(null);draw()}
  function over(e){if(!api.dragged())return;const m=hit(e);reset();if(m&&!m.userData.d){e.preventDefault();e.dataTransfer.dropEffect='move';m.material.emissive.set(c.selected);describe(m)}draw()}
  function drop(e){const id=api.dragged(),m=hit(e);if(!id||!m||m.userData.d)return;e.preventDefault();if(e.dataTransfer.getData('application/x-beesky-device')===id)api.move(id,m.userData.r,m.userData.i)}
  // Run before OrbitControls handles pointerdown, so moving a machine never orbits.
  canvas.addEventListener('pointerdown',start,true);canvas.addEventListener('pointermove',move);canvas.addEventListener('pointerup',end);canvas.addEventListener('pointercancel',cancel);canvas.addEventListener('dragover',over);canvas.addEventListener('drop',drop);
  canvas.addEventListener('pointerleave',()=>{if(!drag&&!rackDrag)api.hover(null)});
  const escape=e=>{if(e.key==='Escape'){cancel();api.status('Đã hủy thao tác kéo.')}if(e.code==='KeyR'&&document.activeElement===canvas&&api.mode()==='racks'&&!rackDrag){const r=racks.find(r=>r.id===api.selectedRack());if(r){e.preventDefault();api.moveRack(r,{...r.placement,rotation:r.placement.rotation+90})}}};window.addEventListener('keydown',escape);
  function focusDevice(id){const m=slots.find(s=>s.userData.d?.id===id);if(!m)return;const pos=new T.Vector3();m.getWorldPosition(pos);controls.target.copy(pos);camera.position.copy(pos).add(new T.Vector3(1.8,1.5,7));controls.update();describe(m);reset();draw()}
  resize();view(api.mode()==='racks'?'top':'hall');selectRack(api.selectedRack());
  if(api.camera){camera.position.fromArray(api.camera.position);controls.target.fromArray(api.camera.target);controls.update()}
  reset();draw();
  const effects=miningEffects(scene,slots,host,{...api,enabled:api.effects},()=>renderer.render(scene,camera));
  modelLoads.forEach(load=>load());
  return {view,selectRack,focusDevice,setEffects(value){effects.setEnabled(value)},highlight(){reset();effects.refresh();draw()},cameraState(){return{position:camera.position.toArray(),target:controls.target.toArray()}},dispose(){if(disposed)return;disposed=true;effects.dispose();observer.disconnect();controls.dispose();window.removeEventListener('keydown',escape);api.hover(null);const geometries=new Set(),materials=new Set();scene.traverse(o=>{if(o.geometry&&!o.geometry.userData.minerShared)geometries.add(o.geometry);for(const material of Array.isArray(o.material)?o.material:[o.material])if(material)materials.add(material)});materials.forEach(m=>{for(const texture of Object.values(m))if(texture?.isTexture&&!texture.userData.minerShared)texture.dispose();m.dispose()});geometries.forEach(g=>g.dispose());renderer.dispose();renderer.forceContextLoss();canvas.remove()}};
}

