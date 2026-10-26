#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
# Copyright (C) 2026 reverse-engineered-printer contributors
"""Render a PDF, run SpliX, and independently decode its 0x15 JBIG bands.

This does not contact a printer or change CUPS configuration.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts"
BUILD = ROOT / "build"
PPD = ROOT / "ppd/Samsung-ML-1865.ppd"
BINARY = BUILD / "stage/Library/Printers/ML1865/filter/rastertoqpdl"


def check(condition, message):
    if not condition:
        raise RuntimeError(message)


def make_pdf(path, pages=1):
    objects = [b"<< /Type /Catalog /Pages 2 0 R >>", b"",
               b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    kids = []
    for page in range(pages):
        page_id = len(objects) + 1
        content_id = page_id + 1
        kids.append((str(page_id) + " 0 R").encode())
        objects.append(("<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
                        "/Resources << /Font << /F1 3 0 R >> >> /Contents %d 0 R >>" % content_id).encode())
        drawing = ["0 g", "BT /F1 24 Tf 54 720 Td (Samsung ML-1865) Tj ET",
                   "BT /F1 16 Tf 54 687 Td (Native Apple Silicon print test) Tj ET",
                   "BT /F1 12 Tf 54 655 Td (SpliX 2.0.2 - ARM64 - JBIG compression 0x15) Tj ET",
                   "BT /F1 12 Tf 54 630 Td (Test ID: ML1865-ARM64-20261025 / page %d) Tj ET" % (page + 1),
                   "54 600 504 2 re f", "BT /F1 12 Tf 54 570 Td (Text, solid black and grayscale should be visible below.) Tj ET"]
        for index in range(8):
            drawing.append("%.4f g %d 460 54 70 re f" % (index / 7.0, 54 + index * 63))
        drawing.extend(["0 g 54 420 504 1 re f", "BT /F1 12 Tf 54 390 Td (Please confirm this physical page is readable.) Tj ET"])
        stream = ("\n".join(drawing) + "\n").encode()
        objects.append(b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"endstream")
    objects[1] = b"<< /Type /Pages /Count " + str(pages).encode() + b" /Kids [" + b" ".join(kids) + b"] >>"
    pdf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for index, obj in enumerate(objects, 1):
        offsets.append(len(pdf))
        pdf.extend(str(index).encode() + b" 0 obj\n" + obj + b"\nendobj\n")
    xref = len(pdf)
    pdf.extend(("xref\n0 %d\n0000000000 65535 f \n" % len(offsets)).encode())
    for offset in offsets[1:]:
        pdf.extend(("%010d 00000 n \n" % offset).encode())
    pdf.extend(("trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(offsets), xref)).encode())
    path.write_bytes(pdf)


def inspect_qpdl(data, decoder):
    marker = b"@PJL ENTER LANGUAGE = QPDL\n"
    offset = data.index(marker) + len(marker)
    pages = []
    while offset < len(data) and data[offset] == 0:
        header = data[offset:offset + 17]
        check(len(header) == 17 and header[14] == 5, "Incorrect QPDL page version")
        check(header[1] == 6 and header[16] == 6, "Expected 600 DPI page")
        offset += 17
        bands = 0
        set_bits = 0
        if data[offset] == 0x13:
            check(data[offset + 5] == 0x15 and data[offset + 15] == 0x14, "Invalid JBIG auxiliary record")
            bih = data[offset + 16:offset + 36]
            width, height = struct.unpack(">II", bih[4:12])
            check(0 < width < 20000 and height == 128, "Unexpected JBIG band dimensions")
            offset += 40
            while data[offset] == 0x0C:
                band = data[offset:offset + 12]
                check(band[6] == 4 and band[7] == 0x15, "Expected black 0x15 band")
                size = int.from_bytes(band[8:12], "big")
                check(4 <= size <= 512 * 1024 + 4, "Invalid band length")
                payload = data[offset + 12:offset + 12 + size - 4]
                checksum = int.from_bytes(data[offset + 12 + size - 4:offset + 12 + size], "big")
                check(len(payload) == size - 4 and sum(payload) & 0xFFFFFFFF == checksum, "Band checksum mismatch")
                decoded = subprocess.run([str(decoder)], input=bih + payload, stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE, check=True, timeout=10).stdout
                pbm = re.match(rb"P4\s+(\d+)\s+(\d+)\s", decoded)
                check(pbm is not None and int(pbm[1]) == width and int(pbm[2]) == height, "JBIG decoded geometry differs")
                pixels = decoded[pbm.end():]
                check(len(pixels) == ((width + 7) // 8) * height, "Truncated decoded JBIG pixels")
                set_bits += sum(bin(value).count("1") for value in pixels)
                bands += 1
                offset += 12 + size
        check(data[offset] == 1 and len(data[offset:offset + 3]) == 3, "Missing page footer")
        offset += 3
        pages.append({"qpdl_version": header[14], "compression": "0x15", "bands": bands, "decoded_set_bits": set_bits})
    check(data[offset:] == b"\t\x1b%-12345X", "Unexpected data after final page")
    return pages


def main():
    OUT.mkdir(exist_ok=True)
    tests = BUILD / "test-tools"
    tests.mkdir(exist_ok=True)
    common = ["/usr/bin/clang", "-arch", "arm64", "-O2"]
    info = tests / "raster-info"
    subprocess.run([*common, str(ROOT / "tests/raster-info.c"), "-lcups", "-o", str(info)], check=True)
    jbig = ROOT / "vendor/jbigkit"
    decoder = tests / "jbgtopbm85"
    subprocess.run([*common, "-I", str(jbig / "libjbig"), str(jbig / "pbmtools/jbgtopbm85.c"),
                    str(BUILD / "libjbig85.a"), "-o", str(decoder)], check=True)
    codec_test = tests / "tstcodec85"
    subprocess.run([*common, "-I", str(jbig / "libjbig"), str(jbig / "libjbig/tstcodec85.c"),
                    str(BUILD / "libjbig85.a"), "-o", str(codec_test)], check=True)
    with (OUT / "jbig-codec-tests.txt").open("wb") as output:
        subprocess.run([str(codec_test)], stdout=output, stderr=subprocess.STDOUT, check=True, timeout=60)
    ppd_text = PPD.read_text()
    check('*ModelName: "Samsung ML-1865"' in ppd_text, "Wrong printer model")
    check('*QPDL QPDLVersion: "5"' in ppd_text and '/cupsCompression 21' in ppd_text, "Wrong model settings")
    with (OUT / "ppd-validation.txt").open("wb") as output:
        subprocess.run(["/usr/bin/cupstestppd", "-W", "filters", "-v", str(PPD)], stdout=output, stderr=subprocess.STDOUT, check=True)
    pdf = ROOT / "tests/test-page.pdf"
    make_pdf(pdf)
    raster = OUT / "test-page.raster"
    with raster.open("wb") as output, (OUT / "rasterization.log").open("wb") as log:
        subprocess.run(["/usr/sbin/cupsfilter", "-p", str(PPD), "-i", "application/pdf", "-m", "application/vnd.cups-raster",
                        "-o", "PageSize=Letter", "-o", "Resolution=600dpi", "-o", "ColorModel=Gray", "-o", "Duplex=None", str(pdf)],
                       stdout=output, stderr=log, check=True, timeout=60)
    raster_info = json.loads(subprocess.check_output([str(info), str(raster)], text=True))
    check(len(raster_info["pages"]) == 1, "Expected one raster page")
    for page in raster_info["pages"]:
        check(page["compression"] == 21 and page["bits_per_color"] == 1 and page["color_space"] == 3,
              "Rasterizer did not apply the ML-1865 monochrome/JBIG settings")
        check(page["set_bits"] > 1000, "Raster page appears empty")
    env = dict(os.environ, PPD=str(PPD), TMPDIR=str(OUT))
    qpdl = OUT / "test-page.qpdl"
    with qpdl.open("wb") as output, (OUT / "conversion.log").open("wb") as log:
        subprocess.run([str(BINARY), "1", "printer-test", "ML1865-ARM64-20261025", "1",
                        "PageSize=Letter Resolution=600dpi ColorModel=Gray Duplex=None", str(raster)],
                       env=env, stdout=output, stderr=log, check=True, timeout=60)
    pages = inspect_qpdl(qpdl.read_bytes(), decoder)
    check(len(pages) == 1 and pages[0]["bands"] > 0 and pages[0]["decoded_set_bits"] > 1000,
          "Encoded page has no visible decoded content")
    check(pages[0]["decoded_set_bits"] == raster_info["pages"][0]["set_bits"],
          "Encoded and input black-pixel counts differ")
    result = {"arm64": subprocess.check_output(["/usr/bin/lipo", "-archs", str(BINARY)], text=True).strip() == "arm64",
              "ppd_model": "Samsung ML-1865", "jbig_upstream_tests": "passed", "raster": raster_info,
              "qpdl": pages, "qpdl_bytes": qpdl.stat().st_size,
              "qpdl_sha256": hashlib.sha256(qpdl.read_bytes()).hexdigest(),
              "filter_sha256": hashlib.sha256(BINARY.read_bytes()).hexdigest(),
              "ppd_sha256": hashlib.sha256(PPD.read_bytes()).hexdigest(),
              "physical_print_verified": False}
    (OUT / "verification.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
