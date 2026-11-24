import { describe, it, expect } from 'vitest';
import {
  newProject,
  appendMedia,
  reorderClip,
  removeClip,
  validateMediaWindows,
  validateProject,
  TICKS,
} from '@amvs/domain';
const image = { id: 'a'.repeat(64), kind: 'image' as const, durationTicks: 0 };
const image2 = { ...image, id: 'b'.repeat(64) };
const video = {
  id: 'c'.repeat(64),
  kind: 'video' as const,
  durationTicks: 2 * TICKS,
};
const audio = {
  id: 'd'.repeat(64),
  kind: 'audio' as const,
  durationTicks: 30 * TICKS,
};
const ids = () => {
  let n = 0;
  return () => `clip-${++n}`;
};
describe('multi-media commands', () => {
  it('places an initial batch without replacing layers or overflowing the video source', () => {
    const input = newProject('p'),
      before = structuredClone(input);
    const p = appendMedia(input, [image, video, audio], ids());
    expect(input).toEqual(before);
    expect(p.items.find((i) => i.id === 'caption')).toEqual(before.items[0]);
    expect(p.items.filter((i) => i.trackId === 'background')).toHaveLength(2);
    expect(p.items.find((i) => i.type === 'video')!.durationTicks).toBe(
      2 * TICKS,
    );
    expect(p.items.find((i) => i.type === 'image')!.durationTicks).toBe(
      13 * TICKS,
    );
    validateProject(p);
    validateMediaWindows(p, [image, video, audio]);
  });
  it('appends new media and extends the project without modifying previous source edits', () => {
    const p = appendMedia(newProject('p'), [image, audio]);
    const existing = structuredClone(p.items);
    const next = appendMedia(p, [image2, video]);
    for (const item of existing)
      expect(next.items.find((i) => i.id === item.id)).toEqual(item);
    expect(next.durationTicks).toBe(22 * TICKS);
    expect(next.assetRefs).toHaveLength(4);
    validateMediaWindows(next, [image, image2, video, audio]);
  });
  it('rejects an over-300s append atomically', () => {
    const p = newProject('p');
    p.durationTicks = 300 * TICKS;
    const full = appendMedia(p, [image]);
    const before = structuredClone(full);
    expect(() => appendMedia(full, [image2])).toThrow();
    expect(full).toEqual(before);
  });
  it('reorders a montage preserving duration, source trim, IDs and styles; undo restores it', () => {
    const p = appendMedia(newProject('p'), [image, video], ids());
    const clip = p.items.find((i) => i.type === 'video')!;
    clip.durationTicks = TICKS;
    clip.sourceStartTicks = TICKS;
    const next = reorderClip(p, clip.id, -1);
    expect(next.items.find((i) => i.id === clip.id)).toEqual({
      ...clip,
      startTicks: 0,
    });
    expect(p.items.find((i) => i.id === clip.id)!.startTicks).not.toBe(0);
    expect(next.items.find((i) => i.type === 'image')!.startTicks).toBe(TICKS);
    validateMediaWindows(next, [image, video]);
  });
  it('removes only an item/ref, retaining a shared asset referenced by another clip', () => {
    const p = appendMedia(newProject('p'), [image, image], ids());
    const first = p.items.find((i) => i.type === 'image')!;
    const next = removeClip(p, first.id);
    expect(next.assetRefs).toEqual([image.id]);
    const last = next.items.find((i) => i.type === 'image')!;
    expect(removeClip(next, last.id).assetRefs).toEqual([]);
  });
  it('rejects wrong kinds, missing assets and source overflow including playback rate', () => {
    const p = appendMedia(newProject('p'), [video]);
    const clip = p.items.find((i) => i.type === 'video')!;
    expect(() => validateMediaWindows(p, [])).toThrow();
    expect(() =>
      validateMediaWindows(p, [{ ...video, kind: 'image' }]),
    ).toThrow();
    clip.speed = { numerator: 5, denominator: 4 };
    expect(() => validateMediaWindows(p, [video])).toThrow();
  });
});
