#!/usr/bin/env bash
set -euo pipefail
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
# Pass version arguments to build a subset, e.g. bash compileVersionsMacLinux.sh 3.14.
if [ "$#" -eq 0 ]; then
    set -- 3.9 3.10 3.11 3.12 3.13 3.14
fi
for python_version in "$@"; do
    build_root="$(mktemp -d "${TMPDIR:-/tmp}/doces-python.XXXXXX")"
    conda create --yes --prefix "$build_root/python" --override-channels -c conda-forge "python=$python_version" pip
    conda run --prefix "$build_root/python" --no-capture-output python "$project_dir/build-scripts/build_and_test.py" --output-dir "$project_dir/dist"
    conda env remove --yes --prefix "$build_root/python"
done
