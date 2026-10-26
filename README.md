# Samsung ML-1865 on Apple Silicon

I wanted to get my old Samsung ML-1865 printer working on my M3 Mac without
relying on outdated Samsung drivers. This repo is the result.

I'm a CS student, and I started this as a personal reverse engineering project.
It turned out that SpliX already had support for this printer, so the work was
getting it built natively for Apple Silicon and working with macOS printing.
I kept the source, scripts, and notes here so I can come back to how it all works
later.

## Does it work?

Yes. A real test page printed correctly on my **M3 Mac running macOS 26.6.2**
on October 25, 2026, including the text and grayscale blocks.

The setup uses **SpliX 2.0.2**, **JBIG-KIT 2.2**, and the exact **ML-1865** PPD.
The filter runs natively as ARM64, with JBIG compression `0x15` enabled.
It doesn't need Rosetta or a proprietary Samsung driver.

I tested one-sided printing on the actual printer. The longer 34-page cache test
was done offline, so physical manual duplex is still untested.

## Printing

Once it's installed, turn the printer on, connect it by USB, and select
**Samsung ML-1865 (Native ARM64)** in the print dialog.

The queue is called `Samsung_ML1865_ARM64`. Its defaults are Letter paper,
600 DPI, and one-sided printing. The setup leaves the default printer alone.

You can also print from Terminal:

```sh
lp -d Samsung_ML1865_ARM64 /absolute/path/to/document.pdf
lpstat -p Samsung_ML1865_ARM64
```

One slightly confusing detail: USB reports this printer as **ML-1860 Series**.
That's its shared hardware-family name. The driver configuration here is still
specifically for the **ML-1865**, using QPDL version 5.

## Building and testing

You'll need Apple's Command Line Tools on an Apple Silicon Mac. They were
already installed on mine. JBIG is built from the included source, so there's
no Homebrew dependency or precompiled driver to download.

From the repo folder, run:

```sh
/usr/bin/python3 -B scripts/build.py
/usr/bin/python3 -B scripts/verify.py
/usr/bin/python3 -B -m unittest discover -s tests -p 'test_install_safety.py' -v
```

The build stays inside the repo until you run the installer. The tests check
the ARM64 executable, raster-to-QPDL conversion, JBIG decoding, the PPD, and
the installation and removal safeguards.

More detail is in [the build instructions](docs/BUILDING.md) and
[the test results](docs/VERIFICATION.md).

## Installing

Make sure the printer is powered on, connected by USB, and labelled **ML-1865**.
First, check what the installer is going to do:

```sh
/usr/bin/python3 -B scripts/install.py
```

If you're happy with the plan, install it with administrator privileges:

```sh
sudo /usr/bin/python3 -B scripts/install.py --apply
```

It creates a dedicated queue and refuses to replace an existing queue or
installation. There's also a guarded removal script if you want to undo it.
See [installation and removal](docs/INSTALLING.md) for the full steps, or
[the installation audit](docs/INSTALLATION-AUDIT.md) for exactly what changes.

## What's in here

| Folder or file | What's there |
| --- | --- |
| `vendor/splix` | The original SpliX 2.0.2 source |
| `vendor/jbigkit` | The original JBIG-KIT 2.2 source |
| `UPSTREAM.json` | Source URLs, versions, commits, and patch hashes |
| `patches` | The macOS page-cache fix and its attribution |
| `scripts` | Build, test, install, removal, and diagnostic scripts |
| `ppd/Samsung-ML-1865.ppd` | The ML-1865 configuration |
| `tests` | Test sources; the test PDF gets generated locally |
| `docs` | Instructions, troubleshooting, implementation notes, and results |

Build outputs go into `build`, and local logs and print data go into
`artifacts`. Those stay out of Git.

## Understanding it later

I didn't end up needing to reverse engineer a Samsung binary to get this
working. The existing open-source driver already handled the printer's language.

[The implementation notes](docs/IMPLEMENTATION.md) explain how a PDF becomes
raster data, how SpliX compresses it with JBIG, and how CUPS sends it over USB.
They also cover the PPD and the macOS cache fixes. If something stops working,
start with [troubleshooting](docs/TROUBLESHOOTING.md).

## Credits and license

This project builds on SpliX, JBIG-KIT, and the existing macOS cache patch.
The original source and copyright notices are kept in the repo.

SpliX and this project's integration code are GPL-2.0. JBIG-KIT keeps its
GPL-2.0-or-later license. See [LICENSE](LICENSE) and [NOTICE.md](NOTICE.md)
for the full licenses, credits, and modification details.

No proprietary Samsung binaries are included.
