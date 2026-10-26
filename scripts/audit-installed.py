#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
# Copyright (C) 2026 reverse-engineered-printer contributors
"""Read-only verification of the installed filter, exact model, and queue."""
import hashlib
import json
from pathlib import Path
import stat
import subprocess

ROOT = Path(__file__).resolve().parents[1]
DEST = Path("/Library/Printers/ML1865")
QUEUE = "Samsung_ML1865_ARM64"


def main():
    receipt = json.loads((DEST / "install-receipt.json").read_text())
    for name, expected in receipt["file_sha256"].items():
        path = DEST / name
        if path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise RuntimeError("Installed file differs from receipt: " + name)
    binary = DEST / "filter/rastertoqpdl"
    architecture = subprocess.check_output(["/usr/bin/lipo", "-archs", str(binary)], text=True).strip()
    if architecture != "arm64" or binary.stat().st_uid != 0:
        raise RuntimeError("Incorrect architecture or installed owner")
    subprocess.run(["/usr/bin/codesign", "--verify", "--strict", str(binary)], check=True)
    ppd = Path("/etc/cups/ppd") / (QUEUE + ".ppd")
    text = ppd.read_text()
    for expected in ('*ModelName: "Samsung ML-1865"', '*QPDL QPDLVersion: "5"',
                     '/cupsCompression 21', str(binary)):
        if expected not in text:
            raise RuntimeError("Installed CUPS PPD is missing " + expected)
    status = subprocess.check_output(["/usr/bin/lpstat", "-p", QUEUE], text=True).strip()
    default = subprocess.run(["/usr/bin/lpstat", "-d"], text=True, capture_output=True)
    result = {"queue": QUEUE, "model": "Samsung ML-1865", "architecture": architecture,
              "filter_sha256": receipt["filter_sha256"], "installed_file_hashes_match": True,
              "filter_mode": oct(stat.S_IMODE(binary.stat().st_mode)), "filter_owner_uid": binary.stat().st_uid,
              "qpdl_version": 5, "compression": "0x15", "queue_status": status,
              "default_printer_status": (default.stdout + default.stderr).strip()}
    (ROOT / "artifacts/installed-audit.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
