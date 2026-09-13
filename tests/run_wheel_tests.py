"""Test an installed DOCES wheel with minimum and latest compatible NumPy 2."""

from pathlib import Path
import subprocess
import sys


def run(*args):
    subprocess.run([sys.executable, *args], check=True)


def main():
    tests = Path(__file__).resolve().parent
    minimum = "2.0.0" if sys.version_info < (3, 13) else (
        "2.1.0" if sys.version_info < (3, 14) else "2.3.3"
    )
    for requirement in ("numpy==" + minimum, "numpy>=2,<3"):
        run("-m", "pip", "install", "--upgrade", "--only-binary=:all:", requirement)
        run("-c", "import sys, numpy, doces, doces_core; "
            "print(sys.version); print('NumPy', numpy.__version__); "
            "print('DOCES', doces.__file__); print('Extension', doces_core.__file__)")
        run("-m", "pip", "check")
        run("-m", "unittest", "discover", "-s", str(tests), "-v")
        run(str(tests.parent / "docs" / "tutorial" / "example.py"))
        run(str(tests.parent / "docs" / "tutorial" / "custom_filters.py"))


if __name__ == "__main__":
    main()
