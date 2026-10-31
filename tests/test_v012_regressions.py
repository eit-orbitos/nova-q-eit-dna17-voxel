"""V0.1.2 regression tests: the five V0.1.1 replay findings (R1-R5) plus a deep
structural fuzz that injects garbage at every nested position, dict key and list slot."""
import copy
import math
import unittest

from dna17_voxel.validator import (check_transition, sha256_text, validate_network,
                             validate_record)
from test_dna17_validator import make, net

HUGE = 10 ** 10000  # str()/repr() raises ValueError (int->str digit limit)
SUR = "\ud800"


def rec(mut):
    r = make("A", ["B"], bio=["B"])
    mut(r)
    return r


class R1toR3HugeIntegersInStringPositions(unittest.TestCase):
    def test_bio_vector(self):
        self.assertIn("E_TYPE", validate_record(rec(lambda x: x.update(BIO_HOLOGRAPHIC_VOXEL_VECTOR=[HUGE]))).codes())

    def test_neighbors(self):
        r = rec(lambda x: x["DYNAMIC_TOPOLOGICAL_STRUCTURE"].update(neighbors=[HUGE]))
        self.assertIn("E_TYPE", validate_record(r).codes())

    def test_unknown_keys(self):
        for k in (HUGE, -HUGE, SUR, (1, 2), None, 1.5):
            with self.subTest(key=type(k).__name__):
                rep = validate_record(rec(lambda x: x.update({k: 0})))
                self.assertIn("E_UNKNOWN_KEY", rep.codes())
                for _, where, _ in rep.errors:
                    where.encode("utf-8")  # report text itself must be clean UTF-8

    def test_unknown_nested_key(self):
        rep = validate_record(rec(lambda x: x["CYCLIC_INDEX"].update({HUGE: 0})))
        self.assertIn("E_UNKNOWN_KEY", rep.codes())


class R4HashFullmatch(unittest.TestCase):
    def test_source_sha_trailing_newline(self):
        h = sha256_text("src")
        ok = rec(lambda x: x["PROVENANCE_CONFIDENCE"].update(source_sha256=h))
        self.assertTrue(validate_record(ok).ok)
        for bad in (h + "\n", h + "\r\n", " " + h, h.upper(), h[:-1]):
            with self.subTest(variant=repr(bad[-2:])):
                r = rec(lambda x: x["PROVENANCE_CONFIDENCE"].update(source_sha256=bad))
                self.assertIn("E_HASH_FORMAT", validate_record(r).codes())

    def test_payload_sha_trailing_newline(self):
        r = rec(lambda x: x["INFORMATION_IDENTITY"].update(
            payload_sha256=x["INFORMATION_IDENTITY"]["payload_sha256"] + "\n"))
        self.assertIn("E_HASH_FORMAT", validate_record(r).codes())


class R5TransitionSemantics(unittest.TestCase):
    def flip(self):
        before = [make("A", ["B"], preserving=False), make("B", ["A"])]
        after = [make("A", ["B"], t=1.0, payload="rewritten", preserving=True), make("B", ["A"], t=1.0)]
        return before, after

    def test_before_governs_allows_but_reports(self):
        rep = check_transition(*self.flip())
        self.assertTrue(rep.ok, rep.errors)
        codes = {w[0] for w in rep.warnings}
        self.assertIn("W_TAU_DECLARATION_CHANGED", codes)
        self.assertIn("W_IDENTITY_REWRITTEN", codes)

    def test_strict_policy_rejects(self):
        rep = check_transition(*self.flip(), tau_policy="EITHER_PRESERVING_PROTECTS")
        self.assertIn("E_P_M_VIOLATION", rep.codes())

    def test_preserving_before_still_rejected(self):
        before, after = net(0.0), net(1.0)
        after[0] = make("A", ["B"], bio=["B"], t=1.0, payload="x")
        for pol in ("BEFORE_GOVERNS", "EITHER_PRESERVING_PROTECTS"):
            with self.subTest(policy=pol):
                self.assertIn("E_P_M_VIOLATION", check_transition(before, after, tau_policy=pol).codes())

    def test_unknown_policy_raises(self):
        with self.assertRaises(ValueError):
            check_transition(net(0.0), net(1.0), tau_policy="X")


# ---------- deep structural fuzz ----------

