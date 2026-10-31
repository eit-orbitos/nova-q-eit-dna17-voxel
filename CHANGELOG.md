# Changelog

## 0.1.3 — 2026-10-31 (release candidate)
- Decisions D1–D7 ratified by the author, Toni Mladenovski, on 2026-10-31 (D7 variant A: append-only).
- Decisions D1–D7 applied (see DECISIONS.md): snapshot envelope with schema version; DIMENSIONAL_INDEX {3,5} with 11 reserved;
  defaults DIRECTED_ALLOWED / N_EQUALS_LINK_TARGETS / BEFORE_GOVERNS; integers within ±(2**53−1); append-only spectral history under P_M.
- New `validate_snapshot`; new codes E_SCHEMA, E_RESERVED_PROFILE, E_SPECTRAL_HISTORY_REWRITTEN, W_SPECTRAL_APPENDED, W_SPECTRAL_CHANGED.
- Consolidated spec `spec/DNA17_FIELD_SPEC_V0_1_3.json`; package layout `src/dna17_voxel`.
- Two inherited test expectations intentionally updated (marked in the tests): DIMENSIONAL_INDEX=11 now E_RESERVED_PROFILE (D2); integer 10**300 now rejected (D6).
- 71 tests (29 V0.1 + 11 V0.1.1 + 16 V0.1.2 + 15 V0.1.3).

## 0.1.2 — 2026-10-31 (correction candidate)
- C4 no stringification of unvalidated values; C5 fullmatch for hashes; C6 τ transition semantics; C7 identifier format; C8 cycle_count bound.
- Deep structural fuzz (4070 mutants).

## 0.1.1 — 2026-10-31 (correction candidate)
- C1 huge integers rejected; C2 strict UTF-8; C3 duplicate links and edge-contract profiles.

## 0.1 — 2026-10-31 (type proposal)
- First typed proposal for the 17 fields, validator and 29 tests.
