import type { ProjectContent } from '@amvs/domain';
import type { Asset } from '../lib/api';
import { useEffect, useState } from 'react';
import type { RefObject } from 'react';
import type { PlayerRef } from '@remotion/player';
import { TICKS } from '@amvs/domain';
const names = {
  background: 'Hình ảnh',
  music: 'Âm nhạc',
  text: 'Chú thích',
  lyrics: 'Lời hát',
};
export function Timeline({
  project,
  selected,
  select,
  move,
  seek,
  assets,
  zoom,
  setZoom,
  player,
  change,
  editable,
}: {
  project: ProjectContent;
  selected: string;
  select: (id: string) => void;
  move: (id: string, start: number) => void;
  seek: (frame: number) => void;
  assets: Asset[];
  zoom: number;
  setZoom: (value: number) => void;
  player: RefObject<PlayerRef | null>;
  change: (op: (p: ProjectContent) => void) => boolean;
  editable: boolean;
}) {
  const [frame, setFrame] = useState(0);
  const [kind, setKind] =
    useState<ProjectContent['orderedTracks'][number]['kind']>('text');
  useEffect(() => {
    const timer = setInterval(
      () => setFrame(player.current?.getCurrentFrame() ?? 0),
      100,
    );
    return () => clearInterval(timer);
  }, [player]);
  return (
    <section className="timeline">
      <header>
        <strong>Dòng thời gian</strong>
        <label>
          Thu phóng
          <input
            aria-label="Thu phóng timeline"
            type="range"
            min="1"
            max="8"
            step="0.5"
            value={zoom}
            onChange={(e) => setZoom(Number(e.target.value))}
          />
        </label>
        <span>
          {(project.durationTicks / TICKS).toFixed(1)} giây ·{' '}
          {project.preset.fps} FPS
        </span>
      </header>
      <div className="timeline-scroll">
        <div style={{ width: `${zoom * 100}%`, position: 'relative' }}>
          <div
            aria-label="Vị trí phát"
            style={{
              position: 'absolute',
              top: 0,
              bottom: 0,
              left: `calc(90px + ${((frame * TICKS) / project.preset.fps / project.durationTicks) * 100}% - ${((frame * TICKS) / project.preset.fps / project.durationTicks) * 90}px)`,
              width: 2,
              background: '#a3b7ff',
              pointerEvents: 'none',
              zIndex: 5,
            }}
          />
          <div
            className="ruler"
            onClick={(e) => {
              const box = e.currentTarget.getBoundingClientRect();
              seek(
                Math.round(
                  (((e.clientX - box.left) / box.width) *
                    project.durationTicks *
                    project.preset.fps) /
                    TICKS,
                ),
              );
            }}
          >
            {Array.from({ length: 6 }, (_, i) => (
              <span key={i}>
                {((i * project.durationTicks) / TICKS / 5).toFixed(1)}s
              </span>
            ))}
          </div>
          {project.orderedTracks.map((track) => (
            <div className="track" key={track.id}>
              <div className="track-label">
                <span>
                  {names[track.kind]}{' '}
                  {project.orderedTracks
                    .filter((t) => t.kind === track.kind)
                    .findIndex((t) => t.id === track.id) + 1}
                </span>
                <div>
                  {([-1, 1] as const).map((direction) => (
                    <button
                      key={direction}
                      disabled={!editable}
                      aria-label={`${direction < 0 ? 'Hạ' : 'Nâng'} lớp ${track.id}`}
                      onClick={() =>
                        change((p) => {
                          const from = p.orderedTracks.findIndex(
                              (t) => t.id === track.id,
                            ),
                            to = from + direction;
                          if (to >= 0 && to < p.orderedTracks.length)
                            [p.orderedTracks[from], p.orderedTracks[to]] = [
                              p.orderedTracks[to],
                              p.orderedTracks[from],
                            ];
                        })
                      }
                    >
                      {direction < 0 ? '↓' : '↑'}
                    </button>
                  ))}
                  {!project.items.some((i) => i.trackId === track.id) &&
                    project.orderedTracks.length > 1 && (
                      <button
                        disabled={!editable}
                        aria-label={`Gỡ lớp trống ${track.id}`}
                        onClick={() =>
                          change((p) => {
                            const index = p.orderedTracks.findIndex(
                              (t) => t.id === track.id,
                            );
                            if (index >= 0 && p.orderedTracks.length > 1)
                              p.orderedTracks.splice(index, 1);
                          })
                        }
                      >
                        ×
                      </button>
                    )}
                </div>
              </div>
              <div className="track-items">
                {project.items
                  .filter((i) => i.trackId === track.id)
                  .map((item) => (
                    <button
                      key={item.id}
                      data-clip-id={item.id}
                      aria-label={
                        item.type === 'lyrics'
                          ? `Lời ${project.lyrics.find((l) => l.id === item.lyricId)?.text ?? ''}`
                          : item.type === 'text'
                            ? `Chú thích ${item.text}`
                            : `${item.type === 'audio' ? 'Nhạc' : item.type === 'video' ? 'Video' : 'Ảnh'} ${assets.find((a) => a.id === item.assetId)?.name ?? 'Media'}`
                      }
                      className={`clip ${track.kind} ${selected === item.id ? 'selected' : ''}`}
                      style={{
                        left: `${(item.startTicks / project.durationTicks) * 100}%`,
                        width: `${(item.durationTicks / project.durationTicks) * 100}%`,
                      }}
                      onClick={() => select(item.id)}
                      onPointerDown={(event) => {
                        select(item.id);
                        const startX = event.clientX,
                          width =
                            event.currentTarget.parentElement!.getBoundingClientRect()
                              .width;
                        const up = (e: PointerEvent) => {
                          document.removeEventListener('pointerup', up);
                          const frame = project.timebase / project.preset.fps;
                          const delta =
                            Math.round(
                              (((e.clientX - startX) / width) *
                                project.durationTicks) /
                                frame,
                            ) * frame;
                          if (Math.abs(e.clientX - startX) > 3)
                            move(
                              item.id,
                              Math.max(
                                0,
                                Math.min(
                                  project.durationTicks - item.durationTicks,
                                  item.startTicks + delta,
                                ),
                              ),
                            );
                        };
                        document.addEventListener('pointerup', up, {
                          once: true,
                        });
                      }}
                    >
                      {item.type === 'lyrics'
                        ? project.lyrics.find((l) => l.id === item.lyricId)
                            ?.text
                        : item.type === 'text'
                          ? item.text
                          : `${item.type === 'audio' ? '♫' : item.type === 'video' ? '▶' : '▧'} ${assets.find((a) => a.id === item.assetId)?.name ?? 'Media'}`}
                    </button>
                  ))}
              </div>
            </div>
          ))}
        </div>
      </div>
      <div className="clip-actions">
        <select
          aria-label="Loại lớp mới"
          value={kind}
          onChange={(e) => setKind(e.target.value as typeof kind)}
        >
          {Object.entries(names).map(([key, label]) => (
            <option key={key} value={key}>
              {label}
            </option>
          ))}
        </select>
        <button
          disabled={!editable}
          onClick={() =>
            change((p) => {
              p.orderedTracks.push({ id: crypto.randomUUID(), kind });
            })
          }
        >
          Thêm lớp
        </button>
        <button
          disabled={!editable}
          onClick={() =>
            change((p) => {
              let track = p.orderedTracks.find((t) => t.kind === 'text');
              if (!track) {
                track = { id: crypto.randomUUID(), kind: 'text' };
                p.orderedTracks.push(track);
              }
              const start = Math.min(
                p.durationTicks - p.timebase / p.preset.fps,
                Math.max(
                  0,
                  Math.round(
                    ((player.current?.getCurrentFrame() ?? 0) * TICKS) /
                      p.preset.fps,
                  ),
                ),
              );
              p.items.push({
                id: crypto.randomUUID(),
                type: 'text',
                trackId: track.id,
                text: 'Chú thích mới',
                startTicks: start,
                durationTicks: Math.min(TICKS * 3, p.durationTicks - start),
                sourceStartTicks: 0,
                speed: { numerator: 1, denominator: 1 },
                volume: 1,
                style: {
                  x: p.preset.width * 0.08,
                  y: p.preset.height * 0.15,
                  fontFamily: 'Arial',
                  fontSize: 48,
                  color: '#ffffff',
                  shadow: true,
                },
              });
            })
          }
        >
          Thêm chú thích
        </button>
      </div>
      <p>
        Kéo clip để đổi vị trí · Lớp phía sau vẽ đè lên lớp phía trước · Chọn
        clip để chỉnh đoạn nguồn và thời lượng
      </p>
    </section>
  );
}
