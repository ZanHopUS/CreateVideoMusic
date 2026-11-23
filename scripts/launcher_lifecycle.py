"""Windows launcher ownership: one instance, no inherited secret or orphan tree."""

import ctypes
import hashlib
import json
import os
import subprocess
from ctypes import wintypes
from pathlib import Path

import psutil


class AlreadyRunning(RuntimeError):
    pass


class WindowsOwnership:
    def __init__(self, root):
        if os.name != "nt":
            raise RuntimeError("Launcher hiện hỗ trợ Windows 11.")
        self.root = Path(root).resolve()
        self.kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        k = self.kernel
        k.CreateMutexW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR]
        k.CreateMutexW.restype = wintypes.HANDLE
        k.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
        k.CreateJobObjectW.restype = wintypes.HANDLE
        k.SetInformationJobObject.argtypes = [
            wintypes.HANDLE,
            ctypes.c_int,
            ctypes.c_void_p,
            wintypes.DWORD,
        ]
        k.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        k.CloseHandle.argtypes = [wintypes.HANDLE]
        k.ReleaseMutex.argtypes = [wintypes.HANDLE]
        name = "Local\\AMVS-" + hashlib.sha256(str(self.root).lower().encode()).hexdigest()[:24]
        self.mutex = k.CreateMutexW(None, True, name)
        if not self.mutex:
            raise ctypes.WinError(ctypes.get_last_error())
        if ctypes.get_last_error() == 183:
            k.CloseHandle(self.mutex)
            self.mutex = None
            raise AlreadyRunning(
                "Studio đang chạy. Dùng ./scripts/start.ps1 -Restart để mở phiên mới."
            )
        self.job = None
        try:

            class Basic(ctypes.Structure):
                _fields_ = [
                    ("processTime", ctypes.c_longlong),
                    ("jobTime", ctypes.c_longlong),
                    ("flags", wintypes.DWORD),
                    ("minimum", ctypes.c_size_t),
                    ("maximum", ctypes.c_size_t),
                    ("active", wintypes.DWORD),
                    ("affinity", ctypes.c_size_t),
                    ("priority", wintypes.DWORD),
                    ("scheduling", wintypes.DWORD),
                ]

            class IO(ctypes.Structure):
                _fields_ = [
                    (name, ctypes.c_ulonglong)
                    for name in (
                        "readOps",
                        "writeOps",
                        "otherOps",
                        "readBytes",
                        "writeBytes",
                        "otherBytes",
                    )
                ]

            class Extended(ctypes.Structure):
                _fields_ = [
                    ("basic", Basic),
                    ("io", IO),
                    ("processMemory", ctypes.c_size_t),
                    ("jobMemory", ctypes.c_size_t),
                    ("peakProcessMemory", ctypes.c_size_t),
                    ("peakJobMemory", ctypes.c_size_t),
                ]

            info = Extended()
            info.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            self.job = k.CreateJobObjectW(None, None)
            if not self.job or not k.SetInformationJobObject(
                self.job, 9, ctypes.byref(info), ctypes.sizeof(info)
            ):
                raise ctypes.WinError(ctypes.get_last_error())
        except BaseException:
            self.close()
            raise

    def launch(self, args, **options):
        # Assign before the primary thread runs: the venv launcher cannot create
        # an untracked Python child in the Popen-to-job-assignment interval.
        process = subprocess.Popen(args, creationflags=0x00000004, **options)  # CREATE_SUSPENDED
        try:
            if not self.kernel.AssignProcessToJobObject(self.job, int(process._handle)):
                raise ctypes.WinError(ctypes.get_last_error())
            self._resume(process.pid)
            return process
        except BaseException:
            process.kill()
            process.wait(timeout=10)
            raise

    def _resume(self, pid):
        class ThreadEntry(ctypes.Structure):
            _fields_ = [
                ("size", wintypes.DWORD),
                ("usage", wintypes.DWORD),
                ("threadId", wintypes.DWORD),
                ("processId", wintypes.DWORD),
                ("basePriority", wintypes.LONG),
                ("deltaPriority", wintypes.LONG),
                ("flags", wintypes.DWORD),
            ]

        k = self.kernel
        k.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
        k.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
        k.Thread32First.argtypes = [wintypes.HANDLE, ctypes.POINTER(ThreadEntry)]
        k.Thread32Next.argtypes = [wintypes.HANDLE, ctypes.POINTER(ThreadEntry)]
        k.OpenThread.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        k.OpenThread.restype = wintypes.HANDLE
        k.ResumeThread.argtypes = [wintypes.HANDLE]
        k.ResumeThread.restype = wintypes.DWORD
        snapshot = k.CreateToolhelp32Snapshot(4, 0)
        if snapshot == ctypes.c_void_p(-1).value:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            entry = ThreadEntry()
            entry.size = ctypes.sizeof(entry)
            more = k.Thread32First(snapshot, ctypes.byref(entry))
            while more:
                if entry.processId == pid:
                    thread = k.OpenThread(2, False, entry.threadId)
                    if not thread:
                        raise ctypes.WinError(ctypes.get_last_error())
                    try:
                        if k.ResumeThread(thread) != 1:
                            raise RuntimeError("Không resume được tiến trình con an toàn.")
                    finally:
                        k.CloseHandle(thread)
                    return
                more = k.Thread32Next(snapshot, ctypes.byref(entry))
            raise RuntimeError("Không tìm thấy primary thread của owned child.")
        finally:
            k.CloseHandle(snapshot)

    def close(self):
        if self.job:
            self.kernel.CloseHandle(self.job)
            self.job = None
        if self.mutex:
            self.kernel.ReleaseMutex(self.mutex)
            self.kernel.CloseHandle(self.mutex)
            self.mutex = None


def record_path(root):
    return Path(root) / ".local/runtime/launcher.json"


def write_owner(root):
    process = psutil.Process()
    target = record_path(root)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps({"pid": process.pid, "created": process.create_time()}), encoding="utf-8"
    )


def stop_owner(root):
    root = Path(root).resolve()
    record = record_path(root)
    if not record.is_file():
        return False
    data = json.loads(record.read_text())
    try:
        process = psutil.Process(data["pid"])
    except psutil.NoSuchProcess:
        return False
    if abs(process.create_time() - data["created"]) > 0.001:
        return False
    cwd = Path(process.cwd()).resolve()
    expected = (root / "scripts/dev.py").resolve()
    matches = any(
        Path(cwd / arg).resolve() == expected
        for arg in process.cmdline()
        if Path(arg).name == "dev.py"
    )
    if cwd != root or not matches or not process.name().lower().startswith("python"):
        raise RuntimeError("Không dừng PID không khớp launcher của workspace.")
    # Terminate only the verified handle owner. The Job Object closes API/Next
    # descendants atomically; a browser opened by the launcher is not job-owned
    # and may contain unrelated user tabs, so do not kill its PID tree here.
    process.terminate()
    try:
        process.wait(timeout=5)
    except psutil.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)
    return True
