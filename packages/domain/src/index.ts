import Ajv2020 from 'ajv/dist/2020.js';
import canonicalize from 'canonicalize';
import schema from '../project.schema.json';
import templateSchema from '../template.schema.json';
import jobSchema from '../job.schema.json';
import type { ProjectContent } from './generated';
import type { TemplateDefinition } from './generated-template';
import type { JobState } from './generated-job';
export type { ProjectContent };
export type { TemplateDefinition, JobState };
export type TimelineItem = ProjectContent['items'][number];
export const TICKS = 48000;
const validator = new Ajv2020({ allErrors: true, strict: false }).compile(
  schema,
);
const templateValidator = new Ajv2020({ strict: false }).compile(
  templateSchema,
);
const jobValidator = new Ajv2020({ strict: false }).compile(jobSchema);

export function validateTemplate(
  value: unknown,
): asserts value is TemplateDefinition {
  if (!templateValidator(value)) throw new Error('Template không hợp lệ.');
  const template = value as unknown as TemplateDefinition;
  validateProject(template.defaultProject);
  if (new Set(template.slots.map((s) => s.id)).size !== template.slots.length)
    throw new Error('Slot ID trùng.');
  for (const slot of template.slots) {
    if (
      !template.defaultProject.items.some(
        (i) => i.id === slot.itemId && i.type === slot.kind,
      )
    )
      throw new Error('Placeholder không hợp lệ.');
  }
}
export function validateJob(value: unknown): asserts value is JobState {
  if (!jobValidator(value)) throw new Error('Job không hợp lệ.');
}

export function validateProject(
  value: unknown,
): asserts value is ProjectContent {
  if (!validator(value)) throw new Error('Dữ liệu project không hợp lệ.');
  const p = value as unknown as ProjectContent;
  const tracks = new Map(p.orderedTracks.map((t) => [t.id, t.kind]));
  const ids = new Set(p.items.map((i) => i.id));
  if (tracks.size !== p.orderedTracks.length || ids.size !== p.items.length)
    throw new Error('ID trùng.');
  if (
    ![
      [720, 1280],
      [1280, 720],
      [720, 720],
      [1080, 1920],
      [1920, 1080],
      [1080, 1080],
    ].some(([w, h]) => w === p.preset.width && h === p.preset.height)
  )
    throw new Error('Preset không hợp lệ.');
  const kinds = {
    image: 'background',
    video: 'background',
    audio: 'music',
    text: 'text',
    lyrics: 'lyrics',
  };
  for (const item of p.items) {
    if (
      tracks.get(item.trackId) !== kinds[item.type] ||
      item.startTicks + item.durationTicks > p.durationTicks
    )
      throw new Error('Track hoặc thời lượng không hợp lệ.');
    if (item.assetId && !p.assetRefs.includes(item.assetId))
      throw new Error('Asset không tồn tại.');
    if (item.lyricId && !p.lyrics.some((l) => l.id === item.lyricId))
      throw new Error('Lyrics không tồn tại.');
  }
  if (new Set(p.lyrics.map((l) => l.id)).size !== p.lyrics.length)
    throw new Error('Lyric ID trùng.');
  for (const line of p.lyrics) {
    if (line.sourceEndTicks <= line.sourceStartTicks)
      throw new Error('Thời gian lyrics không hợp lệ.');
    let previous = line.sourceStartTicks;
    for (const word of line.words) {
      if (
        word.startTicks < previous ||
        word.endTicks <= word.startTicks ||
        word.endTicks > line.sourceEndTicks
      )
        throw new Error('Thời gian từ không hợp lệ.');
      previous = word.endTicks;
    }
  }
}
export function canonicalContent(p: ProjectContent): string {
  validateProject(p);
  const result = canonicalize(p);
  if (!result) throw new Error('Không thể tạo snapshot.');
  return result;
}
export async function contentHash(p: ProjectContent): Promise<string> {
  const bytes = new TextEncoder().encode(canonicalContent(p));
  const hash = await crypto.subtle.digest('SHA-256', bytes);
  return Array.from(new Uint8Array(hash), (b) =>
    b.toString(16).padStart(2, '0'),
  ).join('');
}
export function frameTicks(frame: number, fps: 30 | 60): number {
  return (frame * TICKS) / fps;
}
export function sourceTicks(item: TimelineItem, timeline: number): number {
  return (
    item.sourceStartTicks +
    ((timeline - item.startTicks) * item.speed.numerator) /
      item.speed.denominator
  );
}
export function newProject(id: string, name = 'Video của tôi'): ProjectContent {
  return {
    schemaVersion: 'amvs-project/1',
    id,
    name,
    timebase: TICKS,
    durationTicks: TICKS * 15,
    preset: { width: 720, height: 1280, fps: 30 },
    templateRef: { id: 'TPL-01', version: 1 },
    orderedTracks: [
      { id: 'background', kind: 'background' },
      { id: 'music', kind: 'music' },
      { id: 'text', kind: 'text' },
    ],
    items: [
      {
        id: 'caption',
        trackId: 'text',
        type: 'text',
        text: 'Giai điệu của bạn',
        startTicks: 0,
        durationTicks: TICKS * 15,
        sourceStartTicks: 0,
        speed: { numerator: 1, denominator: 1 },
        volume: 1,
        style: {
          fontFamily: 'Arial',
          fontSize: 54,
          color: '#ffffff',
          x: 56,
          y: 850,
        },
      },
    ],
    lyrics: [],
    assetRefs: [],
  };
}
export class History {
  private current: ProjectContent;
  private past: ProjectContent[] = [];
  private future: ProjectContent[] = [];
  constructor(p: ProjectContent) {
    validateProject(p);
    this.current = structuredClone(p);
  }
  read() {
    return structuredClone(this.current);
  }
  edit(operation: (p: ProjectContent) => void) {
    const next = this.read();
    operation(next);
    validateProject(next);
    this.past.push(this.current);
    this.past = this.past.slice(-100);
    this.current = next;
    this.future = [];
  }
  undo() {
    const p = this.past.pop();
    if (!p) return false;
    this.future.push(this.current);
    this.current = p;
    return true;
  }
  redo() {
    const p = this.future.pop();
    if (!p) return false;
    this.past.push(this.current);
    this.current = p;
    return true;
  }
}
