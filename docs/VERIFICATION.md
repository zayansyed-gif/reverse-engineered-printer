# Recorded verification: 2026-10-25

| Check | Observed result |
| --- | --- |
| Official SpliX source | Tag 2.0.2, commit `9bde257882a1ebcf15a97ff4685d34053383e3f8` |
| JBIG source | Author's v2.2, commit `802dc4c558f36b3325dac329bf3beb291962baa3` |
| Filter architecture | Mach-O ARM64; no Rosetta |
| Dynamic dependencies | macOS system libraries only; JBIG statically linked |
| Filter signature | Local ad hoc signature verified by codesign |
| PPD model | Samsung ML-1865 |
| PPD protocol | QPDL version 5, compression 21 / 0x15 |
| Upstream JBIG T.85 codec tests | Passed |
| PDF to CUPS Raster | Passed with Apple's cgpdftoraster |
| Test raster | 4921 x 6350 pixels, 600 x 600 DPI, 1 bit, black color space, compression 21 |
| Raster to QPDL | Passed, 19 nonempty JBIG bands |
| Independent decoding | All bands decoded; all checksums valid |
| Black-pixel count | 1,566,286 in input raster and decoded output |
| 34-page cache regression | Passed; expected manual-duplex page order, all bands decoded, swap files cleaned up |
| Installation/removal safety | Six simulated safety tests passed |
| USB discovery | Samsung ML-1860 family device, physical label confirmed ML-1865 |
| Dedicated CUPS queue | Samsung_ML1865_ARM64 created and enabled |
| Real test job | Samsung_ML1865_ARM64-1, CUPS job-state completed |
| Physical output | User confirmed the titled test page and grayscale blocks printed correctly |
| Removal preflight | Passed against the real installation; no removal performed |

Installed filter SHA-256:

```text
e33b2660eb711a657249c813867116331d0f990adaf699629be31ba35dd0f497
```

Hardware-tested installation PPD SHA-256:

```text
e4876f919465cde8ad7a94127b8c7a2ed0d5da06426f6771bd0a5f0657341d51
```

Detailed local evidence is in `build/build-evidence.json` and the ignored
`artifacts/` directory: conversion logs, verification JSON, codec tests, cache
regression, safety tests, job attributes, and the physical confirmation record.
The hardware serial number is not included in committed documentation.

Only one physical simplex test page was required and confirmed. Additional paper
sizes, 1200 DPI, physical manual duplex, and every possible application were not
hardware-tested. CUPS completion and physical confirmation are recorded
separately; offline verification alone is not described as printer success.

The hashes above identify the installed build used for the physical test. The
source-publication review subsequently added comment-only license and dated
modification notices to the derived PPD and patched cache source. New builds can
therefore have different hashes; this does not change the working installation.
The source-publication build was rebuilt successfully before committing. Its
ARM64 check, upstream T.85 codec tests, 19-band independent JBIG decoding,
checksums, black-pixel count, PPD validation, and six installation/removal safety
tests passed. The installed working driver was not replaced during publication.
