# DNA17 V0.1.3 — Decision Record

Seven engineering decisions closed in V0.1.3. Each was proposed by the builder (Claude) and reviewed by the independent reviewer. The review history is in `history/VERSION_HISTORY.md`.

**Status: RATIFIED by the author on 2026-10-31.** D1–D7 are normative for V0.1.3. Ratification is not a freeze: the release stays a pre-release (`v0.1.3-rc1`) until independent verification passes.

| # | Decision | V0.1.3 rule | Alternative kept | Why |
|---|---|---|---|---|
| D1 | `VOXEL_UNIT` | Literal integer `1`. The schema version lives in the snapshot envelope `{schema_id, schema_version, voxels}`. Unknown versions are rejected. | — | Preserves the author's axiom *Voxel = 1*, while versioning stays explicit and fail-closed. |
| D2 | `DIMENSIONAL_INDEX` | `{3, 5}`. `11` returns `E_RESERVED_PROFILE`. | Separate future `EIT_11D` profile | The 3D/5D mapping is the stated meaning. 11D needs its own versioned contract. |
| D3 | Neighborhood symmetry | `DIRECTED_ALLOWED` (asymmetry → warning) | `SYMMETRIC_REQUIRED` | Dynamic topology can be directed. Symmetry is a choice, not a law. |
| D4 | Edge contract | `N_EQUALS_LINK_TARGETS` | `LINKS_SUBSET_OF_N` (compatibility) | One link per neighbor removes ambiguity between N and E. |
| D5 | τ policy | `BEFORE_GOVERNS` | `EITHER_PRESERVING_PROTECTS` (strict) | Follows τᵢ : Vᵢ(t) → Vᵢ(t+dt). The operator at *t* produced *t+dt*. |
| D6 | Integer range | Every integer in a numeric field lies within ±(2⁵³−1). Floats are unaffected. | — | Exact across JSON, Python, JavaScript and IEEE-754. Prevents silent precision loss. |
| D7 | P_M scope (S01) | Under a protected transition, the spectral history is **append-only**: existing `SPECTRAL_MEMORY` and `Spectral_Signature` entries and `Chemical_Ref` are fixed, and new entries may be appended. `Color_Projection` is derived and may change. Every spectral change is reported. | Identity-only (V0.1.2 behaviour); full freeze | `SPECTRAL_MEMORY` is defined as the *record of information*, so a memory-preserving step must not rewrite it. Appending keeps learning possible. This matches the original binding note: "writeback can append new information". |

## Ratification

```
Ratified by:  Toni Mladenovski (author, freeze authority)
ORCID:        0009-0009-8343-662X
Date:         2026-10-31
Accepted:     D1 [x]  D2 [x]  D3 [x]  D4 [x]  D5 [x]  D6 [x]  D7 [x]
D7 variant:   A — append-only spectral history (chosen over B, identity-only)
Changes:      none
```

Any decision that is changed produces V0.1.4, with new tests and a new hash. Decisions are never edited in place after a release.
