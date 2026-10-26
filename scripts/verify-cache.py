#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
# Copyright (C) 2026 reverse-engineered-printer contributors
"""Offline regression for SpliX's 30-page cache; sends nothing to USB."""
import json
import os
from pathlib import Path
import re
import subprocess
import verify


def main():
    out = verify.OUT
    pdf = out / "cache-34-pages.pdf"
    raster = out / "cache-34-pages.raster"
    qpdl = out / "cache-34-pages.qpdl"
    verify.make_pdf(pdf, pages=34)
    options = "PageSize=Letter Resolution=600dpi ColorModel=Gray Duplex=DuplexNoTumble"
    with raster.open("wb") as target, (out / "cache-rasterization.log").open("wb") as log:
        subprocess.run(["/usr/sbin/cupsfilter", "-p", str(verify.PPD), "-i", "application/pdf",
                        "-m", "application/vnd.cups-raster", "-o", "PageSize=Letter", "-o", "Resolution=600dpi",
                        "-o", "ColorModel=Gray", "-o", "Duplex=DuplexNoTumble", str(pdf)],
                       stdout=target, stderr=log, check=True, timeout=120)
    with qpdl.open("wb") as target, (out / "cache-conversion.log").open("wb") as log:
        subprocess.run([str(verify.BINARY), "2", "printer-test", "offline-cache-regression", "1", options, str(raster)],
                       env=dict(os.environ, PPD=str(verify.PPD), TMPDIR=str(out)), stdout=target,
                       stderr=log, check=True, timeout=60)
    pages = verify.inspect_qpdl(qpdl.read_bytes(), verify.BUILD / "test-tools/jbgtopbm85")
    verify.check(len(pages) == 34, "Some cache-regression pages are missing")
    log = (out / "cache-conversion.log").read_text()
    order = [int(value) for value in re.findall(r"^PAGE: (\d+) ", log, re.M)]
    expected = list(range(34, 0, -2)) + list(range(1, 34, 2))
    verify.check(order == expected, "Manual-duplex cache order differs")
    verify.check(not list(out.glob("splixV2-page*")), "Cache swap files were not cleaned up")
    result = {"pages": len(pages), "cache_capacity": 30, "compression": "0x15",
              "manual_duplex_order": order, "all_bands_independently_decoded": True,
              "cache_files_cleaned_up": True, "physical_print_test": False}
    (out / "cache-verification.json").write_text(json.dumps(result, indent=2) + "\n")
    # This generated raster is large and no longer needed; retain logs and QPDL evidence.
    raster.unlink()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
