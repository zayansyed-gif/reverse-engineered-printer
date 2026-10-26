# How the implementation works

## From a document to USB

An application submits a document to CUPS. Apple's `cgpdftoraster` turns its PDF
pages into one-bit black/white CUPS Raster according to the PPD's resolution,
paper size, margins, and color model. SpliX's native `rastertoqpdl` reads that
raster, compresses it, and emits Samsung SPL/QPDL data. Apple's existing CUPS USB
backend delivers those bytes to the printer. No new USB kernel driver is needed.

The PPD is descriptive text; the executable filter performs the conversion.
Merely copying a vendor PPD cannot replace an incompatible executable filter.

## Exact model configuration

The official SpliX 2.0.2 `ppd/samsung.drv.in` contains the **ML-1865** model. It
imports `monochrome-v3.defs`, selects QPDL version 5 and special band-width
handling, and imports manual-duplex options. The monochrome definition requests
compression 21 decimal (`0x15`) through the raster header.

`build.py` expands the upstream `#import` directives and uses Apple's `ppdc` to
generate `ml1865.ppd`. The project changes only its descriptive nickname and the
filter's absolute installation path. Resolution, margins, compression, and
model-specific settings remain upstream. The distinct ML-1865W profile is not
used. The USB device's ML-1860-family name does not override the physical model.

## JBIG and QPDL

SpliX `src/document.cpp` reads raster headers and pixels. `src/compress.cpp`
dispatches compression `0x15` to its banded JBIG path, which calls
`src/algo0x15.cpp`. This uses JBIG-KIT's T.85 encoder (`jbig85.c`) to compress each
band. `src/qpdl.cpp` writes page headers, JBIG auxiliary information, black-plane
records, band lengths, checksums, and page footers; `src/printer.cpp` supplies PJL
job framing. JBIG-KIT is statically linked, so the installed filter has no
Homebrew dependency. No `DISABLE_JBIG` flag is defined.

JBIG-KIT 2.2 was obtained from the author's official Git repository. It retains
source/ABI compatibility for the T.85 interface used here. The encoder, decoder,
and upstream T.85 codec tests were built locally from that same source.

## Native macOS build

The script compiles upstream C/C++ with Apple's compiler, explicitly selecting
ARM64. It uses the system `libcups`, C++ runtime, and pthread interfaces. The
Mac's built-in rasterizer supplies input, so the old PostScript wrapper and a
separate Ghostscript installation are unnecessary for this path.

Upstream still contains `2.0.0` in its internal version header and PPD file-version
field. Those fields remain unchanged to preserve its PPD compatibility check;
the source itself is pinned to the official **2.0.2** commit in `UPSTREAM.json`.

## Cache compatibility patch

The applied patch is the existing macOS patch from
[theshiver/apple-silicon-printer-drivers](https://github.com/theshiver/apple-silicon-printer-drivers/blob/main/build/splix-cache.patch),
with original and locally annotated patch hashes recorded in `UPSTREAM.json`.
The annotation adds a dated modification notice; the cache fix is retained. It:

- Uses CUPS's job `TMPDIR` for swap files rather than a hard-coded `/tmp`.
- Restores the requested swapped-out page before normal cache scheduling, which
  avoids stalling jobs larger than the 30-page cache.
- Prioritizes new cache entries rather than the faulty boolean alternation in
  the original controller.

The patch modifies cache management, not printer framing or JBIG compression.
The 34-page offline manual-duplex regression exercised disk swapping, decoded
every emitted band, checked page order, and confirmed swap-file cleanup.
Physical manual-duplex operation was not tested.

## Evidence and useful reading order

Start with the generated PPD, then read `src/rastertoqpdl.cpp`, `src/document.cpp`,
`src/compress.cpp`, `src/algo0x15.cpp`, `src/qpdl.cpp`, and `src/printer.cpp` under
`vendor/splix`. Compare the cache patch with the original `src/cache.cpp`.

`scripts/verify.py` is a bounded output inspector, not a replacement driver. It
parses the records generated for this test, verifies their checksums, and passes
the extracted JBIG bands to an independently compiled upstream decoder. Real
printing remains the necessary final hardware check.

The REA toolkit was not needed: the working encoder and model profile already
exist as open source. A future reverse-engineering exercise can target a specific
unsupported behavior rather than reproduce the entire driver.