GARBAGE = [None, True, False, 0, -1, 1.5, float("nan"), float("inf"), -float("inf"),
           10 ** 1000, HUGE, -HUGE, "", " ", SUR, "x\n", "\x00", [], {}, [HUGE], [SUR],
           {HUGE: 1}, {SUR: 1}, (1, 2), b"bytes", [[[]]], {"t": {}}]
BAD_KEYS = [HUGE, SUR, None, 1.5, (1, 2), 0, "", "extra"]


def paths(o, prefix=()):
    """Yield every container path (dict key / list index) in a JSON-like object."""
    if isinstance(o, dict):
        for k, v in o.items():
            yield prefix + (k,)
            yield from paths(v, prefix + (k,))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield prefix + (i,)
            yield from paths(v, prefix + (i,))


def containers(o, prefix=()):
    if isinstance(o, (dict, list)):
        yield prefix
        items = o.items() if isinstance(o, dict) else enumerate(o)
        for k, v in items:
            yield from containers(v, prefix + (k,))


def at(o, path):
    for p in path:
        o = o[p]
    return o


class DeepFuzzNoUncaughtExceptions(unittest.TestCase):
    def mutants(self):
        base = net()
        for p in list(paths(base)):
            for g in GARBAGE:
                m = copy.deepcopy(base)
                at(m, p[:-1])[p[-1]] = g
                yield p, m
        for p in list(containers(base)):
            target = at(base, p)
            if isinstance(target, dict):
                for k in BAD_KEYS:
                    m = copy.deepcopy(base)
                    at(m, p)[k] = 0
                    yield p + ("+key",), m
            else:
                for g in GARBAGE:
                    m = copy.deepcopy(base)
                    at(m, p).append(g)
                    yield p + ("+item",), m

    def test_every_mutant(self):
        n = rejected = 0
        reference = net(1.0)
        for p, m in self.mutants():
            n += 1
            try:
                rep = validate_network(m)
                check_transition(m, reference)
                check_transition(reference, m)
                for _, where, msg in rep.errors + rep.warnings:
                    where.encode("utf-8")
                    msg.encode("utf-8")
            except Exception as ex:  # noqa: BLE001
                self.fail(f"uncaught {type(ex).__name__} at path of length {len(p)}")
            rejected += not rep.ok
        self.__class__.counts = (n, rejected)
        self.assertGreater(n, 2000)

    def test_valid_base_is_accepted(self):
        self.assertTrue(validate_network(net()).ok)


if __name__ == "__main__":
    unittest.main()


class C7C8FoundByFuzz(unittest.TestCase):
    IDENT_FIELDS = [
        ("operator_id", lambda x, v: x["DYNAMIC_TOPOLOGICAL_STRUCTURE"]["tau"].update(operator_id=v)),
        ("version", lambda x, v: x["DYNAMIC_TOPOLOGICAL_STRUCTURE"]["tau"].update(version=v)),
        ("source", lambda x, v: x["PROVENANCE_CONFIDENCE"].update(source=v)),
        ("Chemical_Ref", lambda x, v: x["SPECTRAL_FIELD"].update(Chemical_Ref=v)),
    ]

    def test_control_and_edge_whitespace_rejected(self):
        for name, mut in self.IDENT_FIELDS:
            for v in ("\x00", "x\n", " x", "x ", "a\tb", "a\x7fb"):
                with self.subTest(field=name, value=repr(v)):
                    self.assertIn("E_IDENT_FORMAT", validate_record(rec(lambda x: mut(x, v))).codes())

    def test_normal_identifiers_accepted(self):
        for name, mut in self.IDENT_FIELDS:
            with self.subTest(field=name):
                self.assertTrue(validate_record(rec(lambda x: mut(x, "Toni Mladenovski — Н₂О 🧬"))).ok)

    def test_payload_is_free_text(self):
        p = "line one\nline two\t\x00"
        r = rec(lambda x: x["INFORMATION_IDENTITY"].update(payload=p, payload_sha256=sha256_text(p)))
        self.assertTrue(validate_record(r).ok)

    def test_cycle_count_bound(self):
        self.assertTrue(validate_record(rec(lambda x: x["CYCLIC_INDEX"].update(cycle_count=2 ** 53 - 1))).ok)
        for v in (2 ** 53, 10 ** 1000, HUGE):
            with self.subTest(digits=len(str(v)) if v != HUGE else 10001):
                self.assertIn("E_RANGE", validate_record(rec(lambda x: x["CYCLIC_INDEX"].update(cycle_count=v))).codes())
