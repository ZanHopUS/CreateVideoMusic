import React from 'react';
import {AbsoluteFill, Audio, Composition, Img, Loop, OffthreadVideo, registerRoot,
  staticFile, useCurrentFrame, useVideoConfig} from 'remotion';

const art = (first, second) => `data:image/svg+xml,${encodeURIComponent(
  `<svg xmlns="http://www.w3.org/2000/svg" width="720" height="1280"><defs><linearGradient id="g" x2="1" y2="1"><stop stop-color="${first}"/><stop offset="1" stop-color="${second}"/></linearGradient></defs><rect width="720" height="1280" fill="url(#g)"/><circle cx="360" cy="480" r="200" fill="white" opacity=".12"/></svg>`
)}`;

function StressFixture({template = 'TPL03'}) {
  const frame = useCurrentFrame();
  const {fps, width, height, durationInFrames} = useVideoConfig();
  const unit = Math.min(width, height);
  const words = ['Đây', 'là', 'lời', 'thử', 'nghiệm', 'tiếng', 'Việt'];
  const active = Math.floor(frame / fps * 2) % words.length;
  return <AbsoluteFill style={{backgroundColor: '#102036', color: 'white', fontFamily: 'Arial'}}>
    {template === 'TPL03' ? <Loop durationInFrames={15 * fps} layout="none">
      <OffthreadVideo src={staticFile('background.mp4')} muted
        style={{width, height, objectFit: 'cover'}} />
    </Loop> : <Img src={art('#142938', '#634078')} style={{width, height, objectFit: 'cover'}} />}
    <Audio src={staticFile('control.wav')} volume={0.3} />
    <AbsoluteFill style={{padding: unit * .08, background: 'rgba(0,0,0,.2)', justifyContent: 'space-between'}}>
      <div style={{fontSize: unit * .035}}>PoC 300 giây • {template === 'TPL03' ? 'Video nền lặp' : template} • Dữ liệu tự tạo</div>
      {template === 'TPL02' ? <div style={{padding: unit * .06, borderRadius: 24, backgroundColor: '#192132'}}>
        <div style={{display: 'flex', gap: unit * .04}}>
          <Img src={art('#357775', '#d38166')} style={{width: unit * .28, height: unit * .28, borderRadius: 16, objectFit: 'cover'}} />
          <Img src={art('#73558d', '#b0b872')} style={{width: unit * .28, height: unit * .28, borderRadius: 16, objectFit: 'cover'}} />
        </div>
        <h1 style={{fontSize: unit * .055}}>Bản nhạc kiểm thử</h1>
        <p style={{fontSize: unit * .03}}>Hai ảnh • Âm thanh tổng hợp</p>
        <div style={{height: 8, background: '#555'}}>
          <div style={{height: 8, width: `${frame / durationInFrames * 100}%`, background: '#8ce5c3'}} />
        </div>
      </div> : <div style={{fontSize: unit * .065, fontWeight: 700, lineHeight: 1.5, textShadow: '0 2px 5px black'}}>
        {template === 'TPL01' ? 'Tạo video âm nhạc — Kiểm tra đầy đủ dấu tiếng Việt' :
          words.map((word, index) => <span key={index}
            style={{color: index === active ? '#ffee77' : 'white'}}>{word} </span>)}
      </div>}
      <div style={{fontSize: unit * .03}}>
        {(frame / fps).toFixed(2)} / {(durationInFrames / fps).toFixed(2)} giây
        <div style={{height: 8, marginTop: 12, background: '#555'}}>
          <div style={{height: 8, width: `${frame / durationInFrames * 100}%`, background: '#8ce5c3'}} />
        </div>
      </div>
    </AbsoluteFill>
    {frame % (fps * 5) === 0 && <div style={{position: 'absolute', top: 0, right: 0,
      width: 20, height: 20, backgroundColor: 'white'}} />}
  </AbsoluteFill>;
}

function Root() {
  return <>{['TPL01', 'TPL02', 'TPL03'].map(template => <Composition key={template} id={`${template}Stress`} component={StressFixture}
    width={1080} height={1920} fps={60} durationInFrames={18000}
    defaultProps={{template, width: 1080, height: 1920, fps: 60, seconds: 300}}
    calculateMetadata={({props}) => ({width: props.width, height: props.height,
      fps: props.fps, durationInFrames: props.seconds * props.fps})} />)}</>;
}
registerRoot(Root);
