# Source-publication review: 2026-10-25

The existing repository and history are preserved. This publication adds the
native ML-1865 integration; it does not create another repository or replace
existing commits.

## Included

- Source and license notices for SpliX 2.0.2 and JBIG-KIT 2.2.
- Native build and scoped installation/removal scripts.
- The model-specific text PPD, test sources, and documentation.
- The attributed macOS cache patch, its original MIT permission notice, and
  dated GPL modification notices.
- Original upstream codec image fixtures, retained as part of the unmodified
  upstream source/test distribution rather than as printer capture artifacts.

All 354 SpliX files and all 46 JBIG-KIT files match their recorded official
source snapshots, including original copyright, attribution, and license files.
The root GPL text matches the SpliX COPYING file. See `NOTICE.md`.

## Excluded and privacy checks

`.gitignore` excludes compiled filters, archives, objects, build directories,
logs, generated test PDFs, raster/QPDL data, packet captures, private environment
files, credential files, and proprietary installer payloads. Local evidence
remains available in the ignored `artifacts` directory.

Files selected for publication were scanned for private keys, GitHub/OpenAI/AWS
credential patterns, credential-bearing URLs, secret assignments, local home
paths, and hardware serials. No credentials or private personal data were found.
The email-address matches are original upstream author/translator attribution;
the serial in the safety test is the explicit synthetic `TEST-ONLY` fixture.
Neither is a private printer identifier or user credential.

The new commit uses the repository owner's public GitHub username and GitHub
noreply address. Existing commit metadata is preserved with existing history.

## Validation

The publication source was rebuilt natively for ARM64. PPD validation, upstream
JBIG T.85 tests, PDF rasterization, QPDL v5/0x15 output, checksum checks,
independent decoding of all 19 bands, and all six safety tests passed. The
previously confirmed physical print result remains documented separately.
This publication does not reinstall the driver or submit another print job.
