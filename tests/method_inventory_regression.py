#!/usr/bin/env python3
"""Regression for build 22 method-tree inventory checking.

Run from the repository: python3 tests/method_inventory_regression.py
This intentionally exits 1 against the affected build-22 binary. It creates
disposable method copies and temporary registers only; it never touches a real workspace.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def invoke(binary: Path, verb: str, method: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(binary), verb, str(method)],
        capture_output=True, text=True, check=False,
    )


def initial_method_pin(binary: Path, method: Path, workspace: Path) -> str:
    """Create a disposable register without adopting ACR, then inspect METHOD_PINNED."""
    workspace.mkdir()
    register = workspace / ".pcp/register.jsonl"
    env = dict(os.environ, PCPOS_ROOT=str(workspace), PCPOS_METHOD=str(method),
               PCPOS_ACTOR="auditor", PCPOS_PRINCIPAL="operator", PCPOS_EDITION="ENTERPRISE")
    run = subprocess.run(
        [str(binary), "init", str(register), "--principal", "operator"],
        capture_output=True, text=True, check=False, env=env,
    )
    if run.returncode != 0 or not register.is_file():
        return f"INIT_FAILED: exit={run.returncode} {run.stderr.strip()}"
    events = [json.loads(line) for line in register.read_text(encoding="utf-8").splitlines()]
    pins = [event.get("body", {}).get("verified")
            for event in events if event.get("kind") == "METHOD_PINNED"]
    if len(pins) != 1:
        return f"PIN_COUNT_INVALID: {len(pins)}"
    return str(pins[0])


def test(binary: Path, method: Path) -> list[str]:
    problems: list[str] = []
    with tempfile.TemporaryDirectory(prefix="pcpos-method-inventory-") as temp:
        root = Path(temp) / "method"
        shutil.copytree(method, root, symlinks=True)
        clean = invoke(binary, "method", root)
        print("clean:", clean.returncode, clean.stdout.strip())
        if clean.returncode != 0:
            return ["original plugin method did not pass verification"]
        clean_pin = initial_method_pin(binary, root, Path(temp) / "clean-workspace")
        print("clean register METHOD_PINNED:", clean_pin)
        if clean_pin != "FILES_VERIFIED_AGAINST_OWN_MANIFEST":
            problems.append(f"clean method was not verified at register init: {clean_pin}")

        original = root / "MODULES/03_Science/SOURCE/Specification.md"
        source = original.read_text(encoding="utf-8")
        if "acr.science" not in source:
            return ["Science component header not found"]
        extra = root / "MODULES/99_AuditProbe/SOURCE/Specification.md"
        extra.parent.mkdir(parents=True)
        extra.write_text(source.replace("acr.science", "acr.auditprobe", 1), encoding="utf-8")
        result = invoke(binary, "method", root)
        print("unlisted module:", result.returncode, result.stdout.strip())
        if result.returncode == 0:
            problems.append("unlisted module was accepted as release-identical")
        added_pin = initial_method_pin(binary, root, Path(temp) / "modified-workspace")
        print("unlisted-module register METHOD_PINNED:", added_pin)
        if added_pin != "DECLARED_NOT_VERIFIED":
            problems.append(f"unlisted module received inappropriate register pin: {added_pin}")
        modules = invoke(binary, "modules", root)
        if "auditprobe" not in modules.stdout.lower():
            problems.append("unlisted module not discoverable; reproduction differs")
        extra.unlink()

        original.write_text(source + "\nAUDIT_NEGATIVE_CONTROL\n", encoding="utf-8")
        modified = invoke(binary, "method", root)
        print("edited listed file:", modified.returncode, modified.stdout.strip())
        if modified.returncode == 0:
            problems.append("listed file modification was not rejected")
        original.write_text(source, encoding="utf-8")

        stray = root / "unlisted-file.txt"
        stray.write_text("extra payload\n", encoding="utf-8")
        other = invoke(binary, "method", root)
        print("unlisted file:", other.returncode, other.stdout.strip())
        if other.returncode == 0:
            problems.append("unlisted file was accepted as release-identical")
        stray.unlink()

        # An unexpected symbolic link must not silently count as release text.
        # The target is deliberately a real listed source, so this also covers
        # a link that resolves successfully; the scanner should not follow it.
        link = root / "unexpected-source-link.md"
        link.symlink_to("MODULES/03_Science/SOURCE/Specification.md")
        linked = invoke(binary, "method", root)
        print("unlisted symlink:", linked.returncode, linked.stdout.strip())
        if linked.returncode == 0:
            problems.append("unlisted symlink was accepted as release-identical")
        link.unlink()

        # Omission of the packet's TOOLS/ programs is legitimate in the plugin,
        # but addition of unlisted TOOLS/ content is a different condition.
        tools_dir = root / "TOOLS"
        tools_dir.mkdir(exist_ok=True)
        rogue = tools_dir / "not-in-release.txt"
        rogue.write_text("extra executable-support data\\n", encoding="utf-8")
        omitted_subtree = invoke(binary, "method", root)
        print("unlisted TOOLS entry:", omitted_subtree.returncode, omitted_subtree.stdout.strip())
        if omitted_subtree.returncode == 0:
            problems.append("unlisted file under omitted TOOLS/ was accepted as release-identical")
        rogue.unlink()
        tools_dir.rmdir()
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    base = Path(__file__).resolve().parents[1]
    parser.add_argument("--binary", type=Path, default=base / "servers/linux-x86_64/pcpos")
    parser.add_argument("--method", type=Path, default=base / "method")
    args = parser.parse_args()
    binary, method = args.binary.resolve(), args.method.resolve()
    if not binary.is_file() or not method.is_dir():
        parser.error(f"binary or method unavailable: {binary}, {method}")
    problems = test(binary, method)
    for problem in problems:
        print("FAIL:", problem, file=sys.stderr)
    if problems:
        print("Regression not fixed; failure expected on distributed build 22.", file=sys.stderr)
        return 1
    print("All local method-inventory controls passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
