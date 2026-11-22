import {bundle} from '@remotion/bundler';
import {ensureBrowser, renderStill, selectComposition} from '@remotion/renderer';
import {mkdir} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
process.chdir(here);
const local = path.resolve(here, '../../.poc');
const output = path.join(local, 'evidence/poc-04/preflight');
await mkdir(output, {recursive: true});
await ensureBrowser();
const serveUrl = await bundle({entryPoint: path.join(here, 'stress-fixture.jsx'),
  publicDir: path.join(local, 'render/stress-public'), outDir: path.join(local, 'render/stress-preflight-bundle')});
for (const template of ['TPL01', 'TPL02']) {
  const inputProps = {template, width: 1080, height: 1920, fps: 60, seconds: 300};
  const composition = await selectComposition({serveUrl, id: `${template}Stress`, inputProps});
  await renderStill({serveUrl, composition, inputProps, frame: 9000,
    output: path.join(output, `${template}.png`)});
  console.log(JSON.stringify({template, composition: composition.id, frame: 9000, passed: true}));
}
