import * as T from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';

const minerTemplates=new Map();
function minerTemplate(kind){
  if(!minerTemplates.has(kind)){
    const url=kind==='hydro'?'assets/models/s21-hydro.glb':'assets/models/s19-pro-air.glb';
    const promise=new GLTFLoader().loadAsync(url).then(gltf=>{gltf.scene.traverse(o=>{if(o.geometry)o.geometry.userData.minerShared=true;for(const mat of Array.isArray(o.material)?o.material:[o.material])if(mat)for(const value of Object.values(mat))if(value?.isTexture)value.userData.minerShared=true});return gltf.scene}).catch(error=>{minerTemplates.delete(kind);throw error});
    minerTemplates.set(kind,promise);
  }
  return minerTemplates.get(kind);
}

// Render only when the camera, size or selection changes. Data stays in the host.
export function mount(host,api){
  const scene=new T.Scene(),c=api.colors;
  scene.background=new T.Color(c.bg);
  const renderer=new T.WebGLRenderer({antialias:true});
  renderer.setPixelRatio(Math.min(devicePixelRatio,2));
  host.prepend(renderer.domElement);
  const canvas=renderer.domElement;
  canvas.tabIndex=0;canvas.setAttribute('aria-label','Xưởng 3D: kéo nền để xoay, cuộn để zoom. Dùng sơ đồ 2D để thao tác bằng bàn phím.');
  const camera=new T.PerspectiveCamera(42,1,.1,500);
  const controls=new OrbitControls(camera,canvas);
  controls.maxPolarAngle=Math.PI*.49;controls.minDistance=3;controls.maxDistance=120;
  scene.add(new T.HemisphereLight(0xffffff,0x657080,2.4));
  const light=new T.DirectionalLight(0xffffff,3);light.position.set(5,12,8);scene.add(light);
  const slots=[],groups=[],rackMeshes=[],ray=new T.Raycaster(),pointer=new T.Vector2();
  const modelLoads=[];let loadedModels=0;
  const frameMat=new T.MeshStandardMaterial({color:c.frame,roughness:.65,metalness:.35});
  const shelfMat=new T.MeshStandardMaterial({color:c.shelf,roughness:.8});
  const fanMat=new T.MeshStandardMaterial({color:c.fan,roughness:.9});
  const box=new T.BoxGeometry(1,1,1),fanGeo=new T.CylinderGeometry(.28,.28,.025,12),hubGeo=new T.CylinderGeometry(.095,.095,.03,10);
  function block(group,x,y,z,w,h,d,mat){const m=new T.Mesh(box,mat);m.position.set(x,y,z);m.scale.set(w,h,d);group.add(m);return m}
  function label(text,x,y,z,width,parent=scene){
    const el=document.createElement('canvas');el.width=512;el.height=96;
    const ctx=el.getContext('2d');ctx.fillStyle=c.labelBg;ctx.fillRect(0,0,512,96);
    ctx.fillStyle=c.text;ctx.font='600 48px Inter, Arial';ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillText(text,256,48,488);
    const texture=new T.CanvasTexture(el);texture.colorSpace=T.SRGBColorSpace;
    const s=new T.Sprite(new T.SpriteMaterial({map:texture,depthTest:false}));s.position.set(x,y,z);s.scale.set(width,width/5.33,1);parent.add(s);
  }
  const racks=api.racks(),columns=Math.min(3,racks.length||1);
  const span=Math.max(8,...racks.map(r=>r.cols*1.18+1)),height=Math.max(5,...racks.map(r=>r.rows*1.12+1));
  racks.forEach((r,n)=>{
    const w=r.cols*1.18+.35,h=r.rows*1.12+.45,g=new T.Group();
    g.position.set(r.placement.x,0,r.placement.z);g.rotation.y=-r.placement.rotation*Math.PI/180;g.userData.r=r;groups.push(g);scene.add(g);
    for(const x of [-w/2,w/2])for(const z of [-.6,.6])block(g,x,h/2,z,.13,h,.13,frameMat);
    for(let row=0;row<=r.rows;row++)block(g,0,row*1.12+.15,0,w+.1,.1,1.4,shelfMat);
    for(let row=0;row<r.rows;row++)for(let col=0;col<r.cols;col++){
      const i=row*r.cols+col,d=api.device(r.slots[i]);
      const color=d?(d.offline?c.offline:d.temp>=85?c.critical:d.temp>=75?c.warm:c.normal):c.empty;
      const mat=new T.MeshStandardMaterial({color,roughness:.6,metalness:d ? .2 : 0,transparent:true,opacity:d?1:.3});
      const m=block(g,(col-(r.cols-1)/2)*1.18,(r.rows-row-.5)*1.12+.2,.08,1,.86,1.1,mat);
      m.userData={r,i,d,original:color};slots.push(m);
      if(d){
        const fan=new T.Mesh(fanGeo,fanMat);fan.rotation.x=Math.PI/2;fan.position.set(0,0,.515);m.add(fan);const hub=new T.Mesh(hubGeo,frameMat);hub.rotation.x=Math.PI/2;hub.position.set(0,0,.54);m.add(hub);
        const kind=api.visualModel(d);
        if(kind==='air'||kind==='hydro')modelLoads.push(()=>minerTemplate(kind).then(template=>{
          if(disposed)return;
          m.remove(fan,hub);
          const clone=template.clone(true),holder=new T.Group();
          holder.scale.set(1/m.scale.x,1/m.scale.y,1/m.scale.z);
          const materials=[];
          clone.traverse(o=>{if(o.isMesh){o.material=(Array.isArray(o.material)?o.material:[o.material]).map(mat=>{const owned=mat.clone();owned.transparent=true;materials.push(owned);return owned});if(o.material.length===1)o.material=o.material[0]}});
          holder.add(clone);m.add(holder);m.userData.hasModel=true;m.userData.modelMaterials=materials;
          const strip=new T.Mesh(box,new T.MeshBasicMaterial({color}));strip.position.set(0,.45,.53);strip.scale.set(.85,.035,.03);m.add(strip);
          loadedModels++;host.dataset.loadedModels=String(loadedModels);reset();draw();
        }).catch(()=>{if(!disposed)api.status('Không tải được model '+(kind==='hydro'?'máy nước':'máy gió')+'. Vẫn có thể dùng sơ đồ và sắp xếp vị trí.')}));
      }
    }
    g.traverse(o=>{if(o.isMesh){o.userData.rackGroup=g;rackMeshes.push(o)}});
    label(r.name+' · '+r.slots.filter(Boolean).length+'/'+r.slots.length,0,h+.65,0,Math.min(w,7),g);
    label(r.zone,0,.03,1.5,Math.min(w,5),g);
  });
  const floorWidth=api.floor.width,floorDepth=api.floor.depth;
  block(scene,0,-.08,0,floorWidth,.12,floorDepth,new T.MeshStandardMaterial({color:c.floor,roughness:1}));
  // A cutaway hall keeps all rack fronts visible.
  block(scene,0,.7,-floorDepth/2,floorWidth,1.4,.15,shelfMat);
  block(scene,-floorWidth/2,.7,0,.15,1.4,floorDepth,shelfMat);
  const safetyMat=new T.MeshStandardMaterial({color:c.brand,roughness:1});
  for(let lane=0;lane<Math.max(1,Math.floor(floorDepth/6));lane++){
    const z=-floorDepth/2+lane*6+3;
    block(scene,0,.015,z,floorWidth-2,.025,.07,safetyMat);
    block(scene,0,.015,z+1.25,floorWidth-2,.025,.07,safetyMat);
    for(let x=-floorWidth/2+1;x<floorWidth/2-1;x+=2)block(scene,x,.015,z+.63,.65,.025,.08,safetyMat);
  }
  for(const x of [-floorWidth/2,floorWidth/2])for(const z of [-floorDepth/2,floorDepth/2])block(scene,x,height/2,z,.2,height,.2,frameMat);
  const grid=new T.GridHelper(floorWidth,Math.ceil(floorWidth),c.grid,c.grid);grid.scale.z=floorDepth/floorWidth;grid.position.y=.001;scene.add(grid);
  const extent=new T.Box3();groups.forEach(g=>extent.expandByObject(g));
  const center=extent.isEmpty()?new T.Vector3(0,1.5,0):extent.getCenter(new T.Vector3());center.y=height*.4;
  const size=extent.isEmpty()?new T.Vector3(20,5,12):extent.getSize(new T.Vector3());
  const selection=new T.BoxHelper(new T.Object3D(),c.selected);selection.visible=false;scene.add(selection);
  function selectRack(id){const g=groups.find(g=>g.userData.r.id===id);selection.visible=!!g&&api.mode()==='racks';if(g)selection.setFromObject(g);draw()}
  function draw(){renderer.render(scene,camera)}
  function view(mode='overview'){
    controls.target.copy(center);const dist=Math.max(12,size.x*.95,size.z*.95,height*2)*Math.max(1,1.6/camera.aspect);
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
  function end(e){const m=hit(e),wasDrag=drag;controls.enabled=true;if(canvas.hasPointerCapture(e.pointerId))canvas.releasePointerCapture(e.pointerId);if(rackDrag){const data=rackDrag;rackDrag=null;data.g.position.copy(data.old);if(data.moved&&data.next){if(data.error)api.status(data.error+' Vị trí cũ được giữ nguyên.');else api.moveRack(data.g.userData.r,data.next)}down=null;selection.material.color.set(c.selected);if(!disposed){selectRack(api.selectedRack());draw()}return}if(api.mode()==='racks'){down=null;return}if(drag&&m&&m!==drag){if(m.userData.d)api.status('Ô đã có máy. Vị trí cũ được giữ nguyên.');else api.move(drag.userData.d.id,m.userData.r,m.userData.i)}else if(down&&!wasDrag&&Math.hypot(e.clientX-down.x,e.clientY-down.y)<6&&m){if(api.pending()&&!m.userData.d)api.move(api.pending(),m.userData.r,m.userData.i);else api.inspect(m.userData.r,m.userData.i)}down=null;drag=null;reset();if(!disposed)draw()}
  function cancel(){if(rackDrag){rackDrag.g.position.copy(rackDrag.old);rackDrag=null;selection.material.color.set(c.selected);selectRack(api.selectedRack())}down=null;drag=null;controls.enabled=true;reset();api.hover(null);draw()}
  function over(e){if(!api.dragged())return;const m=hit(e);reset();if(m&&!m.userData.d){e.preventDefault();e.dataTransfer.dropEffect='move';m.material.emissive.set(c.selected);describe(m)}draw()}
  function drop(e){const id=api.dragged(),m=hit(e);if(!id||!m||m.userData.d)return;e.preventDefault();if(e.dataTransfer.getData('application/x-beesky-device')===id)api.move(id,m.userData.r,m.userData.i)}
  // Run before OrbitControls handles pointerdown, so moving a machine never orbits.
  canvas.addEventListener('pointerdown',start,true);canvas.addEventListener('pointermove',move);canvas.addEventListener('pointerup',end);canvas.addEventListener('pointercancel',cancel);canvas.addEventListener('dragover',over);canvas.addEventListener('drop',drop);
  canvas.addEventListener('pointerleave',()=>{if(!drag&&!rackDrag)api.hover(null)});
  const escape=e=>{if(e.key==='Escape'){cancel();api.status('Đã hủy thao tác kéo.')}if(e.code==='KeyR'&&document.activeElement===canvas&&api.mode()==='racks'&&!rackDrag){const r=racks.find(r=>r.id===api.selectedRack());if(r){e.preventDefault();api.moveRack(r,{...r.placement,rotation:r.placement.rotation+90})}}};window.addEventListener('keydown',escape);
  function focusDevice(id){const m=slots.find(s=>s.userData.d?.id===id);if(!m)return;const pos=new T.Vector3();m.getWorldPosition(pos);controls.target.copy(pos);camera.position.copy(pos).add(new T.Vector3(1.8,1.5,7));controls.update();describe(m);reset();draw()}
  resize();view(api.mode()==='racks'?'top':'overview');selectRack(api.selectedRack());
  if(api.camera){camera.position.fromArray(api.camera.position);controls.target.fromArray(api.camera.target);controls.update()}
  reset();draw();
  modelLoads.forEach(load=>load());
  return {view,selectRack,focusDevice,highlight(){reset();draw()},cameraState(){return{position:camera.position.toArray(),target:controls.target.toArray()}},dispose(){if(disposed)return;disposed=true;observer.disconnect();controls.dispose();window.removeEventListener('keydown',escape);api.hover(null);const geometries=new Set(),materials=new Set();scene.traverse(o=>{if(o.geometry&&!o.geometry.userData.minerShared)geometries.add(o.geometry);for(const material of Array.isArray(o.material)?o.material:[o.material])if(material)materials.add(material)});materials.forEach(m=>{for(const texture of Object.values(m))if(texture?.isTexture&&!texture.userData.minerShared)texture.dispose();m.dispose()});geometries.forEach(g=>g.dispose());renderer.dispose();renderer.forceContextLoss();canvas.remove()}};
}
