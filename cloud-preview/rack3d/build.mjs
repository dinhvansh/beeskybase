import {build} from 'esbuild';
import {fileURLToPath} from 'node:url';
await build({entryPoints:[fileURLToPath(new URL('scene.js',import.meta.url))],bundle:true,minify:true,format:'esm',outfile:fileURLToPath(new URL('../rack-scene.js',import.meta.url)),legalComments:'eof'});
