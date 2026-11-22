import React from 'react';
import {
  AbsoluteFill, Audio, Composition, Img, OffthreadVideo, registerRoot,
  staticFile, useCurrentFrame, useVideoConfig,
} from 'remotion';

const art = (first, second) => `data:image/svg+xml,${encodeURIComponent(
  `<svg xmlns="http://www.w3.org/2000/svg" width="720" height="1280"><defs><linearGradient id="g" x2="1" y2="1"><stop stop-color="${first}"/><stop offset="1" stop-color="${second}"/></linearGradient></defs><rect width="720" height="1280" fill="url(#g)"/><circle cx="360" cy="480" r="200" fill="white" opacity="0.12"/></svg>`,
)}`;

export function Fixture({template}) {
  const frame = useCurrentFrame();
  const {width, height, fps, durationInFrames} = useVideoConfig();
  const unit = Math.min(width, height);
  const words = ['Đây', 'là', 'lời', 'thử', 'nghiệm', 'tiếng', 'Việt'];
  const active = Math.floor(frame / fps * 2) % words.length;
  return <AbsoluteFill style={{backgroundColor: '#102036', color: 'white', fontFamily: 'Arial'}}>
    {template === 'TPL03'
      ? <OffthreadVideo src={staticFile('background.mp4')} muted style={{width, height, objectFit: 'cover'}} />
      : <Img src={art('#142938', '#634078')} style={{width, height, objectFit: 'cover'}} />}
    <Audio src={staticFile('control.wav')} volume={0.3} />
    <AbsoluteFill style={{padding: unit * 0.08, background: 'rgba(0,0,0,0.2)', justifyContent: 'space-between'}}>
      <div style={{fontSize: unit * 0.035}}>PoC local • {template} • Dữ liệu tự tạo</div>
      {template === 'TPL02' ? <div style={{padding: unit * 0.06, borderRadius: 24, backgroundColor: '#192132'}}>
        <Img src={art('#357775', '#d38166')} style={{width: unit * 0.28, height: unit * 0.28, borderRadius: 16}} />
        <h1 style={{fontSize: unit * 0.055}}>Bản nhạc kiểm thử</h1>
        <p style={{fontSize: unit * 0.03}}>Âm thanh tổng hợp • Không phải bài hát thật</p>
        <div style={{height: 8, background: '#555'}}><div style={{height: 8, width: `${frame / durationInFrames * 100}%`, background: '#8ce5c3'}} /></div>
      </div> : <div style={{fontSize: unit * 0.065, fontWeight: 700, lineHeight: 1.5, textShadow: '0 2px 5px black'}}>
        {template === 'TPL03' ? words.map((word, index) => <span key={index} style={{color: index === active ? '#ffee77' : 'white'}}>{word} </span>)
          : 'Tạo video âm nhạc\nKiểm tra đầy đủ dấu tiếng Việt'}
      </div>}
      <div style={{fontSize: unit * 0.025}}>Fixture tổng hợp — chưa đánh giá chất lượng lyrics AI</div>
    </AbsoluteFill>
    {frame % (fps * 5) === 0 && <div style={{position: 'absolute', top: 0, right: 0, width: 20, height: 20, background: 'white'}} />}
  </AbsoluteFill>;
}

function Root() {
  return <>{['TPL01', 'TPL02', 'TPL03'].map(template => <Composition
    key={template} id={template} component={Fixture}
    width={720} height={1280} fps={30} durationInFrames={450}
    defaultProps={{template, width: 720, height: 1280, fps: 30, seconds: 15}}
    calculateMetadata={({props}) => ({width: props.width, height: props.height,
      fps: props.fps, durationInFrames: Math.round(props.seconds * props.fps)})}
  />)}</>;
}

registerRoot(Root);
