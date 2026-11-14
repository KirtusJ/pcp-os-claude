# Build 22 clause source-snapshot regression (unfixed)

**Status:** Reproduced on the distributed Linux x86_64 `pcpos` build 22 executable. This PR contains only a bounded regression reproducer and acceptance criteria. The Rust source is in the separately supplied proprietary `PCP_OS_Rust` archive, not in this plugin repository. Neither the binary nor the governing method is changed.

## Run

```sh
python3 tests/clause_snapshot_regression.py
```

Optional positional arguments are a path to a compatible `pcpos` binary and a method directory.

The test makes a temporary copy of `method/`, creates two complete variants of Core Specification §1.1 with independently calculated SHA-256 values, then asks the binary for `clause core 1.1` under two stable-source controls and a bounded sequence of atomic replacements.

- **Exit 1:** a mismatched whole-Specification SHA-256 header and served §1.1 variant was *observed*. This is a confirmed failure on the tested invocation.
- **Exit 0:** no mismatch was found *in this finite run*. This is **not** evidence that the race has been repaired.
- **Exit 2:** the swapping thread reported an error.

The script does not change a real register, commission a review, obtain new authority, or modify the distributed method. The writer is one Python thread in the same test process, not an AI subagent or an independent reviewer.

## Exact mechanism

In build 22's `crates/pcpos-host/src/pcpos.rs`, `modules_and_oddities()` reads each Specification to compute `Module.sha256`. `clause_text()` later reads the selected file again, then prints that earlier SHA in its header while rendering the later read.

Under atomic file replacement, each read can observe a different **complete** Specification. The returned clause can then bear the wrong *whole-Specification* digest. The separately printed provision digest is derived from the rendered text and is **not** implicated by this reproduction.

Two stable-file controls passed. Under a bounded swap run of the original binary (82 atomic replacements across the first three clause requests), two clauses returned with the *other* variant's Specification digest, all with exit 0. This is not a rate estimate or an assertion about normal deployment. It does not by itself establish any failure of the register guard or privilege system.

## Acceptance requirements

1. Use a coherent byte snapshot to derive the returned module identity, entire-Specification digest and provision text.
2. A file changed between module discovery and clause rendering should either be refused as changed, or labelled consistently from the same *new* snapshot. No mixed-source identity.
3. Retain the existing duplicate-module ambiguity refusal and the 4 MiB Specification-size policy; consider symlink/path replacement explicitly.
4. Test stable-file positive controls, mismatched-content negative controls, and a **deterministic Rust unit test** of the single-snapshot or digest-comparison invariant. A bounded race stress test alone is not sufficient.
5. Exercise `pcpos clause` and MCP `acr_clause`, which share `clause_text()`, before declaring both corrected.
6. Rebuild all released target binaries, update release indexes, confirm permissions and reproducibility, and rerun the existing suites.

This is distinct from [method-directory inventory issue #1](https://github.com/KirtusJ/pcp-os-claude/issues/1) and its [draft regression PR #2](https://github.com/KirtusJ/pcp-os-claude/pull/2). Fixing the whole-tree inventory scanner alone does not remove the two-read clause inconsistency.

**Related issue:** #4.

**No claim:** compiled Rust fix, host-enforced ACR compliance, independent calibration, or production suitability.
