#!/usr/bin/env python3
"""Bounded, non-deterministic build-22 clause source-identity regression.

Run from repo root: python3 tests/clause_snapshot_regression.py
Exit 1 means a crossed source identity was observed on a disposable method tree.
Exit 0 means no mismatch observed in this finite run, NOT proof of race freedom.
No register, review, real project, or distributed method file is modified.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time

BASE = Path(__file__).resolve().parents[1]
HEADER = re.compile(r"acr\.core\s+1\.0\s*\|\s*Specification SHA-256 ([0-9a-f]{64})")
MARKERS = ("SOURCE_SNAPSHOT_ALPHA", "SOURCE_SNAPSHOT_BETA")


def query(binary: Path, method: Path, hashes: tuple[str, str]) -> tuple[dict, str]:
    p = subprocess.run([str(binary), "clause", str(method), "core", "1.1"],
                       text=True, capture_output=True, check=False, timeout=4)
    m = HEADER.search(p.stdout)
    claimed = m.group(1) if m else None
    observed = [i for i, marker in enumerate(MARKERS) if marker in p.stdout]
    matching = p.returncode == 0 and len(observed) == 1 and claimed == hashes[observed[0]]
    if p.returncode == 0:
        verdict = "SERVED_CONSISTENT" if matching else "SERVED_MIXED_IDENTITY"
    elif p.returncode == 6 and "changed during clause retrieval" in p.stderr:
        # A fixed host may reject a method that changed between source
        # discovery and retrieval. That is a safe, expected race outcome.
        verdict = "REFUSED_CHANGED_SOURCE"
    else:
        verdict = "UNEXPECTED_REFUSAL"
    return {
        "exit": p.returncode,
        "header_sha256": claimed,
        "served_variant": observed,
        "sha256_of_served_variant": hashes[observed[0]] if len(observed) == 1 else None,
        "stderr": p.stderr.strip()[:240] if p.returncode else "",
        "verdict": verdict,
    }, verdict


def probe(binary: Path, method: Path, max_calls: int = 90, deadline_seconds: float = 8.0) -> dict:
    with tempfile.TemporaryDirectory(prefix="pcpos-clause-snapshot-") as directory:
        directory = Path(directory)
        copy = directory / "method"
        shutil.copytree(method, copy, symlinks=True)
        spec = copy / "MODULES/01_Core/SOURCE/Specification.md"
        source = spec.read_bytes()
        heading = b"### 1.1 Authority of this document\n"
        if source.count(heading) != 1:
            raise ValueError("unexpected Core 1.1 heading")
        versions = tuple(source.replace(heading, heading + b"\n" + marker.encode() + b"\n", 1)
                         for marker in MARKERS)
        hashes = tuple(hashlib.sha256(v).hexdigest() for v in versions)
        controls = []
        for i in (0, 1):
            spec.write_bytes(versions[i])
            row, verdict = query(binary, copy, hashes)
            controls.append(row)
            if verdict != "SERVED_CONSISTENT" or row["served_variant"] != [i]:
                raise AssertionError(f"stable variant {i} control failed: {row}")
        spec.write_bytes(versions[0])

        staging = directory / "staging.md"  # outside the method tree
        stop = threading.Event()
        count = [0]
        errors = []
        def swap() -> None:
            variant = 1
            while not stop.is_set():
                try:
                    staging.write_bytes(versions[variant])
                    os.replace(staging, spec)  # atomic, complete-file replacement
                    count[0] += 1
                    variant ^= 1
                except Exception as exc:
                    errors.append(str(exc))
                    break
        writer = threading.Thread(target=swap, daemon=True)
        writer.start()
        mismatches = []
        refused = 0
        unexpected = []
        calls = 0
        start = time.monotonic()
        try:
            while calls < max_calls and time.monotonic() - start < deadline_seconds:
                calls += 1
                row, verdict = query(binary, copy, hashes)
                if verdict == "REFUSED_CHANGED_SOURCE":
                    refused += 1
                elif verdict == "UNEXPECTED_REFUSAL":
                    row["call"] = calls
                    unexpected.append(row)
                    break
                elif verdict == "SERVED_MIXED_IDENTITY":
                    row["call"] = calls
                    mismatches.append(row)
                    if len(mismatches) == 2:
                        break
        finally:
            stop.set()
            writer.join(timeout=2)
        return {
            "binary_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
            "controls": controls,
            "calls": calls,
            "atomic_replacements": count[0],
            "observed_mismatches": mismatches,
            "safe_changed_source_refusals": refused,
            "unexpected_failures": unexpected,
            "writer_errors": errors,
            "result": ("CROSSED_IDENTITY_OBSERVED" if mismatches else
                       "UNEXPECTED_FAILURE" if unexpected else "NOT_OBSERVED_IN_BOUNDED_RUN"),
            "limitation": "No mismatch in a finite race test is not proof of race freedom. Source code must use one coherent byte snapshot.",
        }


if __name__ == "__main__":
    executable = Path(sys.argv[1]) if len(sys.argv) > 1 else BASE / "servers/linux-x86_64/pcpos"
    method = Path(sys.argv[2]) if len(sys.argv) > 2 else BASE / "method"
    if not executable.is_file() or not method.is_dir():
        raise SystemExit("Requires packaged Linux x86_64 pcpos and method folder, or explicit paths")
    outcome = probe(executable.resolve(), method.resolve())
    print(json.dumps(outcome, indent=2))
    raise SystemExit(2 if outcome["writer_errors"] else 1 if outcome["observed_mismatches"] or outcome["unexpected_failures"] else 0)
