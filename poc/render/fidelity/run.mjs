import {bundle} from '@remotion/bundler';
import {openBrowser, renderMedia, renderStill, selectComposition} from '@remotion/renderer';
import {createServer} from 'node:http';
import {createReadStream} from 'node:fs';
import {readFile, writeFile, mkdir, stat} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import assert from 'node:assert/strict';
import {makeProjects, probeFrames} from './projects.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
process.chdir(path.resolve(here, '..'));
const root = path.resolve(here, '../../..');
const local = path.join(root, '.poc');
const flag = process.argv.indexOf('--run-id');
const runId = flag < 0 ? 'full-01' : process.argv[flag + 1];
assert(/^[a-z0-9-]+$/.test(runId));
const quick = process.argv.includes('--quick');
const proxyMode = process.argv.includes('--proxy-vfr');
const seekNudge = process.argv.includes('--seek-nudge');
const output = path.join(local, 'evidence/poc-03/fidelity', runId);
await mkdir(output, {recursive: false});
const assets = path.join(local, 'render/fidelity-public');
const projects = makeProjects().filter(p => !(proxyMode || seekNudge) || p.id === 'TPL03');
if (proxyMode) for (const project of projects) for (const item of project.items) {
  if (item.asset === 'vfr.mp4') item.asset = 'vfr-cfr30.mp4';
}
if (seekNudge) for (const project of projects) for (const item of project.items) {
  if (item.type === 'video') item.seekNudgeFrames = .0003; // 10us at the 30FPS fixture timebase.
}
const inventory = [];
for (const file of ['projects.mjs', 'scene.jsx', 'root.jsx', 'player.jsx', 'run.mjs']) {
  const data = await readFile(path.join(here, file));
  inventory.push({file, sha256: createHash('sha256').update(data).digest('hex')});
}
await writeFile(path.join(output, 'config.json'), JSON.stringify({quick, proxyMode, seekNudge, projects, probeFrames,
  proxyManifest: proxyMode ? JSON.parse(await readFile(path.join(assets, 'proxy-manifest.json'), 'utf8')) : null,
  inventory, assetManifest: JSON.parse(await readFile(path.join(assets, 'manifest.json'), 'utf8'))}, null, 2));
console.log(JSON.stringify({phase: 'bundle', runId}));
const renderBundle = await bundle({entryPoint: path.join(here, 'root.jsx'), publicDir: assets,
  outDir: path.join(local, 'render/fidelity-render-bundle')});
const playerBundle = await bundle({entryPoint: path.join(here, 'root.jsx'), publicDir: assets,
  outDir: path.join(local, 'render/fidelity-player-bundle'), webpackOverride: config => ({...config,
    entry: path.join(here, 'player.jsx')})});
const html = '<!doctype html><html><head><meta charset="utf-8"><style>html,body{margin:0;padding:0;overflow:hidden;background:#101827}</style></head><body><div id="root"></div><script>window.remotion_staticBase="/public";</script><script src="/bundle.js"></script></body></html>';
await writeFile(path.join(playerBundle, 'preview.html'), html);
const types = {'.html':'text/html', '.js':'application/javascript', '.json':'application/json',
  '.mp4':'video/mp4', '.wav':'audio/wav', '.svg':'image/svg+xml', '.png':'image/png'};
