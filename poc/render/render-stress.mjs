import {bundle} from '@remotion/bundler';
import {ensureBrowser, renderMedia, renderStill, selectComposition} from '@remotion/renderer';
import {readFile, writeFile, mkdir, access} from 'node:fs/promises';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {performance} from 'node:perf_hooks';

const here = path.dirname(fileURLToPath(import.meta.url));
process.chdir(here);
const root = path.resolve(here, '../..');
const local = path.join(root, '.poc');
const templateIndex = process.argv.indexOf('--template');
const template = templateIndex < 0 ? 'TPL03' : process.argv[templateIndex + 1];
assert(['TPL01', 'TPL02', 'TPL03'].includes(template));
const ratioIndex = process.argv.indexOf('--ratio');
const ratio = ratioIndex < 0 ? '9-16' : process.argv[ratioIndex + 1];
assert(['9-16', '16-9', '1-1'].includes(ratio));
assert(template === 'TPL03' || ratio === '9-16', 'Planned TPL01/02 stress uses portrait only');
const sizes = {'9-16': [1080, 1920], '16-9': [1920, 1080], '1-1': [1080, 1080]};
const [width, height] = sizes[ratio];
const settings = {template, width, height, fps: 60, seconds: 300};
const output = path.join(local, 'evidence/poc-04', `${template.toLowerCase()}-${ratio}-300s-1080p60`);
await mkdir(output, {recursive: true});
for (const filename of ['raw.mp4', 'bounded.mp4']) {
  try {await access(path.join(output, filename)); throw new Error(`Output exists: ${filename}`);}
  catch (error) {if (error.code !== 'ENOENT') throw error;}
}
const sourceFiles = [fileURLToPath(import.meta.url), path.join(here, 'stress-fixture.jsx'),
  path.join(here, 'finalize_mp4.py'), path.join(here, 'package-lock.json'),
  path.join(local, 'render/stress-public/control.wav'), path.join(local, 'render/stress-public/background.mp4')];
const inventory = [];
for (const file of sourceFiles) {
  const data = await readFile(file);
  inventory.push({path: path.relative(root, file), bytes: data.length,
    sha256: createHash('sha256').update(data).digest('hex')});
  const snapshot = path.join(output, 'source-snapshot', path.relative(root, file));
  await mkdir(path.dirname(snapshot), {recursive: true});
  await writeFile(snapshot, data);
}
await writeFile(path.join(output, 'run-config.json'), JSON.stringify({settings, ratio,
  concurrency: 2, offthreadVideoThreads: 1, offthreadVideoCacheMiB: 64,
  x264Preset: 'ultrafast', hardwareAcceleration: 'disable', inventory}, null, 2));
try {
  const browser = await ensureBrowser();
  await writeFile(path.join(output, 'browser.json'), JSON.stringify(browser, null, 2));
  const serveUrl = await bundle({entryPoint: path.join(here, 'stress-fixture.jsx'),
    publicDir: path.join(local, 'render/stress-public'), outDir: path.join(local, 'render/stress-bundle')});
  const composition = await selectComposition({serveUrl, id: `${template}Stress`, inputProps: settings});
  let previous = 0, reported = -1;
  const began = performance.now();
  await renderMedia({serveUrl, composition, inputProps: settings, codec: 'h264', audioCodec: 'aac',
    pixelFormat: 'yuv420p', outputLocation: path.join(output, 'raw.mp4'), concurrency: 2,
    offthreadVideoThreads: 1, offthreadVideoCacheSizeInBytes: 64 * 1024 * 1024,
    x264Preset: 'ultrafast', hardwareAcceleration: 'disable',
    onProgress: ({progress}) => {
      assert(progress + .001 >= previous, 'Non-monotonic render progress');
      previous = progress;
      const percent = Math.floor(progress * 100);
      if (percent > reported) {
        reported = percent;
        console.log(JSON.stringify({phase: 'renderMedia', percent, elapsed_s: (performance.now() - began) / 1000}));
      }
    }});
  const renderSeconds = (performance.now() - began) / 1000;
  console.log(JSON.stringify({phase: 'audio-finalize', renderSeconds}));
  const python = path.join(local, 'venv-asr/Scripts/python.exe');
  const finalized = JSON.parse(execFileSync(python, [path.join(here, 'finalize_mp4.py'),
    '--input', path.join(output, 'raw.mp4'), '--output', path.join(output, 'bounded.mp4'),
    '--seconds', '300'], {encoding: 'utf8'}));
  for (const second of [0, 150, 299.9]) {
    await renderStill({serveUrl, composition, inputProps: settings, frame: Math.round(second * 60),
      output: path.join(output, `frame-${second}.png`)});
  }
  const probe = path.join(here, 'node_modules/@remotion/compositor-win32-x64-msvc/ffprobe.exe');
  for (const name of ['raw', 'bounded']) {
    const metadata = JSON.parse(execFileSync(probe, ['-v', 'error', '-show_format', '-show_streams',
      '-of', 'json', path.join(output, `${name}.mp4`)], {encoding: 'utf8'}));
    await writeFile(path.join(output, `${name}.ffprobe.json`), JSON.stringify(metadata, null, 2));
  }
  const result = {settings, renderSeconds, rtf: renderSeconds / 300, finalized,
    qualityEvidence: 'generated-only single stress run; pending full decode validation'};
  await writeFile(path.join(output, 'render-result.json'), JSON.stringify(result, null, 2));
  console.log(JSON.stringify({phase: 'render-complete', renderSeconds, rtf: result.rtf}));
} catch (error) {
  await writeFile(path.join(output, 'error.json'), JSON.stringify({message: error.message, stack: error.stack}, null, 2));
  throw error;
}
