#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
# Copyright (C) 2026 reverse-engineered-printer contributors
"""Review or remove only the dedicated ML-1865 installation.

Requires separate administrator approval for --apply. Refuses modified files,
unrecognised queue configuration, unexpected files, symlinks, and pending jobs.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

DEST = Path("/Library/Printers/ML1865")
QUEUE = "Samsung_ML1865_ARM64"
FILES = {"filter/rastertoqpdl", "ppd/Samsung-ML-1865.ppd",
         "licenses/SpliX-COPYING", "licenses/JBIG-KIT-COPYING"}
FILTER = str(DEST / "filter/rastertoqpdl")
QUEUE_PPD = Path("/etc/cups/ppd") / (QUEUE + ".ppd")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def preflight():
    if DEST.is_symlink() or not DEST.is_dir():
        raise RuntimeError("No ordinary installation directory exists: " + str(DEST))
    entries = list(DEST.rglob("*"))
    if any(path.is_symlink() for path in entries):
        raise RuntimeError("Refusing an installation containing symlinks")
    actual = {str(path.relative_to(DEST)) for path in entries if path.is_file()}
    if actual != FILES | {"install-receipt.json"}:
        raise RuntimeError("Unexpected or missing files; removal requires manual review")
    receipt = json.loads((DEST / "install-receipt.json").read_text())
    if receipt["new_directory"] != str(DEST) or receipt["new_queue"] != QUEUE or set(receipt["files"]) != FILES:
        raise RuntimeError("Receipt does not describe this exact installation")
    for name in FILES:
        if digest(DEST / name) != receipt["file_sha256"][name]:
            raise RuntimeError("Installed file has changed: " + name)
    subprocess.run(["/usr/bin/lpstat", "-r"], check=True, stdout=subprocess.PIPE)
    queue = subprocess.run(["/usr/bin/lpstat", "-p", QUEUE], capture_output=True)
    exists = queue.returncode == 0
    if exists:
        content = QUEUE_PPD.read_text()
        if '*ModelName: "Samsung ML-1865"' not in content or FILTER not in content:
            raise RuntimeError("Queue no longer uses this project's ML-1865 PPD/filter")
        device = subprocess.check_output(["/usr/bin/lpstat", "-v", QUEUE], text=True).strip().split(": ", 1)[1]
        if hashlib.sha256(device.encode()).hexdigest() != receipt["device_uri_sha256"]:
            raise RuntimeError("Queue device changed since installation")
        pending = subprocess.check_output(["/usr/bin/lpstat", "-W", "not-completed", "-o", QUEUE], text=True)
        if pending.strip():
            raise RuntimeError("Queue has pending jobs; finish or cancel them before removal")
    return exists


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    print(json.dumps({"queue_to_remove": QUEUE, "directory_to_remove": str(DEST),
                      "files": sorted(FILES | {"install-receipt.json"}),
                      "unrelated_queues_and_files": "untouched"}, indent=2))
    if not DEST.exists():
        print("Nothing is installed; no changes made.")
        return
    if args.apply and os.geteuid() != 0:
        raise RuntimeError("Removal requires root privileges and prior administrator approval")
    queue_exists = preflight()
    if not args.apply:
        print("Removal preflight passed. No changes made.")
        return
    if queue_exists:
        subprocess.run(["/usr/sbin/lpadmin", "-x", QUEUE], check=True)
    # Fixed allowlist only. Never recursively delete arbitrary directories.
    for name in sorted(FILES):
        (DEST / name).unlink()
    (DEST / "install-receipt.json").unlink()
    for name in ("filter", "ppd", "licenses"):
        (DEST / name).rmdir()
    DEST.rmdir()
    print("Removed only the dedicated queue and this project's installed files.")


if __name__ == "__main__":
    main()
