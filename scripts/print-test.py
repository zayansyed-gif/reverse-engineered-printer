#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
# Copyright (C) 2026 reverse-engineered-printer contributors
"""Submit one real test page and record its CUPS job state, never physical success."""
import json
from pathlib import Path
import re
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
QUEUE = "Samsung_ML1865_ARM64"
OUT = ROOT / "artifacts"


def main():
    result_path = OUT / "print-result.json"
    if result_path.exists():
        result = json.loads(result_path.read_text())
        print("Monitoring the recorded test job; not submitting a duplicate.")
    else:
        subprocess.run(["/usr/bin/lpstat", "-p", QUEUE], check=True)
        output = subprocess.check_output(["/usr/bin/lp", "-d", QUEUE, "-t", "ML1865-ARM64-20261025",
                    "-o", "PageSize=Letter", "-o", "Resolution=600dpi", "-o", "Duplex=None",
                    str(ROOT / "tests/test-page.pdf")], text=True)
        print(output, flush=True)
        match = re.search(re.escape(QUEUE) + r"-(\d+)", output)
        if not match:
            raise RuntimeError("Cannot identify the submitted CUPS job")
        result = {"queue": QUEUE, "job_id": int(match[1]), "submission": output.strip(),
                  "physical_print_verified": False, "physical_confirmation": "pending"}
        result_path.write_text(json.dumps(result, indent=2) + "\n")
    uri = "ipp://localhost/jobs/" + str(result["job_id"])
    deadline = time.monotonic() + 120
    while time.monotonic() < deadline:
        query = subprocess.run(["/usr/bin/ipptool", "-T", "10", "-t", "-v", uri,
                                str(ROOT / "tests/get-job-state.test")], text=True, capture_output=True, timeout=15)
        status = query.stdout + query.stderr
        (OUT / "test-job-attributes.txt").write_text(status)
        match = re.search(r"job-state \(enum\) = ([\w-]+)", status)
        if match:
            state = match[1]
            result["cups_job_state"] = state
            result_path.write_text(json.dumps(result, indent=2) + "\n")
            print("CUPS job state:", state, flush=True)
            if state in {"completed", "canceled", "aborted"}:
                break
        elif query.returncode:
            print("Job status query failed; details saved to artifacts/test-job-attributes.txt", flush=True)
        time.sleep(2)
    else:
        result["monitor_timeout"] = True
    queue = subprocess.run(["/usr/bin/lpstat", "-l", "-p", QUEUE], text=True, capture_output=True)
    (OUT / "queue-status.txt").write_text(queue.stdout + queue.stderr)
    result_path.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    if result.get("cups_job_state") != "completed":
        raise SystemExit(1)
    print("CUPS completed the job. A readable physical page must still be confirmed by the user.")


if __name__ == "__main__":
    main()
