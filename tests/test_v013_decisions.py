"""V0.1.3 tests for decisions D1-D7 (DECISIONS.md)."""
import copy
import unittest

from dna17_voxel.validator import (SCHEMA_VERSION, SPEC_ID, check_transition,
                                   validate_record, validate_snapshot)
from test_dna17_validator import make, net


def snap(voxels=None, **over):
    env = {"schema_id": SPEC_ID, "schema_version": SCHEMA_VERSION,
           "voxels": voxels if voxels is not None else net()}
    env.update(over)
    return env


class D1Envelope(unittest.TestCase):
    def test_valid_snapshot(self):
        self.assertTrue(validate_snapshot(snap()).ok)

    def test_unknown_version_rejected(self):
        for v in ("0.1.2", "0.2", "2", 2, None):
            with self.subTest(version=repr(v)):
                self.assertIn("E_SCHEMA", validate_snapshot(snap(schema_version=v)).codes())

    def test_wrong_schema_id(self):
        self.assertIn("E_SCHEMA", validate_snapshot(snap(schema_id="OTHER")).codes())

    def test_extra_or_missing_envelope_keys(self):
        self.assertIn("E_UNKNOWN_KEY", validate_snapshot(snap(extra=1)).codes())
        env = snap()
        del env["voxels"]
        self.assertIn("E_MISSING", validate_snapshot(env).codes())

    def test_voxel_unit_stays_literal_one(self):
        v = net()
        v[0]["VOXEL_UNIT"] = {"schema_version": 1}
        self.assertFalse(validate_snapshot(snap(v)).ok)

    def test_garbage_envelope(self):
        for g in (None, [], "x", 10 ** 10000, {"\ud800": 1}):
            with self.subTest(value=type(g).__name__):
                self.assertFalse(validate_snapshot(g).ok)


class D2Dimensions(unittest.TestCase):
    def test_profile(self):
        for d, code in ((3, None), (5, None), (11, "E_RESERVED_PROFILE"), (4, "E_RANGE"), (0, "E_RANGE")):
            r = make("A", [])
            r["DIMENSIONAL_INDEX"] = d
            rep = validate_record(r)
            with self.subTest(dim=d):
                self.assertTrue(rep.ok) if code is None else self.assertIn(code, rep.codes())


class D6SafeIntegers(unittest.TestCase):
    def test_bounds_in_every_numeric_position(self):
        muts = [
            lambda x, v: x.update(ENERGY_DYNAMICS=v),
            lambda x, v: x.update(INNER_FORCE_VECTOR=[v, 0, 0]),
            lambda x, v: x["DYNAMIC_TOPOLOGICAL_STRUCTURE"].update(t=v),
            lambda x, v: x.update(SPATIAL_TRANSLATION=[0, v, 0]),
        ]
        for k, m in enumerate(muts):
            for v, ok in ((2 ** 53 - 1, True), (-(2 ** 53 - 1), True), (2 ** 53, False), (-(2 ** 53), False)):
                if k == 0 and v < 0:
                    continue  # ENERGY_DYNAMICS has its own lower bound 0
                r = make("A", [])
                m(r, v)
                with self.subTest(position=k, value=v):
                    self.assertEqual(validate_record(r).ok, ok)


class D7SpectralHistory(unittest.TestCase):
    def pair(self, preserving):
        before = [make("A", ["B"], bio=["B"], preserving=preserving), make("B", ["A"])]
        after = [make("A", ["B"], bio=["B"], t=1.0), make("B", ["A"], t=1.0)]
        return before, after

    def codes(self, rep):
        return rep.codes(), {w[0] for w in rep.warnings}

    def test_append_allowed_and_reported(self):
        b, a = self.pair(True)
        a[0]["SPECTRAL_MEMORY"] = b[0]["SPECTRAL_MEMORY"] + [0.9]
        a[0]["SPECTRAL_FIELD"]["Spectral_Signature"] = b[0]["SPECTRAL_FIELD"]["Spectral_Signature"] + [0.4]
        rep = check_transition(b, a)
        self.assertTrue(rep.ok, rep.errors)
        self.assertIn("W_SPECTRAL_APPENDED", self.codes(rep)[1])

    def test_rewrite_rejected_when_protected(self):
        for field in ("memory", "signature", "chemical", "truncate"):
            b, a = self.pair(True)
            if field == "memory":
                a[0]["SPECTRAL_MEMORY"][0] = 0.11
            elif field == "signature":
                a[0]["SPECTRAL_FIELD"]["Spectral_Signature"][1] = 0.3
            elif field == "chemical":
                a[0]["SPECTRAL_FIELD"]["Chemical_Ref"] = "O"
            else:
                a[0]["SPECTRAL_MEMORY"] = a[0]["SPECTRAL_MEMORY"][:1]
            with self.subTest(field=field):
                self.assertIn("E_SPECTRAL_HISTORY_REWRITTEN", check_transition(b, a).codes())

    def test_rewrite_allowed_but_reported_when_not_protected(self):
        b, a = self.pair(False)
        a[0]["SPECTRAL_MEMORY"] = [0.0]
        rep = check_transition(b, a)
        self.assertTrue(rep.ok, rep.errors)
        self.assertIn("W_SPECTRAL_CHANGED", self.codes(rep)[1])

    def test_color_projection_is_derived(self):
        b, a = self.pair(True)
        a[0]["SPECTRAL_FIELD"]["Color_Projection"] = [1.0, 0.0, 0.0]
        rep = check_transition(b, a)
        self.assertTrue(rep.ok, rep.errors)
        self.assertIn("W_SPECTRAL_CHANGED", self.codes(rep)[1])

    def test_strict_policy_protects_from_after_declaration(self):
        b, a = self.pair(False)
        a[0]["DYNAMIC_TOPOLOGICAL_STRUCTURE"]["tau"]["memory_preserving"] = True
        a[0]["SPECTRAL_MEMORY"] = [0.0]
        self.assertTrue(check_transition(b, a).ok)
        self.assertIn("E_SPECTRAL_HISTORY_REWRITTEN",
                      check_transition(b, a, tau_policy="EITHER_PRESERVING_PROTECTS").codes())

    def test_unchanged_is_silent(self):
        b, a = self.pair(True)
        rep = check_transition(b, a)
        self.assertTrue(rep.ok)
        self.assertFalse({w for w in self.codes(rep)[1] if w.startswith("W_SPECTRAL")})


class DefaultsD3D4D5(unittest.TestCase):
    def test_defaults(self):
        import inspect
        from dna17_voxel import validator as V
        self.assertEqual(inspect.signature(V.validate_network).parameters["symmetry"].default, "DIRECTED_ALLOWED")
        self.assertEqual(V.DEFAULT_EDGE_CONTRACT, "N_EQUALS_LINK_TARGETS")
        self.assertEqual(V.DEFAULT_TAU_POLICY, "BEFORE_GOVERNS")


if __name__ == "__main__":
    unittest.main()
