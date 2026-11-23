"""PoC reference/pin gate; no production retention or automatic cleanup policy."""
from storage import asset_path, load_manual, owned, references


def pins(runtime, library, manual=(), recovery=(), templates=(), jobs=()):
    protected = runtime.pins() | set(jobs)
    for path in [*manual, *recovery]: protected |= references(load_manual(path, library)['project'])
    for template in templates: protected |= references(template['project'])
    return protected


def collect(candidates, catalog, library, protected, confirmed=False):
    if not confirmed: raise PermissionError('Managed asset deletion needs explicit confirmation')
    removed = []
    library = owned(library)
    for name in candidates:
        asset_path(name)
        if name in protected: continue
        if name not in catalog: raise ValueError('Unknown managed asset')
        target = owned(library / name)
        if not target.is_relative_to(library) or target.is_symlink(): raise ValueError('Managed path escape')
        target.unlink(); removed.append(name)
    return removed
