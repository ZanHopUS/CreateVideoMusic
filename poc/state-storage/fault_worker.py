"""A dedicated crashable process; only disposable PoC data is accepted."""
import argparse
import json
import os
from pathlib import Path
import time

from storage import Runtime, export_package, manual_save, owned

parser = argparse.ArgumentParser()
parser.add_argument('--folder', type=Path, required=True)
parser.add_argument('--library', type=Path, required=True)
parser.add_argument('--input', type=Path, required=True)
parser.add_argument('--action', choices=['db','manual','package'], required=True)
parser.add_argument('--crash-at')
parser.add_argument('--pause-at')
args = parser.parse_args()
folder, library, input_file = owned(args.folder), owned(args.library), owned(args.input)
payload = json.loads(input_file.read_text(encoding='utf-8'))
def hook(phase):
    if phase == args.crash_at: os._exit(77)
    if phase == args.pause_at:
        (folder / 'paused.signal').write_text(phase, encoding='utf-8')
        deadline = time.monotonic() + 10
        while not (folder / 'continue.signal').exists():
            if time.monotonic() > deadline: raise TimeoutError('Parent did not release test pause')
            time.sleep(.01)
if args.action == 'db':
    runtime = Runtime(folder / 'runtime.sqlite')
    runtime.save(payload['project'], payload['catalog'], hook); runtime.close()
elif args.action == 'manual':
    manual_save(folder / 'manual.json', payload['project'], payload['catalog'], library, hook)
else:
    export_package(folder / 'new.pocpkg', payload['project'], payload['catalog'], library, hook)
