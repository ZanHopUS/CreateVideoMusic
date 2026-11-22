import React, {useEffect, useRef, useState} from 'react';
import {createRoot} from 'react-dom/client';
import {Player} from '@remotion/player';
import {FidelityScene} from './scene.jsx';
import {makeProjects} from './projects.mjs';

const tick = () => new Promise(resolve => requestAnimationFrame(resolve));
function App() {
  const [project, setProject] = useState(makeProjects()[0]);
  const player = useRef(null);
  useEffect(() => {
    window.__poc = {
      load: async value => {setProject(value); await tick(); await tick();},
      seek: async frame => {
        const began = performance.now();
        player.current.pause(); player.current.seekTo(frame);
        const deadline = began + 5000;
        for (;;) {
          await tick();
          const videos = [...document.querySelectorAll('video')];
          const ready = window.__fidelityFrame?.frame === frame && videos.every(v => !v.seeking && v.readyState >= 2)
            && [...document.images].every(img => img.complete && img.naturalWidth > 0);
          if (ready) {await tick(); await tick(); break;}
          if (performance.now() > deadline) throw new Error(`Seek timeout at ${frame}`);
        }
        await document.fonts.ready;
        return {...window.__fidelityFrame, elapsedMs: performance.now() - began,
          videos: [...document.querySelectorAll('video')].map(v => ({src: v.currentSrc.split('/').pop(), time: v.currentTime}))};
      },
      playFor: async milliseconds => {
        let count = 0;
        const listener = () => count++;
        player.current.addEventListener('frameupdate', listener);
        player.current.seekTo(0); const began = performance.now(); player.current.play();
        await new Promise(resolve => setTimeout(resolve, milliseconds)); player.current.pause();
        player.current.removeEventListener('frameupdate', listener);
        return {elapsedMs: performance.now() - began, frameEvents: count};
      },
    };
  }, []);
  return <Player ref={player} component={FidelityScene} inputProps={{project}}
    compositionWidth={project.width} compositionHeight={project.height} fps={project.fps}
    durationInFrames={project.durationInFrames} style={{width: project.width, height: project.height}}
    controls={false} initiallyMuted loop acknowledgeRemotionLicense />;
}
createRoot(document.getElementById('root')).render(<App />);
