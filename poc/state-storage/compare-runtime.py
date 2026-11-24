"""Matched JSON-runtime vs SQLite working-state round trips; not manual save."""
import json
import argparse
import os
import statistics
import time

from storage import SANDBOX, Runtime, decoded, digest, encoded, owned, validate_assets, validate_project

parser=argparse.ArgumentParser(); parser.add_argument('--run-id',default='run-01'); args=parser.parse_args()
assert args.run_id and all(c in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in args.run_id)
directory=owned(SANDBOX/args.run_id)
fixtures=decoded((directory/'state-fixtures.json').read_bytes())
catalog={a['path']:a for a in decoded((directory/'catalog.json').read_bytes())}
target=directory/'comparison'; target.mkdir(exist_ok=False)
db=Runtime(target/'runtime.sqlite'); db.register(catalog)
rows=[]
for case in fixtures['cases']:
    validate_assets(case['initial'],catalog,directory/'library')
    times={'json':[],'sqlite':[]}
    for n in range(5):
        project=case['initial'] if n%2==0 else case['edited']
        for backend in (['json','sqlite'] if n%2==0 else ['sqlite','json']):
            began=time.perf_counter()
            if backend=='json':
                validate_project(project,catalog)
                path=owned(target/f"{case['id']}.json"); stage=owned(target/f"{case['id']}.stage")
                body={'revision':n+1,'project':project,'hash':digest(project)}
                with stage.open('wb') as file: file.write(encoded(body)); file.flush(); os.fsync(file.fileno())
                os.replace(stage,path)
                loaded=decoded(path.read_bytes())
                assert digest(loaded['project'])==loaded['hash'] and loaded['project']==project
            else:
                db.save(project,catalog); assert db.load(project['id'])==project
            times[backend].append((time.perf_counter()-began)*1000)
    rows.append({'id':case['id'],'samples_per_backend':5,
        **{backend:{'median_ms':statistics.median(values),'min_ms':min(values),'max_ms':max(values)} for backend,values in times.items()}})
db.close()
result={'all_passed':True,'cases':rows,'scope':'working state only, assets verified before timing; warm exploratory five samples; no app/driver choice'}
(directory/'comparison-results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result))
