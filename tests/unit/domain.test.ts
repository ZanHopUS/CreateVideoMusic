import { describe, it, expect } from 'vitest';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import {
  canonicalContent,
  contentHash,
  frameTicks,
  History,
  sourceTicks,
  validateProject,
  validateTemplate,
  validateJob,
  type ProjectContent,
} from '@amvs/domain';
import fixture from '../fixtures/project.json';
const project = () => structuredClone(fixture) as unknown as ProjectContent;
describe('canonical project', () => {
  it('matches the Python JCS golden hash for Unicode and floating values', async () => {
    const bytes = canonicalContent(project());
    expect(await contentHash(project())).toBe(
      createHash('sha256').update(bytes).digest('hex'),
    );
    const expected = readFileSync(
      'tests/fixtures/project.sha256',
      'utf8',
    ).trim();
    expect(await contentHash(project())).toBe(expected);
    const reordered = Object.fromEntries(
      Object.entries(project()).reverse(),
    ) as ProjectContent;
    expect(canonicalContent(reordered)).toBe(bytes);
  });
  it('uses an absolute time mapping without accumulated frame rounding', () => {
    expect(frameTicks(18000, 60)).toBe(14400000);
    const item = project().items[0];
    item.startTicks = 48000;
    item.sourceStartTicks = 96000;
    item.speed = { numerator: 5, denominator: 4 };
    expect(sourceTicks(item, 96000)).toBe(156000);
  });
  it.each(['version', 'range', 'reference', 'track', 'duplicate', 'preset'])(
    'rejects %s',
    (kind) => {
      const p = project();
      if (kind === 'version') (p as any).schemaVersion = 'amvs-project/99';
      if (kind === 'range') p.items[0].durationTicks = p.durationTicks + 1;
      if (kind === 'reference') {
        p.items[0].type = 'image';
        p.items[0].assetId = 'a'.repeat(64);
      }
      if (kind === 'track') p.items[0].trackId = 'missing';
      if (kind === 'duplicate') p.items.push(structuredClone(p.items[0]));
      if (kind === 'preset') ((p.preset.height = 720), (p.preset.width = 1920));
      expect(() => validateProject(p)).toThrow();
    },
  );
  it('undoes a transaction; invalid edits do not corrupt history; new edits drop redo', () => {
    const history = new History(project()),
      initial = canonicalContent(history.read());
    history.edit((p) => {
      p.name = 'Đã chỉnh';
      p.items[0].text = 'Mới';
    });
    expect(() =>
      history.edit((p) => {
        p.items[0].durationTicks = 0;
      }),
    ).toThrow();
    expect(history.read().name).toBe('Đã chỉnh');
    history.undo();
    expect(canonicalContent(history.read())).toBe(initial);
    history.redo();
    expect(history.read().items[0].text).toBe('Mới');
    history.undo();
    history.edit((p) => {
      p.name = 'Nhánh mới';
    });
    expect(history.redo()).toBe(false);
  });
  it('validates template defaults and rejects mismatched placeholders', () => {
    const template = {
      schemaVersion: 'amvs-template/1',
      id: 'my-template',
      version: 1,
      name: 'Mẫu thử',
      defaultProject: project(),
      slots: [
        { id: 'caption-slot', itemId: 'caption', kind: 'text', required: true },
      ],
    };
    expect(() => validateTemplate(template)).not.toThrow();
    template.slots[0].kind = 'image';
    expect(() => validateTemplate(template)).toThrow();
  });
  it('requires validated job progress and a supported DTO version', () => {
    const job = {
      schemaVersion: 'amvs-job/1',
      id: 'a'.repeat(32),
      kind: 'render',
      projectId: 'fixture-project',
      status: 'succeeded',
      phase: 'succeeded',
      progress: 1,
      snapshotHash: 'b'.repeat(64),
      message: 'Sẵn sàng',
    };
    expect(() => validateJob(job)).not.toThrow();
    job.progress = 0.95;
    expect(() => validateJob(job)).toThrow();
    job.progress = 1;
    job.schemaVersion = 'amvs-job/99';
    expect(() => validateJob(job)).toThrow();
  });
});
