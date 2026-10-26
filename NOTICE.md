# Copyright, licensing, and upstream attribution

The project's integration code is distributed under GNU GPL version 2 only
(`GPL-2.0-only`), with the complete license in `LICENSE`. It is provided without
warranty. Upstream components retain their original copyright and license notices.

## SpliX 2.0.2

Source: https://github.com/OpenPrinting/splix/tree/2.0.2
Commit: `9bde257882a1ebcf15a97ff4685d34053383e3f8`.

Original authors include Aurélien Croc, Till Kamppeter, ValdikSS, and the
contributors credited in `vendor/splix/AUTHORS`, source headers, and `ChangeLog`.
The GPL version 2 license and all upstream notices remain in `vendor/splix`.
That directory is an unmodified source snapshot, including upstream PPDs.

Downstream changes, dated **2026-10-25**, are separate and reviewable:

- `patches/0001-macos-page-cache.patch` adds macOS cache compatibility and a
  prominent dated modification notice to the patched `cache.cpp` build copy.
- `scripts/build.py` supplies native Apple compiler invocations and staging.
- The derived `ppd/Samsung-ML-1865.ppd` adds an absolute installed filter path,
  an ARM64 nickname, and a dated modification/license notice. Its source is the
  included official driver definitions and the included generation script.

## JBIG-KIT 2.2

Author and source: Markus Kuhn,
https://www.cl.cam.ac.uk/~mgk25/jbigkit/ .
Commit: `802dc4c558f36b3325dac329bf3beb291962baa3` (tag `v2.2`).

The unmodified source and original notices are in `vendor/jbigkit`; its license
is GNU GPL version 2 or later (`GPL-2.0-or-later`), as stated in its source
headers. The bundled license is `vendor/jbigkit/COPYING`. The included `.jbg`
and `.pgm` images are upstream codec test fixtures, not compiled executables or
private printer captures; their provenance is described in upstream
`examples/README`.

## macOS cache patch attribution

The cache fix comes from theshiver's open-source Apple Silicon printer project:
https://github.com/theshiver/apple-silicon-printer-drivers/blob/main/build/splix-cache.patch .

Copyright (c) 2026 theshiver. Its original build-tooling MIT permission and
disclaimer are reproduced verbatim in `LICENSES/cache-patch-MIT.txt`. The cache
patch modifies GPL-2.0 SpliX code and is distributed here with SpliX under GPL
version 2, retaining both the original code notices and this additional
permission notice. Its original and locally annotated patch hashes are recorded
in `UPSTREAM.json`.

## Publication contents

This repository publishes source, the build/installation scripts, a derived
text PPD, and test sources. Compiled filters, archives, object files, generated
PDF/raster/QPDL output, local job logs, hardware serials, and private configuration
are excluded. No proprietary Samsung binary or third-party binary installer is
distributed. The source needed to build the filter, including its JBIG component
and local patch, is included.
