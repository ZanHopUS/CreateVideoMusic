import assert from 'node:assert/strict';
import {readFile, writeFile} from 'node:fs/promises';
import path from 'node:path';
import {digest, instantiate} from './model.mjs';

const directory = path.resolve(process.argv[2]);
const data = JSON.parse(await readFile(path.join(directory, 'state-fixtures.json'), 'utf8'));
const catalog = JSON.parse(await readFile(path.join(directory, 'catalog.json'), 'utf8'));
const rows = [];
for (const template of data.templates) {
  const slot = template.slots[0], before = digest(template);
  const kind = slot.kind === 'image' ? 'image/' : slot.kind === 'audio' ? 'audio/' : 'video/';
  const valid = catalog.find(a => a.mime.startsWith(kind) && a.path !== template.project.items.find(i => i.id === slot.itemId).asset);
  const wrong = catalog.find(a => !a.mime.startsWith(kind));
  assert(valid && wrong);
  const good = instantiate(template, `bound-${template.project.id}`, {[slot.id]: valid.path});
  const bad = instantiate(template, `invalid-${template.project.id}`, {[slot.id]: wrong.path});
  assert.equal(good.items.find(i => i.id.endsWith(`-${slot.itemId}`)).asset, valid.path);
  assert.equal(digest(template), before);
  rows.push({templateId:template.id, good, bad, templateUnchanged:true});
}
await writeFile(path.join(directory, 'binding-fixtures.json'), JSON.stringify(rows, null, 2));
console.log(JSON.stringify({placeholderBindings: rows.length, templateUnchanged:true,
  note:'MIME validation is performed at the storage/catalog boundary'}));