const server = createServer(async (req, res) => {
  try {
    const url = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
    const file = path.resolve(playerBundle, `.${url}`);
    if (!file.startsWith(playerBundle + path.sep)) {res.writeHead(403).end(); return;}
    const info = await stat(file);
    const range = req.headers.range?.match(/^bytes=(\d+)-(\d*)$/);
    const start = range ? Number(range[1]) : 0;
    const end = range && range[2] ? Math.min(Number(range[2]), info.size - 1) : info.size - 1;
    if (start > end) {res.writeHead(416).end(); return;}
    res.writeHead(range ? 206 : 200, {'Content-Type': types[path.extname(file)] ?? 'application/octet-stream',
      'Accept-Ranges':'bytes', 'Content-Length':end-start+1,
      ...(range ? {'Content-Range':`bytes ${start}-${end}/${info.size}`} : {})});
    if (req.method === 'HEAD') res.end(); else createReadStream(file, {start, end}).pipe(res);
  } catch {res.writeHead(404).end();}
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const browser = await openBrowser('chrome', {forceDeviceScaleFactor: 1, logLevel: 'error'});
const errors = [];
const result = {runId, quick, cases: [], errors};
try {
  const page = await browser.newPage({context: () => null, logLevel: 'error', indent: false,
    pageIndex: 0, onBrowserLog: log => {if (log.type === 'error') errors.push(log.text);}, onLog: () => {}});
  await page.setViewport({width: 1280, height: 720, deviceScaleFactor: 1});
  await page.goto({url: `http://127.0.0.1:${server.address().port}/preview.html`, timeout: 30000});
  for (let attempt=0; attempt<100; attempt++) {
    if (await page.evaluate(() => Boolean(window.__poc))) break;
    await new Promise(resolve => setTimeout(resolve, 100));
  }
  assert(await page.evaluate(() => Boolean(window.__poc)), 'Player API not ready');
  for (const project of projects) {
    const folder = path.join(output, project.id);
    await mkdir(folder, {recursive: true});
    await writeFile(path.join(folder, 'snapshot.json'), JSON.stringify(project, null, 2));
    await page.evaluate(async p => window.__poc.load(p), project);
    const composition = await selectComposition({serveUrl: renderBundle, id: project.id,
      inputProps: {project}, puppeteerInstance: browser});
    const row = {projectId: project.id, probes: []};
    result.cases.push(row);
    if (!quick) {
      const began = performance.now();
      await renderMedia({serveUrl: renderBundle, composition, inputProps: {project}, puppeteerInstance: browser,
        outputLocation: path.join(folder, 'raw.mp4'), codec: 'h264', audioCodec: 'aac', pixelFormat: 'yuv420p',
        x264Preset: 'ultrafast', concurrency: 2, offthreadVideoThreads: 1,
        offthreadVideoCacheSizeInBytes: 64 * 1024 * 1024, hardwareAcceleration: 'disable'});
      row.renderSeconds = (performance.now() - began) / 1000;
      execFileSync(path.join(local, 'venv-asr/Scripts/python.exe'), [path.join(here, '../finalize_mp4.py'),
        '--input', path.join(folder, 'raw.mp4'), '--output', path.join(folder, 'export.mp4'), '--seconds', '12']);
    }
    for (const frame of quick ? [0, 30, 180, 210, 359] : probeFrames) {
      await renderStill({serveUrl: renderBundle, composition, inputProps: {project}, frame,
        puppeteerInstance: browser, output: path.join(folder, `render-${frame}.png`)});
      await page.bringToFront();
      const probe = await page.evaluate(async value => window.__poc.seek(value), frame);
      const capture = await page._client().send('Page.captureScreenshot', {format: 'png', fromSurface: true});
      await writeFile(path.join(folder, `player-${frame}.png`), Buffer.from(capture.value.data, 'base64'));
      row.probes.push(probe);
      console.log(JSON.stringify({project: project.id, frame, sourceTimes: probe.videos, seekMs: probe.elapsedMs}));
    }
    if (!quick && !proxyMode && !seekNudge) {
      row.seekSamples = [];
      for (let i=0; i<100; i++) row.seekSamples.push(await page.evaluate(async frame => window.__poc.seek(frame), (i * 137) % 360));
    }
    await writeFile(path.join(output, 'results.json'), JSON.stringify(result, null, 2));
  }
  if (!quick && !proxyMode && !seekNudge) {
    await page.evaluate(async project => window.__poc.load(project), projects[0]);
    result.simplePlayerPlayback = await page.evaluate(() => window.__poc.playFor(60000));
  }
  await writeFile(path.join(output, 'results.json'), JSON.stringify(result, null, 2));
} catch (error) {
  await writeFile(path.join(output, 'error.json'), JSON.stringify({message: error.message, stack: error.stack}, null, 2));
  throw error;
} finally {
  await browser.close({silent: true}); server.closeAllConnections();
  await new Promise(resolve => server.close(resolve));
}
console.log(JSON.stringify({phase: 'complete', cases: result.cases.length, runId}));
