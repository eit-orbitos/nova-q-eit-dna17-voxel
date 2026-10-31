# Version and review history

| Step | Artifact | SHA-256 | Verified by builder |
|---|---|---|---|
| Field registry (draft) | DNA17_FIELD_REGISTRY_DRAFT.json + binding note | — (supplied by reviewer chain) | read |
| V0.1 type proposal | DNA17_FIELD_SPEC_V0_1.zip | `519eee265ede9326f67162acce8ebd0860f2e74db8a9ffd77ee75ad65d958ec5` | yes |
| Audit of separate Kimi implementation | Kimi_Agent_DNA17_FIELD_SPEC_V0.1 (outer) | `4fd2b3d9ef83274d38660100963baf84fe059d9f40b90280d813dab87e766c56` | reported by reviewer |
| | DNA17_FIELD_SPEC_V0_1_KIMI_INDEPENDENT.zip | `649ae6d98e10a6386680849e53c3a272bb5cc7519fbe3efc7edb473a300c04f5` | reported by reviewer |
| Scoped cross-audit V0.1 | NOVA_Q_EIT_DNA17_V01_SCOPED_CROSS_AUDIT_20261031.zip | `fcc437d6ded0a857f7632b8eae45912008d2a86194f7aeaffc970e3de68ef1d3` | yes (7/7 internal hashes) |
| V0.1.1 correction | DNA17_FIELD_SPEC_V0_1_1_CORRECTION_CANDIDATE.zip | `efe3a042a7cbe7361b26285e86fbd0bd516789c1c24222e63b8b9b82ba56bca9` | yes |
| Replay of V0.1.1 | reviewer ZIP | `ef268f6597e6940eea89c1042dd9fd68614aecb672ce88a1e56bd21f243d73d1` | reported by reviewer, not received |
| V0.1.2 correction | DNA17_FIELD_SPEC_V0_1_2_CORRECTION_CANDIDATE.zip | `d4bf32be6a05397b29002f883eacff64bd41fc69e445fcb4199ffa2cd5b016f4` | yes |
| Replay of V0.1.2 (PASS_WITH_NOTES) | reviewer ZIP | `127670b57a81721aebe94dc58bbe25324b93269a9de182e75f64ab34b2a04536` | reported by reviewer, not received |
| V0.1.3 release candidate | this repository | see `MANIFEST.sha256` | — |

## Review findings and where they were closed
| Finding | Source | Closed in |
|---|---|---|
| F01 huge integer crash | cross-audit V0.1 | C1 (V0.1.1), D6 (V0.1.3) |
| F02 unhashable τ | cross-audit V0.1 | not applicable to this implementation |
| F03 lone surrogate | cross-audit V0.1 | C2 (V0.1.1) |
| F04 mixed key sort | cross-audit V0.1 | not applicable to this implementation |
| G01 edge contract gap | cross-audit V0.1 | C3 (V0.1.1), D4 (V0.1.3) |
| G02 schema_version in VOXEL_UNIT | cross-audit V0.1 | D1 (V0.1.3) |
| R1–R3 int→str limit | replay V0.1.1 | C4 (V0.1.2) |
| R4 hash trailing newline | replay V0.1.1 | C5 (V0.1.2) |
| R5 τ semantics | replay V0.1.1 | C6 (V0.1.2), D5 (V0.1.3) |
| control chars, unbounded counter | builder fuzz | C7, C8 (V0.1.2) |
| S01 P_M spectral scope | replay V0.1.2 | D7 (V0.1.3) |
| baseline manifests list files not carried | replay V0.1.2 | baselines replaced by this hash table |

Common-mode note: F01 and F03 occurred in both independent implementations (this one and Kimi's).
Two implementations agreeing is not evidence of correctness.
