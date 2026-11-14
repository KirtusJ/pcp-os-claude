# Build 22 method-tree inventory regression (unfixed)

Status: **reproduced against distributed Linux x86_64 host binary**. This is a
diagnostic-only draft change, not an implementation correction.

## What the test establishes

Run `python3 tests/method_inventory_regression.py` in this plugin repository on
Linux x86_64, with its packaged `servers/linux-x86_64/pcpos` executable.

The test copies the distributed `method/` directory to a temporary location.
It also creates isolated temporary registers through the CLI's `init` command.
No review is adopted or commissioned, and no actual project register is changed.
It exercises:

1. The unchanged plugin method tree, which must succeed.
2. A new `MODULES/99_AuditProbe/SOURCE/Specification.md` declaring
   `acr.auditprobe`, which must NOT be accepted as exactly the released method tree.
3. Discovery of that extra module, as evidence that it is not merely ignored.
4. A one-line modification of a manifest-listed Science source, which must fail.
5. An unlisted ordinary file, which must also invalidate a *whole-tree* identity
   assertion.
6. An unexpected symlink to a valid listed source, which must not count as
   packaged release text merely because its target can be read.
7. An unlisted file inside an optional `TOOLS/` directory: legitimate omission
   of a plugin tool is not permission to add an untracked file in that subtree.
8. A **disposable** register initialized under both the clean and the extra-module
   method trees. The clean tree must produce `METHOD_PINNED` with
   `FILES_VERIFIED_AGAINST_OWN_MANIFEST`; the extra-module tree must instead
   produce `DECLARED_NOT_VERIFIED`, rather than inheriting the clean status.
9. An unlisted **empty directory**, checked after removing the injected module
   and its parent folders, so no earlier mutation influences the result.
10. A symlink replacing a **manifest-listed** Specification with identical
    bytes outside the method tree, refused despite matching its listed digest.
11. A manifest-listed but **optional** `TOOLS/acr.py` that exists and is
    unreadable: a read permission error is not a legitimate omitted-file
    condition. A readable modified file is the paired positive control.
    This case is skipped only when the test runner can read a mode-000 file
    (for example as root).

The current build 22 binary passes controls 1 and 4, discovers the new module,
but incorrectly succeeds on controls 2, 5, 6, 7, 9 and 10, and on 11 when run without privileged file-read override. It exits 0 for the original method directory and for the unlisted-entry variants, while
reporting the same manifest fingerprint and listed-file counts. The disposable
register also records `FILES_VERIFIED_AGAINST_OWN_MANIFEST` for the injected
module, contrary to the requirement's intended difference from released text. Thus the regression script intentionally exits
with code 1 until the binary is repaired.

## What the test does NOT establish

This does not show that a participant can commission a review, gain authority,
forge a provenance record, or alter released source bytes undetected. It tests
**identity reporting of the method directory**, not permission enforcement.
A method manifest match over listed entries is weaker than verification of the
complete directory tree. It is also not an atomic filesystem snapshot.

## Source-side repair required

The host's `method_check` and `MethodCheck::complete` implementation in the
separate proprietary source archive, at
`PCP_OS_Rust/crates/pcpos-host/src/pcpos.rs`, must report unexpected entries
and withhold whole-tree identity when they exist. Ensure the same distinction is
retained when a fresh register records `METHOD_PINNED`.
Handle symlinks, unexpected directories and directory read failures explicitly;
only `NotFound` establishes that an optional tool/probe is absent. `PermissionDenied`
and other I/O errors must never be treated as legitimate omissions. Keep the documented
text-only plugin omissions distinct from *additional* and *unreadable* files.

The Rust source and reproducible build system are not in this GitHub repository.
Do not label this PR a product fix. The rights holder must apply, compile and
verify a source correction, then rebuild x86_64 and aarch64 binaries and update
all release manifests before the regression should pass. The test must then be
rerun for a full method packet and the text-only plugin, in addition to other
guard and register tests. No subagents or ACR host enforcement were involved
in producing this finding.

Linked issue: #1. Date: 13 November 2026 (PCT, UTC−07:00).
