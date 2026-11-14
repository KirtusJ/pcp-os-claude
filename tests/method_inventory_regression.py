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


def require_integrity_rejection(
    name: str, result: subprocess.CompletedProcess[str], marker: str, problems: list[str]
) -> None:
    """Only the documented integrity refusal (exit 6) counts, never a crash."""
    diagnostic = (result.stdout + "\n" + result.stderr).lower()
    if result.returncode != 6:
        problems.append(f"{name}: expected exit 6, observed {result.returncode}")
    elif marker.lower() not in diagnostic:
        problems.append(f"{name}: exit 6 without {marker!r} diagnostic")


def initial_method_pin(binary: Path, method: Path, workspace: Path) -> str:
    """Create a disposable register without adopting ACR, then inspect METHOD_PINNED."""
    workspace.mkdir()
    register = workspace / ".pcp/register.jsonl"
    env = dict(os.environ, PCPOS_ROOT=str(workspace), PCPOS_METHOD=str(method),
               PCPOS_ACTOR="auditor", PCPOS_PRINCIPAL="operator", PCPOS_EDITION="COMMERCIAL")
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
        original_bytes = original.read_bytes()
        source = original_bytes.decode("utf-8")
        if "acr.science" not in source:
            return ["Science component header not found"]
        extra = root / "MODULES/99_AuditProbe/SOURCE/Specification.md"
        extra.parent.mkdir(parents=True)
        extra.write_text(source.replace("acr.science", "acr.auditprobe", 1), encoding="utf-8")
        result = invoke(binary, "method", root)
        print("unlisted module:", result.returncode, result.stdout.strip())
        require_integrity_rejection("unlisted module", result, "unexpected", problems)
        added_pin = initial_method_pin(binary, root, Path(temp) / "modified-workspace")
        print("unlisted-module register METHOD_PINNED:", added_pin)
        if added_pin != "DECLARED_NOT_VERIFIED":
            problems.append(f"unlisted module received inappropriate register pin: {added_pin}")
        modules = invoke(binary, "modules", root)
        print("module discovery (diagnostic only):", modules.returncode,
              "rogue listed:", "auditprobe" in modules.stdout.lower())
        # A repaired host may suppress untrusted modules when verification fails.
        # Either withholding or exposing the rogue is acceptable to this test.
        if modules.returncode not in (0, 6):
            problems.append(f"module inspection crashed or failed unexpectedly: exit {modules.returncode}")
        extra.unlink()
        extra.parent.rmdir()  # SOURCE
        extra.parent.parent.rmdir()  # 99_AuditProbe

        # An otherwise empty, entirely unlisted directory also changes the
        # method-tree inventory. Keep it isolated from subsequent controls.
        empty_module = root / "MODULES/99_Empty"
        empty_module.mkdir()
        empty = invoke(binary, "method", root)
        print("unlisted empty directory:", empty.returncode, empty.stdout.strip())
        require_integrity_rejection("unlisted empty directory", empty, "unexpected", problems)
        empty_module.rmdir()

        original.write_bytes(original_bytes + b"\nAUDIT_NEGATIVE_CONTROL\n")
        modified = invoke(binary, "method", root)
        print("edited listed file:", modified.returncode, modified.stdout.strip())
        require_integrity_rejection("changed listed file", modified, "differing", problems)
        original.write_bytes(original_bytes)

        stray = root / "unlisted-file.txt"
        stray.write_text("extra payload\n", encoding="utf-8")
        other = invoke(binary, "method", root)
        print("unlisted file:", other.returncode, other.stdout.strip())
        require_integrity_rejection("unlisted ordinary file", other, "unexpected", problems)
        stray.unlink()

        # An unexpected symbolic link must not silently count as release text.
        # The target is deliberately a real listed source, so this also covers
        # a link that resolves successfully; the scanner should not follow it.
        link = root / "unexpected-source-link.md"
        link.symlink_to("MODULES/03_Science/SOURCE/Specification.md")
        linked = invoke(binary, "method", root)
        print("unlisted symlink:", linked.returncode, linked.stdout.strip())
        require_integrity_rejection("unlisted symlink", linked, "unexpected", problems)
        link.unlink()

        # This symlink REPLACES a manifest-listed path with byte-identical
        # content kept outside the method tree. Hash matching alone is not
        # sufficient to assert the packaged file's local identity.
        shadow = Path(temp) / "shadow-science-spec.md"
        shadow.write_bytes(original_bytes)
        original.unlink()
        original.symlink_to(shadow)
        listed_link = invoke(binary, "method", root)
        print("manifest-listed symlink:", listed_link.returncode, listed_link.stdout.strip())
        require_integrity_rejection("listed symlink to outside source", listed_link,
                                    "unexpected", problems)
        original.unlink()
        original.write_bytes(original_bytes)

        # Omission of the packet's TOOLS/ programs is legitimate in the plugin,
        # but addition of unlisted TOOLS/ content is a different condition.
        tools_dir = root / "TOOLS"
        tools_dir.mkdir(exist_ok=True)
        rogue = tools_dir / "not-in-release.txt"
        rogue.write_text("extra executable-support data\\n", encoding="utf-8")
        omitted_subtree = invoke(binary, "method", root)
        print("unlisted TOOLS entry:", omitted_subtree.returncode, omitted_subtree.stdout.strip())
        require_integrity_rejection("unlisted file in TOOLS", omitted_subtree,
                                    "unexpected", problems)
        rogue.unlink()

        # This path IS listed in the manifest but MAY be missing in a plugin.
        # A present but unreadable file is not an omission and cannot inherit
        # verification of the released bytes. The old code treated all
        # fs::read failures as "absent", including PermissionDenied.
        optional = tools_dir / "acr.py"
        optional.write_bytes(b"INJECTED NOT-RELEASE DATA\\n")
        readable = invoke(binary, "method", root)
        print("readable changed optional tool:", readable.returncode, readable.stdout.strip())
        require_integrity_rejection("readable altered optional tool", readable,
                                    "differing", problems)
        optional.chmod(0o000)
        try:
            try:
                optional.read_bytes()
            except PermissionError:
                unreadable = invoke(binary, "method", root)
                print("unreadable optional tool:", unreadable.returncode,
                      unreadable.stdout.strip())
                require_integrity_rejection("unreadable optional tool", unreadable,
                                            "unreadable", problems)
            else:
                print("SKIP unreadable-optional-tool control: this account can read mode 000 files")
        finally:
            optional.chmod(0o600)
            optional.unlink()
        tools_dir.rmdir()
        # An apparently successful negative check can be caused by leftover
        # mutations. Confirm that the exact original bytes still verify.
        restored = invoke(binary, "method", root)
        print("restored clean method:", restored.returncode, restored.stdout.strip())
        if restored.returncode != 0:
            problems.append(f"method was not restored after testing: exit {restored.returncode}")
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
    if not os.access(binary, os.X_OK):
        parser.error(f"pcpos binary is not executable: {binary}; restore its Git executable mode")
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
