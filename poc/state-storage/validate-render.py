"""Verify that portable restores remain usable as layered renderer inputs."""
import json
import argparse
from pathlib import Path

import av
import numpy as np

from storage import SANDBOX, owned

parser=argparse.ArgumentParser(); parser.add_argument('--output-name',default='render-check'); parser.add_argument('--run-id',default='run-01'); args=parser.parse_args()
assert args.output_name and all(c in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in args.output_name)
assert args.run_id and all(c in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in args.run_id)
directory=owned(SANDBOX/args.run_id/args.output_name)
cases=json.loads((directory/'results.json').read_text(encoding='utf-8'))
def image(path):
    with av.open(str(path)) as c: return next(c.decode(video=0)).to_ndarray(format='rgb24')
def psnr(a,b):
    assert a.shape==b.shape
    mse=float(np.mean((a.astype(np.float32)-b.astype(np.float32))**2))
    return 100 if mse==0 else float(10*np.log10(255**2/mse))
results=[]
for case in cases:
    folder=directory/case['id']; decoded={}; count=errors=0
    with av.open(str(folder/'restored.mp4')) as c:
        assert c.streams.video[0].codec_context.name=='h264' and c.streams.audio[0].codec_context.name=='aac'
        duration=c.duration/av.time_base
        for f in c.decode(video=0):
            if abs(float(f.pts*f.time_base)-count/30)>.000001: errors+=1
            if count in case['frames']: decoded[count]=f.to_ndarray(format='rgb24')
            count+=1
    with av.open(str(folder/'restored.mp4')) as c: assert sum(f.samples for f in c.decode(audio=0))>0
    checks=[{'frame':n,'before_restored_png_psnr':psnr(image(folder/f'before-{n}.png'),image(folder/f'restored-{n}.png')),
             'restored_png_mp4_psnr':psnr(image(folder/f'restored-{n}.png'),decoded[n])} for n in case['frames']]
    passed=count==360 and errors==0 and abs(duration-12)<1/30 and all(c['before_restored_png_psnr']>=60 and c['restored_png_mp4_psnr']>=30 for c in checks)
    results.append({'id':case['id'],'all_passed':passed,'decoded_frames':count,'timestamp_errors':errors,'duration_s':duration,'comparisons':checks})
(directory/'validation.json').write_text(json.dumps({'all_passed':all(r['all_passed'] for r in results),'cases':results},indent=2),encoding='utf-8')
print(json.dumps(results))
assert all(r['all_passed'] for r in results)
