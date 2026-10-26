# Installation, printing, and safe removal

The driver is already installed and a physical test page was confirmed on
2026-10-25. The instructions below allow the installation to be understood or
reproduced on an Apple Silicon Mac with the same physical ML-1865 printer.

## Review first

Complete the build and offline verification. Then inspect the plan:

```sh
/usr/bin/python3 -B scripts/install.py
```

The plan prints hashes and every proposed file. An installation is refused if
the staged files differ from the verified binaries, contain symlinks or extra
files, or lack an exact ARM64 filter. The script also refuses an existing
`/Library/Printers/ML1865` installation or `Samsung_ML1865_ARM64` queue.

## Administrator operation

Only after approving the displayed plan:

```sh
sudo /usr/bin/python3 -B scripts/install.py --apply
```

Enter a password only in your own Terminal or macOS administrator dialog.
During this project's installation, macOS's own authentication dialog was used.

The installer creates `/Library/Printers/ML1865` and copies the filter, PPD, and
two licenses. It writes a hash-based receipt and creates the new CUPS queue using
the discovered USB URI. The physical device label must be ML-1865 even though
USB reports its shared ML-1860-family name. The driver is never substituted with
the ML-1860 or ML-1865W PPD.

The filter is root-owned, mode 0555. Directories are mode 0755; PPD, licenses, and
receipt are mode 0644. The queue defaults to Letter, 600 DPI, simplex, and no
network sharing. Neither the default printer nor another queue is changed.

No protected `/usr` files, global CUPS configuration, security controls, or
startup services are edited. CUPS maintains its own metadata for the newly
created queue. An early device-discovery failure exits before creating files.

## Use the printer

Select **Samsung ML-1865 (Native ARM64)** in the application's print dialog, or:

```sh
lp -d Samsung_ML1865_ARM64 /absolute/path/to/document.pdf
lpstat -p Samsung_ML1865_ARM64
lpstat -W not-completed -o Samsung_ML1865_ARM64
```

The supplied `scripts/print-test.py` submits one real test page and records its
job ID. If a result file already exists, it monitors that job rather than
submitting a duplicate. For an intentional additional test, print
`tests/test-page.pdf` using the `lp` command above. CUPS completion alone does not
establish physical output; check the sheet.

## Read-only installed audit

```sh
/usr/bin/python3 -B scripts/audit-installed.py
/usr/bin/python3 -B scripts/uninstall.py
```

These commands inspect the installation and change nothing. macOS's CUPS socket
must be accessible from the process; a restricted automation sandbox can block
inspection even when the actual printer works.

## Reverse the installation

After separate approval to remove the dedicated printer:

```sh
sudo /usr/bin/python3 -B scripts/uninstall.py --apply
```

The removal command verifies the recorded file hashes, checks that the queue
still uses this model/filter/device, and refuses pending jobs, symlinks, modified
files, or unexpected files. It removes only `Samsung_ML1865_ARM64` and the fixed
list of files and empty directories under `/Library/Printers/ML1865`. It does not
use recursive deletion or remove other queues. If a guard fails, review the
reported difference instead of deleting files blindly.

The removal preflight passed against the real installed queue. Actual removal
was not performed, because the working printer should remain installed.
