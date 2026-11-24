'use client';
import { useEffect, useRef, useState } from 'react';
import { Player } from '@remotion/player';
import { ProjectScene } from '@amvs/composition';
import { TICKS } from '@amvs/domain';
import { useStudio } from '../hooks/use-studio';
import { Timeline } from './timeline';
import { Inspector } from './inspector';
import { StorageWorkspace } from './storage-workspace';
import { LyricsPanel, type LyricsWorkspaceDraft } from './lyrics-panel';
import { ProjectTools } from './project-tools';
import { SettingsWorkspace } from './settings-workspace';
import { RecoveryWorkspace } from './recovery-workspace';
export function Studio() {
  const rightsInput = useRef<HTMLInputElement>(null);
  const [uploadHint, setUploadHint] = useState('');
  const [workspace, setWorkspace] = useState<
    'dashboard' | 'editor' | 'projects' | 'storage' | 'settings'
  >('dashboard');
  const [projectView, setProjectView] = useState<'grid' | 'list'>('grid');
  const [search, setSearch] = useState('');
  const [projectFilter, setProjectFilter] = useState<'all' | 'recent'>('all');
  const [projectSort, setProjectSort] = useState<'name' | 'opened'>('opened');
  const [recoveryProject, setRecoveryProject] = useState<string | null>(null);
  const [exportOpen, setExportOpen] = useState(false);
  const exportDialog = useRef<HTMLElement>(null);
  const previewRef = useRef<HTMLDivElement>(null);
  const [previewStatus, setPreviewStatus] = useState('');
  const [timelineHeight, setTimelineHeight] = useState(280);
  const prefsLoaded = useRef(false);
  const confirmedHeight = useRef(280);
  const layoutWrites = useRef<Promise<unknown>>(Promise.resolve());
  const viewSaving = useRef(false);
  const [viewPending, setViewPending] = useState(false);
  const [preferenceStatus, setPreferenceStatus] = useState('');
  const lyricDrafts = useRef<Record<string, LyricsWorkspaceDraft>>({});
  const {
    apiClient,
    refresh,
    reloadFromServer,
    zoom,
    setZoom,
    panels,
    setPanel,
    prepareBackup,
    ready,
    message,
    missingMedia,
    writeAllowed,
    takeOver,
    project,
    projects,
    recent,
    selected,
    setSelected,
    busy,
    dirty,
    job,
    backgroundJobs,
    selectBackgroundJob,
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
  } = useStudio();

  function canSwitchProject(nextId?: string) {
    if (!project || project.id === nextId) return true;
    const draft = lyricDrafts.current[project.id];
    if (!draft) return true;
    if (
      draft.input.trim() ||
      JSON.stringify(draft.lines) !== JSON.stringify(project.lyrics)
    ) {
      return window.confirm(
        'Lời hát có bản nháp chưa ghi vào project. Chuyển project? Bản nháp vẫn được giữ trong phiên này.',
      );
    }
    return true;
  }
  async function openProject(id: string) {
    if (canSwitchProject(id)) await open(id);
  }
  async function createProject(template?: Parameters<typeof create>[0]) {
    if (canSwitchProject()) await create(template);
  }
  async function openManualProject() {
    if (canSwitchProject()) await openManual();
  }

  useEffect(() => {
    if (!exportOpen) return;
    const previous =
      document.activeElement instanceof HTMLElement
        ? document.activeElement
        : null;
    const dialog = exportDialog.current;
    dialog?.querySelector<HTMLButtonElement>('button')?.focus();
    const key = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        event.preventDefault();
        setExportOpen(false);
        return;
      }
      if (event.key !== 'Tab' || !dialog) return;
      const controls = [
        ...dialog.querySelectorAll<HTMLElement>(
          'button:not(:disabled), a[href], input:not(:disabled), select:not(:disabled)',
        ),
      ];
      const first = controls[0],
        last = controls[controls.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last?.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first?.focus();
      }
    };
    document.addEventListener('keydown', key);
    return () => {
      document.removeEventListener('keydown', key);
      previous?.focus();
    };
  }, [exportOpen]);
  useEffect(() => {
    if (!apiClient) return;
    let active = true;
    apiClient
      .call<{
        preferences: {
          timelineHeight: number;
          projectViewMode: 'grid' | 'list';
        };
      }>('ui-state')
      .then((state) => {
        if (!active) return;
        setTimelineHeight(
          Math.max(
            180,
            Math.min(
              Math.floor(window.innerHeight * 0.55),
              state.preferences.timelineHeight,
            ),
          ),
        );
        setProjectView(state.preferences.projectViewMode);
        confirmedHeight.current = Math.max(
          180,
          Math.min(
            Math.floor(window.innerHeight * 0.55),
            state.preferences.timelineHeight,
          ),
        );
        prefsLoaded.current = true;
      })
      .catch(() => {
        if (active)
          setPreferenceStatus(
            'Không tải được tùy chọn giao diện; đang dùng bố cục mặc định.',
          );
      });
    return () => {
      active = false;
      prefsLoaded.current = false;
    };
  }, [apiClient]);
  useEffect(() => {
    if (
      !apiClient ||
      !prefsLoaded.current ||
      timelineHeight === confirmedHeight.current
    )
      return;
    setPreferenceStatus('Đang lưu bố cục…');
    let active = true;
    const timer = window.setTimeout(() => {
      const write = layoutWrites.current
        .catch(() => {})
        .then(() =>
          apiClient.json('ui-state', 'PATCH', {
            key: 'timelineHeight',
            value: timelineHeight,
          }),
        );
      layoutWrites.current = write;
      write
        .then(() => {
          confirmedHeight.current = timelineHeight;
          if (active) setPreferenceStatus('Đã lưu bố cục.');
        })
        .catch(() => {
          if (active) {
            setTimelineHeight(confirmedHeight.current);
            setPreferenceStatus(
              'Không lưu được bố cục; đã khôi phục kích thước trước.',
            );
          }
        });
    }, 500);
    return () => {
      active = false;
      window.clearTimeout(timer);
    };
  }, [apiClient, timelineHeight]);
  async function changeProjectView(next: 'grid' | 'list') {
    if (
      !apiClient ||
      !prefsLoaded.current ||
      next === projectView ||
      viewSaving.current
    )
      return;
    viewSaving.current = true;
    setViewPending(true);
    const previous = projectView;
    setProjectView(next);
    setPreferenceStatus('Đang lưu chế độ xem…');
    try {
      await apiClient.json('ui-state', 'PATCH', {
        key: 'projectViewMode',
        value: next,
      });
      setPreferenceStatus('Đã lưu chế độ xem.');
    } catch {
      setProjectView(previous);
      setPreferenceStatus(
        'Không lưu được chế độ xem; đã khôi phục lựa chọn trước.',
      );
    } finally {
      viewSaving.current = false;
      setViewPending(false);
    }
  }
  useEffect(() => {
    if (project?.id) setWorkspace('editor');
  }, [project?.id]);
  const shownProjects = projects
    .filter(
      (p) =>
        p.name
          .toLocaleLowerCase('vi')
          .includes(search.toLocaleLowerCase('vi')) &&
        (projectFilter === 'all' || recent.some((r) => r.id === p.id)),
    )
    .sort((a, b) =>
      projectSort === 'name'
        ? a.name.localeCompare(b.name, 'vi')
        : (recent.findIndex((r) => r.id === a.id) < 0
            ? Number.MAX_SAFE_INTEGER
            : recent.findIndex((r) => r.id === a.id)) -
          (recent.findIndex((r) => r.id === b.id) < 0
            ? Number.MAX_SAFE_INTEGER
            : recent.findIndex((r) => r.id === b.id)),
    );
  return (
    <div className="studio-shell">
      <aside className="navigation">
        <a className="brand" href="#">
          <span>◈</span> hòa âm<small>VIDEO ÂM NHẠC</small>
        </a>
        {(
          [
            ['dashboard', 'Tổng quan'],
            ['projects', 'Dự án'],
            ['storage', 'Lưu trữ'],
            ['settings', 'Cài đặt'],
          ] as const
        ).map(([id, label]) => (
          <button
            key={id}
            className={workspace === id ? 'nav-active' : ''}
            aria-current={workspace === id ? 'page' : undefined}
            onClick={() => setWorkspace(id)}
          >
            {label}
          </button>
        ))}
        {project && (
          <button
            className={workspace === 'editor' ? 'nav-active' : ''}
            onClick={() => setWorkspace('editor')}
          >
            Trình chỉnh sửa
          </button>
        )}
        <div className="local-badge">
          <i /> Chạy trên máy của bạn
          <small>Drive chỉ tải lên khi bạn chọn sao lưu</small>
        </div>
      </aside>
      <main>
        <header className="topbar">
          <div>
            <span className="breadcrumb">Hòa Âm / </span>
            <strong>
              {workspace === 'editor'
                ? project?.name
                : (
                    {
                      dashboard: 'Tổng quan',
                      projects: 'Quản lý dự án',
                      storage: 'Kho lưu trữ',
                      settings: 'Cài đặt',
                    } as const
                  )[workspace]}
            </strong>
            {project && workspace === 'editor' && (
              <span className={`save-state ${dirty ? 'unsaved' : ''}`}>
                {dirty ? '● Chưa lưu thủ công' : '✓ Đã lưu'}
              </span>
            )}
          </div>
          <div className="actions">
            {backgroundJobs.some(
              (j) =>
                !['succeeded', 'failed', 'cancelled', 'interrupted'].includes(
                  j.status,
                ),
            ) && (
              <span role="status" className="background-status">
                {
                  backgroundJobs.filter(
                    (j) =>
                      ![
                        'succeeded',
                        'failed',
                        'cancelled',
                        'interrupted',
                      ].includes(j.status),
                  ).length
                }{' '}
                tác vụ đang chạy
              </span>
            )}
            {project && workspace === 'editor' && (
              <>
                <button disabled={busy || !writeAllowed} onClick={save}>
                  Lưu project
                </button>
                <button
                  className="primary"
                  disabled={
                    busy || !writeAllowed || Boolean(missingMedia.length)
                  }
                  onClick={() => setExportOpen(true)}
                >
                  Xuất video ↗
                </button>
              </>
            )}
          </div>
        </header>
        {backgroundJobs.length > 0 && (
          <details className="activity">
            <summary>Tác vụ nền ({backgroundJobs.length})</summary>
            <ul>
              {backgroundJobs.slice(0, 10).map((row) => (
                <li key={row.id}>
                  <span>
                    {row.kind === 'render'
                      ? 'Xuất video'
                      : row.kind === 'asr'
                        ? 'Nhận dạng lời'
                        : row.kind === 'alignment'
                          ? 'Căn lời'
                          : 'Đóng gói'}{' '}
                    · {row.message} · {row.status}
                  </span>
                  {row.kind === 'render' && row.projectId === project?.id && (
                    <button
                      onClick={() => {
                        selectBackgroundJob(row.id);
                        setExportOpen(true);
                      }}
                    >
                      Theo dõi xuất video
                    </button>
                  )}
                  {row.kind === 'render' && row.projectId !== project?.id && (
                    <button onClick={() => openProject(row.projectId)}>
                      Mở project
                    </button>
                  )}
                </li>
              ))}
            </ul>
          </details>
        )}
        <div hidden={workspace !== 'storage'}>
          <StorageWorkspace
            api={apiClient}
            active={workspace === 'storage'}
            beforeBackup={prepareBackup}
          />
        </div>
        <div hidden={workspace !== 'dashboard'}>
          <section className="dashboard">
            <div className="eyebrow">
              TỪ MỘT GIAI ĐIỆU, THÀNH MỘT CÂU CHUYỆN
            </div>
            <h1>
              Âm nhạc của bạn.
              <br />
              <em>Khung hình của bạn.</em>
            </h1>
            <p>
              Chọn mẫu, thêm media và tạo video mang dấu ấn riêng.
              <br />
              Mọi thứ được xử lý ngay trên máy của bạn.
            </p>
            <button
              className="primary large"
              disabled={!ready || busy}
              onClick={() => createProject()}
            >
              ＋ Tạo video mới
            </button>
            <div className="template-grid">
              <button
                className="template-card"
                disabled={!ready || busy}
                onClick={() => createProject()}
              >
                <div className="artwork">
                  <span>
                    khoảnh
                    <br />
                    <i>khắc.</i>
                  </span>
                  <b>♫</b>
                </div>
                <div>
                  <strong>Ảnh + Caption + Nhạc</strong>
                  <small>Một khoảnh khắc, một giai điệu.</small>
                  <span className="tag">Bắt đầu tại đây ↗</span>
                </div>
              </button>
              <button
                className="template-card"
                disabled={!ready || busy}
                onClick={() => createProject('TPL-02')}
              >
                <div className="artwork second">◉</div>
                <div>
                  <strong>Music Card</strong>
                  <small>Hai ảnh, nhạc và thẻ bài hát.</small>
                </div>
              </button>
              <button
                className="template-card"
                disabled={!ready || busy}
                onClick={() => createProject('TPL-03')}
              >
                <div className="artwork third">
                  lời hát
                  <br />
                  thành hình.
                </div>
                <div>
                  <strong>Lyrics Video</strong>
                  <small>Nhập lời, duyệt và đồng bộ theo nhạc.</small>
                </div>
              </button>
            </div>
            <section className="recent-projects">
              <div className="workspace-heading">
                <h2>Dự án gần đây</h2>
                <button onClick={() => setWorkspace('projects')}>
                  Xem tất cả
                </button>
              </div>
              <div className="recent-grid">
                {recent.slice(0, 6).map((entry) => {
                  const found = projects.find((p) => p.id === entry.id);
                  return found ? (
                    <button
                      key={entry.id}
                      disabled={busy}
                      onClick={() => openProject(entry.id)}
                    >
                      {found.name}
                      <small>
                        {new Date(entry.openedAt).toLocaleString('vi-VN')}
                      </small>
                    </button>
                  ) : null;
                })}
              </div>
              {!recent.length && <p>Chưa có dự án nào được mở gần đây.</p>}
            </section>
            <button
              className="text-button"
              disabled={!ready || busy}
              onClick={openManualProject}
            >
              Mở file project đã lưu →
            </button>
          </section>
        </div>
        <section
          hidden={workspace !== 'projects'}
          className="projects-workspace"
        >
          <h1>Quản lý dự án</h1>
          {recoveryProject ? (
            <RecoveryWorkspace
              api={apiClient}
              projectId={recoveryProject}
              onBack={() => setRecoveryProject(null)}
              onOpen={() => openProject(recoveryProject)}
            />
          ) : (
            <>
              <div className="project-toolbar">
                <input
                  aria-label="Tìm dự án theo tên"
                  placeholder="Tìm dự án…"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
                <button
                  aria-pressed={projectView === 'grid'}
                  disabled={viewPending}
                  onClick={() => void changeProjectView('grid')}
                >
                  Lưới
                </button>
                <button
                  aria-pressed={projectView === 'list'}
                  disabled={viewPending}
                  onClick={() => void changeProjectView('list')}
                >
                  Danh sách
                </button>
                <button
                  aria-pressed={projectFilter === 'all'}
                  onClick={() => setProjectFilter('all')}
                >
                  Tất cả
                </button>
                <button
                  aria-pressed={projectFilter === 'recent'}
                  onClick={() => setProjectFilter('recent')}
                >
                  Gần đây
                </button>
                <label>
                  Sắp xếp{' '}
                  <select
                    aria-label="Sắp xếp dự án"
                    value={projectSort}
                    onChange={(e) =>
                      setProjectSort(e.target.value as 'name' | 'opened')
                    }
                  >
                    <option value="opened">Gần đây</option>
                    <option value="name">Tên A–Z</option>
                  </select>
                </label>
                <button onClick={refresh}>Làm mới</button>
              </div>
              {preferenceStatus && <p role="status">{preferenceStatus}</p>}
              <div
                className={
                  projectView === 'grid' ? 'project-grid' : 'project-list'
                }
              >
                {shownProjects.map((entry) => (
                  <article className="project-card" key={entry.id}>
                    <div className="project-card-art" aria-hidden="true">
                      ▣
                    </div>
                    <strong>{entry.name}</strong>
                    <button
                      disabled={busy}
                      onClick={() => openProject(entry.id)}
                    >
                      Mở dự án
                    </button>
                    <button onClick={() => setRecoveryProject(entry.id)}>
                      Recovery
                    </button>
                  </article>
                ))}
              </div>
              {!shownProjects.length && (
                <p role="status">
                  {projects.length
                    ? 'Không tìm thấy dự án phù hợp.'
                    : 'Chưa có dự án trên máy.'}
                </p>
              )}
              <button disabled={busy} onClick={openManualProject}>
                Mở file project…
              </button>
            </>
          )}
        </section>
        <div hidden={workspace !== 'settings'}>
          <SettingsWorkspace
            api={apiClient}
            prepare={prepareBackup}
            projectView={projectView}
            onProjectView={changeProjectView}
            preferenceStatus={preferenceStatus}
            viewPending={viewPending}
            active={workspace === 'settings'}
            onStorage={() => setWorkspace('storage')}
          />
        </div>
        {project && (
          <div hidden={workspace !== 'editor'} className="editor-workspace">
            <div className="editor-layout">
              <aside className="editor-tools" aria-label="Công cụ chỉnh sửa">
                {' '}
                <div className="import-bar">
                  <label className="rights">
                    <input
                      ref={rightsInput}
                      type="checkbox"
                      checked={rights}
                      onChange={(e) => {
                        setRights(e.target.checked);
                        if (e.target.checked) setUploadHint('');
                      }}
                    />
                    Tôi có quyền sử dụng media này
                  </label>
                  <label className={`upload-button ${busy ? 'disabled' : ''}`}>
                    ＋ Thêm ảnh / video / nhạc
                    <input
                      aria-label="Thêm ảnh, video hoặc nhạc"
                      type="file"
                      multiple
                      disabled={busy}
                      accept="image/png,image/jpeg,video/mp4,audio/*"
                      onClick={(event) => {
                        if (!rights) {
                          event.preventDefault();
                          setUploadHint(
                            'Tích ô “Tôi có quyền sử dụng media này” trước khi chọn file.',
                          );
                          rightsInput.current?.focus();
                        }
                      }}
                      onChange={(e) => {
                        const files = Array.from(e.target.files ?? []);
                        if (files.length) upload(files);
                        e.target.value = '';
                      }}
                    />
                  </label>
                  {uploadHint && (
                    <span className="upload-hint" role="status">
                      {uploadHint}
                    </span>
                  )}
                </div>
                <ProjectTools
                  key={project.id + 'tools'}
                  project={project}
                  assets={assets}
                  api={apiClient}
                  prepare={prepareBackup}
                  open={openProject}
                  refresh={refresh}
                  reload={reloadFromServer}
                  change={change}
                  selected={selected}
                  panels={panels}
                  setPanel={setPanel}
                />
                <LyricsPanel
                  key={project.id}
                  project={project}
                  assets={assets}
                  api={apiClient}
                  change={change}
                  prepare={prepareBackup}
                  expanded={
                    panels.lyrics ?? project.templateRef.id === 'TPL-03'
                  }
                  toggle={(value) => setPanel('lyrics', value)}
                  initialDraft={lyricDrafts.current[project.id]}
                  onDraftChange={(draft) => {
                    lyricDrafts.current[project.id] = draft;
                  }}
                />
              </aside>
              <section className="editor-main">
                {!writeAllowed && (
                  <p role="status">
                    Tab này chỉ đọc.{' '}
                    <button disabled={busy} onClick={takeOver}>
                      Nhận quyền chỉnh sửa
                    </button>
                  </p>
                )}
                {Boolean(missingMedia.length) && (
                  <p role="alert">
                    Có {missingMedia.length} media bị thiếu/hỏng. Mở Dữ liệu
                    project để chọn lại file gốc; dữ liệu chỉnh sửa vẫn được
                    giữ.
                  </p>
                )}
                <div className="editor-toolbar">
                  <span>XEM TRƯỚC</span>
                  <div>
                    <button aria-label="Hoàn tác" onClick={undo}>
                      ↶
                    </button>
                    <button aria-label="Làm lại" onClick={redo}>
                      ↷
                    </button>
                  </div>
                  <span>
                    {project.preset.width} × {project.preset.height}
                  </span>
                </div>
                <div className="preview-stage" ref={previewRef}>
                  <Player
                    ref={player}
                    component={ProjectScene}
                    inputProps={{ project, assets: urls }}
                    durationInFrames={Math.ceil(
                      (project.durationTicks * project.preset.fps) / TICKS,
                    )}
                    compositionWidth={project.preset.width}
                    compositionHeight={project.preset.height}
                    fps={project.preset.fps}
                    controls={false}
                    style={{
                      height: '100%',
                      maxWidth: '100%',
                      aspectRatio: `${project.preset.width}/${project.preset.height}`,
                    }}
                  />
                </div>
                <div className="preview-controls">
                  <button
                    onClick={() => {
                      const target = previewRef.current;
                      if (!target) return;
                      if (document.fullscreenElement)
                        document
                          .exitFullscreen()
                          .catch((e) => setPreviewStatus(String(e)));
                      else
                        target
                          .requestFullscreen()
                          .catch(() =>
                            setPreviewStatus(
                              'Không thể mở toàn màn hình. Kiểm tra quyền của trình duyệt.',
                            ),
                          );
                    }}
                    aria-label="Toàn màn hình Preview"
                  >
                    Toàn màn hình
                  </button>
                  {previewStatus && <span role="status">{previewStatus}</span>}
                </div>
                <button
                  aria-label="Phát hoặc tạm dừng"
                  onClick={() => player.current?.toggle()}
                >
                  ▶ Phát / Tạm dừng
                </button>
              </section>
              <Inspector
                editable={writeAllowed}
                project={project}
                preset={(value) =>
                  change((p) => {
                    const previous = p.preset;
                    for (const item of p.items) {
                      if (!item.style) continue;
                      if (item.style.x !== undefined)
                        item.style.x *= value.width / previous.width;
                      if (item.style.y !== undefined)
                        item.style.y *= value.height / previous.height;
                      if (item.style.fontSize !== undefined)
                        item.style.fontSize = Math.min(
                          300,
                          Math.max(
                            8,
                            (item.style.fontSize * value.width) /
                              previous.width,
                          ),
                        );
                    }
                    p.preset = value;
                  })
                }
                item={project.items.find((i) => i.id === selected)}
                edit={editItem}
                assets={assets}
                reorder={reorder}
                remove={removeSelected}
                cardText={(id, text) =>
                  change((p) => {
                    const item = p.items.find((i) => (i.role ?? i.id) === id);
                    if (item) item.text = text;
                  })
                }
                rename={(name) =>
                  change((p) => {
                    p.name = name;
                  })
                }
                duration={(seconds) =>
                  change((p) => {
                    if (
                      !Number.isFinite(seconds) ||
                      seconds < 1 ||
                      seconds > 300
                    )
                      throw new Error('Độ dài phải từ 1 đến 300 giây.');
                    p.durationTicks =
                      (Math.round(seconds * p.preset.fps) * TICKS) /
                      p.preset.fps;
                    p.items = p.items.filter(
                      (i) => i.startTicks < p.durationTicks,
                    );
                    for (const item of p.items)
                      item.durationTicks = Math.min(
                        item.durationTicks,
                        p.durationTicks - item.startTicks,
                      );
                  })
                }
              />
              <div className="timeline-dock" style={{ height: timelineHeight }}>
                <div
                  className="timeline-resize"
                  role="separator"
                  aria-label="Thay đổi chiều cao Timeline"
                  aria-orientation="horizontal"
                  aria-valuemin={180}
                  aria-valuemax={Math.floor(
                    (typeof window === 'undefined' ? 768 : window.innerHeight) *
                      0.55,
                  )}
                  aria-valuenow={timelineHeight}
                  tabIndex={0}
                  onDoubleClick={() => setTimelineHeight(280)}
                  onKeyDown={(e) => {
                    if (e.key === 'ArrowUp' || e.key === 'ArrowDown') {
                      e.preventDefault();
                      setTimelineHeight((h) =>
                        Math.max(
                          180,
                          Math.min(
                            Math.floor(window.innerHeight * 0.55),
                            h + (e.key === 'ArrowUp' ? 20 : -20),
                          ),
                        ),
                      );
                    }
                  }}
                  onPointerDown={(e) => {
                    const startY = e.clientY,
                      startHeight = timelineHeight;
                    const move = (event: PointerEvent) =>
                      setTimelineHeight(
                        Math.max(
                          180,
                          Math.min(
                            Math.floor(window.innerHeight * 0.55),
                            startHeight + startY - event.clientY,
                          ),
                        ),
                      );
                    const stop = () => {
                      window.removeEventListener('pointermove', move);
                      window.removeEventListener('pointerup', stop);
                    };
                    window.addEventListener('pointermove', move);
                    window.addEventListener('pointerup', stop);
                  }}
                />
                <button
                  className="timeline-reset"
                  onClick={() => setTimelineHeight(280)}
                >
                  Đặt lại chiều cao
                </button>{' '}
                <Timeline
                  assets={assets}
                  change={change}
                  editable={writeAllowed}
                  zoom={zoom}
                  setZoom={setZoom}
                  player={player}
                  project={project}
                  selected={selected}
                  select={setSelected}
                  move={moveClip}
                  seek={(frame) =>
                    player.current?.seekTo(
                      Math.min(
                        frame,
                        Math.ceil(
                          (project.durationTicks * project.preset.fps) / TICKS,
                        ) - 1,
                      ),
                    )
                  }
                />
              </div>
            </div>
          </div>
        )}
        {exportOpen && project && (
          <div className="dialog-backdrop">
            <section
              className="export-dialog"
              ref={exportDialog}
              role="dialog"
              aria-modal="true"
              aria-label="Xuất video"
            >
              <header>
                <h2>Xuất video</h2>
                <button
                  aria-label="Đóng dialog xuất video"
                  onClick={() => setExportOpen(false)}
                >
                  ×
                </button>
              </header>
              <div className="export-columns">
                <div>
                  <h3>Xem trước project</h3>
                  <div className="export-scene">
                    <Player
                      component={ProjectScene}
                      inputProps={{ project, assets: urls }}
                      durationInFrames={Math.ceil(
                        (project.durationTicks * project.preset.fps) / TICKS,
                      )}
                      compositionWidth={project.preset.width}
                      compositionHeight={project.preset.height}
                      fps={project.preset.fps}
                      controls={false}
                      style={{
                        height: '100%',
                        maxWidth: '100%',
                        aspectRatio: `${project.preset.width}/${project.preset.height}`,
                      }}
                    />
                  </div>
                  <p>{project.name}</p>
                  <p>
                    {project.preset.width} × {project.preset.height} ·{' '}
                    {project.preset.fps} FPS
                  </p>
                  <p>
                    {missingMedia.length
                      ? `${missingMedia.length} media bị thiếu`
                      : 'Media hiện có trong project'}
                  </p>
                </div>
                <div>
                  <h3>Cấu hình</h3>
                  <p>
                    Preset lấy từ project; thay đổi trong Inspector trước khi
                    xuất.
                  </p>
                  <p>Thư mục lưu sẽ được chọn bằng bộ chọn hệ thống.</p>
                  {job && <p>{job.message}</p>}
                </div>
              </div>
              <footer>
                <button onClick={() => setExportOpen(false)}>Đóng</button>
                <button
                  className="primary"
                  disabled={
                    busy || !writeAllowed || Boolean(missingMedia.length)
                  }
                  onClick={render}
                >
                  Bắt đầu xuất video
                </button>
              </footer>
            </section>
          </div>
        )}
        {job && (
          <section className="job-panel" aria-live="polite">
            <div>
              <strong>{job.message}</strong>
              <span>{Math.round(job.progress * 100)}%</span>
            </div>
            <progress max="1" value={job.progress} />
            {job.kind === 'render' && (
              <button onClick={() => setExportOpen(true)}>
                Mở lại Xuất video
              </button>
            )}
            {job.status === 'succeeded' ? (
              <div>
                <a
                  href={`/api/v1/outputs/${job.id}`}
                  target="_blank"
                  rel="noreferrer"
                >
                  Xem / tải MP4 ↗
                </a>
                <button onClick={openOutputFolder}>Mở thư mục</button>
              </div>
            ) : !['failed', 'cancelled', 'interrupted'].includes(job.status) ? (
              <button onClick={cancelJob}>Hủy render</button>
            ) : (
              <button onClick={render} disabled={busy}>
                Thử xuất lại
              </button>
            )}
          </section>
        )}
        <footer role="status">
          {busy ? 'Đang xử lý… ' : ''}
          {message}
        </footer>
      </main>
    </div>
  );
}
