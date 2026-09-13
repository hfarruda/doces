"""Build an sdist and wheel, then test the installed wheel outside the checkout.

Run with the Python interpreter to test. Build and runtime environments are
temporary; --output-dir optionally keeps the tested distribution artifacts.
"""

import argparse
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
import venv


def run(*command, cwd):
    print("Running:", " ".join(map(str, command)), flush=True)
    child_env = os.environ.copy()
    child_env.pop("PYTHONPATH", None)
    if sys.platform == "darwin":
        # Match the interpreter when Intel and ARM Conda environments coexist.
        child_env.setdefault("ARCHFLAGS", "-arch " + platform.machine())
    subprocess.run(list(map(str, command)), cwd=str(cwd), env=child_env, check=True)


def environment(path):
    venv.EnvBuilder(with_pip=True).create(str(path))
    return path / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = args.output_dir.resolve() if args.output_dir else None
    with tempfile.TemporaryDirectory(prefix="doces-build-") as directory:
        work = Path(directory)
        source = work / "source"
        source.mkdir()
        for name in ("setup.py", "pyproject.toml", "requirements.txt", "MANIFEST.in", "README.md", "LICENSE"):
            shutil.copy2(root / name, source / name)
        shutil.copytree(root / "doces", source / "doces", ignore=shutil.ignore_patterns("__pycache__", "*.so", "*.pyd"))
        shutil.copytree(root / "tests", source / "tests", ignore=shutil.ignore_patterns("__pycache__"))
        (source / "docs" / "tutorial").mkdir(parents=True)
        shutil.copy2(root / "docs" / "tutorial" / "example.py", source / "docs" / "tutorial" / "example.py")
        shutil.copy2(root / "docs" / "tutorial" / "custom_filters.py", source / "docs" / "tutorial" / "custom_filters.py")
        builder = environment(work / "builder")
        run(builder, "-m", "pip", "install", "build", cwd=work)
        # With no --wheel/--sdist flag, build creates the wheel from the sdist.
        run(builder, "-m", "build", "--outdir", work / "dist", source, cwd=work)
        wheel, = (work / "dist").glob("*.whl")
        runtime = environment(work / "runtime")
        run(runtime, "-m", "pip", "install", wheel, cwd=work)
        shutil.copytree(source / "tests", work / "tests")
        shutil.copytree(source / "docs", work / "docs")
        run(runtime, "tests/run_wheel_tests.py", cwd=work)
        if output:
            output.mkdir(parents=True, exist_ok=True)
            for artifact in (work / "dist").iterdir():
                shutil.copy2(artifact, output / artifact.name)
        print("Source distribution, installed wheel, and tutorial checks passed.", flush=True)


if __name__ == "__main__":
    main()
