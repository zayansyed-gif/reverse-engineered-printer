# Building the native filter

## Known working environment

- Apple M3, ARM64; macOS 26.6.2.
- Existing Apple Command Line Tools, Apple clang 17.0.0, SDK 15.5.
- Apple's CUPS libraries and tools; `cups-config --version` reports 2.3.4.
- Apple's `/usr/bin/python3`, `clang`, `clang++`, `ar`, `ppdc`, `lipo`, and `codesign`.

No package manager or global build dependency was installed. JBIG is compiled
from the source in this repository and linked statically into the filter.

## Rebuild

From the repository root:

```sh
/usr/bin/python3 -B scripts/build.py
/usr/bin/python3 -B scripts/verify.py
```

`build.py` copies SpliX into `build/splix`, applies the recorded patch, compiles
JBIG's `jbig85.c` and `jbig_ar.c`, and builds all translation units listed in
upstream `rastertoqpdl_SRC`. It uses `-arch arm64`, a macOS 12 minimum deployment
target, and the GNU C++98 language mode required by this older source.

The only required printer filter is `rastertoqpdl`. The legacy PostScript wrapper
`pstoqpdl` is not used for this monochrome PDF-to-CUPS-Raster pipeline, so it is
not built or installed. macOS supplies `cgpdftoraster`.

SpliX's Linux-oriented Makefiles require package discovery and installation
paths that are unsuitable here. The project build script replaces that build
orchestration without replacing the raster or compression implementation. The
source compiled without errors; remaining legacy initializer warnings do not
prevent the build.

The locally compiled executable receives an ad hoc code signature and is checked
with `codesign --verify --strict`. This is normal local signing, not a Gatekeeper
or SIP bypass and not a claim of Apple notarization. The build rejects executable
architectures other than ARM64 and non-system dynamic library dependencies.

## Outputs

- `build/stage/Library/Printers/ML1865/filter/rastertoqpdl`
- `build/stage/Library/Printers/ML1865/ppd/Samsung-ML-1865.ppd`
- `build/build-evidence.json`
- `ppd/Samsung-ML-1865.ppd`

No system installation occurs during a build. Native binaries are generated
locally and excluded from Git. Debug information is retained, so builds in
different directories need not produce identical binary hashes.

## Tests

`scripts/verify.py` renders the supplied PDF with Apple's rasterizer, verifies
the resulting raster header, runs SpliX, checks QPDL v5 and every band checksum,
and decodes all nonempty bands with the separately compiled upstream JBIG
decoder. It also runs the upstream JBIG T.85 codec tests.

```sh
/usr/bin/python3 -B -m unittest discover -s tests -p 'test_install_safety.py' -v
/usr/bin/python3 -B scripts/verify-cache.py
```

The cache regression converts 34 pages in manual-duplex order to exercise the
30-page cache and disk swapping. It prints nothing physically and temporarily
uses about 140 MB for a generated raster. Neither offline verification command
contacts USB or changes a queue.

Upstream snapshots and their exact revisions are recorded in `UPSTREAM.json`.
Vendor directories remain unmodified; downstream changes live in `patches`.

The generated `tests/test-page.pdf` is intentionally ignored by Git; verification
creates it before testing. Original upstream JBIG image fixtures remain included
so the vendored source and its upstream test data stay intact. See `NOTICE.md`
for licenses and the distinction between these fixtures and local generated
print captures.
