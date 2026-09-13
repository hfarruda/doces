#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
python_executable="${PYTHON:-python}"
python_executable="$("$python_executable" -c 'import sys; print(sys.executable)')"
"$python_executable" -m pip install --editable "$project_dir"

tutorial_dir="$(mktemp -d "${TMPDIR:-/tmp}/doces-example.XXXXXX")"
trap 'rm -rf -- "$tutorial_dir"' EXIT
cd -- "$tutorial_dir"
"$python_executable" "$project_dir/docs/tutorial/example.py"
