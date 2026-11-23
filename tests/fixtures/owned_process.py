"""Tiny real child tree for supervisor cancellation; no media/model allocation."""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(120)"])
Path(sys.argv[1]).write_text(json.dumps({"parent": os.getpid(), "child": child.pid}))
time.sleep(120)
