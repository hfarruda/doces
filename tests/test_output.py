"""Check native diagnostic output through the installed extension."""

import subprocess
import sys
import unittest


class DiagnosticOutputTests(unittest.TestCase):
    def run_simulation(self, *, directed, verbose, unbuffered=False):
        script = """
import doces

simulator = doces.Opinion_dynamics(
    3, [[0, 1], [1, 2], [2, 0]], directed={directed}, verbose={verbose},
)
simulator.simulate_dynamics(
    number_of_iterations=10, b=[-0.5, 0.0, 0.5], feed_size=2,
    phi=0.0, mu=0.2, posting_filter=doces.COSINE,
    receiving_filter=doces.COSINE,
    rewire=False, rand_seed=42, verbose={verbose},
)
del simulator
print("AFTER_CLEANUP", flush=True)
""".format(directed=directed, verbose=verbose)
        result = subprocess.run(
            [sys.executable] + (["-u"] if unbuffered else []) + ["-c", script],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        self.assertEqual(result.returncode, 0, result.stderr.decode(errors="replace"))
        return result.stdout

    def test_cleanup_finishes_progress_line(self):
        for directed in (True, False):
            for unbuffered in (True, False):
                with self.subTest(directed=directed, unbuffered=unbuffered):
                    output = self.run_simulation(
                        directed=directed, verbose=True, unbuffered=unbuffered,
                    )
                    # Preserve bare carriage returns so a missing newline fails.
                    # Windows can translate the newline after the progress CR
                    # into CRLF, producing CRCRLF in native stdout.
                    output = output.replace(b"\r\r\n", b"\n").replace(b"\r\n", b"\n")
                    self.assertIn(b"Inverted edge list:\n", output)
                    heading = b"Directed" if directed else b"Undirected"
                    self.assertIn(heading + b" network with 3 nodes.\n", output)
                    self.assertTrue(output.endswith(b"100%\nAFTER_CLEANUP\n"), output)

    def test_quiet_simulation_emits_no_cleanup_output(self):
        output = self.run_simulation(directed=True, verbose=False)
        self.assertEqual(output.replace(b"\r\n", b"\n"), b"AFTER_CLEANUP\n")


if __name__ == "__main__":
    unittest.main()
