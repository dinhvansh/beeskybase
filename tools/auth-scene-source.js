import * as T from '../cloud-preview/rack3d/node_modules/three/build/three.module.js';
import {GLTFLoader} from '../cloud-preview/rack3d/node_modules/three/examples/jsm/loaders/GLTFLoader.js';
import {RoomEnvironment} from '../cloud-preview/rack3d/node_modules/three/examples/jsm/environments/RoomEnvironment.js';
import {RoundedBoxGeometry} from '../cloud-preview/rack3d/node_modules/three/examples/jsm/geometries/RoundedBoxGeometry.js';
let cleanup=()=>{};
function mount(){
 cleanup();
 const host=document.querySelector('.auth-scene');
 if(!host||innerWidth<761)return;
 host.dataset.threeMounted='1';
 let disposed=false,frame,last=0,elapsed=0,pointer=0,visible=true,dirty=true;
 const scene=new T.Scene(),camera=new T.PerspectiveCamera(32,1,.1,80);
 let renderer;
 try{renderer=new T.WebGLRenderer({alpha:true,antialias:true})}catch{return}
 renderer.setPixelRatio(Math.min(devicePixelRatio,1.75));
 renderer.toneMapping=T.ACESFilmicToneMapping;
 renderer.toneMappingExposure=.95;
 renderer.shadowMap.enabled=true;
 renderer.shadowMap.type=T.PCFSoftShadowMap;
 renderer.domElement.className='auth-webgl';
 renderer.domElement.setAttribute('aria-hidden','true');host.append(renderer.domElement);
 const pmrem=new T.PMREMGenerator(renderer),room=new RoomEnvironment();
 const environment=pmrem.fromScene(room,.025);scene.environment=environment.texture;
 scene.environmentIntensity=.8;room.dispose();pmrem.dispose();
 scene.add(new T.HemisphereLight(0xdce6f2,0x15191f,1));
 const key=new T.DirectionalLight(0xfff6e9,2.3);key.position.set(1,6,5);key.castShadow=true;
 key.shadow.mapSize.set(1024,1024);Object.assign(key.shadow.camera,{left:-5,right:5,top:6,bottom:-4});key.shadow.bias=-.001;key.shadow.normalBias=.025;key.shadow.radius=4;scene.add(key);
 const rim=new T.DirectionalLight(0xc6dcff,2);rim.position.set(-4,3,-3);scene.add(rim);
 const root=new T.Group();scene.add(root);
 const graphite=new T.MeshStandardMaterial({color:0x222a33,metalness:.72,roughness:.29});
 const trim=new T.MeshStandardMaterial({color:0x9faab8,metalness:.9,roughness:.23});
 const shelf=new T.MeshStandardMaterial({color:0x313c48,metalness:.68,roughness:.34});
 const accent=new T.MeshBasicMaterial({color:0xc9dbed});
 function box(x,y,z,w,h,d,material=graphite,r=.025){
  const mesh=new T.Mesh(new RoundedBoxGeometry(w,h,d,3,r),material);
  mesh.position.set(x,y,z);mesh.castShadow=true;mesh.receiveShadow=true;root.add(mesh);return mesh;
 }
 // One quiet architectural base, with a narrow machined edge.
 box(0,-.1,0,3.55,.17,1.9,graphite,.07);
 box(0,-.016,.03,3.38,.018,1.75,trim,.007);
 for(const x of [-1.43,1.43])for(const z of [-.59,.59])box(x,1.04,z,.06,2.05,.06,graphite,.012);
 for(const y of [.09,1.02,1.97]){
  box(0,y,0,2.98,.065,1.36,shelf,.02);
  box(0,y-.018,.69,2.94,.022,.018,trim,.006);
 }
 for(const y of [.1,1.03]){
  box(-1.11,y+.035,.69,.27,.012,.014,accent,.004);
  for(let i=0;i<7;i++)box(.84+i*.065,y+.034,.69,.025,.008,.012,trim,.003);
 }
 // Small upright brand plaque floats above the cabinet, inside the camera bounds.
 const badge=new T.Group();root.add(badge);badge.position.set(.08,2.75,0);
 const plaque=new T.Mesh(new RoundedBoxGeometry(1.25,1.25,.13,6,.16),new T.MeshStandardMaterial({color:0x586370,metalness:.88,roughness:.21}));badge.add(plaque);
 new T.TextureLoader().load('/static/auth-logo.svg',texture=>{
  if(disposed){texture.dispose();return}texture.colorSpace=T.SRGBColorSpace;
  const face=new T.Mesh(new T.CircleGeometry(.48,80),new T.MeshBasicMaterial({map:texture}));face.position.z=.071;badge.add(face);dirty=true;
 });
 const loader=new GLTFLoader();
 Promise.all(['s19-pro-air.glb','s21-hydro.glb'].map(file=>loader.loadAsync('/static/assets/models/'+file))).then(models=>{
  if(disposed)return;
  for(let row=0;row<2;row++)for(let col=0;col<2;col++){
   const model=models[col].scene.clone(true);
   // Match material response to the studio lighting without losing the supplied textures.
   model.traverse(o=>{if(o.isMesh){o.castShadow=true;o.receiveShadow=true;o.material=Array.isArray(o.material)?o.material.map(m=>m.clone()):o.material.clone();for(const m of Array.isArray(o.material)?o.material:[o.material]){if('envMapIntensity' in m)m.envMapIntensity=.6;}}});
   const bounds=new T.Box3().setFromObject(model),size=bounds.getSize(new T.Vector3()),center=bounds.getCenter(new T.Vector3());
   const scale=Math.min(1.12/size.x,.75/size.y,1.08/size.z);
   model.scale.setScalar(scale);model.position.copy(center.multiplyScalar(-scale));
   const holder=new T.Group();holder.add(model);holder.position.set((col-.5)*1.4,.14+row*.93+size.y*scale/2,.03);root.add(holder);
  }
  host.classList.add('webgl-ready');dirty=true;
 }).catch(()=>{});
 const floor=new T.Mesh(new T.PlaneGeometry(20,20),new T.ShadowMaterial({opacity:.23}));floor.rotation.x=-Math.PI/2;floor.position.y=-.2;floor.receiveShadow=true;scene.add(floor);
 // Fit the whole composition, including every corner of the plaque, with safe margins.
 const target=new T.Vector3(0,1.48,0),direction=new T.Vector3(4.8,2.5,8.6).normalize();
 function resize(){
  const w=host.clientWidth,h=host.clientHeight;if(!w||!h)return;
  renderer.setSize(w,h);camera.aspect=w/h;
  const half=Math.min(T.MathUtils.degToRad(camera.fov/2),Math.atan(Math.tan(T.MathUtils.degToRad(camera.fov/2))*camera.aspect));
  camera.position.copy(target).addScaledVector(direction,2.45/Math.sin(half));camera.lookAt(target);camera.updateProjectionMatrix();dirty=true;
 }
 const ro=new ResizeObserver(resize);ro.observe(host);resize();
 const io=new IntersectionObserver(([entry])=>{visible=entry.isIntersecting;last=0;dirty=true});io.observe(host);
 const reduced=matchMedia('(prefers-reduced-motion:reduce)');
 const move=e=>{pointer=(e.clientX/innerWidth-.5)*.12;dirty=true};addEventListener('pointermove',move);
 const pause=document.createElement('button');pause.type='button';pause.className='auth-motion-toggle';pause.textContent='Dừng chuyển động';pause.setAttribute('aria-pressed','false');host.append(pause);
 let paused=false;pause.onclick=()=>{paused=!paused;pause.textContent=paused?'Bật chuyển động':'Dừng chuyển động';pause.setAttribute('aria-pressed',String(paused));dirty=true};
 function draw(t){
  if(disposed)return;frame=requestAnimationFrame(draw);
  if(!visible||document.hidden){last=0;return}if(t-last<40)return;
  const still=reduced.matches||paused;
  if(!still)elapsed+=last?Math.min((t-last)/1000,.1):0;last=t;
  if(still&&!dirty)return;
  root.rotation.y=still?0:Math.sin(elapsed*.3)*.045+pointer;
  badge.rotation.y=still?0:Math.sin(elapsed*.4)*.06;
  badge.position.y=2.75+(still?0:Math.sin(elapsed*.85)*.025);
  renderer.render(scene,camera);dirty=false;
 }
 frame=requestAnimationFrame(draw);
 cleanup=()=>{disposed=true;cancelAnimationFrame(frame);ro.disconnect();io.disconnect();removeEventListener('pointermove',move);const geometries=new Set(),materials=new Set(),textures=new Set();scene.traverse(o=>{if(o.geometry)geometries.add(o.geometry);for(const m of o.material?(Array.isArray(o.material)?o.material:[o.material]):[]){materials.add(m);for(const value of Object.values(m))if(value?.isTexture)textures.add(value)}});geometries.forEach(g=>g.dispose());materials.forEach(m=>m.dispose());textures.forEach(t=>t.dispose());environment.dispose();renderer.dispose();renderer.domElement.remove();pause.remove();};
}
new MutationObserver(()=>{const host=document.querySelector('.auth-scene');if(host&&!host.dataset.threeMounted)mount();else if(!host)cleanup()}).observe(document.querySelector('#cloud-app'),{childList:true});
mount();
