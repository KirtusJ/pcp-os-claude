# Build 22 method-tree inventory regression (unfixed)

Status: **reproduced against distributed Linux x86_64 host binary**. This is a
diagnostic-only draft change, not an implementation correction.

## What the test establishes

Run `python3 tests/method_inventory_regression.py` in this plugin repository on
Linux x86_64, with its packaged `servers/linux-x86_64/pcpos` executable.

The test copies the distributed `method/` directory to a temporary location.
It exercises:

1. The unchanged plugin method tree, which must succeed.
2. A new `MODULES/99_AuditProbe/SOURCE/Specification.md` declaring
   `acr.auditprobe`, which must NOT be accepted as exactly the released method tree.
3. Discovery of that extra module, as evidence that it is not merely ignored.
4. A one-line modification of a manifest-listed Science source, which must fail.
5. An unlisted ordinary file, which must also invalidate a *whole-tree* identity
   assertion.

The current build 22 binary passes controls 1 and 4, discovers the new module,
but incorrectly succeeds on controls 2 and 5. It exits 0 for the original method
directory and for both unlisted-entry variants, while reporting the same manifest
fingerprint and listed-file counts. Thus the regression script intentionally exits
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
Handle symlinks and directory read failures explicitly; keep the documented
text-only plugin omissions distinct from *additional* files.

The Rust source and reproducible build system are not in this GitHub repository.
Do not label this PR a product fix. The rights holder must apply, compile and
verify a source correction, then rebuild x86_64 and aarch64 binaries and update
all release manifests before the regression should pass. The test must then be
rerun for a full method packet and the text-only plugin, in addition to other
guard and register tests. No subagents or ACR host enforcement were involved
in producing this finding.

Linked issue: #1. Date: 13 November 2026 (PCT, UTC−07:00).
