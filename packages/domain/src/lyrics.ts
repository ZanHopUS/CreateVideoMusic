import type { ProjectContent } from './generated';
import { TICKS, newProject, sourceTicks } from './index';
export type LyricLine = ProjectContent['lyrics'][number];
export type LyricDraft = { lines: LyricLine[]; errors: string[] };
const tick = (s: number) => Math.round(s * TICKS);
function timestamp(value: string): number {
  const parts = value.trim().replace(',', '.').split(':').map(Number);
  if (
    parts.some((n) => !Number.isFinite(n) || n < 0) ||
    parts.length < 2 ||
    parts.length > 3 ||
    parts.at(-1)! >= 60 ||
    (parts.length === 3 && parts[1] >= 60)
  )
    throw new Error('Mốc thời gian không hợp lệ.');
  return parts.reduce((sum, n) => sum * 60 + n, 0);
}
export function parseLyrics(
  input: string,
  format: 'lrc' | 'srt',
  sourceDurationTicks: number,
): LyricDraft {
  const errors: string[] = [],
    cues: { start: number; end?: number; text: string }[] = [];
  const text = input.replace(/^\uFEFF/, '').replace(/\r/g, '');
  if (text.length > 1024 * 1024)
    return { lines: [], errors: ['File lời vượt 1 MiB.'] };
  if (format === 'srt') {
    text
      .trim()
      .split(/\n\s*\n/)
      .filter(Boolean)
      .forEach((block, index) => {
        const rows = block.split('\n');
        if (/^\d+$/.test(rows[0])) rows.shift();
        const range = rows.shift()?.split(/\s*-->\s*/);
        try {
          if (range?.length !== 2 || !rows.join('').trim()) throw new Error();
          cues.push({
            start: tick(timestamp(range[0])),
            end: tick(timestamp(range[1])),
            text: rows.join('\n').trim(),
          });
        } catch {
          errors.push(
            `Khối ${index + 1}: timestamp hoặc nội dung SRT không hợp lệ.`,
          );
        }
      });
  } else {
    text.split('\n').forEach((row, index) => {
      if (!row.trim() || /^\[(ar|ti|al|by):/i.test(row)) return;
      try {
        const stamps = [...row.matchAll(/\[(\d+:\d+(?:\.\d+)?)\]/g)];
        const content = row.replace(/\[[^\]]*\]/g, '').trim();
        if (!stamps.length || !content) throw new Error();
        for (const match of stamps)
          cues.push({ start: tick(timestamp(match[1])), text: content });
      } catch {
        errors.push(`Dòng ${index + 1}: LRC cần [phút:giây] và nội dung.`);
      }
    });
  }
  cues.sort((a, b) => a.start - b.start);
  const lines: LyricLine[] = [];
  cues.forEach((cue, index) => {
    const end = cue.end ?? cues[index + 1]?.start ?? sourceDurationTicks;
    if (cue.start >= end || end > sourceDurationTicks) {
      errors.push(`Câu ${index + 1}: thời gian vượt nguồn hoặc không tăng.`);
      return;
    }
    lines.push({
      id: crypto.randomUUID(),
      text: cue.text,
      sourceStartTicks: cue.start,
      sourceEndTicks: end,
      source: 'import',
      status: 'draft',
      alignmentStatus: 'sentence',
      words: [],
    });
  });
  return { lines, errors };
}
/** Reviewed source cues clipped and mapped through one selected music item. */
export function applyLyrics(
  project: ProjectContent,
  lines: LyricLine[],
  audioId: string,
): ProjectContent {
  const p = structuredClone(project),
    audio = p.items.find((i) => i.id === audioId && i.type === 'audio');
  if (!audio) throw new Error('Chọn clip nhạc để gắn lời.');
  const existing = new Map(
    p.items.filter((i) => i.type === 'lyrics').map((i) => [i.lyricId, i]),
  );
  p.items = p.items.filter((i) => i.type !== 'lyrics');
  p.lyrics = structuredClone(lines).map((l) => ({
    ...l,
    sourceAudioItemId: audio.id,
  }));
  let track = p.orderedTracks.find((t) => t.kind === 'lyrics');
  if (!track) {
    track = { id: crypto.randomUUID(), kind: 'lyrics' };
    p.orderedTracks.push(track);
  }
  const end = sourceTicks(audio, audio.startTicks + audio.durationTicks);
  const rate = audio.speed.numerator / audio.speed.denominator;
  for (const line of p.lyrics) {
    if (line.status !== 'reviewed') continue;
    const startSource = Math.max(line.sourceStartTicks, audio.sourceStartTicks),
      endSource = Math.min(line.sourceEndTicks, end);
    if (endSource <= startSource) continue;
    const start =
      audio.startTicks +
      Math.round((startSource - audio.sourceStartTicks) / rate);
    const stop = Math.min(
      p.durationTicks,
      audio.startTicks +
        Math.round((endSource - audio.sourceStartTicks) / rate),
    );
    if (stop <= start) continue;
    p.items.push({
      id: existing.get(line.id)?.id ?? crypto.randomUUID(),
      trackId: existing.get(line.id)?.trackId ?? track.id,
      type: 'lyrics',
      lyricId: line.id,
      startTicks: start,
      durationTicks: stop - start,
      sourceStartTicks: startSource,
      speed: { ...audio.speed },
      volume: 1,
      style: existing.get(line.id)?.style ?? {
        fontFamily: 'Arial',
        fontSize: Math.min(p.preset.width, p.preset.height) * 0.067,
        color: '#ffffff',
        highlightColor: '#a3b7ff',
        x: p.preset.width * 0.08,
        y: p.preset.height * 0.7,
        shadow: true,
      },
    });
  }
  return p;
}
export function newLyricsProject(id: string) {
  const p = newProject(id, 'Video lời hát của tôi');
  p.templateRef = { id: 'TPL-03', version: 1 };
  p.items = [];
  p.orderedTracks.push({ id: 'lyrics', kind: 'lyrics' });
  return p;
}
export const PRESETS = (
  [
    [720, 1280],
    [1280, 720],
    [720, 720],
    [1080, 1920],
    [1920, 1080],
    [1080, 1080],
  ] as const
).flatMap(([width, height]) =>
  ([30, 60] as const).map((fps) => ({ width, height, fps })),
);

export function remapLyrics(project: ProjectContent): ProjectContent {
  const audioId = project.lyrics.find(
    (l) => l.sourceAudioItemId,
  )?.sourceAudioItemId;
  if (!audioId) return project;
  if (!project.items.some((i) => i.id === audioId && i.type === 'audio')) {
    const p = structuredClone(project);
    p.items = p.items.filter((i) => i.type !== 'lyrics');
    p.lyrics = p.lyrics.map(({ sourceAudioItemId: _source, ...line }) => ({
      ...line,
      status: 'draft',
    }));
    return p;
  }
  return applyLyrics(project, project.lyrics, audioId);
}
