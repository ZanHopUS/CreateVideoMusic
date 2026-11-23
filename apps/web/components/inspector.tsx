import type { ProjectContent, TimelineItem } from '@amvs/domain';
import { TICKS } from '@amvs/domain';
import type { Asset } from '../lib/api';
export function Inspector({
  project,
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
      <div className="section-label">THUỘC TÍNH</div>
      <h2>Chỉnh theo ý bạn</h2>
      <label>
        Tên project
        <input
          aria-label="Tên project"
          key={project.id}
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
                key={project.id + id}
                defaultValue={
                  project.items.find((i) => i.id === id)?.text ?? ''
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
            {item.type === 'text'
              ? 'Chú thích'
              : item.type === 'audio'
                ? 'Âm nhạc'
                : item.type === 'video'
                  ? 'Video nền'
                  : 'Hình ảnh'}
          </h3>
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
          {item.type === 'text' && (
            <>
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
                  i.durationTicks = Math.round(Number(e.target.value) * TICKS);
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
      <div className="preset-note">
        <strong>720 × 1280</strong>
        <span>9:16 · 30 FPS · MP4</span>
        <small>Preset đầu tiên của bản nội bộ.</small>
      </div>
    </aside>
  );
}
