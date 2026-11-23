"""Exercise only windows owned by a disposable picker process; no global keys."""

import ctypes
import json
import os
import subprocess
import sys
import time
from ctypes import wintypes
from pathlib import Path

import psutil

ROOT = Path(__file__).resolve().parents[1]


def main():
    if os.name != "nt":
        raise SystemExit("Windows only")
    user = ctypes.WinDLL("user32", use_last_error=True)
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    user.EnumWindows.argtypes = [callback_type, wintypes.LPARAM]
    user.EnumChildWindows.argtypes = [wintypes.HWND, callback_type, wintypes.LPARAM]
    user.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user.GetDlgItem.argtypes = [wintypes.HWND, ctypes.c_int]
    user.GetDlgItem.restype = wintypes.HWND
    user.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    user.SendMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    user.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
    evidence = ROOT / ".local/native-picker" / str(time.time_ns())
    evidence.mkdir(parents=True)
    unicode_folder = evidence / "Thu muc — tiếng Việt"
    unicode_folder.mkdir()
    results = []
    for action in ["cancel", "select"]:
        env = dict(
            os.environ, AMVS_PICKER_INITIAL_DIR=str(unicode_folder), PYTHONIOENCODING="utf-8"
        )
        child = subprocess.Popen(
            [sys.executable, str(ROOT / "services/local-api/amvs/picker.py")],
            cwd=ROOT,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
        )
        try:
            dialog = None
            for _ in range(150):
                windows = []
                try:
                    owned_pids = {
                        child.pid,
                        *[p.pid for p in psutil.Process(child.pid).children(recursive=True)],
                    }
                except psutil.NoSuchProcess:
                    owned_pids = {child.pid}

                @callback_type
                def enum(hwnd, _):
                    pid = wintypes.DWORD()
                    user.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                    name = ctypes.create_unicode_buffer(256)
                    user.GetClassNameW(hwnd, name, 256)
                    if pid.value in owned_pids and name.value == "#32770":
                        windows.append(hwnd)
                    return True

                user.EnumWindows(enum, 0)
                if windows:
                    dialog = windows[0]
                    break
                if child.poll() is not None:
                    break
                time.sleep(0.1)
            if not dialog:
                raise RuntimeError("Native dialog not found for owned picker PID")
            # Hide the test dialog and interact only with controls in this PID.
            user.ShowWindow(dialog, 0)
            if action == "cancel":
                user.PostMessageW(dialog, 0x0010, 0, 0)
            else:
                button = user.GetDlgItem(dialog, 1)
                if not button:
                    raise RuntimeError("Owned dialog has no Select control")
                user.SendMessageW(button, 0x00F5, 0, 0)  # BM_CLICK / IDOK
            stdout, stderr = child.communicate(timeout=15)
            if child.returncode:
                raise RuntimeError("Picker process failed")
            result = json.loads(stdout)
            if action == "cancel":
                assert result["path"] is None, result
            else:
                assert Path(result["path"]).resolve() == unicode_folder.resolve(), result
            results.append(
                {"action": action, "passed": True, "unicode_path_selected": action == "select"}
            )
        finally:
            if child.poll() is None:
                child.kill()
                child.communicate(timeout=10)
    (evidence / "results.json").write_text(
        json.dumps({"all_passed": True, "cases": results}, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {"all_passed": True, "cases": len(results), "evidence": str(evidence.relative_to(ROOT))}
        )
    )


if __name__ == "__main__":
    main()
