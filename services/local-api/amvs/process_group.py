"""Per-command Windows Job Object, reusing the production launcher's primitive.

Reference: https://learn.microsoft.com/windows/win32/api/winnt/ns-winnt-jobobject_basic_process_id_list
Nested jobs: https://learn.microsoft.com/windows/win32/procthread/nested-jobs
"""

import ctypes
import importlib.util
import os
from ctypes import wintypes

import psutil

from .domain import ROOT

spec = importlib.util.spec_from_file_location(
    "amvs_product_launcher_ownership", ROOT / "scripts/launcher_lifecycle.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class OwnedGroup:
    def __init__(self, scope):
        if os.name != "nt":
            raise RuntimeError("Windows process ownership required")
        self.owner = module.WindowsOwnership(scope)

    def launch(self, args, **options):
        return self.owner.launch(args, **options)

    def members(self):
        if not self.owner.job:
            return []
        kernel = self.owner.kernel
        kernel.QueryInformationJobObject.argtypes = [
            wintypes.HANDLE,
            ctypes.c_int,
            ctypes.c_void_p,
            wintypes.DWORD,
            ctypes.POINTER(wintypes.DWORD),
        ]
        kernel.QueryInformationJobObject.restype = wintypes.BOOL
        count = 128
        while count <= 65536:

            class Pids(ctypes.Structure):
                _fields_ = [
                    ("assigned", wintypes.DWORD),
                    ("returned", wintypes.DWORD),
                    ("pids", ctypes.c_size_t * count),
                ]

            result = Pids()
            length = wintypes.DWORD()
            success = kernel.QueryInformationJobObject(
                self.owner.job, 3, ctypes.byref(result), ctypes.sizeof(result), ctypes.byref(length)
            )
            if success and result.returned >= result.assigned:
                return list(result.pids[: result.returned])
            error = ctypes.get_last_error()
            if not success and error != 234:
                raise ctypes.WinError(error)
            count = max(count * 2, result.assigned + 16)
        raise RuntimeError("Owned process list exceeds safe query budget")

    def close(self):
        members = []
        error = None
        try:
            for pid in self.members():
                try:
                    members.append(psutil.Process(pid))
                except psutil.NoSuchProcess:
                    pass
        except BaseException as failure:
            error = failure
        finally:
            self.owner.close()
        _, alive = psutil.wait_procs(members, timeout=5)
        if alive:
            raise RuntimeError("Owned child processes did not stop")
        if error:
            raise error
