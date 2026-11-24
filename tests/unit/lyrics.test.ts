import { describe, it, expect } from 'vitest';
import {
  appendMedia,
  applyLyrics,
  History,
  newLyricsProject,
  parseLyrics,
  PRESETS,
  remapLyrics,
  TICKS,
  validateProject,
  validateMediaWindows,
} from '@amvs/domain';
const hash = 'a'.repeat(64);
function project() {
  const p = newLyricsProject('lyrics-test');
  return appendMedia(p, [
    { id: hash, kind: 'audio', durationTicks: 40 * TICKS },
  ]);
}
describe('lyrics source time and review', () => {
  it('parses LRC repeated timestamps, metadata and reports malformed lines', () => {
    const result = parseLyrics(
      '[ar:Kiểm thử]\n[00:01.20][00:03.00]Lời Việt\nbroken\n[00:04.00]Cuối',
      'lrc',
      10 * TICKS,
    );
    expect(result.lines).toHaveLength(3);
    expect(result.lines[0].sourceEndTicks).toBe(3 * TICKS);
    expect(result.lines.every((l) => l.status === 'draft')).toBe(true);
    expect(result.errors).toHaveLength(1);
  });
  it('rejects backwards/out-of-range SRT and invalid seconds without discarding valid cues', () => {
    const result = parseLyrics(
      '1\n00:00:01,000 --> 00:00:02,000\nXin chào\n\n2\n00:00:04,000 --> 00:00:03,000\nSai\n\n3\n00:00:61,000 --> 00:01:02,000\nSai',
      'srt',
      10 * TICKS,
    );
    expect(result.lines).toHaveLength(1);
    expect(result.errors).toHaveLength(2);
  });
  it('maps reviewed lyrics through source trim/rate and clips edges, leaves draft invisible', () => {
    const p = project(),
      audio = p.items[0];
    audio.startTicks = TICKS;
    audio.durationTicks = 5 * TICKS;
    audio.sourceStartTicks = 10 * TICKS;
    audio.speed = { numerator: 2, denominator: 1 };
    const draft = parseLyrics(
      '[00:09.00]Đầu\n[00:12.00]Giữa\n[00:21.00]Ngoài',
      'lrc',
      40 * TICKS,
    ).lines;
    draft[0].status = 'reviewed';
    draft[1].status = 'reviewed';
    const next = applyLyrics(p, draft, audio.id);
    validateProject(next);
    const items = next.items.filter((i) => i.type === 'lyrics');
    expect(items).toHaveLength(2);
    expect(items[0].startTicks).toBe(TICKS);
    expect(items[0].durationTicks).toBe(TICKS);
    expect(items[1].startTicks).toBe(2 * TICKS);
    expect(items[1].durationTicks).toBe(4 * TICKS);
    expect(p.lyrics).toEqual([]);
  });
  it('remaps lyrics after audio edits preserving style/IDs and undo restores atomic state', () => {
    const p = project();
    const lines = parseLyrics('[00:01]Một câu', 'lrc', 5 * TICKS).lines.map(
      (l) => ({ ...l, status: 'reviewed' as const }),
    );
    const applied = applyLyrics(p, lines, p.items[0].id);
    const item = applied.items.find((i) => i.type === 'lyrics')!;
    item.style = { fontSize: 88 };
    const h = new History(applied);
    h.edit((p) => {
      p.items[0].startTicks = TICKS;
      p.items[0].durationTicks -= TICKS;
      Object.assign(p, remapLyrics(p));
    });
    const changed = h.read().items.find((i) => i.type === 'lyrics')!;
    expect(changed.id).toBe(item.id);
    expect(changed.style?.fontSize).toBe(88);
    expect(changed.startTicks).toBe(item.startTicks + TICKS);
    h.undo();
    expect(h.read()).toEqual(applied);
  });
  it('rejects manual cue beyond the actual source duration', () => {
    const p = project();
    const l = parseLyrics('[00:01]Câu', 'lrc', 100 * TICKS).lines.map((l) => ({
      ...l,
      status: 'reviewed' as const,
    }));
    const applied = applyLyrics(p, l, p.items[0].id);
    expect(() =>
      validateMediaWindows(applied, [
        { id: hash, kind: 'audio', durationTicks: 40 * TICKS },
      ]),
    ).toThrow();
  });
  it('supports exactly twelve valid presets without silently altering project content', () => {
    expect(PRESETS).toHaveLength(12);
    for (const preset of PRESETS) {
      const p = project();
      p.preset = preset;
      validateProject(p);
      expect(p.templateRef.id).toBe('TPL-03');
    }
  });
});

it('history pins removed media until the session history is released', () => {
  const p = project();
  const history = new History(p);
  history.edit((p) => {
    p.items = [];
    p.assetRefs = [];
  });
  expect(history.assetPins()).toContain(hash);
  history.undo();
  expect(history.read().assetRefs).toContain(hash);
});

it('lyrics remain visible on square presets and keep a user-selected lyrics track', () => {
  const p = project();
  p.preset = { width: 720, height: 720, fps: 60 };
  p.orderedTracks.push({ id: 'lyrics-secondary', kind: 'lyrics' });
  const lines = parseLyrics('[00:01]Một câu', 'lrc', 3 * TICKS).lines.map(
    (l) => ({ ...l, status: 'reviewed' as const }),
  );
  const applied = applyLyrics(p, lines, p.items[0].id);
  const item = applied.items.find((i) => i.type === 'lyrics')!;
  expect(item.style!.y! < 720).toBe(true);
  item.trackId = 'lyrics-secondary';
  const mapped = remapLyrics(applied);
  expect(mapped.items.find((i) => i.id === item.id)?.trackId).toBe(
    'lyrics-secondary',
  );
});
