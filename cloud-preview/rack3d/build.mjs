import {build} from 'esbuild';
import {fileURLToPath} from 'node:url';
import {readFile,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
await build({entryPoints:[fileURLToPath(new URL('scene.js',import.meta.url))],bundle:true,minify:true,format:'esm',outfile:fileURLToPath(new URL('../rack-scene.js',import.meta.url)),legalComments:'eof'});
const hash=createHash('sha256').update(await readFile(new URL('../rack-scene.js',import.meta.url))).digest('hex').slice(0,10);
const adapter=new URL('../rack-3d.js',import.meta.url);
await writeFile(adapter,(await readFile(adapter,'utf8')).replace(/rack-scene\.js\?v=[^']+/,`rack-scene.js?v=${hash}`));
