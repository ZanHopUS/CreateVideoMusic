import React, {useLayoutEffect} from 'react';
import {AbsoluteFill, Audio, Img, OffthreadVideo, Sequence, staticFile, useCurrentFrame} from 'remotion';

// sourceStart is a source-time offset in project-FPS units, not a VFR frame index.
const trimFor = item => (item.sourceStart ?? 0) + (item.seekNudgeFrames ?? 0);

function Layer({item}) {
  const frame = useCurrentFrame();
  const fade = Math.min(1, (frame + 1) / 15, (item.duration - frame) / 15);
  if (item.type === 'audio') return <Audio src={staticFile(item.asset)} playbackRate={item.speed}
    trimBefore={trimFor(item)} volume={.3} />;
  if (item.type === 'video') return <OffthreadVideo src={staticFile(item.asset)} muted
    playbackRate={item.speed} trimBefore={trimFor(item)} acceptableTimeShiftInSeconds={.001}
    style={{width: '100%', height: '100%', objectFit: 'cover'}} />;
  if (item.type === 'image') {
    const [left, top, width, height] = item.box ?? [0, 0, 1280, 720];
    return <Img src={staticFile(item.asset)} style={{position: 'absolute', left, top, width, height}} />;
  }
  if (item.type === 'lyrics') {
    const active = Math.min(7, Math.floor(frame / 12));
    return <div style={{position: 'absolute', bottom: 72, left: 48, right: 48, fontSize: 32, opacity: fade}}>
      {item.text.split(' ').map((word, i) => <span key={i} style={{color: i === active ? '#ffe66d' : 'white'}}>{word} </span>)}
    </div>;
  }
  return <div style={{position: 'absolute', top: 110 + (item.z - 8) * 30, left: 70,
    padding: '12px 22px', fontSize: 38, background: '#171b2c', opacity: fade,
    transform: `translateX(${Math.max(0, 15 - frame) * 2}px)`}}>{item.text}</div>;
}

export function FidelityScene({project}) {
  const frame = useCurrentFrame();
  const active = project.items.filter(item => frame >= item.start && frame < item.start + item.duration);
  useLayoutEffect(() => {
    window.__fidelityFrame = {frame, projectId: project.id, activeIds: active.map(item => item.id).sort()};
  }, [frame, project]);
  return <AbsoluteFill style={{background: '#101827', color: 'white', fontFamily: 'Arial'}}>
    {project.items.slice().sort((a, b) => (a.z ?? 0) - (b.z ?? 0)).map(item =>
      <Sequence key={item.id} from={item.start} durationInFrames={item.duration} layout="none">
        <AbsoluteFill style={{zIndex: item.z ?? 0}}><Layer item={item} /></AbsoluteFill>
      </Sequence>)}
    <div data-fidelity-frame={frame} style={{position: 'absolute', top: 22, left: 30, zIndex: 100,
      fontSize: 28, background: '#101827'}}>PoC • {project.template} • {frame} / {project.durationInFrames}</div>
    {project.markerFrames.includes(frame) && <div style={{position: 'absolute', right: 0, top: 0,
      width: 20, height: 20, background: 'white', zIndex: 101}} />}
  </AbsoluteFill>;
}
