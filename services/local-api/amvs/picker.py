"""Native local picker, fixed entrypoint. Paths are returned only to the API parent."""

import json
import os
import sys
import tkinter as tk
from tkinter import filedialog


def main():
    root = tk.Tk()
    root.withdraw()
    try:
        if "--smoke" in sys.argv:
            root.update()
            print(json.dumps({"tk": "available", "nativeDialogInteraction": "not-tested"}))
            return
        if "--open" in sys.argv:
            selected = filedialog.askopenfilename(
                title="Mở project đã lưu",
                filetypes=[("Project AMVS", "*.amvs.json")],
                parent=root,
                initialdir=os.environ.get("AMVS_PICKER_INITIAL_DIR"),
            )
        else:
            selected = filedialog.askdirectory(
                title="Chọn thư mục lưu video/project",
                mustexist=True,
                parent=root,
                initialdir=os.environ.get("AMVS_PICKER_INITIAL_DIR"),
            )
        print(json.dumps({"path": selected or None}, ensure_ascii=False))
    finally:
        root.destroy()


if __name__ == "__main__":
    main()
