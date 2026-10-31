"""V0.1.1 regression tests: one test per audit finding (F01, F03, G01) plus no-exception sweep."""
import unittest

from dna17_voxel.validator import (check_transition, validate_network,
                             validate_record)
from test_dna17_validator import make, net

BIG = 10 ** 1000
HUGE = 10 ** 10000  # repr() of this would hit the int->str digit limit
SUR = "\ud800"


def rec(mut):
    r = make("A", ["B"], bio=["B"])
    mut(r)
    return r


class F01HugeIntegers(unittest.TestCase):
    CASES = [
        ("ENERGY_DYNAMICS", lambda x, v: x.update(ENERGY_DYNAMICS=v)),
        ("SPECTRAL_MEMORY", lambda x, v: x.update(SPECTRAL_MEMORY=[v])),
        ("phase", lambda x, v: x["CYCLIC_INDEX"].update(phase=v)),
        ("Spectral_Signature", lambda x, v: x["SPECTRAL_FIELD"].update(Spectral_Signature=[v])),
        ("weight", lambda x, v: x["DYNAMIC_TOPOLOGICAL_STRUCTURE"]["links"][0].update(weight=v)),
        ("t", lambda x, v: x["DYNAMIC_TOPOLOGICAL_STRUCTURE"].update(t=v)),
        ("INNER_FORCE_VECTOR", lambda x, v: x.update(INNER_FORCE_VECTOR=[v, 0, 0])),
    ]

    def test_rejected_not_raised(self):
        for name, mut in self.CASES:
            for v in (BIG, -BIG, HUGE):
                with self.subTest(field=name, digits=len(str(abs(v))) if v != HUGE else 10001):
                    self.assertIn("E_TYPE", validate_record(rec(lambda x: mut(x, v))).codes())

    def test_normal_ints_still_accepted(self):
        # Superseded by D6 (V0.1.3): integers are bounded to +-(2**53-1); 10**300 is now rejected.
        self.assertTrue(validate_record(rec(lambda x: x.update(ENERGY_DYNAMICS=2 ** 53 - 1))).ok)
        self.assertIn("E_TYPE", validate_record(rec(lambda x: x.update(ENERGY_DYNAMICS=10 ** 300))).codes())
        self.assertTrue(validate_record(rec(lambda x: x.update(ENERGY_DYNAMICS=1e300))).ok)  # floats unaffected


class F03StrictUtf8(unittest.TestCase):
    CASES = [
        ("voxel_id", lambda x: x["INFORMATION_IDENTITY"].update(voxel_id=SUR)),
        ("payload", lambda x: x["INFORMATION_IDENTITY"].update(payload=SUR)),
        ("Chemical_Ref", lambda x: x["SPECTRAL_FIELD"].update(Chemical_Ref=SUR)),
        ("operator_id", lambda x: x["DYNAMIC_TOPOLOGICAL_STRUCTURE"]["tau"].update(operator_id=SUR)),
        ("version", lambda x: x["DYNAMIC_TOPOLOGICAL_STRUCTURE"]["tau"].update(version="0." + SUR)),
        ("source", lambda x: x["PROVENANCE_CONFIDENCE"].update(source=SUR)),
        ("bio_ref", lambda x: x.update(BIO_HOLOGRAPHIC_VOXEL_VECTOR=[SUR])),
    ]

    def test_lone_surrogates_rejected(self):
        for name, mut in self.CASES:
            with self.subTest(field=name):
                self.assertIn("E_UTF8", validate_record(rec(mut)).codes())

    def test_valid_non_ascii_accepted(self):
        payload = "Информациски идентитет 🧬"
        from dna17_voxel.validator import sha256_text
        r = rec(lambda x: x["INFORMATION_IDENTITY"].update(
            payload=payload, payload_sha256=sha256_text(payload)))
        self.assertTrue(validate_record(r).ok)


class G01EdgeContract(unittest.TestCase):
    def test_duplicate_link_rejected_in_both_profiles(self):
        r = rec(lambda x: x["DYNAMIC_TOPOLOGICAL_STRUCTURE"]["links"].append({"target": "B", "weight": 2.0}))
        for prof in ("N_EQUALS_LINK_TARGETS", "LINKS_SUBSET_OF_N"):
            with self.subTest(profile=prof):
                self.assertIn("E_DUPLICATE_LINK", validate_record(r, edge_contract=prof).codes())

    def test_neighbor_without_link(self):
        r = rec(lambda x: x["DYNAMIC_TOPOLOGICAL_STRUCTURE"].update(links=[]))
        self.assertIn("E_NEIGHBOR_WITHOUT_LINK", validate_record(r).codes())
        self.assertTrue(validate_record(r, edge_contract="LINKS_SUBSET_OF_N").ok)

    def test_link_target_must_be_string(self):
        r = rec(lambda x: x["DYNAMIC_TOPOLOGICAL_STRUCTURE"].update(links=[{"target": {}, "weight": 1}]))
        self.assertIn("E_TYPE", validate_record(r).codes())

    def test_unknown_profile_raises(self):
        with self.assertRaises(ValueError):
            validate_record(make("A", []), edge_contract="ANYTHING")


class NoUncaughtExceptions(unittest.TestCase):
    GARBAGE = [None, 0, BIG, HUGE, "x", SUR, [], {}, [None], {1: 2}, [[]], {"a": []}, 1.5, float("inf")]

    def test_record_level(self):
        for g in self.GARBAGE:
            with self.subTest(value=type(g).__name__):
                self.assertFalse(validate_record(g).ok)

    def test_every_field_replaced_with_garbage(self):
        base = make("A", ["B"], bio=["B"])
        for key in list(base):
            for g in self.GARBAGE:
                r = dict(base)
                r[key] = g
                with self.subTest(field=key, value=type(g).__name__):
                    validate_record(r)  # must not raise

    def test_network_and_transition(self):
        for g in self.GARBAGE:
            with self.subTest(value=type(g).__name__):
                self.assertFalse(validate_network(g).ok)
                self.assertFalse(check_transition(g, net()).ok)
                self.assertFalse(check_transition(net(), g).ok)


if __name__ == "__main__":
    unittest.main()
