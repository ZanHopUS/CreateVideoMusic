import type { ProjectContent } from '@amvs/domain';
export type Asset = {
  id: string;
  name: string;
  kind: 'image' | 'audio' | 'video';
  durationTicks: number;
  mime: string;
  tags?: string[];
};
export type RecordState = {
  project: ProjectContent;
  view: Record<string, unknown>;
  revision: number;
  contentHash: string;
  manualSavedHash: string | null;
  dirty: boolean;
};
export type Job = {
  kind: 'render' | 'asr' | 'alignment' | 'package';
  id: string;
  status: string;
  phase: string;
  progress: number;
  message: string;
  resourceSampledPass?: boolean;
};
export class Api {
  private editor = crypto.randomUUID();
  constructor(private token: string) {}
  async call<T>(path: string, init: RequestInit = {}): Promise<T> {
    const headers = new Headers(init.headers);
    headers.set('authorization', `Bearer ${this.token}`);
    headers.set('x-amvs-editor', this.editor);
    if (init.body && !(init.body instanceof FormData))
      headers.set('content-type', 'application/json');
    const response = await fetch(`/api/v1/${path}`, {
      ...init,
      headers,
      cache: 'no-store',
    });
    const value = await response.json();
    if (!response.ok)
      throw new Error(value.message ?? 'Thao tác chưa hoàn tất.');
    return value as T;
  }
  json<T>(path: string, method: string, value: unknown) {
    return this.call<T>(path, { method, body: JSON.stringify(value) });
  }
}
