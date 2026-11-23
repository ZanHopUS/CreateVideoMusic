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
  return (
    <AbsoluteFill style={{ backgroundColor: '#171d2d' }}>
      {project.orderedTracks.flatMap((track) =>
        project.items
          .filter((i) => i.trackId === track.id)
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
      <div data-frame={frame} style={{ display: 'none' }} />
    </AbsoluteFill>
  );
}
