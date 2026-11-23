import { bundle } from '@remotion/bundler';
import { renderMedia, selectComposition } from '@remotion/renderer';
import { readFile, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
const here = path.dirname(fileURLToPath(import.meta.url));
const folder = path.resolve(process.argv[2]);
const input = JSON.parse(
  await readFile(path.join(folder, 'input.json'), 'utf8'),
);
// This process is invoked only with an API-owned job folder, never client argv.
const serveUrl = await bundle({
  entryPoint: path.join(here, 'root.tsx'),
  publicDir: path.join(folder, 'public'),
  outDir: path.join(folder, 'bundle'),
});
const browserExecutable = process.env.AMVS_BROWSER;
if (!browserExecutable)
  throw new Error('Chưa chuẩn bị browser render local. Chạy setup trước.');
const inputProps = { project: input.project, assets: input.assets };
const composition = await selectComposition({
  serveUrl,
  id: 'Project',
  inputProps,
  browserExecutable,
});
let last = -1;
await renderMedia({
  serveUrl,
  composition,
  inputProps,
  browserExecutable,
  outputLocation: path.join(folder, 'raw.mp4'),
  codec: 'h264',
  audioCodec: 'aac',
  pixelFormat: 'yuv420p',
  concurrency: 1,
  offthreadVideoThreads: 1,
  offthreadVideoCacheSizeInBytes: 64 * 1024 * 1024,
  x264Preset: 'ultrafast',
  hardwareAcceleration: 'disable',
  onProgress: ({ progress }) => {
    const p = Math.floor(progress * 100);
    if (p > last) {
      last = p;
      console.log(
        JSON.stringify({
          phase: 'running',
          progress: Math.min(0.85, progress * 0.85),
        }),
      );
    }
  },
});
await writeFile(
  path.join(folder, 'rendered.json'),
  JSON.stringify({
    frames: composition.durationInFrames,
    fps: composition.fps,
  }),
);
