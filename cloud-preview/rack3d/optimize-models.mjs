import {NodeIO} from '@gltf-transform/core';
import {ALL_EXTENSIONS} from '@gltf-transform/extensions';
import {dedup,weld,simplify,join,prune,textureCompress,meshopt} from '@gltf-transform/functions';
import {MeshoptEncoder,MeshoptDecoder,MeshoptSimplifier} from 'meshoptimizer';
import sharp from 'sharp';
import {fileURLToPath} from 'node:url';
process.chdir(fileURLToPath(new URL('../../',import.meta.url)));
import {stat,writeFile} from 'node:fs/promises';
await Promise.all([MeshoptEncoder.ready,MeshoptDecoder.ready,MeshoptSimplifier.ready]);
const io=new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({'meshopt.encoder':MeshoptEncoder,'meshopt.decoder':MeshoptDecoder});
const report=[];
for(const name of ['s19-pro-air','s21-hydro']){
 const source='cloud-preview/assets/models/'+name+'.glb',target='cloud-preview/assets/models/'+name+'-fast.glb';
 const doc=await io.read(source);
 const triangles=()=>doc.getRoot().listMeshes().reduce((total,m)=>total+m.listPrimitives().reduce((n,p)=>n+(p.getIndices()?.getCount()??p.getAttribute('POSITION').getCount())/3,0),0);
 const before=triangles();
 await doc.transform(dedup(),weld(),simplify({simplifier:MeshoptSimplifier,ratio:.22,error:.002,lockBorder:true}),join(),prune(),textureCompress({encoder:sharp,targetFormat:'webp',resize:[512,512],quality:82}),meshopt({encoder:MeshoptEncoder,level:'medium'}));
 await io.write(target,doc);
 report.push({name,originalBytes:(await stat(source)).size,optimizedBytes:(await stat(target)).size,originalTriangles:before,optimizedTriangles:triangles()});
}
await writeFile('cloud-preview/assets/models/optimized-stats.json',JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(report));
