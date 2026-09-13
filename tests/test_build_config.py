"""Source-only checks for the extension's platform-specific build commands."""

import contextlib
import importlib.util
import io
import os
from pathlib import Path
import runpy
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(
    (ROOT / "setup.py").is_file() and importlib.util.find_spec("setuptools"),
    "requires the source checkout and setuptools",
)
class BuildConfigTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from setuptools import Distribution
        from setuptools.command.build_ext import build_ext
        from setuptools._distutils.unixccompiler import UnixCCompiler

        cls.distribution_class = Distribution
        cls.base_build_ext = build_ext
        cls.compiler_class = UnixCCompiler
        previous_directory = Path.cwd()
        try:
            os.chdir(ROOT)
            with mock.patch("setuptools.setup") as setup, contextlib.redirect_stdout(io.StringIO()):
                runpy.run_path(str(ROOT / "setup.py"))
            cls.build_ext_class = setup.call_args.kwargs["cmdclass"]["build_ext"]
        finally:
            os.chdir(previous_directory)

    def build_command(self, platform_name, flags, compiler_type="unix"):
        command = self.build_ext_class(self.distribution_class())
        compiler = self.compiler_class(force=True)
        compiler.compiler_type = compiler_type
        compiler.set_executables(linker_so=flags, compiler_so=["clang", "-O3", "-funroll-loops"])
        compiler.linker_so_cxx = list(flags)
        command.compiler = compiler
        with mock.patch("platform.system", return_value=platform_name):
            with mock.patch.object(self.base_build_ext, "build_extensions") as build:
                command.build_extensions()
        build.assert_called_once_with()
        self.assertEqual(compiler.compiler_so, ["clang", "-O3", "-funroll-loops"])
        return compiler

    def test_macos_link_command_preserves_search_order_and_other_flags(self):
        flags = [
            "clang", "-bundle", "-Wl,-rpath,/conda/lib", "-L/conda/lib",
            "-Wl,-rpath,/other/lib", "-Wl,-rpath,/conda/lib", "-L/conda/lib",
            "-O3", "-Wl,-rpath,/other/lib",
        ]
        expected = [
            "clang", "-bundle", "-Wl,-rpath,/conda/lib", "-L/conda/lib",
            "-Wl,-rpath,/other/lib", "-L/conda/lib", "-O3",
        ]
        compiler = self.build_command("Darwin", flags)
        self.assertEqual(compiler.linker_so_cxx, expected)
        # Older setuptools uses spawn; current versions use call. Capture both
        # without executing a compiler or creating a shared library.
        commands = []
        with mock.patch.object(compiler, "spawn", side_effect=commands.append):
            with mock.patch.object(compiler, "call", side_effect=commands.append, create=True):
                with mock.patch.object(compiler, "mkpath"), mock.patch.dict(os.environ, {"ARCHFLAGS": ""}):
                    compiler.link_shared_object(["example.o"], "example.so")
        self.assertEqual(commands, [expected + ["example.o", "-o", "example.so"]])
        self.assertEqual(flags.count("-Wl,-rpath,/conda/lib"), 2)

    def test_other_platforms_and_compilers_keep_their_flags(self):
        flags = ["cc", "-Wl,-rpath,/lib", "-Wl,-rpath,/lib"]
        for platform_name, compiler_type in (("Linux", "unix"), ("Windows", "msvc"), ("Darwin", "other")):
            with self.subTest(platform=platform_name, compiler=compiler_type):
                compiler = self.build_command(platform_name, flags, compiler_type)
                self.assertEqual(compiler.linker_so, flags)
                self.assertEqual(compiler.linker_so_cxx, flags)

    def test_combined_linker_options_are_preserved(self):
        combined = "-Wl,-rpath,/lib,-dead_strip"
        flags = ["clang", combined, combined]
        compiler = self.build_command("Darwin", flags)
        self.assertEqual(compiler.linker_so, flags)


if __name__ == "__main__":
    unittest.main()
