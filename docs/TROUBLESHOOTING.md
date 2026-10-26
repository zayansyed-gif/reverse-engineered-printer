# Troubleshooting

## Printer not found over USB

Turn the ML-1865 on, load plain paper, and firmly reconnect the square USB-B end
at the printer and the USB-A/USB-C connection at the Mac. Use a data-capable
cable/adapter. If a hub is involved, try connecting the adapter directly to the
Mac. Keep the printer connected throughout installation and printing.

```sh
lpinfo -v
ioreg -p IOUSB -w 0
```

The expected family URI starts with `usb://Samsung/ML-1860%20Series`. If it is
absent from both CUPS and the USB device tree, address power/cabling/adapter
connectivity first. The printer disappeared during this installation and
returned after reconnection; that failure occurred before any system changes.

## Queue exists but a job does not print

```sh
lpstat -l -p Samsung_ML1865_ARM64
lpstat -W not-completed -o Samsung_ML1865_ARM64
/usr/bin/python3 -B scripts/audit-installed.py
```

The audit checks the installed executable hashes, ARM64 architecture, ownership,
signature, and exact ML-1865 PPD. The filter must be under
`/Library/Printers/ML1865/filter/rastertoqpdl`; a build in a user home directory
is not the system installation.

Detailed job attributes for the original test are in the ignored local
`artifacts/test-job-attributes.txt`. Do not enable a global web interface or
change CUPS security settings just to inspect a queue.

## “Bad file descriptor” from automation

The restricted execution sandbox used during development could not connect to
the CUPS service. The same inspection commands succeeded outside that sandbox.
This is distinct from a broken print queue or driver. Run diagnostic commands
from a normal Terminal, or grant the automation the required execution access.

## Blank, garbled, or “use proper driver” sheet

Confirm the physical model is ML-1865 and the queue uses the exact provided PPD,
not the ML-1865W or a nearby Samsung model. Confirm QPDL version 5 and
`cupsCompression 21` in the PPD. Keep JBIG enabled. Run the offline verification
before changing printer options. Save the CUPS status and the page's error text.

## Larger or manual-duplex jobs

The included cache patch passed a 34-page offline regression. That test does not
prove the printer's physical manual-feed/duplex behavior. Use simplex printing
for the established working configuration. A genuine hang should be investigated
with the recorded job state; do not continuously resubmit copies.

## Removing the driver

Use the guarded removal procedure in `INSTALLING.md`. If files, device identity,
or queue configuration have changed since installation, the preflight stops for
review. Never remove other printer queues to troubleshoot this dedicated one.
