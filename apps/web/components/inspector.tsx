import type { ProjectContent, TimelineItem } from '@amvs/domain';
import { TICKS, PRESETS } from '@amvs/domain';
import type { Asset } from '../lib/api';
export function Inspector({
  project,
  editable,
  preset,
  item,
  edit,
  rename,
  duration,
  assets,
  reorder,
  remove,
  cardText,
}: {
  project: ProjectContent;
  editable: boolean;
  preset: (value: ProjectContent['preset']) => void;
  item?: TimelineItem;
  edit: (operation: (item: TimelineItem) => void) => void;
  rename: (name: string) => void;
  duration: (seconds: number) => void;
  assets: Asset[];
  reorder: (direction: -1 | 1) => void;
  remove: () => void;
  cardText: (id: 'song-title' | 'artist-name', text: string) => void;
}) {
  return (
    <aside className="inspector">
      <fieldset
        disabled={!editable}
        style={{ border: 0, padding: 0, margin: 0, minWidth: 0 }}
      >
        <div className="section-label">THUỘC TÍNH</div>
        <h2>Chỉnh theo ý bạn</h2>
        <label>
          Tên project
          <input
            aria-label="Tên project"
            key={project.id + project.name}
            defaultValue={project.name}
            onBlur={(e) => {
              if (e.target.value.trim()) rename(e.target.value.trim());
            }}
          />
        </label>
        <label>
          Độ dài video (giây)
          <input
            aria-label="Độ dài video"
            type="number"
            step="0.1"
            min="1"
            max="300"
            value={project.durationTicks / TICKS}
            onChange={(e) => duration(Number(e.target.value))}
          />
        </label>
        <div className="divider" />
        {project.templateRef.id === 'TPL-02' && (
          <>
            <div className="section-label">MUSIC CARD</div>
            {(
              [
                ['song-title', 'Tên bài hát'],
                ['artist-name', 'Tên nghệ sĩ'],
              ] as const
            ).map(([id, label]) => (
              <label key={id}>
                {label}
                <input
                  aria-label={label}
                  key={
                    project.id +
                    id +
                    (project.items.find((i) => (i.role ?? i.id) === id)?.text ??
                      '')
                  }
                  defaultValue={
                    project.items.find((i) => (i.role ?? i.id) === id)?.text ??
                    ''
                  }
                  onBlur={(event) => cardText(id, event.target.value.trim())}
                />
              </label>
            ))}
            <small>Ảnh thứ nhất mở đầu; ảnh thứ hai là bìa Music Card.</small>
            <div className="divider" />
          </>
        )}
        {item ? (
          <>
            <div className="section-label">CLIP ĐANG CHỌN</div>
            <h3>
              {item.type === 'lyrics'
                ? 'Lời hát'
                : item.type === 'text'
                  ? 'Chú thích'
                  : item.type === 'audio'
                    ? 'Âm nhạc'
                    : item.type === 'video'
                      ? 'Video nền'
                      : 'Hình ảnh'}
            </h3>
            <label>
              Lớp chứa clip
              <select
                aria-label="Lớp chứa clip"
                value={item.trackId}
                onChange={(e) =>
                  edit((i) => {
                    i.trackId = e.target.value;
                  })
                }
              >
                {project.orderedTracks
                  .filter(
                    (t) =>
                      t.kind ===
                      project.orderedTracks.find(
                        (current) => current.id === item.trackId,
                      )?.kind,
                  )
                  .map((t, index) => (
                    <option key={t.id} value={t.id}>
                      Lớp {index + 1}
                    </option>
                  ))}
              </select>
            </label>
            {item.assetId && (
              <p className="asset-caption">
                {assets.find((a) => a.id === item.assetId)?.name ??
                  'Media không tìm thấy'}
              </p>
            )}
            {['image', 'video', 'audio'].includes(item.type) && (
              <div className="clip-actions">
                <button
                  aria-label="Đưa clip lên trước"
                  onClick={() => reorder(-1)}
                >
                  ← Trước
                </button>
                <button aria-label="Đưa clip ra sau" onClick={() => reorder(1)}>
                  Sau →
                </button>
              </div>
            )}
            {['image', 'video', 'audio'].includes(item.type) && (
              <small className="edit-hint">
                Đổi thứ tự sẽ xếp các clip liền nhau trong track.
              </small>
            )}
            {['image', 'video'].includes(item.type) && (
              <label>
                Cách hiển thị
                <select
                  aria-label="Cách hiển thị"
                  value={item.style?.fit ?? 'cover'}
                  onChange={(e) =>
                    edit((i) => {
                      i.style = {
                        ...i.style,
                        fit: e.target.value as 'cover' | 'contain',
                      };
                    })
                  }
                >
                  <option value="cover">Lấp đầy khung</option>
                  <option value="contain">Giữ trọn ảnh / video</option>
                </select>
              </label>
            )}
            {(item.type === 'text' || item.type === 'lyrics') && (
              <>
                {item.type === 'text' ? (
                  <label>
                    Nội dung
                    <textarea
                      aria-label="Nội dung caption"
                      key={item.id + project.id + (item.text ?? '')}
                      defaultValue={item.text}
                      onBlur={(e) =>
                        edit((i) => {
                          i.text = e.target.value;
                        })
                      }
                    />
                  </label>
                ) : (
                  <p>Sửa lời và mốc nguồn trong bảng duyệt lời hát.</p>
                )}
                <label>
                  Cỡ chữ
                  <input
                    aria-label="Cỡ chữ"
                    type="number"
                    min="8"
                    max="300"
                    value={item.style?.fontSize ?? 54}
                    onChange={(e) =>
                      edit((i) => {
                        i.style = {
                          ...i.style,
                          fontSize: Number(e.target.value),
                        };
                      })
                    }
                  />
                </label>
                <label>
                  Màu chữ
                  <input
                    aria-label="Màu chữ"
                    type="color"
                    value={item.style?.color ?? '#ffffff'}
                    onChange={(e) =>
                      edit((i) => {
                        i.style = { ...i.style, color: e.target.value };
                      })
                    }
                  />
                </label>
              </>
            )}
            <label>
              Hiệu ứng
              <select
                aria-label="Hiệu ứng clip"
                value={item.style?.animation ?? 'none'}
                onChange={(e) =>
                  edit((i) => {
                    i.style = {
                      ...i.style,
                      animation: e.target.value as
                        'none' | 'fade' | 'slide' | 'scale',
                    };
                  })
                }
              >
                {[
                  ['none', 'Không'],
                  ['fade', 'Mờ dần'],
                  ['slide', 'Trượt vào'],
                  ['scale', 'Phóng vào'],
                ]
                  .filter(
                    ([v]) =>
                      item.type !== 'audio' || ['none', 'fade'].includes(v),
                  )
                  .map(([v, n]) => (
                    <option key={v} value={v}>
                      {n}
                    </option>
                  ))}
              </select>
            </label>
            {['image', 'video'].includes(item.type) && (
              <>
                {(
                  [
                    ['blur', 'Độ mờ', 0, 40, 1],
                    ['brightness', 'Độ sáng', 0, 2, 0.05],
                    ['cropX', 'Vùng cắt ngang (%)', 0, 100, 1],
                    ['cropY', 'Vùng cắt dọc (%)', 0, 100, 1],
                  ] as const
                ).map(([key, label, min, max, step]) => (
                  <label key={key}>
                    {label}
                    <input
                      aria-label={label}
                      type="number"
                      min={min}
                      max={max}
                      step={step}
                      value={
                        item.style?.[key] ??
                        (key === 'brightness'
                          ? 1
                          : key.startsWith('crop')
                            ? 50
                            : 0)
                      }
                      onChange={(e) =>
                        edit((i) => {
                          i.style = {
                            ...i.style,
                            [key]: Number(e.target.value),
                          };
                        })
                      }
                    />
                  </label>
                ))}
              </>
            )}
            {['text', 'lyrics'].includes(item.type) && (
              <>
                <label>
                  Phông chữ
                  <select
                    aria-label="Phông chữ"
                    value={item.style?.fontFamily ?? 'Arial'}
                    onChange={(e) =>
                      edit((i) => {
                        i.style = {
                          ...i.style,
                          fontFamily: e.target.value as 'Arial' | 'Segoe UI',
                        };
                      })
                    }
                  >
                    <option>Arial</option>
                    <option>Segoe UI</option>
                  </select>
                </label>
                {(['x', 'y', 'strokeWidth'] as const)
                  .filter(
                    (key) =>
                      key === 'strokeWidth' ||
                      project.templateRef.id !== 'TPL-02' ||
                      !['song-title', 'artist-name'].includes(
                        item.role ?? item.id,
                      ),
                  )
                  .map((key) => (
                    <label key={key}>
                      {key === 'x'
                        ? 'Vị trí chữ ngang'
                        : key === 'y'
                          ? 'Vị trí chữ dọc'
                          : 'Độ dày viền'}
                      <input
                        aria-label={key}
                        type="number"
                        min={key === 'strokeWidth' ? 0 : -1920}
                        max={key === 'strokeWidth' ? 10 : 1920}
                        value={item.style?.[key] ?? 0}
                        onChange={(e) =>
                          edit((i) => {
                            i.style = {
                              ...i.style,
                              [key]: Number(e.target.value),
                            };
                          })
                        }
                      />
                    </label>
                  ))}
                <label>
                  Màu viền
                  <input
                    type="color"
                    value={item.style?.strokeColor ?? '#000000'}
                    onChange={(e) =>
                      edit((i) => {
                        i.style = { ...i.style, strokeColor: e.target.value };
                      })
                    }
                  />
                </label>
                <label>
                  <input
                    type="checkbox"
                    checked={item.style?.shadow !== false}
                    onChange={(e) =>
                      edit((i) => {
                        i.style = { ...i.style, shadow: e.target.checked };
                      })
                    }
                  />
                  Đổ bóng chữ
                </label>
              </>
            )}
            <label>
              Vị trí bắt đầu (giây)
              <input
                aria-label="Vị trí bắt đầu"
                type="number"
                min="0"
                step="0.1"
                value={item.startTicks / TICKS}
                onChange={(e) =>
                  edit((i) => {
                    i.startTicks = Math.round(Number(e.target.value) * TICKS);
                  })
                }
              />
            </label>
            <label>
              Thời lượng clip (giây)
              <input
                aria-label="Thời lượng clip"
                type="number"
                min="0.1"
                step="0.1"
                value={item.durationTicks / TICKS}
                onChange={(e) =>
                  edit((i) => {
                    i.durationTicks = Math.round(
                      Number(e.target.value) * TICKS,
                    );
                  })
                }
              />
            </label>
            {['audio', 'video'].includes(item.type) && (
              <>
                <label>
                  Cắt từ nguồn (giây)
                  <input
                    aria-label="Cắt từ nguồn"
                    type="number"
                    min="0"
                    step="0.1"
                    value={item.sourceStartTicks / TICKS}
                    onChange={(e) =>
                      edit((i) => {
                        i.sourceStartTicks = Math.round(
                          Number(e.target.value) * TICKS,
                        );
                      })
                    }
                  />
                </label>
                {item.type === 'audio' && (
                  <label>
                    Âm lượng
                    <input
                      aria-label="Âm lượng"
                      type="range"
                      min="0"
                      max="2"
                      step="0.05"
                      value={item.volume}
                      onChange={(e) =>
                        edit((i) => {
                          i.volume = Number(e.target.value);
                        })
                      }
                    />
                  </label>
                )}
              </>
            )}
            <button className="remove-clip" onClick={remove}>
              Gỡ clip khỏi project
            </button>
          </>
        ) : (
          <p className="muted">Chọn clip trên timeline để chỉnh sửa.</p>
        )}
        <label>
          Định dạng xuất
          <select
            aria-label="Định dạng xuất"
            value={`${project.preset.width}x${project.preset.height}-${project.preset.fps}`}
            onChange={(e) => {
              const value = PRESETS.find(
                (p) => `${p.width}x${p.height}-${p.fps}` === e.target.value,
              );
              if (value) preset(value);
            }}
          >
            {PRESETS.map((p) => (
              <option
                key={`${p.width}x${p.height}-${p.fps}`}
                value={`${p.width}x${p.height}-${p.fps}`}
              >
                {p.width} × {p.height} · {p.fps} FPS
              </option>
            ))}
          </select>
        </label>
      </fieldset>
    </aside>
  );
}
