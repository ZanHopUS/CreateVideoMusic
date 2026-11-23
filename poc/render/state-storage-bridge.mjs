import {bundle} from '@remotion/bundler';
import {renderMedia, renderStill, selectComposition} from '@remotion/renderer';
import {readFile, writeFile, readdir, mkdir} from 'node:fs/promises';
import {execFileSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import assert from 'node:assert/strict';

const here = path.dirname(fileURLToPath(import.meta.url));
process.chdir(here);
const root = path.resolve(here, '../..');
const run = path.resolve(root, process.argv[2]);
assert(run.startsWith(path.join(root, '.poc/state-storage') + path.sep));
const option = (name, fallback) => {const index=process.argv.indexOf(name); return index<0 ? fallback : process.argv[index+1];};
const concurrency=Number(option('--concurrency','2'));
assert([1,2].includes(concurrency));
const outputName=option('--output-name','render-check'); assert(/^[a-z0-9-]+$/.test(outputName));
const output = path.join(run, outputName); await mkdir(output, {recursive: false});
const fixtures = JSON.parse(await readFile(path.join(run,'state-fixtures.json'),'utf8'));
const originalBundle = await bundle({entryPoint:path.join(here,'fidelity/root.jsx'),publicDir:path.join(run,'library'),
  outDir:path.join(output,'original-bundle')});
const results = [];
for (const id of ['TPL02-12','TPL03-12']) {
  let restoredRoot, restored;
  for (const name of await readdir(path.join(run,'restored'))) {
    const folder = path.join(run,'restored',name);
    const project = JSON.parse(await readFile(path.join(folder,'project.json'),'utf8'));
    if (project.id===id) {restoredRoot=folder; restored=project; break;}
  }
  assert(restoredRoot);
  const original = fixtures.cases.find(c=>c.id===id).edited;
  assert.deepEqual(restored,original);
  const folder = path.join(output,id); await mkdir(folder);
  const restoredBundle = await bundle({entryPoint:path.join(here,'fidelity/root.jsx'),publicDir:restoredRoot,
    outDir:path.join(folder,'restored-bundle')});
  const originalComposition = await selectComposition({serveUrl:originalBundle,id:original.template,inputProps:{project:original}});
  const restoredComposition = await selectComposition({serveUrl:restoredBundle,id:restored.template,inputProps:{project:restored}});
  for (const frame of [60,150,300]) {
    await renderStill({serveUrl:originalBundle,composition:originalComposition,inputProps:{project:original},frame,output:path.join(folder,`before-${frame}.png`)});
    await renderStill({serveUrl:restoredBundle,composition:restoredComposition,inputProps:{project:restored},frame,output:path.join(folder,`restored-${frame}.png`)});
  }
  await renderMedia({serveUrl:restoredBundle,composition:restoredComposition,inputProps:{project:restored},
    outputLocation:path.join(folder,'raw.mp4'),codec:'h264',audioCodec:'aac',pixelFormat:'yuv420p',
    x264Preset:'ultrafast',hardwareAcceleration:'disable',concurrency,offthreadVideoThreads:1,
    offthreadVideoCacheSizeInBytes:64*1024*1024});
  const finalized = JSON.parse(execFileSync(path.join(root,'.poc/venv-asr/Scripts/python.exe'),
    [path.join(here,'finalize_mp4.py'),'--input',path.join(folder,'raw.mp4'),'--output',path.join(folder,'restored.mp4'),
      '--seconds','12'],{encoding:'utf8'}));
  results.push({id,frames:[60,150,300],semanticMatch:true,restoredRoot,concurrency,finalized});
  console.log(JSON.stringify({id,phase:'rendered-restored-project'}));
}
await writeFile(path.join(output,'results.json'),JSON.stringify(results,null,2));
