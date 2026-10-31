"""Positive and negative tests (written for V0.1; carried forward to V0.1.3)."""
import copy
import unittest

from dna17_voxel.validator import (FIELD_KEYS, check_transition, sha256_text,
                             validate_network, validate_record)


def make(vid, neighbors, bio=(), t=0.0, payload=None, preserving=True):
    payload = payload if payload is not None else f"payload-{vid}"
    return {
        "VOXEL_UNIT": 1,
        "SPECTRAL_MEMORY": [0.1, 0.5, 0.0],
        "ENERGY_DYNAMICS": 2.0,
        "SPECTRAL_FIELD": {"Chemical_Ref": "H", "Spectral_Signature": [1.0, 0.2],
                           "Color_Projection": [0.2, 0.4, 1.0]},
        "TRANSFER_IMPEDANCE": 0.3,
        "VOXEL_CAPACITY": 1.0,
        "INNER_FORCE_VECTOR": [0.0, 1.0, -1.0],
        "RESONANT_HARMONIC": 0.7,
        "DIMENSIONAL_INDEX": 3,
        "CYCLIC_INDEX": {"phase": 0.25, "cycle_count": 0},
        "ORBITAL_PATH": [[0, 0, 0], [1, 0, 0]],
        "BIO_HOLOGRAPHIC_VOXEL_VECTOR": list(bio),
        "PROVENANCE_CONFIDENCE": {"source": "author", "confidence": 0.9},
        "DYNAMIC_TOPOLOGICAL_STRUCTURE": {
            "t": t, "neighbors": list(neighbors),
            "links": [{"target": n, "weight": 1.0} for n in neighbors],
            "tau": {"operator_id": "TAU_IDENTITY", "version": "0.1", "memory_preserving": preserving},
        },
        "INTERNAL_HARMONY": 0.8,
        "SPATIAL_TRANSLATION": [0.0, 0.0, 1.0],
        "INFORMATION_IDENTITY": {"voxel_id": vid, "payload": payload,
                                 "payload_sha256": sha256_text(payload)},
    }


def net(t=0.0):
    return [make("A", ["B"], bio=["B"], t=t), make("B", ["A"], t=t)]


class RecordTests(unittest.TestCase):
    def test_17_keys(self):
        self.assertEqual(len(FIELD_KEYS), 17)

    def test_valid_record(self):
        r = validate_record(make("A", []))
        self.assertTrue(r.ok, r.errors)

    def bad(self, mutate, code):
        rec = make("A", ["B"])
        mutate(rec)
        r = validate_record(rec)
        self.assertIn(code, r.codes(), r.errors)

    def test_missing_field(self):
        self.bad(lambda x: x.pop("INTERNAL_HARMONY"), "E_MISSING")

    def test_symbol_key_rejected(self):
        self.bad(lambda x: x.update({"H_i": 0.5}), "E_UNKNOWN_KEY")

    def test_voxel_unit(self):
        self.bad(lambda x: x.update({"VOXEL_UNIT": 2}), "E_RANGE")
        self.bad(lambda x: x.update({"VOXEL_UNIT": True}), "E_RANGE")

    def test_nan_and_bool(self):
        self.bad(lambda x: x.update({"ENERGY_DYNAMICS": float("nan")}), "E_TYPE")
        self.bad(lambda x: x.update({"TRANSFER_IMPEDANCE": True}), "E_TYPE")

    def test_negative_energy(self):
        self.bad(lambda x: x.update({"ENERGY_DYNAMICS": -1}), "E_RANGE")

    def test_capacity_zero(self):
        self.bad(lambda x: x.update({"VOXEL_CAPACITY": 0}), "E_RANGE")

    def test_harmony_range(self):
        self.bad(lambda x: x.update({"INTERNAL_HARMONY": 1.01}), "E_RANGE")

    def test_dimension(self):
        # D2 (V0.1.3): 11 is reported as reserved for the EIT_11D profile; other values stay E_RANGE.
        self.bad(lambda x: x.update({"DIMENSIONAL_INDEX": 11}), "E_RESERVED_PROFILE")
        self.bad(lambda x: x.update({"DIMENSIONAL_INDEX": 4}), "E_RANGE")

    def test_phase_open_interval(self):
        self.bad(lambda x: x["CYCLIC_INDEX"].update({"phase": 1.0}), "E_RANGE")

    def test_color(self):
        self.bad(lambda x: x["SPECTRAL_FIELD"].update({"Color_Projection": [0, 0, 2]}), "E_RANGE")

    def test_orbit_too_short(self):
        self.bad(lambda x: x.update({"ORBITAL_PATH": [[0, 0, 0]]}), "E_TYPE")

    def test_payload_hash(self):
        self.bad(lambda x: x["INFORMATION_IDENTITY"].update({"payload": "tampered"}), "E_PAYLOAD_HASH")

    def test_link_must_be_neighbor(self):
        self.bad(lambda x: x["DYNAMIC_TOPOLOGICAL_STRUCTURE"]["links"].append(
            {"target": "Z", "weight": 1}), "E_LINK_NOT_NEIGHBOR")

    def test_tau_extra_key_rejected(self):
        self.bad(lambda x: x["DYNAMIC_TOPOLOGICAL_STRUCTURE"]["tau"].update(
            {"code": "exec('x')"}), "E_UNKNOWN_KEY")


