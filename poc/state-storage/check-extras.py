"""New catalog/type guard plus positive archive regression; no crash-suite rerun."""
import json
import importlib.util
import argparse
from pathlib import Path

from storage import SANDBOX, decoded, inspect_package, owned, validate_project

parser=argparse.ArgumentParser(); parser.add_argument('--run-id',default='run-01'); args=parser.parse_args()
assert args.run_id and all(c in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in args.run_id)
directory = owned(SANDBOX / args.run_id)
catalog = {a['path']:a for a in decoded((directory/'catalog.json').read_bytes())}
bindings = decoded((directory/'binding-fixtures.json').read_bytes())
before=None; archived=directory/'source-snapshot/storage.py'
if archived.exists():
    spec=importlib.util.spec_from_file_location('trusted_storage_snapshot',archived)
    before=importlib.util.module_from_spec(spec); spec.loader.exec_module(before)
accepted_before=0 if before else None
for row in bindings:
    if before:
        try: before.validate_project(row['bad'],catalog); accepted_before+=1
        except ValueError: pass
    validate_project(row['good'],catalog)
    try: validate_project(row['bad'],catalog); raise AssertionError('Wrong MIME binding accepted')
    except ValueError as error: assert str(error)=='Asset kind/MIME mismatch'
packages = sorted((directory/'packages').glob('*.pocpkg'))
assert len(packages)==10
for package in packages: inspect_package(package)
result={'all_passed':True,'valid_bindings':len(bindings),'wrong_mime_bindings_rejected':len(bindings),
        'old_guard_accepted_invalid_bindings':accepted_before,'existing_positive_packages_validated':len(packages)}
(directory/'extra-results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result))
