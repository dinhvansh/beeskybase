import * as T from '../cloud-preview/rack3d/node_modules/three/build/three.module.js';
import {GLTFLoader} from '../cloud-preview/rack3d/node_modules/three/examples/jsm/loaders/GLTFLoader.js';
const host=document.querySelector('.mine-live-stage');
if(host){
 const scene=new T.Scene(),camera=new T.PerspectiveCamera(32,1,.1,60),renderer=new T.WebGLRenderer({alpha:true,antialias:true});
 renderer.setPixelRatio(Math.min(devicePixelRatio,1.5));renderer.toneMapping=T.ACESFilmicToneMapping;renderer.toneMappingExposure=1.25;renderer.shadowMap.enabled=true;renderer.shadowMap.type=T.PCFSoftShadowMap;host.prepend(renderer.domElement);
 camera.position.set(5,3.7,7.6);camera.lookAt(0,1,0);
 scene.add(new T.HemisphereLight(0xffffff,0xb7c8c2,2.5));const key=new T.DirectionalLight(0xffffff,3);key.position.set(3,7,5);key.castShadow=true;key.shadow.mapSize.set(1024,1024);key.shadow.camera.left=-5;key.shadow.camera.right=5;key.shadow.camera.top=6;key.shadow.camera.bottom=-5;key.shadow.bias=-.001;scene.add(key);const rim=new T.DirectionalLight(0xc9e5ed,2);rim.position.set(-5,3,-3);scene.add(rim);
 const root=new T.Group();scene.add(root);
 const silver=new T.MeshStandardMaterial({color:0x94aaa1,metalness:.65,roughness:.35}),shelf=new T.MeshStandardMaterial({color:0xcbd7d0,metalness:.45,roughness:.42});
 function block(x,y,z,w,h,d,mat){const mesh=new T.Mesh(new T.BoxGeometry(w,h,d),mat);mesh.position.set(x,y,z);mesh.castShadow=true;mesh.receiveShadow=true;root.add(mesh);return mesh}
 const plinth=new T.Mesh(new T.CylinderGeometry(2.5,2.6,.18,80),new T.MeshStandardMaterial({color:0xf0f5f2,roughness:.4,metalness:.2}));plinth.position.y=-.14;plinth.receiveShadow=true;root.add(plinth);
 for(const x of [-1.16,1.16])for(const z of [-.5,.5])block(x,1.28,z,.055,2.56,.055,silver);
 for(let row=0;row<4;row++)block(0,.1+row*.8,0,2.4,.055,1.15,shelf);
 const loader=new GLTFLoader();let disposed=false;
 Promise.all(['s19-pro-air.glb','s21-hydro.glb'].map(file=>loader.loadAsync('../cloud-preview/assets/models/'+file))).then(models=>{
  if(disposed)return;
  for(let row=0;row<3;row++)for(let col=0;col<2;col++){
   const model=models[col].scene.clone(true),box=new T.Box3().setFromObject(model),size=box.getSize(new T.Vector3()),center=box.getCenter(new T.Vector3()),scale=Math.min(.92/size.x,.67/size.y,.92/size.z);
   model.scale.setScalar(scale);model.position.copy(center.multiplyScalar(-scale));const holder=new T.Group();holder.add(model);holder.position.set((col-.5)*1.13,.48+row*.8,0);root.add(holder);model.traverse(o=>{if(o.isMesh){o.castShadow=true;o.receiveShadow=true;}});
   const led=block((col-.5)*1.13+.32,.24+row*.8,.54,.075,.025,.02,new T.MeshBasicMaterial({color:0x8ed5ae}));
  }
  host.dataset.models='ready';draw();
 }).catch(()=>{host.dataset.models='error';host.querySelector('.mine-model-fallback').hidden=false;});
 function draw(){renderer.render(scene,camera)}
 const ro=new ResizeObserver(()=>{const w=host.clientWidth,h=host.clientHeight;renderer.setSize(w,h);camera.aspect=w/h;camera.updateProjectionMatrix();draw()});ro.observe(host);
 let visible=false,last=0,elapsed=0;const media=matchMedia('(prefers-reduced-motion:reduce)');
 const io=new IntersectionObserver(([e])=>{visible=e.isIntersecting;last=0});io.observe(host);
 function animate(t){if(disposed)return;requestAnimationFrame(animate);if(!visible||document.hidden||media.matches||document.body.classList.contains('still')){last=0;return;}if(last&&t-last<33)return;elapsed+=last?Math.min((t-last)/1000,.1):0;last=t;root.rotation.y=Math.sin(elapsed*.35)*.10-.08;draw();}requestAnimationFrame(animate);
 addEventListener('pagehide',()=>{disposed=true;ro.disconnect();io.disconnect();renderer.dispose()},{once:true});draw();
}
