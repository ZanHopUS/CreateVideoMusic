import type { ProjectContent } from './generated';

export type MediaInfo = {
  id: string;
  kind: 'image' | 'video' | 'audio';
  durationTicks: number;
};
const MAX_DURATION = 14_400_000;

function refs(project: ProjectContent) {
  project.assetRefs = [
    ...new Set(project.items.flatMap((i) => (i.assetId ? [i.assetId] : []))),
  ];
}

function extend(project: ProjectContent, end: number) {
  if (end > MAX_DURATION)
    throw new Error(
      'Các clip vượt 300 giây. Hãy rút ngắn hoặc gỡ clip trước khi thêm.',
    );
  project.durationTicks = Math.max(project.durationTicks, end);
}

/** Return a new project: existing edits and caller state are never mutated. */
export function appendMedia(
  project: ProjectContent,
  media: MediaInfo[],
  makeId: () => string = () => crypto.randomUUID(),
): ProjectContent {
  const next = structuredClone(project);
  const frame = next.timebase / next.preset.fps;
  const floorFrame = (ticks: number) => Math.floor(ticks / frame) * frame;
  const track = (kind: 'background' | 'music') => {
    const existing = next.orderedTracks.find((t) => t.kind === kind);
    if (existing) return existing.id;
    const id = `track-${makeId()}`;
    if (kind === 'background') next.orderedTracks.unshift({ id, kind });
    else next.orderedTracks.push({ id, kind });
    return id;
  };
  const add = (
    asset: MediaInfo,
    trackId: string,
    start: number,
    duration: number,
  ) => {
    if (!Number.isFinite(duration) || duration < frame)
      throw new Error(
        'Media ngắn hơn một frame hoặc không đọc được thời lượng.',
      );
    extend(next, start + duration);
    next.items.push({
      id: makeId(),
      trackId,
      type: asset.kind,
      assetId: asset.id,
      startTicks: start,
      durationTicks: duration,
      sourceStartTicks: 0,
      speed: { numerator: 1, denominator: 1 },
      volume: asset.kind === 'video' ? 0 : 1,
      ...(asset.kind !== 'audio' ? { style: { fit: 'cover' as const } } : {}),
    });
  };
  const visuals = media.filter((a) => a.kind !== 'audio');
  if (visuals.length) {
    const id = track('background');
    const existing = next.items.filter((i) => i.trackId === id);
    let cursor = Math.max(
      0,
      ...existing.map((i) => i.startTicks + i.durationTicks),
    );
    if (!existing.length) {
      extend(next, visuals.length * frame);
      const base = Math.max(
        frame,
        floorFrame(next.durationTicks / visuals.length),
      );
      const capacities = visuals.map((a) =>
        a.kind === 'image' ? MAX_DURATION : floorFrame(a.durationTicks),
      );
      const lengths = capacities.map((cap) => Math.min(base, cap));
      let remaining = floorFrame(
        next.durationTicks - lengths.reduce((a, b) => a + b, 0),
      );
      lengths.forEach((length, index) => {
        const extra = Math.min(remaining, capacities[index] - length);
        lengths[index] += extra;
        remaining -= extra;
      });
      visuals.forEach((asset, index) => {
        add(asset, id, cursor, lengths[index]);
        cursor += lengths[index];
      });
    } else {
      for (const asset of visuals) {
        const duration = floorFrame(
          Math.min(
            5 * next.timebase,
            asset.kind === 'image' ? MAX_DURATION : asset.durationTicks,
          ),
        );
        add(asset, id, cursor, duration);
        cursor += duration;
      }
    }
  }
  const audio = media.filter((a) => a.kind === 'audio');
  if (audio.length) {
    const id = track('music');
    const existing = next.items.filter((i) => i.trackId === id);
    let cursor = Math.max(
      0,
      ...existing.map((i) => i.startTicks + i.durationTicks),
    );
    for (const asset of audio) {
      const duration = floorFrame(
        Math.min(
          asset.durationTicks,
          cursor === 0 ? next.durationTicks : 5 * next.timebase,
        ),
      );
      add(asset, id, cursor, duration);
      cursor += duration;
    }
  }
  refs(next);
  return next;
}

/** Reordering is an explicit compact montage operation, preserving source cuts. */
export function reorderClip(
  project: ProjectContent,
  id: string,
  direction: -1 | 1,
): ProjectContent {
  const next = structuredClone(project),
    item = next.items.find((i) => i.id === id);
  if (!item || !['image', 'video', 'audio'].includes(item.type))
    throw new Error('Chọn clip ảnh, video hoặc nhạc để đổi thứ tự.');
  const siblings = next.items
    .filter((i) => i.trackId === item.trackId)
    .sort((a, b) => a.startTicks - b.startTicks);
  const from = siblings.findIndex((i) => i.id === id),
    to = from + direction;
  if (to < 0 || to >= siblings.length) return next;
  [siblings[from], siblings[to]] = [siblings[to], siblings[from]];
  let cursor = 0;
  for (const clip of siblings) {
    clip.startTicks = cursor;
    cursor += clip.durationTicks;
  }
  extend(next, cursor);
  next.items = [
    ...next.items.filter((i) => i.trackId !== item.trackId),
    ...siblings,
  ];
  return next;
}

export function removeClip(
  project: ProjectContent,
  id: string,
): ProjectContent {
  const next = structuredClone(project);
  next.items = next.items.filter((i) => i.id !== id);
  refs(next);
  return next;
}

export function validateMediaWindows(
  project: ProjectContent,
  catalog: MediaInfo[],
) {
  const assets = new Map(catalog.map((a) => [a.id, a]));
  for (const item of project.items) {
    if (!item.assetId) continue;
    const asset = assets.get(item.assetId);
    if (!asset || asset.kind !== item.type)
      throw new Error('Media thiếu hoặc loại media không khớp.');
    const sourceEnd =
      item.sourceStartTicks +
      (item.durationTicks * item.speed.numerator) / item.speed.denominator;
    if (asset.kind !== 'image' && sourceEnd > asset.durationTicks)
      throw new Error('Đoạn cắt vượt thời lượng nguồn.');
  }
}
