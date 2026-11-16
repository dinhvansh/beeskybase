import {build} from 'esbuild';
import {readFile, writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
const base=new URL('../',import.meta.url);
await build({entryPoints:[fileURLToPath(new URL('editor.jsx',import.meta.url))],bundle:true,minify:true,format:'iife',outfile:fileURLToPath(new URL('flow-editor.js',base))});
let html=await readFile(new URL('index.html',base),'utf8');
for(const match of [...html.matchAll(/(src|href)="([\w-]+\.(?:css|js))(?:\?[^"\s]*)?"/g)]){
  const hash=createHash('sha256').update(await readFile(new URL(match[2],base))).digest('hex').slice(0,10);
  html=html.replace(match[0],`${match[1]}="${match[2]}?v=${hash}"`);
}
await writeFile(new URL('index.html',base),html);
console.log('Built React Flow and refreshed local asset versions.');
