import assert from 'node:assert/strict';
import {readFile, writeFile} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {performance} from 'node:perf_hooks';
import {makeProjects} from '../render/fidelity/projects.mjs';
import {clone, digest, History, instantiate, makeTemplate} from './model.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const output = path.resolve(process.argv[2]);
assert(output.startsWith(path.join(root, '.poc') + path.sep));
const catalog = JSON.parse(await readFile(path.join(output, 'catalog.json'), 'utf8'));
const cases = [], templates = [], stats = [];
for (const original of makeProjects()) {
  for (const count of [12, 100]) {
    const project = clone(original);
    project.id = `${original.id}-${count}`; project.name = `Dự án kiểm thử ${original.id} — ${count} items`;
    project.durationInFrames = count === 100 ? 9000 : 360;
    project.items = Array.from({length: count}, (_, n) => {
      const item = clone(original.items[n % original.items.length]);
      item.duration = Math.min(item.duration, original.durationInFrames - item.start);
      item.id = `item-${n}`; item.start += Math.floor(n / original.items.length) * 360;
      if (item.asset) item.asset = catalog.find(a => a.originalName === item.asset).path;
      return item;
    });
    project.uiState = {playheadFrame: 0, selectedIds: [project.items[0].id]};
    const initial = clone(project), history = new History(project), hashes = [digest(project)], times = [];
    for (let n = 0; n < 50; n++) {
      const began = performance.now();
      history.edit(next => {
        const caption = next.items.find(i => i.type === 'caption');
        if (n % 5 === 0) {
          const media = next.items.find(i => i.type === 'video' || i.type === 'image');
          const sourceEnd = (media.sourceStart ?? 0) + media.duration * (media.speed ?? 1);
          media.start++; media.duration--;
          if (media.type === 'video') {
            media.sourceStart += media.speed;
            assert(Math.abs(media.sourceStart + media.duration * media.speed - sourceEnd) < 1e-8);
          }
        } else if (n % 5 === 1) next.items.push(next.items.shift());
        else if (n % 5 === 2) caption.z = 8 + n % 6;
        else if (n % 5 === 3) caption.text = `Đã sửa lần ${n} — chữ Việt đầy đủ`;
        else caption.duration = Math.max(1, caption.duration - 1);
      });
      times.push(performance.now() - began); hashes.push(digest(history.read()));
    }
    const edited = history.read(); assert(history.dirty);
    for (let n = 49; n >= 0; n--) {assert(history.undo()); assert.equal(digest(history.read()), hashes[n]);}
    assert(!history.dirty); assert.deepEqual(history.read(), initial);
    for (let n = 1; n <= 50; n++) {assert(history.redo()); assert.equal(digest(history.read()), hashes[n]);}
    assert.deepEqual(history.read(), edited);
    const beforeInvalid = digest(history.read());
    assert.throws(() => history.edit(next => {next.items[0].duration = 999999;}));
    assert.equal(digest(history.read()), beforeInvalid);
    const saving = history.read();
    history.edit(next => {next.name += ' — thay đổi khi đang lưu';});
    history.markSaved(saving); assert(history.dirty);
    history.undo(); assert(!history.dirty);
    history.edit(next => {next.name += ' — nhánh mới';}); assert(!history.redo());
    const external = history.read(); external.name = 'Không được mutate nội bộ'; assert.notEqual(history.read().name, external.name);
    const template = makeTemplate(initial, `template-${project.id}`), originalHash = digest(template);
    const a = instantiate(template, `instance-a-${project.id}`), b = instantiate(template, `instance-b-${project.id}`);
    const bHash = digest(b); a.items.find(i => i.type === 'caption').text = 'Chỉ đổi instance A';
    assert.equal(digest(template), originalHash); assert.equal(digest(b), bHash);
    assert(a.items.every(i => !b.items.some(j => j.id === i.id)));
    assert.deepEqual([...new Set(a.items.filter(i => i.asset).map(i => i.asset))].sort(),
      [...new Set(b.items.filter(i => i.asset).map(i => i.asset))].sort());
    cases.push({id: project.id, initial, edited}); templates.push(template);
    times.sort((a, b) => a-b);
    stats.push({id: project.id, itemCount: count, editCount: 50, undoVerified: 50, redoVerified: 50,
      editModelP95Ms: times[Math.ceil(times.length * .95)-1], heapUsedBytes: process.memoryUsage().heapUsed,
      invalidEditRejected: true, dirtyAndBranchChecks: true, templateIsolation: true});
  }
}
await writeFile(path.join(output, 'state-fixtures.json'), JSON.stringify({cases, templates}, null, 2));
await writeFile(path.join(output, 'state-results.json'), JSON.stringify({allPassed: true, stats,
  scope: 'model operations only; no editor UI latency or production state library selection'}, null, 2));
console.log(JSON.stringify({allPassed: true, scenarios: stats.length, edits: 300, undo: 300, redo: 300, stats}));
