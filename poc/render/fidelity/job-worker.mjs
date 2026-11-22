import {makeCancelSignal, RenderInternals, renderMedia, selectComposition} from '@remotion/renderer';
import {readFile, writeFile, rename, mkdir} from 'node:fs/promises';
import {existsSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import readline from 'node:readline';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import assert from 'node:assert/strict';

const here = path.dirname(fileURLToPath(import.meta.url));
process.chdir(path.resolve(here, '..'));
const root = path.resolve(here, '../../..');
const folder = path.resolve(process.argv[2]);
assert(folder.startsWith(path.join(root, '.poc') + path.sep));
await mkdir(folder, {recursive: true});
const inputPath = path.join(folder, 'snapshot.json');
const input = await readFile(inputPath);
const snapshotHash = createHash('sha256').update(input).digest('hex');
function freeze(value) {if (value && typeof value === 'object') {Object.values(value).forEach(freeze); Object.freeze(value);} return value;}
const project = freeze(JSON.parse(input));
const final = path.join(folder, 'final.mp4');
assert(!existsSync(final));
const began = performance.now();
const events = [];
function emit(state, progress, extra = {}) {
  const event = {state, progress, elapsedMs: performance.now() - began, snapshotHash,
    finalExists: existsSync(final), ...extra};
  events.push(event); console.log(JSON.stringify(event));
}
const {cancelSignal, cancel} = makeCancelSignal();
let cancelRequested = false;
const commands = readline.createInterface({input: process.stdin});
commands.on('line', line => {
  const message = JSON.parse(line);
  if (message.type === 'cancel') {cancelRequested = true; emit('cancel-requested', null); cancel();}
});
try {
  emit('preparing', 0);
  const serveUrl = path.join(root, '.poc/render/fidelity-render-bundle');
  const composition = await selectComposition({serveUrl, id: project.id, inputProps: {project}});
  let previous = 0, lastFrames = -30;
  await renderMedia({serveUrl, composition, inputProps: {project}, cancelSignal,
    outputLocation: path.join(folder, 'raw.partial.mp4'), codec: 'h264', audioCodec: 'aac',
    pixelFormat: 'yuv420p', x264Preset: 'ultrafast', hardwareAcceleration: 'disable',
    concurrency: 2, offthreadVideoThreads: 1, offthreadVideoCacheSizeInBytes: 64 * 1024 * 1024,
    onProgress: ({progress, renderedFrames}) => {
      assert(progress + .001 >= previous); previous = progress;
      if (renderedFrames - lastFrames >= 30) {lastFrames = renderedFrames; emit('rendering', progress * 90, {renderedFrames});}
    }});
  assert(!cancelRequested);
  emit('finalizing', 95);
  const finalized = JSON.parse(execFileSync(path.join(root, '.poc/venv-asr/Scripts/python.exe'),
    [path.join(here, '../finalize_mp4.py'), '--input', path.join(folder, 'raw.partial.mp4'),
      '--output', path.join(folder, 'bounded.partial.mp4'), '--seconds', String(project.durationInFrames / project.fps)], {encoding: 'utf8'}));
  assert(createHash('sha256').update(await readFile(inputPath)).digest('hex') === snapshotHash);
  await rename(path.join(folder, 'bounded.partial.mp4'), final);
  emit('completed', 100, {finalized});
} catch (error) {
  if (cancelRequested && RenderInternals.isUserCancelledRender(error)) emit('cancelled', null, {message: error.message});
  else {emit('failed', null, {message: error.message}); process.exitCode = 1;}
} finally {
  await writeFile(path.join(folder, 'job-events.json'), JSON.stringify(events, null, 2));
  commands.close(); process.stdin.destroy();
}
