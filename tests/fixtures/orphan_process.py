"""Exit root unexpectedly while an inherited child remains alive."""

import json
import os
import subprocess
import sys
from pathlib import Path

child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(120)"])
Path(sys.argv[1]).write_text(json.dumps({"child": child.pid}))
os._exit(int(sys.argv[2]))
