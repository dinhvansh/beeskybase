import * as T from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';

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
  const slots=[],ray=new T.Raycaster(),pointer=new T.Vector2();
  const frameMat=new T.MeshStandardMaterial({color:c.frame,roughness:.65,metalness:.35});
  const shelfMat=new T.MeshStandardMaterial({color:c.shelf,roughness:.8});
  const fanMat=new T.MeshStandardMaterial({color:c.fan,roughness:.9});
  const box=new T.BoxGeometry(1,1,1),fanGeo=new T.CylinderGeometry(.28,.28,.025,12),hubGeo=new T.CylinderGeometry(.095,.095,.03,10);
  function block(group,x,y,z,w,h,d,mat){const m=new T.Mesh(box,mat);m.position.set(x,y,z);m.scale.set(w,h,d);group.add(m);return m}
  function label(text,x,y,z,width){
    const el=document.createElement('canvas');el.width=512;el.height=96;
    const ctx=el.getContext('2d');ctx.fillStyle=c.labelBg;ctx.fillRect(0,0,512,96);
    ctx.fillStyle=c.text;ctx.font='600 48px Inter, Arial';ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillText(text,256,48,488);
    const texture=new T.CanvasTexture(el);texture.colorSpace=T.SRGBColorSpace;
    const s=new T.Sprite(new T.SpriteMaterial({map:texture,depthTest:false}));s.position.set(x,y,z);s.scale.set(width,width/5.33,1);scene.add(s);
  }
  const racks=api.racks(),columns=Math.min(3,racks.length||1);
  const span=Math.max(8,...racks.map(r=>r.cols*1.18+1)),height=Math.max(5,...racks.map(r=>r.rows*1.12+1));
  racks.forEach((r,n)=>{
    const w=r.cols*1.18+.35,h=r.rows*1.12+.45,g=new T.Group();
    g.position.set((n%columns-(columns-1)/2)*(span+2),0,Math.floor(n/columns)*5);scene.add(g);
    for(const x of [-w/2,w/2])for(const z of [-.6,.6])block(g,x,h/2,z,.13,h,.13,frameMat);
    for(let row=0;row<=r.rows;row++)block(g,0,row*1.12+.15,0,w+.1,.1,1.4,shelfMat);
    for(let row=0;row<r.rows;row++)for(let col=0;col<r.cols;col++){
      const i=row*r.cols+col,d=api.device(r.slots[i]);
      const color=d?(d.offline?c.offline:d.temp>=85?c.critical:d.temp>=75?c.warm:c.normal):c.empty;
      const mat=new T.MeshStandardMaterial({color,roughness:.6,metalness:d ? .2 : 0,transparent:true,opacity:d?1:.3});
      const m=block(g,(col-(r.cols-1)/2)*1.18,(r.rows-row-.5)*1.12+.2,.08,1,.86,1.1,mat);
      m.userData={r,i,d,original:color};slots.push(m);
      if(d){const fan=new T.Mesh(fanGeo,fanMat);fan.rotation.x=Math.PI/2;fan.position.set(0,0,.515);m.add(fan);const hub=new T.Mesh(hubGeo,frameMat);hub.rotation.x=Math.PI/2;hub.position.set(0,0,.54);m.add(hub)}
    }
    label(r.name+' · '+r.slots.filter(Boolean).length+'/'+r.slots.length,g.position.x,h+.65,g.position.z,Math.min(w,7));
    label(r.zone,g.position.x,.03,g.position.z+1.5,Math.min(w,5));
  });
  const floorWidth=columns*(span+2)+4,floorDepth=Math.ceil(racks.length/columns)*5+7;
  block(scene,0,-.08,(floorDepth-10)/2,floorWidth,.12,floorDepth,new T.MeshStandardMaterial({color:c.floor,roughness:1}));
  // A cutaway hall keeps all rack fronts visible.
  block(scene,0,.7,-2.2,floorWidth,1.4,.15,shelfMat);
  block(scene,-floorWidth/2,.7,(floorDepth-10)/2,.15,1.4,floorDepth,shelfMat);
  const safetyMat=new T.MeshStandardMaterial({color:c.brand,roughness:1});
  for(let lane=0;lane<Math.ceil(racks.length/columns);lane++){
    const z=lane*5+2.2;
    block(scene,0,.015,z,floorWidth-2,.025,.07,safetyMat);
    block(scene,0,.015,z+1.25,floorWidth-2,.025,.07,safetyMat);
    for(let x=-floorWidth/2+1;x<floorWidth/2-1;x+=2)block(scene,x,.015,z+.63,.65,.025,.08,safetyMat);
  }
  for(const x of [-floorWidth/2,floorWidth/2])for(const z of [-2.2,floorDepth-6.5])block(scene,x,height/2,z,.2,height,.2,frameMat);
  const grid=new T.GridHelper(Math.max(floorWidth,floorDepth),Math.ceil(Math.max(floorWidth,floorDepth)),c.grid,c.grid);grid.position.y=.001;scene.add(grid);
  const center=new T.Vector3(0,height*.4,Math.max(0,(Math.ceil(racks.length/columns)-1)*2.5));
  function draw(){renderer.render(scene,camera)}
  function view(mode='overview'){
    controls.target.copy(center);const dist=Math.max(12,floorWidth*.86,height*2)*Math.max(1,1.6/camera.aspect);
    if(mode==='front')camera.position.set(0,center.y,center.z+dist);
    else if(mode==='top')camera.position.set(.01,dist*1.2,center.z+.01);
    else camera.position.set(dist*.35,height+dist*.26,dist*.8);
    controls.update();draw();
  }
  controls.addEventListener('change',draw);
  function resize(){const w=host.clientWidth,h=host.clientHeight,old=camera.aspect;renderer.setSize(w,h);camera.aspect=w/Math.max(h,1);camera.updateProjectionMatrix();if(Math.abs(old-camera.aspect)>.3)view();else draw()}
  const observer=new ResizeObserver(resize);observer.observe(host);
  let down=null,drag=null,disposed=false;
  function hit(e){const rect=canvas.getBoundingClientRect();pointer.set((e.clientX-rect.left)/rect.width*2-1,-(e.clientY-rect.top)/rect.height*2+1);ray.setFromCamera(pointer,camera);return ray.intersectObjects(slots,false)[0]?.object}
  function reset(){const ids=api.matches();slots.forEach(m=>{m.material.emissive.set(ids.has(m.userData.d?.id)?c.selected:0x000000);m.material.opacity=api.query()&&!ids.has(m.userData.d?.id) ? .2 : m.userData.d?1:.3})}
  function describe(m){if(m){const {r,i,d}=m.userData;api.status((d?d.ip+' · '+(d.offline?'Mất kết nối':d.temp+'°C'):'Ô trống')+' · '+api.position(r,i))}}
  function start(e){if(e.button!==0)return;const m=hit(e);down={x:e.clientX,y:e.clientY,m};if(api.edit()&&m?.userData.d){controls.enabled=false;canvas.setPointerCapture(e.pointerId)}}
  function move(e){const m=hit(e);if(down&&api.edit()&&down.m?.userData.d&&Math.hypot(e.clientX-down.x,e.clientY-down.y)>6){drag=down.m;canvas.style.cursor='grabbing'}reset();if(drag){drag.material.emissive.set(c.selected);if(m&&m!==drag){m.material.emissive.set(m.userData.d?c.critical:c.selected);api.status(m.userData.d?'Ô đã có máy. Chọn ô trống.':'Thả để chuyển '+drag.userData.d.ip+' → '+api.position(m.userData.r,m.userData.i))}}else{canvas.style.cursor=api.edit()&&m?.userData.d?'grab':m?'pointer':'default';if(m){m.material.emissive.set(c.selected);describe(m)}}draw()}
  function end(e){const m=hit(e),wasDrag=drag;controls.enabled=true;if(canvas.hasPointerCapture(e.pointerId))canvas.releasePointerCapture(e.pointerId);if(drag&&m&&m!==drag){if(m.userData.d)api.status('Ô đã có máy. Vị trí cũ được giữ nguyên.');else api.move(drag.userData.d.id,m.userData.r,m.userData.i)}else if(down&&!wasDrag&&Math.hypot(e.clientX-down.x,e.clientY-down.y)<6&&m){if(api.pending()&&!m.userData.d)api.move(api.pending(),m.userData.r,m.userData.i);else api.inspect(m.userData.r,m.userData.i)}down=null;drag=null;reset();if(!disposed)draw()}
  function cancel(){down=null;drag=null;controls.enabled=true;reset();draw()}
  function over(e){if(!api.dragged())return;const m=hit(e);reset();if(m&&!m.userData.d){e.preventDefault();e.dataTransfer.dropEffect='move';m.material.emissive.set(c.selected);describe(m)}draw()}
  function drop(e){const id=api.dragged(),m=hit(e);if(!id||!m||m.userData.d)return;e.preventDefault();if(e.dataTransfer.getData('application/x-beesky-device')===id)api.move(id,m.userData.r,m.userData.i)}
  // Run before OrbitControls handles pointerdown, so moving a machine never orbits.
  canvas.addEventListener('pointerdown',start,true);canvas.addEventListener('pointermove',move);canvas.addEventListener('pointerup',end);canvas.addEventListener('pointercancel',cancel);canvas.addEventListener('dragover',over);canvas.addEventListener('drop',drop);
  const escape=e=>{if(e.key==='Escape'){cancel();api.status('Đã hủy kéo máy.')}};window.addEventListener('keydown',escape);
  function focusDevice(id){const m=slots.find(s=>s.userData.d?.id===id);if(!m)return;const pos=new T.Vector3();m.getWorldPosition(pos);controls.target.copy(pos);camera.position.copy(pos).add(new T.Vector3(1.8,1.5,7));controls.update();describe(m);reset();draw()}
  resize();view();
  if(api.camera){camera.position.fromArray(api.camera.position);controls.target.fromArray(api.camera.target);controls.update()}
  reset();draw();
  return {view,focusDevice,highlight(){reset();draw()},cameraState(){return{position:camera.position.toArray(),target:controls.target.toArray()}},dispose(){if(disposed)return;disposed=true;observer.disconnect();controls.dispose();window.removeEventListener('keydown',escape);const geometries=new Set(),materials=new Set();scene.traverse(o=>{if(o.geometry)geometries.add(o.geometry);if(o.material)materials.add(o.material)});materials.forEach(m=>{m.map?.dispose();m.dispose()});geometries.forEach(g=>g.dispose());renderer.dispose();renderer.forceContextLoss();canvas.remove()}};
}
