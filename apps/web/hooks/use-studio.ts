'use client';
import { useCallback, useEffect, useRef, useState } from 'react';
import type { PlayerRef } from '@remotion/player';
import {
  canonicalContent,
  contentHash,
  History,
  newProject,
  newMusicCardProject,
  TICKS,
  type ProjectContent,
  type TimelineItem,
  appendMedia,
  reorderClip,
  removeClip,
  validateMediaWindows,
} from '@amvs/domain';
import { Api, type Asset, type Job, type RecordState } from '../lib/api';

export function useStudio() {
  const api = useRef<Api | null>(null),
    record = useRef<RecordState | null>(null),
    history = useRef<History | null>(null),
    player = useRef<PlayerRef>(null);
  const [ready, setReady] = useState(false),
    [message, setMessage] = useState('Đang mở studio…'),
    [project, setProject] = useState<ProjectContent | null>(null);
  const [assets, setAssets] = useState<Asset[]>([]),
    [projects, setProjects] = useState<{ id: string; name: string }[]>([]),
    [selected, setSelected] = useState('caption');
  const [busy, setBusy] = useState(false),
    [dirty, setDirty] = useState(false),
    [job, setJob] = useState<Job | null>(null),
    [rights, setRights] = useState(false);
  const latest = useRef<ProjectContent | null>(null),
    serial = useRef<Promise<unknown>>(Promise.resolve());
  const pendingSeek = useRef<{ id: string; frame: number } | null>(null);
  const assetsRef = useRef<Asset[]>([]);
  const operationBusy = useRef(false);
  function show(p: ProjectContent) {
    latest.current = p;
    setProject(p);
  }
  const adopt = useCallback((value: RecordState) => {
    record.current = value;
    history.current = new History(value.project);
    latest.current = value.project;
    setProject(value.project);
    setDirty(value.dirty);
    setSelected('caption');
    const tick = Number(value.view.playheadTicks ?? 0);
    const maximum =
      Math.ceil(
        (value.project.durationTicks * value.project.preset.fps) / TICKS,
      ) - 1;
    pendingSeek.current = {
      id: value.project.id,
      frame: Math.max(
        0,
        Math.min(
          maximum,
          Number.isFinite(tick)
            ? Math.round((tick * value.project.preset.fps) / TICKS)
            : 0,
        ),
      ),
    };
    api.current
      ?.call<(Job & { projectId: string })[]>('jobs')
      .then((rows) => {
        if (latest.current?.id === value.project.id)
          setJob(rows.find((j) => j.projectId === value.project.id) ?? null);
      })
      .catch(() => {});
  }, []);
  const refresh = useCallback(async () => {
    const client = api.current!;
    assetsRef.current = await client.call<Asset[]>('assets');
    setAssets(assetsRef.current);
    setProjects(await client.call<{ id: string; name: string }[]>('projects'));
  }, []);
  useEffect(() => {
    const target = pendingSeek.current;
    if (target && target.id === project?.id && player.current) {
      player.current.seekTo(target.frame);
      pendingSeek.current = null;
    }
  }, [project]);
  useEffect(() => {
    let active = true;
    const fromFragment = new URLSearchParams(location.hash.slice(1)).get(
      'session',
    );
    if (fromFragment) window.history.replaceState(null, '', location.pathname);
    async function connect() {
      try {
        const token =
          fromFragment ||
          (await fetch('/api/v1/session/bootstrap', {
            cache: 'no-store',
            credentials: 'same-origin',
          }).then(async (response) => {
            if (!response.ok)
              throw new Error(
                'Không mở được phiên Studio. Hãy chạy scripts/start.ps1 -Restart.',
              );
            return (await response.json()).session as string;
          }));
        if (!active) return;
        if (typeof token !== 'string' || !token)
          throw new Error('Phiên Studio không hợp lệ.');
        api.current = new Api(token);
        await api.current.call('session');
        await refresh();
        if (active) {
          setReady(true);
          setMessage('Studio local đã sẵn sàng.');
        }
      } catch (error) {
        if (active)
          setMessage(
            error instanceof Error ? error.message : 'Không mở được Studio.',
          );
      }
    }
    connect();
    return () => {
      active = false;
    };
  }, [refresh]);
  useEffect(() => {
    if (!project) return;
    let active = true;
    contentHash(project).then((hash) => {
      if (active) setDirty(hash !== record.current?.manualSavedHash);
    });
    const warn = (e: BeforeUnloadEvent) => {
      if (dirty) {
        e.preventDefault();
        e.returnValue = '';
      }
    };
    window.addEventListener('beforeunload', warn);
    return () => {
      active = false;
      window.removeEventListener('beforeunload', warn);
    };
  }, [project, dirty]);
  function change(operation: (p: ProjectContent) => void) {
    try {
      history.current!.edit((p) => {
        operation(p);
        validateMediaWindows(p, assetsRef.current);
      });
      show(history.current!.read());
      setMessage('Đã cập nhật bản nháp.');
      return true;
    } catch (e) {
      setMessage((e as Error).message);
      return false;
    }
  }
  async function sync(snapshot: ProjectContent): Promise<RecordState> {
    let result: RecordState | undefined;
    const action = serial.current
      .catch(() => {})
      .then(async () => {
        const current = record.current!;
        if (current.project.id !== snapshot.id)
          throw new Error('Project đã thay đổi.');
        const view = {
          playheadTicks: Math.round(
            ((player.current?.getCurrentFrame() ?? 0) * TICKS) /
              snapshot.preset.fps,
          ),
        };
        if (
          canonicalContent(current.project) === canonicalContent(snapshot) &&
          current.view.playheadTicks === view.playheadTicks
        ) {
          result = current;
          return;
        }
        result = await api.current!.json<RecordState>(
          `projects/${snapshot.id}`,
          'PATCH',
          {
            project: snapshot,
            revision: current.revision,
            view,
          },
        );
        if (record.current?.project.id === snapshot.id) record.current = result;
      });
    serial.current = action;
    await action;
    return result!;
  }
  useEffect(() => {
    if (!project || !ready) return;
    const timer = setTimeout(
      () => sync(project).catch((e) => setMessage(e.message)),
      800,
    );
    return () => clearTimeout(timer);
  }, [project, ready]);
  useEffect(() => {
    if (
      !job ||
      ['succeeded', 'failed', 'cancelled', 'interrupted'].includes(job.status)
    )
      return;
    let active = true;
    const timer = setInterval(
      () =>
        api
          .current!.call<Job>(`jobs/${job.id}`)
          .then((value) => {
            if (active) setJob(value);
          })
          .catch((e) => setMessage(e.message)),
      1000,
    );
    return () => {
      active = false;
      clearInterval(timer);
    };
  }, [job]);
  async function perform(action: () => Promise<void>) {
    if (operationBusy.current) {
      setMessage('Hãy chờ thao tác hiện tại hoàn tất.');
      return;
    }
    operationBusy.current = true;
    setBusy(true);
    try {
      await action();
    } catch (e) {
      setMessage((e as Error).message);
    } finally {
      operationBusy.current = false;
      setBusy(false);
    }
  }
  function canLeave() {
    return (
      !dirty ||
      window.confirm(
        'Project có thay đổi chưa lưu thủ công. Bạn muốn chuyển project? Bản làm việc local vẫn được giữ.',
      )
    );
  }
  async function create(template: 'TPL-01' | 'TPL-02' = 'TPL-01') {
    if (!canLeave()) return;
    await perform(async () => {
      if (latest.current) await sync(latest.current);
      adopt(
        await api.current!.json<RecordState>(
          'projects',
          'POST',
          template === 'TPL-02'
            ? newMusicCardProject(crypto.randomUUID())
            : newProject(crypto.randomUUID()),
        ),
      );
      await refresh();
    });
  }
  async function open(id: string) {
    if (!canLeave()) return;
    await perform(async () => {
      if (latest.current) await sync(latest.current);
      adopt(await api.current!.call<RecordState>(`projects/${id}`));
    });
  }
  async function choose(scope: 'project' | 'export') {
    const result = await api.current!.json<{
      id?: string;
      cancelled?: boolean;
    }>('folder-grants', 'POST', { scope });
    if (!result.id) throw new Error('Đã hủy chọn thư mục.');
    return result.id;
  }
  async function save() {
    await perform(async () => {
      const grantId = await choose('project');
      const snapshot = structuredClone(latest.current!);
      const current = await sync(snapshot);
      const saved = await api.current!.json<RecordState>(
        `projects/${snapshot.id}/save`,
        'POST',
        { project: snapshot, revision: current.revision, grantId },
      );
      if (record.current?.project.id === snapshot.id)
        record.current = {
          ...record.current,
          manualSavedHash: saved.manualSavedHash,
        };
      setDirty((await contentHash(latest.current!)) !== saved.manualSavedHash);
      setMessage(
        'Đã lưu project thủ công. Media được giữ trong thư viện local.',
      );
      await refresh();
    });
  }
  async function render() {
    await perform(async () => {
      const grantId = await choose('export');
      const current = await sync(structuredClone(latest.current!));
      setJob(
        await api.current!.json<Job>('jobs', 'POST', {
          projectId: current.project.id,
          revision: current.revision,
          grantId,
        }),
      );
    });
  }
  async function upload(files: File[]) {
    await perform(async () => {
      if (!rights)
        throw new Error('Hãy xác nhận quyền dùng media trước khi nhập.');
      const projectId = latest.current?.id;
      const imported: Asset[] = [],
        errors: string[] = [];
      for (const file of files) {
        const form = new FormData();
        form.set('file', file);
        form.set('rightsConfirmed', 'true');
        try {
          imported.push(
            await api.current!.call<Asset>('assets', {
              method: 'POST',
              body: form,
            }),
          );
        } catch (error) {
          errors.push(`${file.name}: ${(error as Error).message}`);
        }
      }
      await refresh();
      if (latest.current?.id !== projectId)
        throw new Error(
          'Project đã đổi. Media đã nhập vẫn nằm trong thư viện.',
        );
      if (imported.length) {
        const applied = change((p) =>
          Object.assign(p, appendMedia(p, imported)),
        );
        if (!applied) return;
        const last = latest
          .current!.items.slice()
          .reverse()
          .find((i) => i.assetId === imported.at(-1)!.id);
        if (last) setSelected(last.id);
      }
      setMessage(
        errors.length
          ? `Đã thêm ${imported.length}/${files.length} file. ${errors.join(' · ')}`
          : 'Đã cập nhật bản nháp.',
      );
    });
  }
  function editItem(op: (item: TimelineItem) => void) {
    change((p) => {
      const item = p.items.find((i) => i.id === selected);
      if (!item) return;
      op(item);
    });
  }
  function reorder(direction: -1 | 1) {
    change((p) => Object.assign(p, reorderClip(p, selected, direction)));
  }
  function removeSelected() {
    if (change((p) => Object.assign(p, removeClip(p, selected))))
      setSelected('');
  }
  const urls = Object.fromEntries(
    assets.map((a) => [a.id, `/api/v1/assets/${a.id}/content`]),
  );
  function undo() {
    if (history.current?.undo()) show(history.current.read());
  }
  function redo() {
    if (history.current?.redo()) show(history.current.read());
  }
  async function openManual() {
    if (!canLeave()) return;
    await perform(async () => {
      if (latest.current) await sync(latest.current);
      const result = await api.current!.json<
        RecordState & { cancelled?: boolean }
      >('projects/open', 'POST', {});
      if (!result.cancelled) {
        adopt(result);
        await refresh();
      }
    });
  }
  async function openOutputFolder() {
    if (!job) return;
    await perform(async () => {
      await api.current!.json(`outputs/${job.id}/open-folder`, 'POST', {});
    });
  }
  async function cancelJob() {
    if (!job) return;
    await perform(async () => {
      setJob(await api.current!.json<Job>(`jobs/${job.id}/cancel`, 'POST', {}));
    });
  }
  return {
    apiClient: ready ? api.current : null,
    prepareBackup: async () => {
      if (latest.current) await sync(latest.current);
    },
    ready,
    message,
    project,
    projects,
    selected,
    setSelected,
    busy,
    dirty,
    job,
    rights,
    setRights,
    player,
    urls,
    create,
    open,
    save,
    render,
    upload,
    assets,
    reorder,
    removeSelected,
    editItem,
    change,
    undo,
    redo,
    openManual,
    openOutputFolder,
    cancelJob,
  };
}
