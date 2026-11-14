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

During concurrent replacement, an explicit `exit 6` refusal stating that the Specification **changed during clause retrieval** counts as an appropriate defense, not a mixed-identity failure. Other nonzero exits are reported as unexpected failures. A successful clause response must always pair its rendered variant with that variant's full Specification SHA.

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


## Concurrent named-pipe replacement control

Run `python3 tests/clause_fifo_race_regression.py` on a compatible Linux x86_64 host. It uses the packaged binary and makes only a temporary copy of `method/`. It checks:

1. A stable regular Core Specification is served successfully (exit 0).
2. A stable FIFO substituted for Core is refused promptly (exit 6; no Core module is discoverable).
3. During atomic replacement of the same path between complete regular-file contents and a FIFO, each `pcpos clause` subprocess either returns or is forcibly terminated after 0.45 seconds; at most eight calls are made.
4. For a timed-out child, Linux `/proc/<pid>/wchan` is read when permitted. This is diagnostic only and is not used as a correctness oracle.

**Exit 1:** a timed-out child was observed during the adversarial swapping; an availability defect remains in this run. **Exit 0:** no timeout observed in this bounded run, which is *not* evidence of race freedom. **Exit 2:** prerequisites or writer failed; no behavioral conclusion. The source-level property must be checked deterministically and the normal suite run before claiming a repair.

The original build 22 executable was separately tested. Stable regular Core returned exit 0 in **4.3 ms**; stable FIFO returned exit 6 in **2.4 ms**. Under atomic regular/FIFO replacement, the first clause command remained unfinished at 350 ms, and `/proc/<pid>/wchan` showed **`wait_for_partner`** while it was sleeping. There were **1,575 completed swap cycles** with no writer error. That Linux wait channel is consistent with opening a FIFO without a reader/writer counterpart. These are artificial local conditions, not deployment rates or remote-access findings.

The Rust source currently uses a separate `fs::metadata` then `fs::read` in module discovery and `fs::read_to_string` for clause rendering. Fixing only the digest comparison in the second read would still leave a blocking path. The implementation should use a bounded, non-following, nonblocking regular-file reader for **both discovery and clause rendering**, and refuse to label returned bytes with another read's Specification digest.

This is still an evidence/acceptance PR. It contains neither the proprietary Rust workspace nor rebuilt binaries. See linked issue #4.
