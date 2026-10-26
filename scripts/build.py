#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
# Copyright (C) 2026 reverse-engineered-printer contributors
"""Build the ML-1865 raster filter from pinned source; never install anything."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build"
FILTER_PATH = "/Library/Printers/ML1865/filter/rastertoqpdl"


def run(args, **kwargs):
    print("+", " ".join(map(str, args)), flush=True)
    subprocess.run(list(map(str, args)), check=True, **kwargs)


def expand_imports(path, ancestors=()):
    if path in ancestors:
        raise RuntimeError("Cyclic driver import: " + str(path))
    output = []
    for line in path.read_text().splitlines(True):
        match = re.match(r'\s*#import\s+"([\w.\-]+)"', line)
        output.append(expand_imports(path.parent / match[1], ancestors + (path,))
                      if match else line)
    return "".join(output)


def main():
    if sys.platform != "darwin" or os.uname().machine != "arm64":
        raise SystemExit("Run this native build on an Apple Silicon Mac.")
    for tool in ("clang", "clang++", "ar", "ppdc", "lipo", "codesign"):
        if not shutil.which(tool):
            raise SystemExit("Missing Apple developer tool: " + tool)
    BUILD.mkdir(exist_ok=True)
    obj = BUILD / "objects"
    obj.mkdir(exist_ok=True)
    splix = BUILD / "splix"
    shutil.copytree(ROOT / "vendor/splix", splix, dirs_exist_ok=True)
    for patch in sorted((ROOT / "patches").glob("*.patch")):
        with patch.open("rb") as stream:
            run(["/usr/bin/patch", "--batch", "-p1", "-d", splix], stdin=stream)
    jbig = ROOT / "vendor/jbigkit/libjbig"
    common = ["-arch", "arm64", "-mmacosx-version-min=12.0", "-O2", "-g"]
    jbig_objects = []
    for name in ("jbig85", "jbig_ar"):
        target = obj / (name + ".o")
        run(["/usr/bin/clang", *common, "-I", jbig, "-c", jbig / (name + ".c"), "-o", target])
        jbig_objects.append(target)
    library = BUILD / "libjbig85.a"
    # ar replaces these members without a system installation or shared dependency.
    run(["/usr/bin/ar", "rcs", library, *jbig_objects])

    module = (splix / "src/module.mk").read_text().replace("\\\n", " ")
    source_line = next(line for line in module.splitlines() if line.startswith("rastertoqpdl_SRC"))
    sources = source_line.split("+=", 1)[1].split()
    objects = []
    for source in sources:
        target = obj / (Path(source).stem + ".o")
        run(["/usr/bin/clang++", *common, "-std=gnu++98", "-Wall", "-Wno-deprecated-declarations",
             "-DTHREADS=2", "-DCACHESIZE=30", "-I", splix / "include", "-I", jbig,
             "-c", splix / source, "-o", target])
        objects.append(target)
    stage = BUILD / "stage/Library/Printers/ML1865"
    (stage / "filter").mkdir(parents=True, exist_ok=True)
    binary = stage / "filter/rastertoqpdl"
    run(["/usr/bin/clang++", *common, "-o", binary, *objects, library, "-lcups", "-lpthread"])
    run(["/usr/bin/codesign", "--force", "--sign", "-", binary])
    run(["/usr/bin/codesign", "--verify", "--strict", binary])
    architecture = subprocess.check_output(["/usr/bin/lipo", "-archs", str(binary)], text=True).strip()
    if architecture != "arm64":
        raise RuntimeError("Unexpected binary architecture: " + architecture)
    links = subprocess.check_output(["/usr/bin/otool", "-L", str(binary)], text=True)
    for line in links.splitlines()[1:]:
        dependency = line.strip().split(" ", 1)[0]
        if not dependency.startswith(("/usr/lib/", "/System/Library/")):
            raise RuntimeError("Non-system dynamic dependency: " + dependency)
    # The upstream driver uses #import, a SpliX preprocessing extension.
    driver = BUILD / "samsung.drv"
    driver.write_text(expand_imports(splix / "ppd/samsung.drv.in"))
    ppd_dir = BUILD / "generated-ppd"
    ppd_dir.mkdir(exist_ok=True)
    run(["/usr/bin/ppdc", "-d", ppd_dir, driver])
    ppd = (ppd_dir / "ml1865.ppd").read_text()
    assert '*ModelName: "Samsung ML-1865"' in ppd
    assert '*QPDL QPDLVersion: "5"' in ppd
    assert '/cupsCompression 21' in ppd
    ppd = ppd.replace('*cupsFilter: "application/vnd.cups-raster 0 rastertoqpdl"',
                      '*cupsFilter: "application/vnd.cups-raster 0 ' + FILTER_PATH + '"')
    ppd = re.sub(r'^\*NickName:.*$', '*NickName: "Samsung ML-1865, SpliX 2.0.2 (ARM64)"', ppd, flags=re.M)
    # Preserve a dated modification notice in the generated derived PPD.
    first, rest = ppd.split("\n", 1)
    ppd = first + "\n" + '*% SPDX-License-Identifier: GPL-2.0-only\n*% Based on SpliX 2.0.2; see vendor/splix/AUTHORS and COPYING.\n*% Modified 2026-10-25 by reverse-engineered-printer contributors:\n*% absolute macOS filter path and descriptive ARM64 nickname.\n' + rest
    (ROOT / "ppd/Samsung-ML-1865.ppd").write_text(ppd)
    (stage / "ppd").mkdir(exist_ok=True)
    (stage / "ppd/Samsung-ML-1865.ppd").write_text(ppd)
    (stage / "licenses").mkdir(exist_ok=True)
    shutil.copy2(ROOT / "vendor/splix/COPYING", stage / "licenses/SpliX-COPYING")
    shutil.copy2(ROOT / "vendor/jbigkit/COPYING", stage / "licenses/JBIG-KIT-COPYING")
    evidence = {
        "architecture": architecture, "jbig": True, "compression": "0x15",
        "splix_version": "2.0.2", "jbigkit_version": "2.2",
        "filter_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
        "ppd_sha256": hashlib.sha256(ppd.encode()).hexdigest(),
        "dynamic_dependencies": links,
        "installation_path": FILTER_PATH,
        "installed": False,
    }
    (BUILD / "build-evidence.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print("Built and verified ARM64 filter and exact ML-1865 PPD. No system files changed.")


if __name__ == "__main__":
    main()
