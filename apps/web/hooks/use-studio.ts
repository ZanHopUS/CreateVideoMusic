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
import { EditorLease } from '../lib/editor-lease';
import {
  Api,
  ApiError,
  type Asset,
  type Job,
  type RecordState,
} from '../lib/api';

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
    [recent, setRecent] = useState<{ id: string; openedAt: string }[]>([]),
    [selected, setSelected] = useState('caption');
  const [zoom, setZoom] = useState(1);
  const [panels, setPanels] = useState<Record<string, boolean>>({});
  const viewRef = useRef({ selection: selected, timelineZoom: zoom, panels });
  viewRef.current = { selection: selected, timelineZoom: zoom, panels };
  const [writeAllowed, setWriteAllowed] = useState(false);
  const lease = useRef<EditorLease | null>(null);
  const [missingMedia, setMissingMedia] = useState<string[]>([]);
  const [busy, setBusy] = useState(false),
    [dirty, setDirty] = useState(false),
    [job, setJob] = useState<Job | null>(null),
    [backgroundJobs, setBackgroundJobs] = useState<
      (Job & { projectId: string })[]
    >([]),
    [rights, setRights] = useState(false);
  const latest = useRef<ProjectContent | null>(null),
    serial = useRef<Promise<unknown>>(Promise.resolve());
  const pendingSeek = useRef<{ id: string; frame: number } | null>(null);
  const assetsRef = useRef<Asset[]>([]);
  const operationBusy = useRef(false);
  const mounted = useRef(false);
  function show(p: ProjectContent) {
    latest.current = p;
    setProject(p);
  }
  const applyRecord = useCallback((value: RecordState) => {
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
    const epoch = authority();
    setMissingMedia([]);
    api.current
      ?.call<{ missing: string[] }>(`projects/${value.project.id}/media-status`)
      .then((status) => {
        if (currentAuthority(epoch) && latest.current?.id === value.project.id)
          setMissingMedia(status.missing);
      })
      .catch((error) => {
        if (currentAuthority(epoch)) setMessage(error.message);
      });
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
        if (currentAuthority(epoch) && latest.current?.id === value.project.id)
          setJob(
            rows.find(
              (j) => j.projectId === value.project.id && j.kind === 'render',
            ) ?? null,
          );
      })
      .catch((error) => {
        if (currentAuthority(epoch)) setMessage(error.message);
      });
  }, []);
  function adopt(value: RecordState) {
    lease.current?.open(value.project.id);
    applyRecord(value);
  }
  function writable() {
    return lease.current?.canWrite() ?? false;
  }
  function authority() {
    return { controller: lease.current, epoch: lease.current?.stamp() };
  }
  function currentAuthority(token: ReturnType<typeof authority>) {
    return (
      lease.current === token.controller &&
      !!token.controller?.current(token.epoch!)
    );
  }
  function assertCurrent(token: ReturnType<typeof authority>) {
    if (!currentAuthority(token)) throw new Error('Phiên project đã thay đổi.');
  }
  function assertAuthority(token: ReturnType<typeof authority>) {
    assertCurrent(token);
    if (!writable())
      throw new Error(
        'Quyền chỉnh sửa đã thay đổi. Hãy nhận quyền và tải lại project.',
      );
  }
  const refresh = useCallback(async () => {
    const client = api.current!;
    const loadedAssets = await client.call<Asset[]>('assets');
    const loadedProjects =
      await client.call<{ id: string; name: string }[]>('projects');
    const uiState = await client.call<{
      recent: { id: string; openedAt: string }[];
    }>('ui-state');
    if (!mounted.current || api.current !== client) return;
    assetsRef.current = loadedAssets;
    setAssets(loadedAssets);
    setProjects(loadedProjects);
    setRecent(uiState.recent);
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
    mounted.current = true;
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
        lease.current = new EditorLease(api.current, {
          record: () => record.current,
          apply: applyRecord,
          pins: historyPins,
          state: (allowed) => {
            setWriteAllowed(allowed);
          },
          message: setMessage,
        });
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
      mounted.current = false;
      lease.current?.dispose();
    };
  }, [refresh, applyRecord]);
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
    if (!writable()) {
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
    const epoch = authority();
    let result: RecordState | undefined;
    const action = serial.current
      .catch(() => {})
      .then(async () => {
        assertAuthority(epoch);
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
        assertAuthority(epoch);
        if (record.current?.project.id === snapshot.id) record.current = result;
      });
    serial.current = action;
    try {
      await action;
    } catch (error) {
      if (currentAuthority(epoch)) lease.current?.fail(error);
      throw error;
    }
    return result!;
  }
  useEffect(() => {
    if (!project || !ready || !writeAllowed) return;
    const timer = setTimeout(() => {
      void sync(project).catch(() => {
        /* sync reports current-epoch failures. */
      });
    }, 800);
    return () => clearTimeout(timer);
  }, [project, ready, selected, zoom, panels, writeAllowed]);
  useEffect(() => {
    if (!ready || !api.current) return;
    let active = true;
    const client = api.current;
    const inspect = () =>
      client
        .call<(Job & { projectId: string })[]>('jobs')
        .then((rows) => {
          if (active && api.current === client) setBackgroundJobs(rows);
        })
        .catch(() => {
          /* Job status is retried; the main API session reports connection errors. */
        });
    void inspect();
    const timer = window.setInterval(() => {
      void inspect();
    }, 3000);
    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, [ready]);
  useEffect(() => {
    if (
      !job ||
      ['succeeded', 'failed', 'cancelled', 'interrupted'].includes(job.status)
    )
      return;
    let active = true;
    const epoch = authority();
    const timer = setInterval(
      () =>
        api
          .current!.call<Job>(`jobs/${job.id}`)
          .then((value) => {
            if (active && currentAuthority(epoch)) setJob(value);
          })
          .catch((e) => {
            if (active && currentAuthority(epoch)) setMessage(e.message);
          }),
      1000,
    );
    return () => {
      active = false;
      clearInterval(timer);
    };
  }, [job, writeAllowed, project?.id]);
  async function perform(action: () => Promise<void>) {
    if (operationBusy.current) {
      setMessage('Hãy chờ thao tác hiện tại hoàn tất.');
      return;
    }
    const epoch = authority();
    operationBusy.current = true;
    setBusy(true);
    try {
      await action();
    } catch (e) {
      if (!mounted.current || !currentAuthority(epoch)) return;
      if (e instanceof ApiError && [401, 409].includes(e.status))
        lease.current?.fail(e);
      else setMessage((e as Error).message);
    } finally {
      operationBusy.current = false;
      if (mounted.current) setBusy(false);
    }
  }
  useEffect(() => {
    const release = () => lease.current?.release();
    // pagehide fires only for an actual departure, unlike a cancelled beforeunload.
    window.addEventListener('pagehide', release);
    const check = () => {
      lease.current?.canWrite();
    };
    window.addEventListener('focus', check);
    document.addEventListener('visibilitychange', check);
    return () => {
      window.removeEventListener('pagehide', release);
      window.removeEventListener('focus', check);
      document.removeEventListener('visibilitychange', check);
    };
  }, []);
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
      if (latest.current && writable()) await sync(latest.current);
      const epoch = authority();
      const created = await api.current!.json<RecordState>(
        'projects',
        'POST',
        template === 'TPL-02'
          ? newMusicCardProject(crypto.randomUUID())
          : template === 'TPL-03'
            ? newLyricsProject(crypto.randomUUID())
            : newProject(crypto.randomUUID()),
      );
      assertCurrent(epoch);
      adopt(created);
      await api.current!.json(
        `projects/${created.project.id}/opened`,
        'POST',
        {},
      );
      await refresh();
    });
  }
  async function open(id: string) {
    if (!canLeave()) return;
    await perform(async () => {
      if (latest.current && writable()) await sync(latest.current);
      const epoch = authority();
      const opened = await api.current!.call<RecordState>(`projects/${id}`);
      assertCurrent(epoch);
      adopt(opened);
      await api.current!.json(`projects/${id}/opened`, 'POST', {});
      await refresh();
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
    if (!writable()) {
      setMessage('Tab này chỉ đọc.');
      return;
    }
    await perform(async () => {
      const epoch = authority();
      const grantId = await choose('project');
      assertAuthority(epoch);
      const snapshot = structuredClone(latest.current!);
      const current = await sync(snapshot);
      const saved = await api.current!.json<RecordState>(
        `projects/${snapshot.id}/save`,
        'POST',
        { project: snapshot, revision: current.revision, grantId },
      );
      assertAuthority(epoch);
      if (record.current?.project.id === snapshot.id)
        record.current = {
          ...record.current,
          manualSavedHash: saved.manualSavedHash,
        };
      const currentHash = await contentHash(latest.current!);
      assertAuthority(epoch);
      setDirty(currentHash !== saved.manualSavedHash);
      setMessage(
        'Đã lưu project thủ công. Media được giữ trong thư viện local.',
      );
      await refresh();
    });
  }
  async function render() {
    if (!writable()) {
      setMessage('Tab này chỉ đọc.');
      return;
    }
    await perform(async () => {
      const epoch = authority();
      const grantId = await choose('export');
      assertAuthority(epoch);
      const current = await sync(structuredClone(latest.current!));
      const rendered = await api.current!.json<Job>('jobs', 'POST', {
        projectId: current.project.id,
        revision: current.revision,
        grantId,
      });
      assertAuthority(epoch);
      setJob(rendered);
    });
  }
  async function upload(files: File[]) {
    if (!writable()) {
      setMessage('Tab này chỉ đọc.');
      return;
    }
    await perform(async () => {
      if (!rights)
        throw new Error('Hãy xác nhận quyền dùng media trước khi nhập.');
      const epoch = authority();
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
      assertAuthority(epoch);
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
    if (!writable()) return;
    if (history.current?.undo()) show(history.current.read());
  }
  function redo() {
    if (!writable()) return;
    if (history.current?.redo()) show(history.current.read());
  }
  async function openManual() {
    if (!canLeave()) return;
    await perform(async () => {
      if (latest.current && writable()) await sync(latest.current);
      const epoch = authority();
      const result = await api.current!.json<
        RecordState & { cancelled?: boolean }
      >('projects/open', 'POST', {});
      assertCurrent(epoch);
      if (!result.cancelled) {
        adopt(result);
        await api.current!.json(
          `projects/${result.project.id}/opened`,
          'POST',
          {},
        );
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
      const epoch = authority();
      const cancelled = await api.current!.json<Job>(
        `jobs/${job.id}/cancel`,
        'POST',
        {},
      );
      assertCurrent(epoch);
      setJob(cancelled);
    });
  }
  return {
    refresh,
    writeAllowed,
    takeOver: async () => {
      if (
        !latest.current ||
        operationBusy.current ||
        !window.confirm(
          'Nhận quyền chỉnh sửa và nạp bản mới nhất từ máy? Chỉnh sửa chưa ghi trong tab này sẽ bị bỏ; tab kia chuyển sang chỉ đọc.',
        )
      )
        return;
      await perform(async () => {
        await lease.current?.acquire(true);
      });
    },
    zoom,
    setZoom,
    panels,
    setPanel: (key: string, value: boolean) =>
      setPanels((previous) =>
        previous[key] === value ? previous : { ...previous, [key]: value },
      ),
    reloadFromServer: async () => {
      if (!(await lease.current?.acquire(false)))
        throw new Error(
          'Không thể tải và xác nhận project mới nhất. Tab vẫn chỉ đọc; hãy nhận quyền lại.',
        );
    },
    apiClient: ready ? api.current : null,
    prepareBackup: async () => {
      if (latest.current && writable()) {
        await sync(latest.current);
        await lease.current?.checkpoint();
      }
    },
    ready,
    message,
    missingMedia,
    project,
    projects,
    recent,
    selected,
    setSelected,
    busy,
    dirty,
    job,
    backgroundJobs,
    selectBackgroundJob: (id: string) => {
      const found = backgroundJobs.find(
        (row) => row.id === id && row.kind === 'render',
      );
      if (found) setJob(found);
    },
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
