import {bundle} from '@remotion/bundler';
import {ensureBrowser, renderMedia, renderStill, selectComposition} from '@remotion/renderer';
import {readFile, writeFile, mkdir} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {performance} from 'node:perf_hooks';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {reviewState} from './lyrics-timing.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
process.chdir(here);
const local = path.resolve(here,'../../.poc');
const output = path.join(local,'evidence/poc-03/vi-lyrics-review');
await mkdir(output,{recursive:true});
const input = JSON.parse(await readFile(path.join(output,'input.json'),'utf8'));
assert.equal(reviewState(input.rows,input.rows[0].cue.start_s-0.001).row,null);
const fallback = input.rows.find(row=>row.mode==='sentence_fallback');
assert.equal(reviewState(input.rows,(fallback.cue.start_s+fallback.cue.end_s)/2).activeWord,-1);
assert.notEqual(reviewState(input.rows,fallback.cue.end_s).row?.cue.cue_id,fallback.cue.cue_id);
const word = input.rows[0].words[2];
const wordFrame = Math.ceil(((word.start+word.end)/2-input.sourceStart)*input.fps);
const fallbackFrame = Math.round(((fallback.cue.start_s+fallback.cue.end_s)/2-input.sourceStart)*input.fps);
assert.equal(reviewState(input.rows,input.sourceStart+wordFrame/input.fps).activeWord,2);
await writeFile(path.join(output,'timing-checks.json'),JSON.stringify({status:'passed',
  wordFrame,fallbackFrame,sourceTimeAtFrame0:input.sourceStart,
  wordDisplayQuantizationBoundMs:1000/input.fps,acousticTimingVerified:false},null,2));
const browser = await ensureBrowser();
const serveUrl = await bundle({entryPoint:path.join(here,'lyrics-review.jsx'),
  publicDir:path.join(local,'render/lyrics-review-public'),outDir:path.join(local,'render/lyrics-review-bundle')});
const composition = await selectComposition({serveUrl,id:'VietnameseLyricsReview',inputProps:input});
assert.equal(composition.durationInFrames,input.frames);
const started = performance.now();
let progressStep = -1;
await renderMedia({serveUrl,composition,inputProps:input,codec:'h264',audioCodec:'aac',pixelFormat:'yuv420p',
  outputLocation:path.join(output,'vi-lyrics-review.mp4'),concurrency:1,offthreadVideoThreads:1,
  x264Preset:'fast',crf:20,hardwareAcceleration:'disable',sampleRate:48000,overwrite:true,
  onProgress:({progress})=>{
    const step = Math.floor(progress*4);
    if(step>progressStep){progressStep=step;console.log(JSON.stringify({renderProgress:Math.round(progress*100)}));}
  }});
const renderSeconds = (performance.now()-started)/1000;
for (const [label,frame] of Object.entries({word:wordFrame,fallback:fallbackFrame})) {
  await renderStill({serveUrl,composition,inputProps:input,frame,output:path.join(output,`${label}.png`)});
}
await writeFile(path.join(output,'render-result.json'),JSON.stringify({renderSeconds,
  durationSeconds:input.frames/input.fps,rtf:renderSeconds/(input.frames/input.fps),
  frames:input.frames,fps:input.fps,width:composition.width,height:composition.height,
  sourceStart:input.sourceStart,sourceEnd:input.sourceEnd,browser,reviewRequired:true,
  compositionSha256:createHash('sha256').update(await readFile(path.join(here,'lyrics-review.jsx'))).digest('hex'),
  timingModuleSha256:createHash('sha256').update(await readFile(path.join(here,'lyrics-timing.mjs'))).digest('hex')},null,2));
console.log(JSON.stringify({renderSeconds,frames:input.frames,output:'vi-lyrics-review.mp4'}));
