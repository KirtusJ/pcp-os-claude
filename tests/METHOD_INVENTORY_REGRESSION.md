# Build 22 method-tree inventory regression (unfixed)

Status: **reproduced against distributed Linux x86_64 host binary**. This is a
diagnostic-only draft change, not an implementation correction.

## What the test establishes

Run `python3 tests/method_inventory_regression.py` in this plugin repository on
Linux x86_64, with its packaged `servers/linux-x86_64/pcpos` executable.
The optional `--method` flag also accepts a **complete** extracted ACR
Implementation directory. Tests preserve existing optional tool files and
original Specification bytes.

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

12. A **named pipe** replacing `MANIFEST.json`. The diagnostic must return
    promptly rather than block trying to read a pipe with no writer.
13. A **named pipe** replacing a manifest-listed Science Specification. The
    diagnostic must return promptly and report that this listed entry is
    non-regular or unreadable, not treat it as an omitted plugin program.
14. A symlink replacing `MANIFEST.json` that points to byte-identical
    content outside the method directory. Verification of an unmodified copy
    must not be inferred from following the symlink.

For controls 12–13 each subprocess is bounded to **2 seconds**; on timeout
the test records a failed control, forcibly ends that subprocess and restores
the original file. The test checks restoration after every mutation and at
completion. A timeout is a bounded observation of blocking under the test's
conditions, not proof of a remote denial-of-service exploit.

The build 22 binary passes the clean and manifest-listed-change controls,
but incorrectly succeeds for unlisted entries and substituted links. As an
unprivileged Linux account it also reports success for a present unreadable
optional tool. The disposable register incorrectly pins the injected module
tree as `FILES_VERIFIED_AGAINST_OWN_MANIFEST`. These results were reproduced
both with the full **58-file** method packet and with the **42-file text-only**
plugin method directory, in a separate local probe whose executable SHA-256
was `c2c6795d36027c6e9041d63c5349f97434fe5709a6bcb649f4146faee9f03dcd`.

The test requires the documented integrity-refusal **exit code 6** plus a
relevant diagnostic for negative checks; a crash or arbitrary nonzero exit
is **not** a pass. Discovery of the injected module is recorded as an
observation, not an acceptance condition, because a repaired host may
quarantine it. Source bytes are restored exactly after testing, and the
final clean control must verify again. The current binary is expected to
make this test exit 1 until the underlying source is repaired.

This is a separate pre-read availability failure: a named pipe substituted
for the manifest or a listed Specification blocks `fs::read` before the
old source-level directory scanner would run. An implementation fix must
inspect file types before reading, handle replacement races without following
symlinks, and bound reads. Nonblocking read opens on Linux are one means of
preventing a race-swapped FIFO from blocking; the verifier remains a
non-atomic filesystem diagnostic, not a lock or sandbox.

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
