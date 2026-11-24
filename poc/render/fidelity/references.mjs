import {renderStill, selectComposition} from '@remotion/renderer';
import {readFile} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
process.chdir(path.resolve(here, '..'));
const root = path.resolve(here, '../../..');
const folder = path.resolve(process.argv[2]);
const serveUrl = path.join(root, '.poc/render/fidelity-render-bundle');
for (const [name, file] of [['original', 'snapshot.json'], ['edited', 'working.json']]) {
  const project = JSON.parse(await readFile(path.join(folder, file), 'utf8'));
  const composition = await selectComposition({serveUrl, id: project.id, inputProps: {project}});
  await renderStill({serveUrl, composition, inputProps: {project}, frame: 150,
    output: path.join(folder, `reference-${name}.png`)});
}
