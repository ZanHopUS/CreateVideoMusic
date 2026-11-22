import {bundle} from '@remotion/bundler';
import {ensureBrowser, renderMedia, renderStill, selectComposition} from '@remotion/renderer';
import {mkdir, writeFile, readFile} from 'node:fs/promises';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {performance} from 'node:perf_hooks';

const here = path.dirname(fileURLToPath(import.meta.url));
process.chdir(here);
const root = path.resolve(here, '../..');
const local = path.join(root, '.poc');
// Limit the initial executable smoke. --matrix explicitly runs the planned 36 cases.
const matrix = process.argv.includes('--matrix');
const resume = process.argv.includes('--resume');
const concurrencyFlag = process.argv.indexOf('--concurrency');
const concurrency = concurrencyFlag < 0 ? 1 : Number(process.argv[concurrencyFlag + 1]);
assert(Number.isInteger(concurrency) && concurrency >= 1 && concurrency <= 2, 'Use concurrency 1 or 2');
const output = path.join(local, 'evidence/poc-03', matrix ? 'preset-matrix' : '');
await mkdir(output, {recursive: true});
const fingerprint = createHash('sha256')
  .update(await readFile(fileURLToPath(import.meta.url)))
  .update(await readFile(path.join(here, 'fixture.jsx')))
  .update(await readFile(path.join(here, 'package-lock.json'))).digest('hex');
let results = [];
if (matrix && resume) {
  try {
    const previous = JSON.parse(await readFile(path.join(output,'run-config.json'),'utf8'));
    assert.equal(previous.fingerprint,fingerprint,'Sources differ from previous matrix run');
    assert.equal(previous.concurrency,concurrency,'Concurrency differs from previous matrix run');
    results = JSON.parse(await readFile(path.join(output,'render-results.json'),'utf8'));
  } catch (error) { if (error.code !== 'ENOENT') throw error; }
} else if (matrix) {
  try {
    await readFile(path.join(output,'render-results.json'));
    throw new Error('Matrix results already exist; use --resume with unchanged sources');
  } catch (error) { if(error.code !== 'ENOENT') throw error; }
}
await writeFile(path.join(output,'run-config.json'),JSON.stringify({fingerprint,concurrency,matrix},null,2));
const probe = path.join(here,'node_modules/@remotion/compositor-win32-x64-msvc/ffprobe.exe');
function verifyOutput(name, settings) {
  const metadata = JSON.parse(execFileSync(probe,['-v','error','-show_format','-show_streams','-of','json',path.join(output,`${name}.mp4`)],{encoding:'utf8'}));
  const video = metadata.streams.find(stream=>stream.codec_type==='video');
  const audio = metadata.streams.find(stream=>stream.codec_type==='audio');
  assert.equal(video.width,settings.width); assert.equal(video.height,settings.height);
  assert.equal(video.codec_name,'h264'); assert.equal(audio.codec_name,'aac');
  const [numerator,denominator] = video.avg_frame_rate.split('/').map(Number);
  assert.equal(numerator/denominator,settings.fps);
  assert.equal(Number(video.nb_frames),settings.fps*settings.seconds);
  assert(Math.abs(Number(video.duration)-settings.seconds)<=1/settings.fps);
  return metadata;
}
const cases = [];
for (const template of ['TPL01', 'TPL02', 'TPL03']) {
  for (const [ratio, widths] of Object.entries({'9-16': [720, 1080], '16-9': [1280, 1920], '1-1': [720, 1080]})) {
    for (const [index, width] of widths.entries()) {
      for (const fps of [30, 60]) {
        if (!matrix && (ratio !== '9-16' || index !== 0 || fps !== 30)) continue;
        const height = ratio === '9-16' ? width * 16 / 9 : ratio === '16-9' ? width * 9 / 16 : width;
        cases.push({template, ratio, width, height, fps, seconds: 15});
      }
    }
  }
}
const browser = await ensureBrowser();
await writeFile(path.join(output, 'browser.json'), JSON.stringify(browser, null, 2));
const serveUrl = await bundle({entryPoint: path.join(here, 'fixture.jsx'),
  publicDir: path.join(local, 'render/public'), outDir: path.join(local, 'render/bundle')});
try {
  for (const settings of cases) {
    const name = `${settings.template}-${settings.ratio}-${settings.width}x${settings.height}-${settings.fps}`;
    if (results.some(result=>result.name===name)) {
      verifyOutput(name,settings);
      console.log(JSON.stringify({skippedCompleted:name}));
      continue;
    }
    console.log(JSON.stringify({starting:name,completed:results.length,total:cases.length}));
    const composition = await selectComposition({serveUrl, id: settings.template, inputProps: settings});
    const began = performance.now();
    let previous = 0;
    await renderMedia({serveUrl, composition, inputProps: settings,
      codec: 'h264', audioCodec: 'aac', pixelFormat: 'yuv420p',
      outputLocation: path.join(output, `${name}.mp4`), concurrency, overwrite:true,
      offthreadVideoThreads: 1, offthreadVideoCacheSizeInBytes: 64 * 1024 * 1024,
      x264Preset: 'ultrafast', hardwareAcceleration: 'disable',
      onProgress: ({progress}) => {
        if (progress + 0.001 < previous) throw new Error('Non-monotonic render progress');
        previous = progress;
      }});
    const seconds = (performance.now() - began) / 1000;
    await renderStill({serveUrl, composition, inputProps: settings, frame: settings.fps * 5,
      output: path.join(output, `${name}.png`)});
    const metadata = verifyOutput(name,settings);
    await writeFile(path.join(output,`${name}.ffprobe.json`),JSON.stringify(metadata,null,2));
    const result = {...settings, name, renderSeconds: seconds, rtf: seconds / settings.seconds,
      concurrency,metadataVerified:true,generatedMedia: true, singingQualityEvidence: false};
    results.push(result);
    console.log(JSON.stringify(result));
    await writeFile(path.join(output, 'render-results.json'), JSON.stringify(results, null, 2));
  }
} catch (error) {
  await writeFile(path.join(output, 'error.json'), JSON.stringify({message: error.message, stack: error.stack}, null, 2));
  throw error;
}
