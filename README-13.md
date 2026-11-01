# NOVA Q / EIT — DNA17 Voxel Validator

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23847201.svg)](https://doi.org/10.5281/zenodo.23847201)

**Version:** 0.1.3 · **Author concept:** Toni Mladenovski ([ORCID 0009-0009-8343-662X](https://orcid.org/0009-0009-8343-662X)) · **Builder:** Claude (Anthropic)

A typed data model and fail-closed validator for the **DNA17 voxel**: a 17-field record with a mandatory dynamic topological structure.

$$V_i(t)=\langle 1,M_i,E_i,\Sigma_i,Z_i,C_i,F_i,Rh_i,D_i,Re_i,O_i,Vb_i,P_i,\mathcal T_i(t),H_i,X_i,I_i\rangle,\qquad \mathcal T_i(t)=(\mathcal N_i(t),\mathcal E_i(t),\tau_i(t))$$

In the author's research direction, the DNA17 voxel is a candidate unit of memory and state for future AI architectures. In these, information carries its identity, provenance, spectral history and changing neighborhood together, and every change of state is auditable. This repository delivers the first engineering layer of that idea. It provides a precise, tested contract for what a valid voxel, network and transition are.

## Claim boundary

**Software only.** All values are dimensionless symbols: impedance is not in ohms, capacity is not in farads, and energy is not in joules. No physical, biological, chemical, holographic or cognitive claim is made. τ is a reference to a registered operator and is never executed.

## What it checks

| Function | Checks |
|---|---|
| `validate_record` | 17 fields, types, domains, strict UTF-8, identifier format, payload SHA-256 |
| `validate_network` | unique IDs, resolved references, one shared *t*, symmetry profile, edge contract |
| `check_transition` | identity set stable, time order, provenance fixed, P_M (identity + append-only spectral history), τ semantics, nothing silent |
| `validate_snapshot` | envelope `{schema_id, schema_version, voxels}`; unknown versions rejected |

The field table, invariants and error codes are in `spec/DNA17_FIELD_SPEC_V0_1_3.json`. The seven design decisions are in `DECISIONS.md`. The author ratified them on 2026-10-31.

## Run

Requires Python ≥ 3.10 and nothing else (standard library only).

```sh
PYTHONPATH=src python -m unittest discover -s tests -v   # 71 tests, incl. 4070-mutant fuzz
python -I -B probes/probes_equivalent.py                 # 24 audit probes
python scripts/manifest.py verify                        # SHA-256 of every file
```

```python
from dna17_voxel import validate_snapshot
report = validate_snapshot(snapshot)
print(report.ok, report.errors, report.warnings)
```

## Release and archive

| | |
|---|---|
| GitHub release | [v0.1.3](https://github.com/eit-orbitos/nova-q-eit-dna17-voxel/releases/tag/v0.1.3), commit `f22bff5` |
| Zenodo, this version | [10.5281/zenodo.23847202](https://doi.org/10.5281/zenodo.23847202) |
| Zenodo, all versions | [10.5281/zenodo.23847201](https://doi.org/10.5281/zenodo.23847201) |
| Signed reference ZIP | SHA-256 `df2a20d85f8f441fd06160bd33deef54d72acecce7a3b3d6b4b88ec8dbcae532`, attached to the release and the Zenodo record |

## Verification status

- 71/71 tests pass, 24/24 audit probes pass, and 4070 structural mutants raise 0 uncaught exceptions.
- CI on Linux, macOS and Windows with Python 3.10, 3.12 and 3.13: 9/9 PASS on `f22bff5` ([Actions logs](https://github.com/eit-orbitos/nova-q-eit-dna17-voxel/actions)). This shows cross-platform reproducibility, not scientific validation.
- Independent review 2 (Kimi, 2026-11-01): **PASS**. The report is attached to release v0.1.3 and the Zenodo record, in the original Macedonian and an English translation.
- History: three review rounds (V0.1 → V0.1.3). See `history/VERSION_HISTORY.md`.
- **Fail-closed scope:** JSON-like inputs. Not covered: Python objects with custom `__eq__` / `__hash__` / `__float__`, recursion-depth attacks, and memory exhaustion.

## Not in scope

- H-Space V0.4 binding and `information_key` derivation
- canonical binary serializer
- GF(2) memory-recovery code
- the separate Kimi implementation

```
HASH ≠ SCIENTIFIC PROOF · MULTI_AI_AGREEMENT ≠ TRUTH · ZENODO ≠ VALIDATION
```

## License and citation

- Software is licensed under the **PolyForm Noncommercial 1.0.0** (`LICENSE`).
- Documentation and specification are licensed under **CC BY-NC-SA 4.0** (`LICENSE-DOCS.md`).
- Commercial use requires a separate written agreement: info@eitnetworks.org. See `NOTICE.md`.
- Please cite using `CITATION.cff`.

---

**МК — накратко:** Ова е софтверски валидатор за DNA17 вокселот: 17 полиња со задолжителна динамичка топологија. Тврдењето е само софтверско. Седумте одлуки се во `DECISIONS.md`. Авторот ги ратификуваше на 31.10.2026.
