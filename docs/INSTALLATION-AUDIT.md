# Administrator change audit

The user approved this scope before administrator execution. The first attempt
found no USB device and stopped before changing the system. A later attempt
installed successfully after the printer was reconnected.

## Added files

All project-installed files are under the new `/Library/Printers/ML1865` directory:

| File | Purpose |
| --- | --- |
| `filter/rastertoqpdl` | Locally compiled, ad hoc signed ARM64 filter |
| `ppd/Samsung-ML-1865.ppd` | Exact ML-1865 model configuration |
| `licenses/SpliX-COPYING` | SpliX license |
| `licenses/JBIG-KIT-COPYING` | JBIG-KIT license |
| `install-receipt.json` | File hashes and queue identity for guarded removal |

The only CUPS mutation is `lpadmin -p Samsung_ML1865_ARM64 ...`. Its options enable
that new queue, bind the discovered USB device, select the installed PPD, set
Letter/600-DPI/simplex defaults, and disable sharing for this queue. CUPS creates
its own queue metadata, including `/etc/cups/ppd/Samsung_ML1865_ARM64.ppd`.

The installer never calls `lpadmin -d`, `lpadmin -x`, `cupsctl`, `launchctl`,
`csrutil`, `spctl`, or security-profile configuration tools. It refuses an existing
destination or installation. It does not write to `/usr` or alter permissions
outside its new installation directory.

## Reversal verification

Six tests run installation/removal logic in temporary directories with fake CUPS:

1. Only allowlisted files and the named new queue are installed.
2. Existing installation directories are refused before queue changes.
3. Modified or unexpected installed files block removal.
4. Pending jobs block removal.
5. Removal targets only the owned queue.
6. Removing a remaining installation with an already absent queue preserves
   unrelated files.

The real installation also passed the removal preflight without removing any
files or queues. A receipt is written before queue creation, allowing inspection
if CUPS configuration fails after the files have been copied. A failure before
that receipt is written may require reviewing the partially copied dedicated
directory manually; it never authorizes deleting unrelated files.
