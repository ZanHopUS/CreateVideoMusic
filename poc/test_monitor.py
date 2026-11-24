"""Admission must block child launch and distinguish completion from sampled R0."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from monitor import GIB, admission, sampled_r0


class MonitorTests(unittest.TestCase):
    def decide(self, values, count, timeout):
        tick = [0.0]
        values = iter(values)
        def sleep(seconds): tick[0] += seconds
        return admission(4 * GIB, count, timeout,
                         available=lambda: next(values), now=lambda: tick[0], sleep=sleep)

    def test_low_sample_resets_stability_window(self):
        result = self.decide([4*GIB, 3*GIB, 4*GIB, 4*GIB, 4*GIB], 3, 10)
        self.assertTrue(result['allowed'])
        self.assertEqual(len(result['samples']), 5)

    def test_timeout_does_not_admit(self):
        self.assertFalse(self.decide([3*GIB]*3, 2, 2)['allowed'])

    def test_exact_boundary_and_single_sample(self):
        self.assertTrue(self.decide([4*GIB], 1, 0)['allowed'])

    def test_successful_exit_does_not_hide_low_ram(self):
        row = {'private_bytes': GIB, 'system_available_bytes': 2*GIB}
        self.assertTrue(sampled_r0([row], None, 0))
        self.assertFalse(sampled_r0([dict(row, system_available_bytes=2*GIB-1)], None, 0))
        self.assertFalse(sampled_r0([dict(row, private_bytes=12*GIB+1)], None, 0))
        self.assertFalse(sampled_r0([row], 'cancelled', 0))
        self.assertFalse(sampled_r0([row], None, 1))
        self.assertFalse(sampled_r0([], None, 0))

    def test_cli_denial_never_launches_child(self):
        with tempfile.TemporaryDirectory(prefix='poc-admission-') as folder:
            folder = Path(folder)
            marker = folder/'child-started'
            command = [sys.executable, str(Path(__file__).with_name('monitor.py')),
                       '--out', str(folder/'evidence'), '--min-start-available-gib', '1024',
                       '--admission-timeout', '0', '--', sys.executable, '-c',
                       'from pathlib import Path; import sys; Path(sys.argv[1]).touch()', str(marker)]
            result = subprocess.run(command, capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 4, result.stderr)
            self.assertFalse(marker.exists())
            evidence = json.loads((folder/'evidence/admission.json').read_text())
            self.assertFalse(evidence['allowed'])
            self.assertFalse((folder/'evidence/resources.json').exists())
            again = subprocess.run(command, capture_output=True, text=True, timeout=15)
            self.assertEqual(again.returncode, 2)


if __name__ == '__main__':
    unittest.main()
