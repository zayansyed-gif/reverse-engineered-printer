# Samsung ML-1865 on Apple Silicon

A native ARM64 CUPS driver integration for the Samsung **ML-1865** USB laser
printer, built from official SpliX 2.0.2 and JBIG-KIT source.

**Verified on 2026-10-25:** an Apple M3 Mac running macOS 26.6.2 completed a real
CUPS test job, and the user confirmed that the titled test page and grayscale
blocks printed correctly. The queue is **`Samsung_ML1865_ARM64`**.

## Print

Keep the powered-on printer connected by USB. In any Mac application's print
dialog, select **Samsung ML-1865 (Native ARM64)**. The queue name is
`Samsung_ML1865_ARM64`. Defaults are Letter paper, 600 DPI, one-sided printing.

```sh
lp -d Samsung_ML1865_ARM64 /absolute/path/to/document.pdf
lpstat -p Samsung_ML1865_ARM64
```

The system default printer was not changed. USB discovery may call the device
**ML-1860 Series**; this is the shared device-family identifier, not the PPD model.
The installed PPD is specifically **Samsung ML-1865**, QPDL version 5, with JBIG
compression `0x15` preserved. No Rosetta or proprietary Samsung driver is used.

## Build and test

The Apple Command Line Tools were already installed. No Homebrew or third-party
precompiled dependencies are required. Run on an Apple Silicon Mac:

```sh
/usr/bin/python3 -B scripts/build.py
/usr/bin/python3 -B scripts/verify.py
/usr/bin/python3 -B -m unittest discover -s tests -p 'test_install_safety.py' -v
```

The build only writes to the repository. It does not install system files.
See [building](docs/BUILDING.md) and [recorded test results](docs/VERIFICATION.md).

## Install or remove

Administrator changes require explicit approval. Review the proposed installation:

```sh
/usr/bin/python3 -B scripts/install.py
```

After reviewing the plan and explicitly approving its administrator changes:

```sh
sudo /usr/bin/python3 -B scripts/install.py --apply
```

The printer must be powered on, connected by USB, and physically labelled
**ML-1865**. The installer refuses to replace an existing installation or queue.
A separate guarded removal command is provided. See
[installation and reversal](docs/INSTALLING.md) and the
[installation scope audit](docs/INSTALLATION-AUDIT.md).

## Project contents

| Path | Purpose |
| --- | --- |
| `vendor/splix` | Unmodified official SpliX 2.0.2 source snapshot |
| `vendor/jbigkit` | Official JBIG-KIT 2.2 source snapshot |
| `UPSTREAM.json` | Upstream URLs, tags, commits, and cache patch hash |
| `patches` | Existing macOS page-cache compatibility patch |
| `scripts` | Native build, offline tests, scoped installation/removal, real print test |
| `ppd/Samsung-ML-1865.ppd` | Generated model-specific PPD with absolute installed filter path |
| `tests` | Raster inspector and safety-test sources; verification generates the PDF fixture locally |
| `docs` | Build, installation, troubleshooting, implementation, and results |
| `build` | Ignored objects, staged installation, and ARM64 executable |
| `artifacts` | Ignored detailed logs, generated print data, and local job evidence |

## Learn later

[Implementation notes](docs/IMPLEMENTATION.md) explain PDF rasterization, the PPD,
SPL/QPDL records, banded JBIG, the CUPS USB backend, and the macOS cache fixes.
[Troubleshooting](docs/TROUBLESHOOTING.md) distinguishes USB, queue, rendering,
and encoding failures.

This is a source-based adaptation of an existing driver. Reverse engineering a
proprietary Samsung binary was unnecessary. No proprietary Samsung binaries are
included. SpliX and the integration are GPL-2.0; JBIG-KIT retains its upstream
GPL-2.0-or-later license. License files are preserved in the vendored sources.

See [copyright and third-party notices](NOTICE.md) for upstream attribution,
licenses, and dated modifications. Generated test output and local printer
evidence are intentionally excluded from Git.
