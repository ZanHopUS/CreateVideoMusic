import React from 'react';
import {
  AbsoluteFill,
  Audio,
  Img,
  OffthreadVideo,
  Sequence,
  useCurrentFrame,
} from 'remotion';
import type { ProjectContent, TimelineItem } from '@amvs/domain';
import { TICKS } from '@amvs/domain';
export type SceneProps = {
  project: ProjectContent;
  assets: Record<string, string>;
};

function Layer({
  item,
  assets,
  fps,
}: {
  item: TimelineItem;
  assets: Record<string, string>;
  fps: number;
}) {
  const style = item.style ?? {};
  const mediaStyle: React.CSSProperties = {
    width: '100%',
    height: '100%',
    objectFit: style.fit ?? 'cover',
  };
  const rate = item.speed.numerator / item.speed.denominator;
  const trim = (item.sourceStartTicks * fps) / TICKS;
  if (item.type === 'image')
    return <Img src={assets[item.assetId!]} style={mediaStyle} />;
  if (item.type === 'video')
    return (
      <OffthreadVideo
        src={assets[item.assetId!]}
        muted
        style={mediaStyle}
        trimBefore={trim}
        playbackRate={rate}
      />
    );
  if (item.type === 'audio')
    return (
      <Audio
        src={assets[item.assetId!]}
        trimBefore={trim}
        playbackRate={rate}
        volume={item.volume}
      />
    );
  if (item.type === 'text')
    return (
      <div
        style={{
          position: 'absolute',
          left: style.x ?? 56,
          top: style.y ?? 850,
          right: 56,
          fontFamily: style.fontFamily ?? 'Arial',
          fontSize: style.fontSize ?? 54,
          color: style.color ?? '#ffffff',
          whiteSpace: 'pre-wrap',
          overflowWrap: 'anywhere',
          textShadow: '0 2px 12px #000a',
        }}
      >
        {item.text}
      </div>
    );
  return null;
}
export function ProjectScene({ project, assets }: SceneProps) {
  const frame = useCurrentFrame();
  const cardImages = project.items
    .filter((i) => i.type === 'image')
    .sort((a, b) => a.startTicks - b.startTicks);
  const cover = project.templateRef.id === 'TPL-02' ? cardImages[1] : undefined;
  const cardStart = cover
    ? Math.round((cover.startTicks * project.preset.fps) / TICKS)
    : 0;
  const title =
    project.items.find((i) => i.id === 'song-title')?.text || 'Tên bài hát';
  const artist =
    project.items.find((i) => i.id === 'artist-name')?.text || 'Tên nghệ sĩ';
  const cardVisible = Boolean(cover && frame >= cardStart);
  const progress = cover
    ? Math.min(
        100,
        Math.max(
          0,
          ((frame - cardStart) * 100) /
            Math.max(
              1,
              Math.ceil((project.durationTicks * project.preset.fps) / TICKS) -
                cardStart,
            ),
        ),
      )
    : 0;
  return (
    <AbsoluteFill style={{ backgroundColor: '#171d2d' }}>
      {project.orderedTracks.flatMap((track) =>
        project.items
          .filter(
            (i) =>
              i.trackId === track.id &&
              !(
                project.templateRef.id === 'TPL-02' &&
                ['song-title', 'artist-name'].includes(i.id)
              ),
          )
          .map((item) => {
            const start = Math.round(
              (item.startTicks * project.preset.fps) / TICKS,
            );
            const end = Math.round(
              ((item.startTicks + item.durationTicks) * project.preset.fps) /
                TICKS,
            );
            return (
              <Sequence
                key={item.id}
                from={start}
                durationInFrames={Math.max(1, end - start)}
                layout="none"
              >
                <AbsoluteFill>
                  <Layer item={item} assets={assets} fps={project.preset.fps} />
                </AbsoluteFill>
              </Sequence>
            );
          }),
      )}
      {cardVisible && (
        <AbsoluteFill
          style={{
            background:
              'linear-gradient(180deg, #11182977, #101220ee 58%, #101220)',
            alignItems: 'center',
            justifyContent: 'flex-end',
            paddingBottom: 120,
            color: '#fff',
            fontFamily: 'Segoe UI, Arial, sans-serif',
          }}
        >
          <div
            style={{
              width: 520,
              padding: 36,
              borderRadius: 32,
              background: '#171b2be8',
              boxShadow: '0 24px 75px #0008',
            }}
          >
            <Img
              src={assets[cover!.assetId!]}
              style={{
                width: 448,
                height: 448,
                objectFit: 'cover',
                borderRadius: 22,
              }}
            />
            <div
              style={{
                fontSize: 45,
                fontWeight: 700,
                marginTop: 28,
                overflowWrap: 'anywhere',
              }}
            >
              {title}
            </div>
            <div
              style={{
                fontSize: 30,
                color: '#d5d9e8',
                marginTop: 10,
                overflowWrap: 'anywhere',
              }}
            >
              {artist}
            </div>
            <div
              style={{
                height: 9,
                borderRadius: 9,
                background: '#ffffff44',
                marginTop: 34,
              }}
            >
              <div
                style={{
                  height: '100%',
                  width: `${progress}%`,
                  borderRadius: 9,
                  background: '#a3b7ff',
                }}
              />
            </div>
          </div>
        </AbsoluteFill>
      )}
      <div data-frame={frame} style={{ display: 'none' }} />
    </AbsoluteFill>
  );
}
