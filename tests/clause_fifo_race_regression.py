#!/usr/bin/env python3
"""Bounded clause-read FIFO race reproducer for the build 22 Linux host.

Exit 1: a subprocess timed out while a complete Specification and a FIFO were
atomically swapped. Exit 0: no hang observed (NOT proof of race freedom).
Exit 2: prerequisite/stable control/writer failed; result inconclusive.
No real workspace or register is changed; only disposable files are touched.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
import time


def run(binary: Path, method: Path, timeout: float) -> tuple[int | None, str]:
    args = [str(binary), "clause", str(method), "core", "1.1"]
    try:
        result = subprocess.run(args, text=True, capture_output=True,
                                check=False, timeout=timeout)
        return result.returncode, (result.stdout + result.stderr)[-180:]
    except subprocess.TimeoutExpired:
        return None, "TIMED_OUT"


def examine(binary: Path, source: Path) -> dict:
    result = {
        "binary_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
        "stable_controls": {},
        "observations": [],
        "swap_cycles": 0,
        "writer_errors": [],
        "note": "No timeout in a bounded test cannot establish freedom from a file replacement race.",
    }
    with tempfile.TemporaryDirectory(prefix="pcpos-clause-fifo-") as temp:
        temp_path = Path(temp)
        method = temp_path / "method"
        shutil.copytree(source, method, symlinks=True)
        target = method / "MODULES/01_Core/SOURCE/Specification.md"
        original = target.read_bytes()
        start = time.monotonic()
        rc, info = run(binary, method, timeout=2.0)
        result["stable_controls"]["regular"] = {
            "exit": rc, "elapsed_ms": round(1000 * (time.monotonic() - start), 2),
            "output_tail": info,
        }
        if rc != 0:
            result["result"] = "PREREQUISITE_FAILED"
            return result

        target.unlink()
        os.mkfifo(target)
        start = time.monotonic()
        rc, info = run(binary, method, timeout=2.0)
        result["stable_controls"]["fifo"] = {
            "exit": rc, "elapsed_ms": round(1000 * (time.monotonic() - start), 2),
            "output_tail": info,
        }
        if rc != 6:
            result["result"] = "STABLE_FIFO_CONTROL_FAILED"
            return result
        target.unlink()
        target.write_bytes(original)

        stop = threading.Event()
        errors: list[str] = []
        cycles = [0]
        def writer() -> None:
            regular_stage = temp_path / "regular.stage"
            pipe_stage = temp_path / "fifo.stage"
            while not stop.is_set():
                try:
                    regular_stage.write_bytes(original)
                    os.replace(regular_stage, target)
                    os.mkfifo(pipe_stage)
                    os.replace(pipe_stage, target)
                    cycles[0] += 1
                except OSError as error:
                    errors.append(str(error))
                    break

        worker = threading.Thread(target=writer, daemon=True)
        worker.start()
        try:
            for call in range(1, 9):
                args = [str(binary), "clause", str(method), "core", "1.1"]
                process = subprocess.Popen(args, stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE, text=True)
                try:
                    output, err = process.communicate(timeout=0.45)
                    result["observations"].append({
                        "call": call, "exit": process.returncode,
                        "output_tail": (output + err)[-160:],
                    })
                except subprocess.TimeoutExpired:
                    wait_channel = None
                    try:
                        wait_channel = Path(f"/proc/{process.pid}/wchan").read_text().strip()
                    except OSError:
                        pass  # Optional Linux diagnostic; not required to detect timeout.
                    result["observations"].append({
                        "call": call, "result": "TIMED_OUT",
                        "timeout_seconds": 0.45, "wait_channel": wait_channel,
                    })
                    process.kill()
                    process.communicate(timeout=2.0)
                    break
        finally:
            stop.set()
            worker.join(timeout=2.0)
        result["swap_cycles"] = cycles[0]
        result["writer_errors"] = errors
        if errors or worker.is_alive() or not cycles[0]:
            result["result"] = "INCONCLUSIVE_WRITER_FAILURE"
        elif any(v.get("result") == "TIMED_OUT" for v in result["observations"]):
            result["result"] = "BLOCKED_READ_OBSERVED"
        else:
            result["result"] = "NOT_OBSERVED_IN_BOUNDED_RUN"
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    repo = Path(__file__).resolve().parents[1]
    parser.add_argument("--binary", type=Path, default=repo / "servers/linux-x86_64/pcpos")
    parser.add_argument("--method", type=Path, default=repo / "method")
    args = parser.parse_args()
    binary, method = args.binary.resolve(), args.method.resolve()
    if not binary.is_file() or not os.access(binary, os.X_OK) or not method.is_dir():
        parser.error("requires an executable Linux x86_64 pcpos and an existing method directory")
    outcome = examine(binary, method)
    print(json.dumps(outcome, indent=2))
    return {"BLOCKED_READ_OBSERVED": 1, "NOT_OBSERVED_IN_BOUNDED_RUN": 0}.get(
        outcome["result"], 2,
    )


if __name__ == "__main__":
    raise SystemExit(main())
