"""Copy generated fixtures into a disposable managed library; never touch user media."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

import av

from storage import SANDBOX, asset_path, file_hash, owned

parser = argparse.ArgumentParser()
parser.add_argument('--run-id', default='run-01')
args = parser.parse_args()
assert args.run_id and all(c in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in args.run_id)
directory = owned(SANDBOX / args.run_id)
directory.mkdir(parents=True, exist_ok=False)
library = directory / 'library'
(library / 'assets').mkdir(parents=True)
source = Path(__file__).resolve().parents[2] / '.poc/render/fidelity-public'
types = {'.mp4':'video/mp4', '.wav':'audio/wav', '.png':'image/png', '.svg':'image/svg+xml'}
catalog = []
for name in ['image.svg','alpha.png','cfr.mp4','vfr.mp4','control.wav']:
    file = source / name
    sha = file_hash(file)
    relative = asset_path(f'assets/{sha}{file.suffix}')
    shutil.copy2(file, library / relative)
    entry = {'id':sha, 'path':relative, 'sha256':sha, 'bytes':file.stat().st_size,
             'mime':types[file.suffix], 'originalName':name}
    if file.suffix in ('.mp4','.wav'):
        with av.open(str(file)) as container: entry['duration_s'] = container.duration / av.time_base
    catalog.append(entry)
(directory / 'catalog.json').write_text(json.dumps(catalog, indent=2), encoding='utf-8')
archive = directory / 'source-snapshot'; archive.mkdir()
inventory = []
for file in Path(__file__).resolve().parent.iterdir():
    if file.is_file() and file.suffix in ('.py', '.mjs'):
        data = file.read_bytes(); (archive / file.name).write_bytes(data)
        inventory.append({'path':str(file.relative_to(Path(__file__).resolve().parents[2])),
                          'sha256':hashlib.sha256(data).hexdigest()})
(directory / 'source-inventory.json').write_text(json.dumps({'capture':'at preparation before execution','files':inventory},indent=2),encoding='utf-8')
print(json.dumps({'run_id': args.run_id, 'directory': str(directory), 'managed_assets':len(catalog)}))
