# SpliX modifications

`vendor/splix` is the unmodified official 2.0.2 source snapshot. Build-time patches
are applied to `build/splix`, keeping the original source available for comparison.
The build script replaces Linux package discovery and installation rules with
explicit Apple compiler invocations and a staging directory. It retains the
upstream raster encoder, two compression threads, and all JBIG support.

The generated ML-1865 PPD changes only the filter path and the descriptive nickname.
Model identity, QPDL version 5, compression 0x15, geometry, and options remain upstream.

The cache implementation comes from theshiver's existing macOS SpliX patch.
See `../NOTICE.md` and `../LICENSES/cache-patch-MIT.txt` for attribution and its
original permission notice. The local patch additionally places a dated
2026-10-25 modification notice in the patched build copy of `src/cache.cpp`.
Original and annotated patch hashes are in `../UPSTREAM.json`.

The derived PPD and its generator also include a dated modification notice.
The upstream vendor snapshots and their notices have not been edited.
