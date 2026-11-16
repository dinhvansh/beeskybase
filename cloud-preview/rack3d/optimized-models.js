import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {MeshoptDecoder} from 'three/addons/libs/meshopt_decoder.module.js';

const templates=new Map();
const loader=new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
export function minerTemplate(kind,base='assets/models/'){
 const url=base+(kind==='hydro'?'s21-hydro-fast.glb':'s19-pro-air-fast.glb')+'?v=perf1';
 if(!templates.has(url))templates.set(url,loader.loadAsync(url).then(gltf=>{
  gltf.scene.traverse(object=>{
   if(object.geometry)object.geometry.userData.minerShared=true;
   for(const material of Array.isArray(object.material)?object.material:[object.material])
    if(material)for(const value of Object.values(material))if(value?.isTexture)value.userData.minerShared=true;
  });
  return gltf.scene;
 }).catch(error=>{templates.delete(url);throw error}));
 return templates.get(url);
}
