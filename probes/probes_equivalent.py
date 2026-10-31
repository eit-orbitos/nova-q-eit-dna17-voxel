"""Semantic-equivalent of the SCOPED_CROSS_AUDIT_V0_1 probes (F01-F04, G01, G02),
translated to the DNA17 record shape. Usage (from repository root):
    python3 -I -B probes/probes_equivalent.py
Prints JSON; exit code 1 unless every probe meets expectation with 0 exceptions.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "tests"))
import dna17_voxel.validator as V  # noqa: E402
import test_dna17_validator as T  # noqa: E402

BIG = 10 ** 1000
SUR = "\ud800"


def run(case, fn, args, expected):
    try:
        rep = fn(*args)
        observed = "ACCEPT" if rep.ok else "REJECT"
        detail = sorted(rep.codes())
    except BaseException as ex:  # noqa: BLE001 - probes must catch everything
        observed, detail = "EXCEPTION", repr(ex)[:120]
    return {"case": case, "expected": expected, "observed": observed,
            "detail": detail, "met": observed == expected}


def rec(mut):
    r = T.make("A", ["B"], bio=["B"])
    mut(r)
    return r


def net_with(mut_a):
    n = T.net()
    mut_a(n[0])
    return n


R = V.validate_record
N = V.validate_network
P = []
P.append(run("reference_valid_network", N, (T.net(),), "ACCEPT"))
# F01 giant integers
P.append(run("F01_energy", R, (rec(lambda x: x.update(ENERGY_DYNAMICS=BIG)),), "REJECT"))
P.append(run("F01_memory", R, (rec(lambda x: x.update(SPECTRAL_MEMORY=[BIG])),), "REJECT"))
P.append(run("F01_cyclic_phase", R, (rec(lambda x: x["CYCLIC_INDEX"].update(phase=BIG)),), "REJECT"))
P.append(run("F01_spectral_signature", R, (rec(lambda x: x["SPECTRAL_FIELD"].update(Spectral_Signature=[BIG])),), "REJECT"))
P.append(run("F01_link_weight", R, (rec(lambda x: x["DYNAMIC_TOPOLOGICAL_STRUCTURE"]["links"][0].update(weight=BIG)),), "REJECT"))
P.append(run("F01_time_t", R, (rec(lambda x: x["DYNAMIC_TOPOLOGICAL_STRUCTURE"].update(t=BIG)),), "REJECT"))
# F02 tau wrong container types
P.append(run("F02_tau_list", R, (rec(lambda x: x["DYNAMIC_TOPOLOGICAL_STRUCTURE"].update(tau=[])),), "REJECT"))
P.append(run("F02_tau_dict_empty", R, (rec(lambda x: x["DYNAMIC_TOPOLOGICAL_STRUCTURE"].update(tau={})),), "REJECT"))
P.append(run("F02_neighbor_is_list", R, (rec(lambda x: x["DYNAMIC_TOPOLOGICAL_STRUCTURE"].update(neighbors=[["B"]])),), "REJECT"))
P.append(run("F02_link_target_is_dict", R, (rec(lambda x: x["DYNAMIC_TOPOLOGICAL_STRUCTURE"].update(links=[{"target": {}, "weight": 1}])),), "REJECT"))
# F03 lone surrogates
P.append(run("F03_voxel_id", R, (rec(lambda x: x["INFORMATION_IDENTITY"].update(voxel_id=SUR)),), "REJECT"))
P.append(run("F03_payload", R, (rec(lambda x: x["INFORMATION_IDENTITY"].update(payload=SUR)),), "REJECT"))
P.append(run("F03_chemical_ref", R, (rec(lambda x: x["SPECTRAL_FIELD"].update(Chemical_Ref=SUR)),), "REJECT"))
P.append(run("F03_operator_id", R, (rec(lambda x: x["DYNAMIC_TOPOLOGICAL_STRUCTURE"]["tau"].update(operator_id=SUR)),), "REJECT"))
# F04 mixed unknown key types
P.append(run("F04_mixed_unknown_keys", R, (rec(lambda x: x.update({123: 0, "another_unknown": 0})),), "REJECT"))
# G01 topology contract (expected = proposed V0.1.1 contract)
P.append(run("G01_neighbor_without_link", N, (net_with(lambda a: a["DYNAMIC_TOPOLOGICAL_STRUCTURE"].update(links=[])),), "REJECT"))
P.append(run("G01_link_without_neighbor", R, (rec(lambda x: x["DYNAMIC_TOPOLOGICAL_STRUCTURE"].update(neighbors=[])),), "REJECT"))
P.append(run("G01_duplicate_links", R, (rec(lambda x: x["DYNAMIC_TOPOLOGICAL_STRUCTURE"]["links"].append({"target": "B", "weight": 2.0})),), "REJECT"))
# G02 VOXEL_UNIT literal 1 (author axiom)
P.append(run("G02_voxel_unit_schema_dict", R, (rec(lambda x: x.update(VOXEL_UNIT={"schema_version": 2})),), "REJECT"))
P.append(run("G02_voxel_unit_float_1", R, (rec(lambda x: x.update(VOXEL_UNIT=1.0)),), "REJECT"))
# extra structural
P.append(run("X_network_not_list", N, ({"A": 1},), "REJECT"))
P.append(run("X_record_not_dict", N, ([1, 2],), "REJECT"))
P.append(run("X_transition_garbage", V.check_transition, (None, "x"), "REJECT"))

out = {"validator_spec_id": V.SPEC_ID, "probes": P,
       "met": sum(p["met"] for p in P), "total": len(P),
       "exceptions": sum(p["observed"] == "EXCEPTION" for p in P)}
print(json.dumps(out, indent=1, ensure_ascii=True))
sys.exit(0 if out["met"] == out["total"] and out["exceptions"] == 0 else 1)
