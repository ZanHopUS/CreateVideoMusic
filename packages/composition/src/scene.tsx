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
  line,
}: {
  item: TimelineItem;
  assets: Record<string, string>;
  fps: number;
  line?: ProjectContent['lyrics'][number];
}) {
  const localFrame = useCurrentFrame();
  const style = item.style ?? {};
  const seconds = localFrame / fps;
  const duration = item.durationTicks / TICKS;
  const fade = Math.min(1, seconds / 0.25, (duration - seconds) / 0.25);
  const entrance = Math.min(1, seconds / 0.35);
  const animation: React.CSSProperties = {
    opacity: style.animation === 'fade' ? Math.max(0, fade) : 1,
    transform:
      style.animation === 'slide'
        ? `translateY(${(1 - entrance) * 70}px)`
        : style.animation === 'scale'
          ? `scale(${0.85 + entrance * 0.15})`
          : undefined,
  };
  const mediaStyle: React.CSSProperties = {
    width: '100%',
    height: '100%',
    objectFit: style.fit ?? 'cover',
    objectPosition: `${style.cropX ?? 50}% ${style.cropY ?? 50}%`,
    filter: `blur(${style.blur ?? 0}px) brightness(${style.brightness ?? 1})`,
    ...animation,
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
        volume={
          item.volume * (style.animation === 'fade' ? Math.max(0, fade) : 1)
        }
      />
    );
  if (
    item.type === 'text' ||
    (item.type === 'lyrics' && line?.status === 'reviewed')
  )
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
          textShadow: style.shadow === false ? 'none' : '0 2px 12px #000a',
          WebkitTextStroke: `${style.strokeWidth ?? 0}px ${style.strokeColor ?? '#000000'}`,
          paintOrder: 'stroke fill',
          ...animation,
        }}
      >
        {line
          ? line.alignmentStatus === 'word' && line.words.length
            ? line.words.map((word, index) => {
                const now =
                  item.sourceStartTicks + ((localFrame * TICKS) / fps) * rate;
                return (
                  <React.Fragment key={index}>
                    <span
                      style={{
                        color:
                          now >= word.startTicks && now < word.endTicks
                            ? (style.highlightColor ?? '#a3b7ff')
                            : undefined,
                      }}
                    >
                      {word.text}
                    </span>{' '}
                  </React.Fragment>
                );
              })
            : line.text
          : item.text}
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
  const titleItem = project.items.find(
    (i) => (i.role ?? i.id) === 'song-title',
  );
  const artistItem = project.items.find(
    (i) => (i.role ?? i.id) === 'artist-name',
  );
  const title = titleItem?.text || 'Tên bài hát';
  const artist = artistItem?.text || 'Tên nghệ sĩ';
  const metadataStyle = (
    item: TimelineItem | undefined,
    size: number,
  ): React.CSSProperties => {
    const style = item?.style ?? {};
    const seconds = frame / project.preset.fps;
    const local = seconds - (item?.startTicks ?? 0) / TICKS;
    const duration = (item?.durationTicks ?? project.durationTicks) / TICKS;
    const intro = Math.max(0, Math.min(1, local / 0.35));
    return {
      fontSize: style.fontSize ?? size,
      fontFamily: style.fontFamily ?? 'Segoe UI',
      color: style.color ?? '#ffffff',
      textShadow: style.shadow === false ? 'none' : '0 2px 12px #000a',
      WebkitTextStroke: `${style.strokeWidth ?? 0}px ${style.strokeColor ?? '#000000'}`,
      paintOrder: 'stroke fill',
      opacity:
        local < 0 || local >= duration
          ? 0
          : style.animation === 'fade'
            ? Math.max(0, Math.min(1, local / 0.25, (duration - local) / 0.25))
            : 1,
      transform:
        style.animation === 'slide'
          ? `translateY(${(1 - intro) * 70}px)`
          : style.animation === 'scale'
            ? `scale(${0.85 + intro * 0.15})`
            : undefined,
    };
  };
  const cardVisible = Boolean(cover && frame >= cardStart);
  const music = project.items.find(
    (i) =>
      i.type === 'audio' &&
      (frame * TICKS) / project.preset.fps >= i.startTicks &&
      (frame * TICKS) / project.preset.fps < i.startTicks + i.durationTicks,
  );
  const progress = music
    ? Math.min(
        100,
        Math.max(
          0,
          (((frame * TICKS) / project.preset.fps - music.startTicks) * 100) /
            music.durationTicks,
        ),
      )
    : 0;
  const musicCard = cardVisible && (
    <AbsoluteFill
      style={{
        background:
          'linear-gradient(180deg, #11182977, #101220ee 58%, #101220)',
        alignItems: 'center',
        justifyContent: 'flex-end',
        paddingBottom: project.preset.height * 0.06,
        color: '#fff',
        fontFamily: 'Segoe UI, Arial, sans-serif',
      }}
    >
      <div
        style={{
          boxSizing: 'border-box',
          width: Math.min(
            project.preset.width * 0.75,
            project.preset.height * 0.63,
          ),
          padding: 36,
          borderRadius: 32,
          background: '#171b2be8',
          boxShadow: '0 24px 75px #0008',
        }}
      >
        <Img
          src={assets[cover!.assetId!]}
          style={{
            width: '100%',
            display: 'block',
            aspectRatio: '1',
            objectFit: 'cover',
            borderRadius: 22,
          }}
        />
        <div
          style={{
            ...metadataStyle(titleItem, 45),
            fontWeight: 700,
            marginTop: 28,
            overflowWrap: 'anywhere',
          }}
        >
          {title}
        </div>
        <div
          style={{
            ...metadataStyle(artistItem, 30),
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
  );
  return (
    <AbsoluteFill
      style={{
        backgroundColor: '#171d2d',
        lineHeight: 1.25,
        fontWeight: 400,
        fontFamily: 'Arial',
        boxSizing: 'border-box',
      }}
    >
      {project.orderedTracks.flatMap((track) =>
        project.items
          .filter(
            (i) =>
              i.trackId === track.id &&
              !(
                project.templateRef.id === 'TPL-02' &&
                ['song-title', 'artist-name'].includes(i.role ?? i.id)
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
                  <Layer
                    item={item}
                    assets={assets}
                    fps={project.preset.fps}
                    line={project.lyrics.find((l) => l.id === item.lyricId)}
                  />
                  {item.id === cover?.id && musicCard}
                </AbsoluteFill>
              </Sequence>
            );
          }),
      )}
      <div data-frame={frame} style={{ display: 'none' }} />
    </AbsoluteFill>
  );
}
