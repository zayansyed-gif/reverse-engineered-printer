#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
# Copyright (C) 2026 reverse-engineered-printer contributors
"""Install only this project's filter and add a new dedicated queue.

Run without --apply to review the plan. --apply requires administrator approval
and root privileges; existing installation directories and queues are refused.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / "build/stage/Library/Printers/ML1865"
DEST = Path("/Library/Printers/ML1865")
QUEUE = "Samsung_ML1865_ARM64"
FILES = {"filter/rastertoqpdl", "ppd/Samsung-ML-1865.ppd",
         "licenses/SpliX-COPYING", "licenses/JBIG-KIT-COPYING"}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def plan():
    entries = list(STAGE.rglob("*"))
    if any(path.is_symlink() for path in entries):
        raise RuntimeError("Symlink in installation staging directory")
    if {str(path.relative_to(STAGE)) for path in entries if path.is_file()} != FILES:
        raise RuntimeError("Unexpected installation files; only the filter, ML-1865 PPD, and two licenses are permitted")
    evidence = json.loads((ROOT / "build/build-evidence.json").read_text())
    tests = json.loads((ROOT / "artifacts/verification.json").read_text())
    if not tests["arm64"] or tests["jbig_upstream_tests"] != "passed" or not tests["qpdl"]:
        raise RuntimeError("Complete scripts/verify.py successfully before installing.")
    binary = STAGE / "filter/rastertoqpdl"
    ppd = STAGE / "ppd/Samsung-ML-1865.ppd"
    if sha256(binary) != evidence["filter_sha256"] or sha256(ppd) != evidence["ppd_sha256"]:
        raise RuntimeError("Staged artifacts differ from the verified build.")
    if sha256(binary) != tests.get("filter_sha256") or sha256(ppd) != tests.get("ppd_sha256"):
        raise RuntimeError("Offline tests do not cover these exact staged artifacts.")
    if subprocess.check_output(["/usr/bin/lipo", "-archs", str(binary)], text=True).strip() != "arm64":
        raise RuntimeError("Filter is not exclusively ARM64.")
    subprocess.run(["/usr/bin/codesign", "--verify", "--strict", str(binary)], check=True)
    return {
        "new_directory": str(DEST), "new_queue": QUEUE, "model": "Samsung ML-1865",
        "filter_sha256": sha256(binary), "ppd_sha256": sha256(ppd),
        "files": [str(path.relative_to(STAGE)) for path in sorted(STAGE.rglob("*")) if path.is_file()],
        "file_sha256": {str(path.relative_to(STAGE)): sha256(path)
                        for path in sorted(STAGE.rglob("*")) if path.is_file()},
        "defaults": {"PageSize": "Letter", "Resolution": "600dpi", "Duplex": "None", "printer-is-shared": "false"},
        "existing_queues": "untouched", "system_default_printer": "not changed",
    }


def apply(installation):
    if os.geteuid() != 0:
        raise RuntimeError("Administrator privileges are required. Review the plan and approve before running with sudo.")
    if DEST.exists() or DEST.is_symlink():
        raise RuntimeError("Refusing to replace an existing installation: " + str(DEST))
    subprocess.run(["/usr/bin/lpstat", "-r"], check=True, stdout=subprocess.PIPE)
    existing = subprocess.run(["/usr/bin/lpstat", "-p", QUEUE], capture_output=True)
    if existing.returncode == 0:
        raise RuntimeError("Refusing to modify an existing queue: " + QUEUE)
    devices = subprocess.check_output(["/usr/sbin/lpinfo", "-v"], text=True)
    matches = [line.split(None, 1)[1] for line in devices.splitlines()
               if line.startswith("direct usb://Samsung/ML-1860%20Series")]
    if len(matches) != 1:
        raise RuntimeError("Expected one USB ML-1860-family device for the physically confirmed ML-1865; found " + str(len(matches)))
    uri = matches[0]
    # This private root-owned directory is new; nothing under protected /usr is changed.
    DEST.mkdir(mode=0o755)
    os.chown(DEST, 0, 0)
    for source in sorted(STAGE.rglob("*")):
        relative = source.relative_to(STAGE)
        target = DEST / relative
        if source.is_symlink():
            raise RuntimeError("Symlink in installation staging directory")
        if source.is_dir():
            target.mkdir(mode=0o755)
        else:
            shutil.copyfile(source, target)
            os.chmod(target, 0o555 if relative.parts[0] == "filter" else 0o644)
        os.chown(target, 0, 0)
    if sha256(DEST / "filter/rastertoqpdl") != installation["filter_sha256"]:
        raise RuntimeError("Installed binary checksum mismatch")
    subprocess.run(["/usr/bin/codesign", "--verify", "--strict", str(DEST / "filter/rastertoqpdl")], check=True)
    # Keep a removal receipt before queue creation, including when lpadmin fails.
    installation["installed"] = False
    installation["device_uri_sha256"] = hashlib.sha256(uri.encode()).hexdigest()
    installation["device_family"] = "Samsung ML-1860 Series (physical label ML-1865)"
    receipt = DEST / "install-receipt.json"
    receipt.write_text(json.dumps(installation, indent=2) + "\n")
    os.chmod(receipt, 0o644)
    subprocess.run(["/usr/sbin/lpadmin", "-p", QUEUE, "-E", "-v", uri,
                    "-P", str(DEST / "ppd/Samsung-ML-1865.ppd"),
                    "-D", "Samsung ML-1865 (Native ARM64)",
                    "-o", "printer-is-shared=false", "-o", "PageSize=Letter",
                    "-o", "Resolution=600dpi", "-o", "Duplex=None"], check=True)
    installation["installed"] = True
    receipt.write_text(json.dumps(installation, indent=2) + "\n")
    subprocess.run(["/usr/bin/lpstat", "-p", QUEUE], check=True)
    print("Installed the native filter and added " + QUEUE + ". No test page has been submitted yet.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Apply the reviewed plan; requires root and prior administrator approval")
    args = parser.parse_args()
    installation = plan()
    print(json.dumps(installation, indent=2), flush=True)
    if args.apply:
        apply(installation)


if __name__ == "__main__":
    main()