class NetworkTests(unittest.TestCase):
    def test_valid_network(self):
        r = validate_network(net(), symmetry="SYMMETRIC_REQUIRED")
        self.assertTrue(r.ok, r.errors)

    def test_unresolved(self):
        n = net()
        n[0]["BIO_HOLOGRAPHIC_VOXEL_VECTOR"] = ["Q"]
        self.assertIn("E_UNRESOLVED_REF", validate_network(n).codes())

    def test_duplicate_id(self):
        n = [make("A", []), make("A", [])]
        self.assertIn("E_DUPLICATE_ID", validate_network(n).codes())

    def test_self_reference(self):
        n = [make("A", ["A"])]
        self.assertIn("E_SELF_REFERENCE", validate_network(n).codes())

    def test_time_mismatch(self):
        n = net()
        n[1]["DYNAMIC_TOPOLOGICAL_STRUCTURE"]["t"] = 1.0
        self.assertIn("E_TIME_MISMATCH", validate_network(n).codes())

    def test_asymmetry_modes(self):
        n = [make("A", ["B"]), make("B", [])]
        directed = validate_network(n)
        self.assertTrue(directed.ok)
        self.assertEqual(len(directed.warnings), 1)
        self.assertIn("E_ASYMMETRIC", validate_network(n, "SYMMETRIC_REQUIRED").codes())


class TransitionTests(unittest.TestCase):
    def test_topology_may_change(self):
        before = net(0.0)
        after = net(1.0)
        after[0]["DYNAMIC_TOPOLOGICAL_STRUCTURE"]["neighbors"] = []
        after[0]["DYNAMIC_TOPOLOGICAL_STRUCTURE"]["links"] = []
        r = check_transition(before, after)
        self.assertTrue(r.ok, r.errors)  # P_T may vary

    def test_p_m_violation(self):
        before, after = net(0.0), net(1.0)
        after[0] = make("A", ["B"], bio=["B"], t=1.0, payload="new content")
        self.assertIn("E_P_M_VIOLATION", check_transition(before, after).codes())

    def test_non_preserving_may_rewrite(self):
        before = [make("A", ["B"], preserving=False), make("B", ["A"])]
        after = [make("A", ["B"], t=1.0, payload="new"), make("B", ["A"], t=1.0)]
        self.assertTrue(check_transition(before, after).ok)

    def test_provenance_frozen(self):
        before, after = net(0.0), net(1.0)
        after[1]["PROVENANCE_CONFIDENCE"]["confidence"] = 1.0
        self.assertIn("E_PROVENANCE_CHANGED", check_transition(before, after).codes())

    def test_identity_set(self):
        before, after = net(0.0), net(1.0)
        after.append(make("C", [], t=1.0))
        self.assertIn("E_IDENTITY_SET_CHANGED", check_transition(before, after).codes())

    def test_time_order(self):
        self.assertIn("E_TIME_ORDER", check_transition(net(1.0), net(1.0)).codes())

    def test_inputs_not_mutated(self):
        before, after = net(0.0), net(1.0)
        b0, a0 = copy.deepcopy(before), copy.deepcopy(after)
        check_transition(before, after)
        self.assertEqual((before, after), (b0, a0))


if __name__ == "__main__":
    unittest.main()
