# SPDX-License-Identifier: GPL-2.0-only
# Copyright (C) 2026 reverse-engineered-printer contributors
"""Exercise installation/removal in a temporary filesystem with fake CUPS.

No administrator access, real printer calls, or /Library changes occur here.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class InstallationSafety(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.base = Path(self.directory.name)
        self.install = load("install")
        self.remove = load("uninstall")
        self.install.DEST = self.base / "Library/Printers/ML1865"
        self.install.DEST.parent.mkdir(parents=True)
        self.remove.DEST = self.install.DEST
        self.remove.FILTER = str(self.remove.DEST / "filter/rastertoqpdl")
        self.install.STAGE = ROOT / "build/stage/Library/Printers/ML1865"
        self.calls = []
        self.uri = "usb://Samsung/ML-1860%20Series?serial=TEST-ONLY"
        self.other = self.base / "unrelated-system-file"
        self.other.write_text("leave unchanged")

    def fake_run(self, args, **kwargs):
        self.calls.append(args)
        code = 1 if args[:3] == ["/usr/bin/lpstat", "-p", self.install.QUEUE] else 0
        return subprocess.CompletedProcess(args, code, b"", b"")

    def fake_output(self, args, **kwargs):
        self.calls.append(args)
        if args == ["/usr/sbin/lpinfo", "-v"]:
            return "direct " + self.uri + "\n"
        raise AssertionError("Unexpected command: " + repr(args))

    def simulate_install(self):
        plan = self.install.plan()
        with mock.patch.object(self.install.os, "geteuid", return_value=0), \
             mock.patch.object(self.install.os, "chown"), \
             mock.patch.object(self.install.subprocess, "run", side_effect=self.fake_run), \
             mock.patch.object(self.install.subprocess, "check_output", side_effect=self.fake_output):
            self.install.apply(plan)
        return plan

    def test_installs_allowlisted_files_and_only_new_queue(self):
        self.simulate_install()
        actual = {str(p.relative_to(self.install.DEST)) for p in self.install.DEST.rglob("*") if p.is_file()}
        self.assertEqual(actual, self.install.FILES | {"install-receipt.json"})
        mutations = [call for call in self.calls if call[0].endswith("lpadmin")]
        self.assertEqual(len(mutations), 1)
        self.assertEqual(mutations[0][1:4], ["-p", "Samsung_ML1865_ARM64", "-E"])
        self.assertNotIn("-d", mutations[0])
        self.assertNotIn("-x", mutations[0])
        self.assertEqual(self.other.read_text(), "leave unchanged")

    def test_refuses_existing_installation_before_queue_changes(self):
        self.install.DEST.mkdir()
        plan = self.install.plan()
        with mock.patch.object(self.install.os, "geteuid", return_value=0), \
             mock.patch.object(self.install.subprocess, "run") as run:
            with self.assertRaisesRegex(RuntimeError, "existing installation"):
                self.install.apply(plan)
            run.assert_not_called()

    def test_removal_preflight_detects_changed_or_extra_files(self):
        self.simulate_install()
        binary = self.remove.DEST / "filter/rastertoqpdl"
        binary.chmod(0o755)
        binary.write_bytes(b"modified")
        with self.assertRaisesRegex(RuntimeError, "has changed"):
            self.remove.preflight()
        extra = self.remove.DEST / "unrelated.txt"
        extra.write_text("preserve me")
        with self.assertRaisesRegex(RuntimeError, "Unexpected or missing"):
            self.remove.preflight()
        self.assertTrue(extra.exists())

    def test_removes_only_receipted_files_when_queue_is_absent(self):
        self.simulate_install()
        with mock.patch.object(self.remove.os, "geteuid", return_value=0), \
             mock.patch.object(self.remove.subprocess, "run", side_effect=self.fake_run), \
             mock.patch("sys.argv", ["uninstall.py", "--apply"]):
            self.remove.main()
        self.assertFalse(self.remove.DEST.exists())
        self.assertEqual(self.other.read_text(), "leave unchanged")

    def prepare_owned_queue(self):
        self.remove.QUEUE_PPD = self.base / "queue.ppd"
        self.remove.QUEUE_PPD.write_text('*ModelName: "Samsung ML-1865"\n*cupsFilter: "application/vnd.cups-raster 0 '
                                         + self.remove.FILTER + '"\n')

    def existing_queue_run(self, args, **kwargs):
        self.calls.append(args)
        return subprocess.CompletedProcess(args, 0, b"", b"")

    def owned_queue_output(self, args, **kwargs):
        self.calls.append(args)
        if args[:2] == ["/usr/bin/lpstat", "-v"]:
            return "device for " + self.remove.QUEUE + ": " + self.uri + "\n"
        if args[:3] == ["/usr/bin/lpstat", "-W", "not-completed"]:
            return ""
        raise AssertionError(args)

    def test_removes_only_owned_queue(self):
        self.simulate_install()
        self.prepare_owned_queue()
        self.calls.clear()
        with mock.patch.object(self.remove.os, "geteuid", return_value=0), \
             mock.patch.object(self.remove.subprocess, "run", side_effect=self.existing_queue_run), \
             mock.patch.object(self.remove.subprocess, "check_output", side_effect=self.owned_queue_output), \
             mock.patch("sys.argv", ["uninstall.py", "--apply"]):
            self.remove.main()
        mutations = [call for call in self.calls if call[0].endswith("lpadmin")]
        self.assertEqual(mutations, [["/usr/sbin/lpadmin", "-x", "Samsung_ML1865_ARM64"]])
        self.assertEqual(self.other.read_text(), "leave unchanged")

    def test_pending_jobs_block_removal(self):
        self.simulate_install()
        self.prepare_owned_queue()
        self.calls.clear()
        def output(args, **kwargs):
            if "not-completed" in args:
                return self.remove.QUEUE + "-1 pending\n"
            return self.owned_queue_output(args, **kwargs)
        with mock.patch.object(self.remove.os, "geteuid", return_value=0), \
             mock.patch.object(self.remove.subprocess, "run", side_effect=self.existing_queue_run), \
             mock.patch.object(self.remove.subprocess, "check_output", side_effect=output), \
             mock.patch("sys.argv", ["uninstall.py", "--apply"]):
            with self.assertRaisesRegex(RuntimeError, "pending jobs"):
                self.remove.main()
        self.assertTrue(self.remove.DEST.exists())
        self.assertFalse(any(call[0].endswith("lpadmin") for call in self.calls))


if __name__ == "__main__":
    unittest.main()
