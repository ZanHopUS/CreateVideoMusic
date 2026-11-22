import {bundle} from '@remotion/bundler';
import {ensureBrowser, renderMedia, renderStill, selectComposition} from '@remotion/renderer';
import {mkdir, writeFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {performance} from 'node:perf_hooks';

const here = path.dirname(fileURLToPath(import.meta.url));
process.chdir(here);
const root = path.resolve(here, '../..');
const local = path.join(root, '.poc');
const output = path.join(local, 'evidence/poc-03');
await mkdir(output, {recursive: true});
// Limit the initial executable smoke. --matrix explicitly runs the planned 36 cases.
const matrix = process.argv.includes('--matrix');
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
const results = [];
try {
  for (const settings of cases) {
    const name = `${settings.template}-${settings.ratio}-${settings.width}x${settings.height}-${settings.fps}`;
    const composition = await selectComposition({serveUrl, id: settings.template, inputProps: settings});
    const began = performance.now();
    let previous = 0;
    await renderMedia({serveUrl, composition, inputProps: settings,
      codec: 'h264', audioCodec: 'aac', pixelFormat: 'yuv420p',
      outputLocation: path.join(output, `${name}.mp4`), concurrency: 1,
      offthreadVideoThreads: 1, offthreadVideoCacheSizeInBytes: 64 * 1024 * 1024,
      x264Preset: 'ultrafast', hardwareAcceleration: 'disable',
      onProgress: ({progress}) => {
        if (progress + 0.001 < previous) throw new Error('Non-monotonic render progress');
        previous = progress;
      }});
    const seconds = (performance.now() - began) / 1000;
    await renderStill({serveUrl, composition, inputProps: settings, frame: settings.fps * 5,
      output: path.join(output, `${name}.png`)});
    const result = {...settings, name, renderSeconds: seconds, rtf: seconds / settings.seconds,
      generatedMedia: true, singingQualityEvidence: false};
    results.push(result);
    console.log(JSON.stringify(result));
    await writeFile(path.join(output, 'render-results.json'), JSON.stringify(results, null, 2));
  }
} catch (error) {
  await writeFile(path.join(output, 'error.json'), JSON.stringify({message: error.message, stack: error.stack}, null, 2));
  throw error;
}
