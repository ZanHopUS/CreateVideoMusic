'use client';
import { useRef, useState } from 'react';
import { Player } from '@remotion/player';
import { ProjectScene } from '@amvs/composition';
import { TICKS } from '@amvs/domain';
import { useStudio } from '../hooks/use-studio';
import { Timeline } from './timeline';
import { Inspector } from './inspector';
import { DrivePanel } from './drive-panel';
import { LyricsPanel } from './lyrics-panel';
import { ProjectTools } from './project-tools';
export function Studio() {
  const rightsInput = useRef<HTMLInputElement>(null);
  const [uploadHint, setUploadHint] = useState('');
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
  } = useStudio();

  return (
    <div className="studio-shell">
      <aside className="navigation">
        <a className="brand" href="#">
          <span>◈</span> hòa âm<small>VIDEO ÂM NHẠC</small>
        </a>
        <button className="nav-active">▦ Studio của tôi</button>
        <div className="section-label">DỰ ÁN TRÊN MÁY</div>
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
                <button disabled={busy || !writeAllowed} onClick={save}>
                  Lưu project
                </button>
                <button
                  className="primary"
                  disabled={
                    busy || !writeAllowed || Boolean(missingMedia.length)
                  }
                  onClick={render}
                >
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
              onClick={() => create()}
            >
              ＋ Tạo video mới
            </button>
            <div className="template-grid">
              <button
                className="template-card"
                disabled={!ready || busy}
                onClick={() => create()}
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
                onClick={() => create('TPL-02')}
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
                onClick={() => create('TPL-03')}
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
              {!writeAllowed && (
                <p role="status">
                  Tab này chỉ đọc.{' '}
                  <button onClick={() => takeOver().catch(() => {})}>
                    Nhận quyền chỉnh sửa
                  </button>
                </p>
              )}
              {Boolean(missingMedia.length) && (
                <p role="alert">
                  Có {missingMedia.length} media bị thiếu/hỏng. Mở Dữ liệu
                  project để chọn lại file gốc; dữ liệu chỉnh sửa vẫn được giữ.
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
              <div className="preview-stage">
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
              <button
                aria-label="Phát hoặc tạm dừng"
                onClick={() => player.current?.toggle()}
              >
                ▶ Phát / Tạm dừng
              </button>
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
                open={open}
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
                expanded={panels.lyrics ?? project.templateRef.id === 'TPL-03'}
                toggle={(value) => setPanel('lyrics', value)}
              />
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
                          (item.style.fontSize * value.width) / previous.width,
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
                  if (!Number.isFinite(seconds) || seconds < 1 || seconds > 300)
                    throw new Error('Độ dài phải từ 1 đến 300 giây.');
                  p.durationTicks =
                    (Math.round(seconds * p.preset.fps) * TICKS) / p.preset.fps;
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
