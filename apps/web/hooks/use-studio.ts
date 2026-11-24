'use client';
import { useCallback, useEffect, useRef, useState } from 'react';
import type { PlayerRef } from '@remotion/player';
import {
  canonicalContent,
  contentHash,
  History,
  newProject,
  newMusicCardProject,
  newLyricsProject,
  remapLyrics,
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
  const [zoom, setZoom] = useState(1);
  const [panels, setPanels] = useState<Record<string, boolean>>({});
  const viewRef = useRef({ selection: selected, timelineZoom: zoom, panels });
  viewRef.current = { selection: selected, timelineZoom: zoom, panels };
  const [writeAllowed, setWriteAllowed] = useState(true);
  const writeRef = useRef(true);
  const [missingMedia, setMissingMedia] = useState<string[]>([]);
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
    writeRef.current = false;
    setWriteAllowed(false);
    api.current
      ?.json<{ canWrite: boolean }>(
        `projects/${value.project.id}/editor-session`,
        'POST',
        { takeover: false },
      )
      .then((lease) => {
        if (latest.current?.id !== value.project.id) return;
        writeRef.current = lease.canWrite;
        setWriteAllowed(lease.canWrite);
        if (!lease.canWrite)
          setMessage(
            'Project đang mở ở tab khác. Tab này chỉ đọc; có thể nhận quyền chỉnh sửa.',
          );
      })
      .catch((e) => setMessage(e.message));
    record.current = value;
    history.current = new History(value.project);
    latest.current = value.project;
    setProject(value.project);
    setDirty(value.dirty);
    setSelected(
      typeof value.view.selection === 'string' &&
        value.project.items.some((i) => i.id === value.view.selection)
        ? value.view.selection
        : (value.project.items[0]?.id ?? ''),
    );
    setZoom(
      typeof value.view.timelineZoom === 'number'
        ? Math.max(1, Math.min(8, value.view.timelineZoom))
        : 1,
    );
    setPanels(
      value.view.panels && typeof value.view.panels === 'object'
        ? (Object.fromEntries(
            Object.entries(value.view.panels).filter(
              ([key, v]) =>
                ['lyrics', 'data', 'library', 'templates'].includes(key) &&
                typeof v === 'boolean',
            ),
          ) as Record<string, boolean>)
        : {},
    );
    setMissingMedia([]);
    api.current
      ?.call<{ missing: string[] }>(`projects/${value.project.id}/media-status`)
      .then((status) => {
        if (latest.current?.id === value.project.id)
          setMissingMedia(status.missing);
      })
      .catch(() => {});
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
          setJob(
            rows.find(
              (j) => j.projectId === value.project.id && j.kind === 'render',
            ) ?? null,
          );
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
    if (!writeRef.current) {
      setMessage('Tab này chỉ đọc. Nhận quyền chỉnh sửa trước.');
      return false;
    }
    try {
      history.current!.edit((p) => {
        operation(p);
        Object.assign(p, remapLyrics(p));
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
          ...viewRef.current,
          playheadTicks: Math.round(
            ((player.current?.getCurrentFrame() ?? 0) * TICKS) /
              snapshot.preset.fps,
          ),
        };
        if (
          canonicalContent(current.project) === canonicalContent(snapshot) &&
          JSON.stringify(current.view) === JSON.stringify(view)
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
    if (!project || !ready || !writeAllowed) return;
    const timer = setTimeout(
      () => sync(project).catch((e) => setMessage(e.message)),
      800,
    );
    return () => clearTimeout(timer);
  }, [project, ready, selected, zoom, panels, writeAllowed]);
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
  useEffect(() => {
    if (!project || !ready) return;
    let active = true;
    const timer = setInterval(
      () =>
        writeRef.current &&
        api
          .current!.json<{ canWrite: boolean }>(
            `projects/${project.id}/editor-session`,
            'POST',
            { takeover: false, ...historyPins() },
          )
          .then((lease) => {
            if (!active) return;
            if (writeRef.current && !lease.canWrite)
              setMessage(
                'Tab khác đã nhận quyền. Chỉnh sửa chưa ghi trong tab này vẫn giữ trong bộ nhớ; không ghi đè dữ liệu mới.',
              );
            writeRef.current = lease.canWrite;
            setWriteAllowed(lease.canWrite);
          })
          .catch((e) => {
            if (active) setMessage(e.message);
          }),
      5000,
    );
    return () => {
      active = false;
      clearInterval(timer);
    };
  }, [project?.id, ready]);
  useEffect(() => {
    if (!project || !ready) return;
    const id = project.id;
    const release = () => {
      api.current
        ?.call(`projects/${id}/editor-session`, {
          method: 'DELETE',
          keepalive: true,
        })
        .catch(() => {});
    };
    window.addEventListener('beforeunload', release);
    return () => {
      window.removeEventListener('beforeunload', release);
      release();
    };
  }, [project?.id, ready]);
  function historyPins() {
    const pins = history.current?.assetPins() ?? [];
    return pins.length > 4096
      ? { pinAllAssets: true, assetPins: [] }
      : { pinAllAssets: false, assetPins: pins };
  }
  function canLeave() {
    return (
      !dirty ||
      window.confirm(
        'Project có thay đổi chưa lưu thủ công. Bạn muốn chuyển project? Bản làm việc local vẫn được giữ.',
      )
    );
  }
  async function create(template: 'TPL-01' | 'TPL-02' | 'TPL-03' = 'TPL-01') {
    if (!canLeave()) return;
    await perform(async () => {
      if (latest.current && writeRef.current) await sync(latest.current);
      adopt(
        await api.current!.json<RecordState>(
          'projects',
          'POST',
          template === 'TPL-02'
            ? newMusicCardProject(crypto.randomUUID())
            : template === 'TPL-03'
              ? newLyricsProject(crypto.randomUUID())
              : newProject(crypto.randomUUID()),
        ),
      );
      await refresh();
    });
  }
  async function open(id: string) {
    if (!canLeave()) return;
    await perform(async () => {
      if (latest.current && writeRef.current) await sync(latest.current);
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
    if (!writeRef.current) {
      setMessage('Tab này chỉ đọc.');
      return;
    }
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
    if (!writeRef.current) {
      setMessage('Tab này chỉ đọc.');
      return;
    }
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
    if (!writeRef.current) {
      setMessage('Tab này chỉ đọc.');
      return;
    }
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
  function updateLyricTiming(
    p: ProjectContent,
    item: TimelineItem,
    previous: TimelineItem,
  ) {
    if (
      item.type !== 'lyrics' ||
      (item.startTicks === previous.startTicks &&
        item.durationTicks === previous.durationTicks)
    )
      return;
    const line = p.lyrics.find((l) => l.id === item.lyricId);
    if (!line) return;
    const rate = item.speed.numerator / item.speed.denominator;
    line.sourceStartTicks = Math.round(
      previous.sourceStartTicks +
        (item.startTicks - previous.startTicks) * rate,
    );
    line.sourceEndTicks = Math.round(
      line.sourceStartTicks + item.durationTicks * rate,
    );
    line.source = 'user';
    line.alignmentStatus = 'sentence';
    line.words = [];
    item.sourceStartTicks = line.sourceStartTicks;
  }
  function editItem(op: (item: TimelineItem) => void) {
    change((p) => {
      const item = p.items.find((i) => i.id === selected);
      if (!item) return;
      const previous = structuredClone(item);
      op(item);
      updateLyricTiming(p, item, previous);
    });
  }
  function moveClip(id: string, start: number) {
    change((p) => {
      const item = p.items.find((i) => i.id === id);
      if (!item) return;
      const previous = structuredClone(item);
      item.startTicks = start;
      updateLyricTiming(p, item, previous);
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
    if (!writeRef.current) return;
    if (history.current?.undo()) show(history.current.read());
  }
  function redo() {
    if (!writeRef.current) return;
    if (history.current?.redo()) show(history.current.read());
  }
  async function openManual() {
    if (!canLeave()) return;
    await perform(async () => {
      if (latest.current && writeRef.current) await sync(latest.current);
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
    refresh,
    writeAllowed,
    takeOver: async () => {
      if (
        !latest.current ||
        !window.confirm(
          'Nhận quyền chỉnh sửa và nạp bản mới nhất từ máy? Chỉnh sửa chưa ghi trong tab này sẽ bị bỏ; tab kia chuyển sang chỉ đọc.',
        )
      )
        return;
      const id = latest.current.id;
      const lease = await api.current!.json<{ canWrite: boolean }>(
        `projects/${id}/editor-session`,
        'POST',
        { takeover: true },
      );
      if (lease.canWrite) {
        writeRef.current = true;
        setWriteAllowed(true);
        adopt(await api.current!.call<RecordState>(`projects/${id}`));
      }
    },
    zoom,
    setZoom,
    panels,
    setPanel: (key: string, value: boolean) =>
      setPanels((previous) =>
        previous[key] === value ? previous : { ...previous, [key]: value },
      ),
    reloadFromServer: async () => {
      if (latest.current)
        adopt(
          await api.current!.call<RecordState>(`projects/${latest.current.id}`),
        );
    },
    apiClient: ready ? api.current : null,
    prepareBackup: async () => {
      if (latest.current && writeRef.current) {
        await sync(latest.current);
        await api.current!.json(
          `projects/${latest.current.id}/editor-session`,
          'POST',
          { takeover: false, ...historyPins() },
        );
      }
    },
    ready,
    message,
    missingMedia,
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
    moveClip,
    change,
    undo,
    redo,
    openManual,
    openOutputFolder,
    cancelJob,
  };
}
