/* Generated from project.schema.json. Run npm run types; do not edit. */

export type Id = string;
export type Item = {
  id: Id;
  trackId: Id;
  type: 'image' | 'video' | 'audio' | 'text' | 'lyrics';
  assetId?: Hash;
  text?: string;
  lyricId?: Id;
  startTicks: Tick;
  durationTicks: number;
  sourceStartTicks: Tick;
  speed: {
    numerator: number;
    denominator: number;
  };
  volume: number;
  style?: {
    fontFamily?: 'Arial' | 'Segoe UI';
    fontSize?: number;
    color?: string;
    background?: string;
    x?: number;
    y?: number;
    fit?: 'cover' | 'contain';
  };
};
export type Hash = string;
export type Tick = number;

export interface ProjectContent {
  schemaVersion: 'amvs-project/1';
  id: Id;
  name: string;
  timebase: 48000;
  durationTicks: number;
  preset: {
    width: 720 | 1080 | 1280 | 1920;
    height: 720 | 1080 | 1280 | 1920;
    fps: 30 | 60;
  };
  templateRef: {
    id: 'TPL-01' | 'TPL-02' | 'TPL-03';
    version: number;
  };
  /**
   * @minItems 1
   */
  orderedTracks: [Track, ...Track[]];
  items: Item[];
  lyrics: Lyric[];
  assetRefs: Hash[];
}
export interface Track {
  id: Id;
  kind: 'background' | 'music' | 'lyrics' | 'text';
}
export interface Lyric {
  id: Id;
  text: string;
  sourceStartTicks: Tick;
  sourceEndTicks: Tick;
  source: 'user' | 'import' | 'asr' | 'aligner';
  status: 'draft' | 'reviewed';
  alignmentStatus: 'unknown' | 'sentence' | 'word';
  words: {
    text: string;
    startTicks: Tick;
    endTicks: Tick;
    rawScore?: number;
  }[];
}
