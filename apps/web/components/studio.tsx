'use client';
import { Player } from '@remotion/player';
import { ProjectScene } from '@amvs/composition';
import { TICKS } from '@amvs/domain';
import { useStudio } from '../hooks/use-studio';
import { Timeline } from './timeline';
import { Inspector } from './inspector';
import { DrivePanel } from './drive-panel';
export function Studio() {
  const {
    apiClient,
    prepareBackup,
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
  } = useStudio();

  return (
    <div className="studio-shell">
      <aside className="navigation">
        <a className="brand" href="#">
          <span>◈</span> hòa âm<small>VIDEO STUDIO</small>
        </a>
        <button className="nav-active">▦ Studio của tôi</button>
        <div className="section-label">DỰ ÁN LOCAL</div>
        {projects.map((p) => (
          <button
            key={p.id}
            disabled={busy}
            onClick={() => open(p.id)}
            className={project?.id === p.id ? 'current-project' : ''}
          >
            {p.name}
          </button>
        ))}
        <div className="local-badge">
          <i /> Chạy trên máy của bạn
          <small>Drive chỉ tải lên khi bạn chọn sao lưu</small>
        </div>
      </aside>
      <main>
        <header className="topbar">
          <div>
            <span className="breadcrumb">Studio / </span>
            <strong>{project?.name ?? 'Không gian sáng tạo'}</strong>
            {project && (
              <span className={`save-state ${dirty ? 'unsaved' : ''}`}>
                {dirty ? '● Chưa lưu thủ công' : '✓ Đã lưu'}
              </span>
            )}
          </div>
          <div className="actions">
            {project && (
              <>
                <button disabled={busy} onClick={save}>
                  Lưu project
                </button>
                <button className="primary" disabled={busy} onClick={render}>
                  Xuất video ↗
                </button>
              </>
            )}
          </div>
        </header>
        <DrivePanel api={apiClient} beforeBackup={prepareBackup} />
        {!project ? (
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
              onClick={create}
            >
              ＋ Tạo video mới
            </button>
            <div className="template-grid">
              <button
                className="template-card"
                disabled={!ready || busy}
                onClick={create}
              >
                <div className="artwork">
                  <span>
                    your
                    <br />
                    <i>moment.</i>
                  </span>
                  <b>♫</b>
                </div>
                <div>
                  <strong>Ảnh + Caption + Nhạc</strong>
                  <small>Một khoảnh khắc, một giai điệu.</small>
                  <span className="tag">Bắt đầu tại đây ↗</span>
                </div>
              </button>
              <div className="template-card upcoming">
                <div className="artwork second">◉</div>
                <div>
                  <strong>Music Card</strong>
                  <small>Đang phát triển</small>
                </div>
              </div>
              <div className="template-card upcoming">
                <div className="artwork third">
                  lời hát
                  <br />
                  thành hình.
                </div>
                <div>
                  <strong>Lyrics Video</strong>
                  <small>Đang phát triển</small>
                </div>
              </div>
            </div>
            <button
              className="text-button"
              disabled={!ready || busy}
              onClick={openManual}
            >
              Mở file project đã lưu →
            </button>
          </section>
        ) : (
          <div className="editor-layout">
            <section className="editor-main">
              <div className="editor-toolbar">
                <span>PREVIEW</span>
                <div>
                  <button aria-label="Hoàn tác" onClick={undo}>
                    ↶
                  </button>
                  <button aria-label="Làm lại" onClick={redo}>
                    ↷
                  </button>
                </div>
                <span>9:16</span>
              </div>
              <div className="preview-stage">
                <Player
                  ref={player}
                  component={ProjectScene}
                  inputProps={{ project, assets: urls }}
                  durationInFrames={Math.ceil(
                    (project.durationTicks * project.preset.fps) / TICKS,
                  )}
                  compositionWidth={720}
                  compositionHeight={1280}
                  fps={30}
                  controls
                  style={{
                    height: '100%',
                    maxWidth: '100%',
                    aspectRatio: '9/16',
                  }}
                />
              </div>
              <div className="import-bar">
                <label className="rights">
                  <input
                    type="checkbox"
                    checked={rights}
                    onChange={(e) => setRights(e.target.checked)}
                  />
                  Tôi có quyền sử dụng media này
                </label>
                <label className={`upload-button ${busy ? 'disabled' : ''}`}>
                  ＋ Thêm ảnh / video / nhạc
                  <input
                    aria-label="Thêm ảnh, video hoặc nhạc"
                    type="file"
                    multiple
                    disabled={busy || !rights}
                    accept="image/png,image/jpeg,video/mp4,audio/*"
                    onChange={(e) => {
                      const files = Array.from(e.target.files ?? []);
                      if (files.length) upload(files);
                      e.target.value = '';
                    }}
                  />
                </label>
              </div>
              <Timeline
                assets={assets}
                project={project}
                selected={selected}
                select={setSelected}
                move={(id, start) =>
                  change((p) => {
                    p.items.find((i) => i.id === id)!.startTicks = start;
                  })
                }
                seek={(frame) =>
                  player.current?.seekTo(
                    Math.min(
                      frame,
                      Math.ceil((project.durationTicks * 30) / TICKS) - 1,
                    ),
                  )
                }
              />
            </section>
            <Inspector
              project={project}
              item={project.items.find((i) => i.id === selected)}
              edit={editItem}
              assets={assets}
              reorder={reorder}
              remove={removeSelected}
              rename={(name) =>
                change((p) => {
                  p.name = name;
                })
              }
              duration={(seconds) =>
                change((p) => {
                  if (!Number.isFinite(seconds) || seconds < 1 || seconds > 300)
                    throw new Error('Độ dài phải từ 1 đến 300 giây.');
                  p.durationTicks = (Math.round(seconds * 30) * TICKS) / 30;
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
          </div>
        )}
        {job && (
          <section className="job-panel" aria-live="polite">
            <div>
              <strong>{job.message}</strong>
              <span>{Math.round(job.progress * 100)}%</span>
            </div>
            <progress max="1" value={job.progress} />
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
