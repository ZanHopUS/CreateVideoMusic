import type { ProjectContent } from '@amvs/domain';
import type { Asset } from '../lib/api';
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
}: {
  project: ProjectContent;
  selected: string;
  select: (id: string) => void;
  move: (id: string, start: number) => void;
  seek: (frame: number) => void;
  assets: Asset[];
}) {
  return (
    <section className="timeline">
      <header>
        <strong>Timeline</strong>
        <span>
          {(project.durationTicks / TICKS).toFixed(1)} giây ·{' '}
          {project.preset.fps} FPS
        </span>
      </header>
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
          <label>{names[track.kind]}</label>
          <div className="track-items">
            {project.items
              .filter((i) => i.trackId === track.id)
              .map((item) => (
                <button
                  key={item.id}
                  data-clip-id={item.id}
                  aria-label={
                    item.type === 'text'
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
                    document.addEventListener('pointerup', up, { once: true });
                  }}
                >
                  {item.type === 'text'
                    ? item.text
                    : `${item.type === 'audio' ? '♫' : item.type === 'video' ? '▶' : '▧'} ${assets.find((a) => a.id === item.assetId)?.name ?? 'Media'}`}
                </button>
              ))}
          </div>
        </div>
      ))}
      <p>
        Kéo clip để đổi vị trí · Chọn clip để chỉnh đoạn nguồn và thời lượng
      </p>
    </section>
  );
}
