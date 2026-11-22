export const probeFrames = [0, 1, 29, 30, 31, 59, 60, 89, 90, 119, 120, 149, 150,
  179, 180, 181, 209, 210, 239, 240, 269, 270, 299, 300, 329, 330, 359];

export function makeProjects() {
  return ['TPL01', 'TPL02', 'TPL03'].map(template => {
    const background = template === 'TPL03' ? [
      {id: 'video-fast', type: 'video', asset: 'cfr.mp4', start: 30, duration: 150, sourceStart: 60, speed: 1.25, z: 0},
      {id: 'video-slow-vfr', type: 'video', asset: 'vfr.mp4', start: 180, duration: 150, sourceStart: 96, speed: .8, z: 0},
    ] : [{id: 'image-base', type: 'image', asset: 'image.svg', start: 0, duration: 360, z: 0},
      ...(template === 'TPL02' ? [{id: 'image-alpha', type: 'image', asset: 'alpha.png', start: 30,
        duration: 300, z: 2, box: [520, 210, 240, 240]}] : [])];
    const music = {id: 'music', type: 'audio', asset: 'control.wav', start: 0, duration: 360,
      sourceStart: template === 'TPL01' ? 30 : 0, speed: template === 'TPL01' ? .8 : template === 'TPL02' ? 1.25 : 1};
    const lyrics = Array.from({length: 4}, (_, i) => ({id: `lyric-${i}`, type: 'lyrics',
      start: i * 90, duration: 90, text: `Đây là lời thử nghiệm tiếng Việt ${i + 1}`, z: 5}));
    const captionCount = 12 - background.length - 1 - lyrics.length;
    const captions = Array.from({length: captionCount}, (_, i) => ({id: `caption-${i}`, type: 'caption',
      start: i * 60, duration: 75, text: `Bản nháp gốc — Lớp ${i + 1}`, z: 8 + i}));
    return {schemaVersion: 'poc-fidelity-1', id: template, template, width: 1280, height: 720,
      fps: 30, durationInFrames: 360, items: [...background, music, ...lyrics, ...captions],
      markerFrames: template === 'TPL01' ? [150, 338] : template === 'TPL02' ? [0, 120, 240] : [0, 150, 300]};
  });
}
