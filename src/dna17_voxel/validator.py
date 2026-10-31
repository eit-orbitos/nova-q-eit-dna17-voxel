"""NOVA Q / EIT — DNA17 voxel field validator V0.1.3 (RELEASE_CANDIDATE, NOT_FROZEN).

Author concept: Toni Mladenovski. Builder: Claude.
Spec: spec/DNA17_FIELD_SPEC_V0_1_3.json. Decisions D1-D7: DECISIONS.md.
SOFTWARE claim only; all numbers are dimensionless symbolic values.
Stdlib only. Fail-closed for JSON-like inputs. tau is never executed.

History of corrections carried forward:
  C1 huge integers rejected, never OverflowError        (V0.1.1, audit F01)
  C2 strict UTF-8 for every string                       (V0.1.1, audit F03)
  C3 one link per target; edge-contract profiles         (V0.1.1, audit G01)
  C4 never stringify unvalidated values                  (V0.1.2, replay R1-R3)
  C5 hex hashes use fullmatch                            (V0.1.2, replay R4)
  C6 tau declared at t(before) governs the transition    (V0.1.2, replay R5)
  C7 identifier strings: no control chars / edge spaces  (V0.1.2, fuzz)
  C8 cycle_count bounded to 0..2**53-1                   (V0.1.2, fuzz)
V0.1.3 decisions:
  D1 VOXEL_UNIT literal 1; schema version in a snapshot envelope
  D2 DIMENSIONAL_INDEX {3,5}; 11 reserved for a separate EIT_11D profile
  D3 symmetry default DIRECTED_ALLOWED      D4 edge default N_EQUALS_LINK_TARGETS
  D5 tau policy default BEFORE_GOVERNS
  D6 every integer in a numeric field within +-(2**53-1)
  D7 P_M under a protected transition: spectral history is append-only
"""
from __future__ import annotations

import hashlib
import math
import re
import unicodedata
from dataclasses import dataclass, field

SPEC_ID = "NOVA_Q_EIT_DNA17_FIELD_SPEC_V0_1_3"
SCHEMA_VERSION = "0.1.3"
__version__ = SCHEMA_VERSION
EDGE_CONTRACTS = ("N_EQUALS_LINK_TARGETS", "LINKS_SUBSET_OF_N")
DEFAULT_EDGE_CONTRACT = "N_EQUALS_LINK_TARGETS"  # D4

FIELD_KEYS = (
    "VOXEL_UNIT", "SPECTRAL_MEMORY", "ENERGY_DYNAMICS", "SPECTRAL_FIELD",
    "TRANSFER_IMPEDANCE", "VOXEL_CAPACITY", "INNER_FORCE_VECTOR",
    "RESONANT_HARMONIC", "DIMENSIONAL_INDEX", "CYCLIC_INDEX", "ORBITAL_PATH",
    "BIO_HOLOGRAPHIC_VOXEL_VECTOR", "PROVENANCE_CONFIDENCE",
    "DYNAMIC_TOPOLOGICAL_STRUCTURE", "INTERNAL_HARMONY",
    "SPATIAL_TRANSLATION", "INFORMATION_IDENTITY",
)
assert len(FIELD_KEYS) == 17

HEX64 = re.compile(r"[0-9a-f]{64}")  # C5: always use .fullmatch
MAX_SPECTRUM = 4096
ALLOWED_DIMENSIONS = {3, 5}  # D2
RESERVED_DIMENSIONS = {11}  # D2: EIT_11D profile, not active
MAX_SAFE_INT = 2 ** 53 - 1  # C8: exactly representable in IEEE-754 / JSON


@dataclass
class Report:
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def err(self, code, where, msg):
        self.errors.append((code, where, msg))

    def warn(self, code, where, msg):
        self.warnings.append((code, where, msg))

    def codes(self):
        return {e[0] for e in self.errors}


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def utf8_ok(s) -> bool:
    """True only for str values that encode in strict UTF-8 (no lone surrogates)."""
    if not isinstance(s, str):
        return False
    try:
        s.encode("utf-8", errors="strict")
    except UnicodeEncodeError:
        return False
    return True


# ---------- primitive checks ----------

def _is_num(x):
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        return False
    if isinstance(x, int):
        return -MAX_SAFE_INT <= x <= MAX_SAFE_INT  # C1 + D6
    return math.isfinite(x)


def _is_int(x):
    return isinstance(x, int) and not isinstance(x, bool)


def _num(r, where, x, lo=None, hi=None, lo_open=False, hi_open=False):
    if not _is_num(x):
        # no repr(x): huge ints can exceed the int->str digit limit (ValueError)
        r.err("E_TYPE", where, f"expected finite number (integers within +-2**53-1), got {type(x).__name__}")
        return False
    if lo is not None and (x < lo or (lo_open and x == lo)):
        r.err("E_RANGE", where, f"{x} below allowed minimum {lo}")
        return False
    if hi is not None and (x > hi or (hi_open and x == hi)):
        r.err("E_RANGE", where, f"{x} above allowed maximum {hi}")
        return False
    return True


def _vec3(r, where, v):
    if not isinstance(v, list) or len(v) != 3:
        r.err("E_TYPE", where, "expected [x, y, z]")
        return False
    return all(_num(r, f"{where}[{k}]", c) for k, c in enumerate(v))


def _nonneg_array(r, where, a):
    if not isinstance(a, list):
        r.err("E_TYPE", where, "expected array")
        return
    if len(a) > MAX_SPECTRUM:
        r.err("E_RANGE", where, f"length {len(a)} > {MAX_SPECTRUM}")
    for k, x in enumerate(a):
        _num(r, f"{where}[{k}]", x, lo=0)


def _obj(r, where, o, keys, optional=()):
    if not isinstance(o, dict):
        r.err("E_TYPE", where, "expected object")
        return False
    missing = [k for k in keys if k not in o]
    extra = [k for k in o if k not in keys and k not in optional]
    for k in missing:
        r.err("E_MISSING", f"{where}.{k}", "required key missing")
    for k in extra:
        r.err("E_UNKNOWN_KEY", f"{where}.{_key(k)}", "unknown key (fail-closed)")
    return not missing and not extra


def _key(k):
    """C4: render an untrusted dict key without str() of non-strings."""
    if isinstance(k, str) and utf8_ok(k):
        return k
    return f"<{type(k).__name__} key>"


def _dups(items):
    """C4: duplicate check over string items only; non-strings are reported elsewhere."""
    strs = [x for x in items if isinstance(x, str)]
    return len(set(strs)) != len(strs)


def _nonempty_str(r, where, s):
    if not isinstance(s, str) or not s.strip():
        r.err("E_TYPE", where, "expected non-empty string")
        return False
    if not utf8_ok(s):
        r.err("E_UTF8", where, "string is not strict UTF-8 encodable")
        return False
    # C7: identifier-like strings carry no control chars and no edge whitespace
    if s != s.strip() or any(unicodedata.category(c) == "Cc" for c in s):
        r.err("E_IDENT_FORMAT", where, "control character or leading/trailing whitespace")
        return False
    return True


# ---------- single record ----------

def validate_record(rec, r: Report | None = None, where="record",
                    edge_contract=DEFAULT_EDGE_CONTRACT) -> Report:
    if edge_contract not in EDGE_CONTRACTS:
        raise ValueError("unknown edge_contract")
    r = r or Report()
    if not isinstance(rec, dict):
        r.err("E_TYPE", where, "record must be an object")
        return r
    for k in FIELD_KEYS:
        if k not in rec:
            r.err("E_MISSING", f"{where}.{k}", "required field missing")
    for k in rec:
        if k not in FIELD_KEYS:
            r.err("E_UNKNOWN_KEY", f"{where}.{_key(k)}", "unknown field (use LABEL keys, not symbols)")

    w = lambda k: f"{where}.{k}"
    g = rec.get

    # 1
    if "VOXEL_UNIT" in rec:
        v = g("VOXEL_UNIT")
        if not (_is_int(v) and v == 1):
            r.err("E_RANGE", w("VOXEL_UNIT"), "must be exactly integer 1")
    # 2
    if "SPECTRAL_MEMORY" in rec:
        _nonneg_array(r, w("SPECTRAL_MEMORY"), g("SPECTRAL_MEMORY"))
    # 3
    if "ENERGY_DYNAMICS" in rec:
        _num(r, w("ENERGY_DYNAMICS"), g("ENERGY_DYNAMICS"), lo=0)
    # 4
    if "SPECTRAL_FIELD" in rec:
        s = g("SPECTRAL_FIELD")
        ws = w("SPECTRAL_FIELD")
        if _obj(r, ws, s, ("Chemical_Ref", "Spectral_Signature", "Color_Projection")):
            cr = s["Chemical_Ref"]
            if cr is not None:
                _nonempty_str(r, f"{ws}.Chemical_Ref", cr)
            _nonneg_array(r, f"{ws}.Spectral_Signature", s["Spectral_Signature"])
            cp = s["Color_Projection"]
            if not isinstance(cp, list) or len(cp) != 3:
                r.err("E_TYPE", f"{ws}.Color_Projection", "expected [r, g, b]")
            else:
                for k, c in enumerate(cp):
                    _num(r, f"{ws}.Color_Projection[{k}]", c, lo=0, hi=1)
    # 5, 6
    if "TRANSFER_IMPEDANCE" in rec:
        _num(r, w("TRANSFER_IMPEDANCE"), g("TRANSFER_IMPEDANCE"), lo=0)
    if "VOXEL_CAPACITY" in rec:
        _num(r, w("VOXEL_CAPACITY"), g("VOXEL_CAPACITY"), lo=0, lo_open=True)
    # 7
    if "INNER_FORCE_VECTOR" in rec:
        _vec3(r, w("INNER_FORCE_VECTOR"), g("INNER_FORCE_VECTOR"))
    # 8, 15
    for k in ("RESONANT_HARMONIC", "INTERNAL_HARMONY"):
        if k in rec:
            _num(r, w(k), g(k), lo=0, hi=1)
    # 9
    if "DIMENSIONAL_INDEX" in rec:
        d = g("DIMENSIONAL_INDEX")
        if _is_int(d) and d in RESERVED_DIMENSIONS:
            r.err("E_RESERVED_PROFILE", w("DIMENSIONAL_INDEX"), "11 is reserved for a separate EIT_11D profile")
        elif not _is_int(d) or d not in ALLOWED_DIMENSIONS:
            r.err("E_RANGE", w("DIMENSIONAL_INDEX"), f"must be one of {sorted(ALLOWED_DIMENSIONS)}")
    # 10
    if "CYCLIC_INDEX" in rec:
        c = g("CYCLIC_INDEX")
        wc = w("CYCLIC_INDEX")
        if _obj(r, wc, c, ("phase", "cycle_count")):
            _num(r, f"{wc}.phase", c["phase"], lo=0, hi=1, hi_open=True)
            if not _is_int(c["cycle_count"]) or not 0 <= c["cycle_count"] <= MAX_SAFE_INT:
                r.err("E_RANGE", f"{wc}.cycle_count", "must be integer in 0..2**53-1")
    # 11
    if "ORBITAL_PATH" in rec:
        o = g("ORBITAL_PATH")
        wo = w("ORBITAL_PATH")
        if not isinstance(o, list) or len(o) < 2:
            r.err("E_TYPE", wo, "expected array of >= 2 points")
        else:
            for k, p in enumerate(o):
                _vec3(r, f"{wo}[{k}]", p)
    # 12
    if "BIO_HOLOGRAPHIC_VOXEL_VECTOR" in rec:
        b = g("BIO_HOLOGRAPHIC_VOXEL_VECTOR")
        wb = w("BIO_HOLOGRAPHIC_VOXEL_VECTOR")
        if not isinstance(b, list):
            r.err("E_TYPE", wb, "expected array of voxel_id strings")
        else:
            for k, ref in enumerate(b):
                _nonempty_str(r, f"{wb}[{k}]", ref)
            if _dups(b):
                r.err("E_DUPLICATE", wb, "duplicate references")
    # 13
    if "PROVENANCE_CONFIDENCE" in rec:
        p = g("PROVENANCE_CONFIDENCE")
        wp = w("PROVENANCE_CONFIDENCE")
        if _obj(r, wp, p, ("source", "confidence"), optional=("source_sha256",)):
            _nonempty_str(r, f"{wp}.source", p["source"])
            _num(r, f"{wp}.confidence", p["confidence"], lo=0, hi=1)
            if "source_sha256" in p and not (isinstance(p["source_sha256"], str) and HEX64.fullmatch(p["source_sha256"])):
                r.err("E_HASH_FORMAT", f"{wp}.source_sha256", "must be 64 lowercase hex chars")
    # 14
    if "DYNAMIC_TOPOLOGICAL_STRUCTURE" in rec:
        t = g("DYNAMIC_TOPOLOGICAL_STRUCTURE")
        wt = w("DYNAMIC_TOPOLOGICAL_STRUCTURE")
        if _obj(r, wt, t, ("t", "neighbors", "links", "tau")):
            _num(r, f"{wt}.t", t["t"])
            nb = t["neighbors"]
            if not isinstance(nb, list):
                r.err("E_TYPE", f"{wt}.neighbors", "expected array")
                nb = []
            else:
                for k, n in enumerate(nb):
                    _nonempty_str(r, f"{wt}.neighbors[{k}]", n)
                if _dups(nb):
                    r.err("E_DUPLICATE", f"{wt}.neighbors", "duplicate neighbor")
            lk = t["links"]
            if not isinstance(lk, list):
                r.err("E_TYPE", f"{wt}.links", "expected array")
            else:
                targets = []
                for k, l in enumerate(lk):
                    wl = f"{wt}.links[{k}]"
                    if _obj(r, wl, l, ("target", "weight")):
                        _num(r, f"{wl}.weight", l["weight"], lo=0)
                        if not _nonempty_str(r, f"{wl}.target", l["target"]):
                            continue
                        targets.append(l["target"])
                        if l["target"] not in nb:
                            r.err("E_LINK_NOT_NEIGHBOR", wl, "link target is not in neighbors")
                # C3: one link per target, in every profile
                if len(set(targets)) != len(targets):
                    r.err("E_DUPLICATE_LINK", f"{wt}.links", "more than one link to the same target")
                if edge_contract == "N_EQUALS_LINK_TARGETS":
                    missing = [n for n in nb if isinstance(n, str) and n not in targets]
                    if missing:
                        r.err("E_NEIGHBOR_WITHOUT_LINK", f"{wt}.links",
                              f"{len(missing)} neighbor(s) have no link (profile N_EQUALS_LINK_TARGETS)")
            tau = t["tau"]
            wtau = f"{wt}.tau"
            if _obj(r, wtau, tau, ("operator_id", "version", "memory_preserving")):
                _nonempty_str(r, f"{wtau}.operator_id", tau["operator_id"])
                _nonempty_str(r, f"{wtau}.version", tau["version"])
                if not isinstance(tau["memory_preserving"], bool):
                    r.err("E_TYPE", f"{wtau}.memory_preserving", "expected boolean")
    # 16
    if "SPATIAL_TRANSLATION" in rec:
        _vec3(r, w("SPATIAL_TRANSLATION"), g("SPATIAL_TRANSLATION"))
    # 17
    if "INFORMATION_IDENTITY" in rec:
        ii = g("INFORMATION_IDENTITY")
        wi = w("INFORMATION_IDENTITY")
        if _obj(r, wi, ii, ("voxel_id", "payload", "payload_sha256")):
            _nonempty_str(r, f"{wi}.voxel_id", ii["voxel_id"])
            if not isinstance(ii["payload"], str):
                r.err("E_TYPE", f"{wi}.payload", "expected string")
            elif not utf8_ok(ii["payload"]):
                r.err("E_UTF8", f"{wi}.payload", "payload is not strict UTF-8 encodable")
            elif not (isinstance(ii["payload_sha256"], str) and HEX64.fullmatch(ii["payload_sha256"])):
                r.err("E_HASH_FORMAT", f"{wi}.payload_sha256", "must be 64 lowercase hex chars")
            elif sha256_text(ii["payload"]) != ii["payload_sha256"]:
                r.err("E_PAYLOAD_HASH", f"{wi}.payload_sha256", "does not match SHA-256 of payload")
    return r


# ---------- network snapshot ----------

def _vid(rec):
    try:
        return rec["INFORMATION_IDENTITY"]["voxel_id"]
    except (KeyError, TypeError):
        return None


def validate_network(records, symmetry="DIRECTED_ALLOWED",
                     edge_contract=DEFAULT_EDGE_CONTRACT) -> Report:
    """symmetry: 'DIRECTED_ALLOWED' (asymmetry -> warning) or 'SYMMETRIC_REQUIRED' (-> error)."""
    if symmetry not in ("DIRECTED_ALLOWED", "SYMMETRIC_REQUIRED"):
        raise ValueError("unknown symmetry mode")
    r = Report()
    if not isinstance(records, list) or not records:
        r.err("E_TYPE", "network", "expected non-empty array of records")
        return r
    for k, rec in enumerate(records):
        validate_record(rec, r, where=f"network[{k}]", edge_contract=edge_contract)
    if not r.ok:
        return r  # structural errors first; cross checks need valid records

    ids = [_vid(x) for x in records]
    if len(set(ids)) != len(ids):
        r.err("E_DUPLICATE_ID", "network", "voxel_id not unique")
        return r
    idset = set(ids)
    times = {x["DYNAMIC_TOPOLOGICAL_STRUCTURE"]["t"] for x in records}
    if len(times) != 1:
        r.err("E_TIME_MISMATCH", "network", f"snapshot has multiple t values: {sorted(times)}")

    nbmap = {}
    for vid, rec in zip(ids, records):
        nb = rec["DYNAMIC_TOPOLOGICAL_STRUCTURE"]["neighbors"]
        nbmap[vid] = set(nb)
        for n in nb:
            if n == vid:
                r.err("E_SELF_REFERENCE", f"{vid}.neighbors", "voxel lists itself as neighbor")
            elif n not in idset:
                r.err("E_UNRESOLVED_REF", f"{vid}.neighbors", f"{n!r} not in network")
        for b in rec["BIO_HOLOGRAPHIC_VOXEL_VECTOR"]:
            if b == vid:
                r.err("E_SELF_REFERENCE", f"{vid}.BIO_HOLOGRAPHIC_VOXEL_VECTOR", "self-reference")
            elif b not in idset:
                r.err("E_UNRESOLVED_REF", f"{vid}.BIO_HOLOGRAPHIC_VOXEL_VECTOR", f"{b!r} not in network")

    for a, nbs in nbmap.items():
        for b in nbs:
            if b in nbmap and a not in nbmap[b]:
                msg = f"{a} -> {b} has no reverse edge"
                if symmetry == "SYMMETRIC_REQUIRED":
                    r.err("E_ASYMMETRIC", "network", msg)
                else:
                    r.warn("W_ASYMMETRIC", "network", msg)
    return r


# ---------- transition (before -> after) ----------

TAU_POLICIES = ("BEFORE_GOVERNS", "EITHER_PRESERVING_PROTECTS")
DEFAULT_TAU_POLICY = "BEFORE_GOVERNS"  # D5


def check_transition(before, after, symmetry="DIRECTED_ALLOWED",
                     edge_contract=DEFAULT_EDGE_CONTRACT,
                     tau_policy=DEFAULT_TAU_POLICY) -> Report:
    """Checks INV_6..INV_11. tau is NOT executed; only its declared effect is audited.

    C6 transition semantics (tau_i : V_i(t) x {V_j(t)} -> V_i(t+dt)):
      BEFORE_GOVERNS: the tau declared at t(before) is the operator that produced
        t(after); the tau stored at t(after) governs the NEXT transition.
      EITHER_PRESERVING_PROTECTS: stricter; P_M is enforced if tau at t(before)
        OR at t(after) declares memory_preserving.
    In both policies, any change of the tau declaration is reported as
    W_TAU_DECLARATION_CHANGED, and any rewrite of INFORMATION_IDENTITY under a
    non-preserving transition as W_IDENTITY_REWRITTEN, so it is never silent.
    """
    if tau_policy not in TAU_POLICIES:
        raise ValueError("unknown tau_policy")
    r = Report()
    for label, net in (("before", before), ("after", after)):
        sub = validate_network(net, symmetry, edge_contract)
        r.errors += [(c, f"{label}:{w}", m) for c, w, m in sub.errors]
        r.warnings += [(c, f"{label}:{w}", m) for c, w, m in sub.warnings]
    if not r.ok:
        return r
    b = {_vid(x): x for x in before}
    a = {_vid(x): x for x in after}
    if set(b) != set(a):
        r.err("E_IDENTITY_SET_CHANGED", "transition",
              f"added={sorted(set(a) - set(b))} removed={sorted(set(b) - set(a))}")
        return r
    tb = before[0]["DYNAMIC_TOPOLOGICAL_STRUCTURE"]["t"]
    ta = after[0]["DYNAMIC_TOPOLOGICAL_STRUCTURE"]["t"]
    if not ta > tb:
        r.err("E_TIME_ORDER", "transition", f"t(after)={ta} must be > t(before)={tb}")
    for vid in b:
        x, y = b[vid], a[vid]
        if x["PROVENANCE_CONFIDENCE"] != y["PROVENANCE_CONFIDENCE"]:
            r.err("E_PROVENANCE_CHANGED", vid, "tau must not modify PROVENANCE_CONFIDENCE")
        tau_b = x["DYNAMIC_TOPOLOGICAL_STRUCTURE"]["tau"]
        tau_a = y["DYNAMIC_TOPOLOGICAL_STRUCTURE"]["tau"]
        if tau_b != tau_a:
            r.warn("W_TAU_DECLARATION_CHANGED", vid,
                   "tau declaration differs between t(before) and t(after)")
        protected = tau_b["memory_preserving"] or (
            tau_policy == "EITHER_PRESERVING_PROTECTS" and tau_a["memory_preserving"])
        rewritten = x["INFORMATION_IDENTITY"] != y["INFORMATION_IDENTITY"]
        if rewritten and protected:
            r.err("E_P_M_VIOLATION", vid,
                  f"INFORMATION_IDENTITY changed under a protected transition ({tau_policy})")
        elif rewritten:
            r.warn("W_IDENTITY_REWRITTEN", vid,
                   "INFORMATION_IDENTITY rewritten under a non-preserving tau (allowed)")
        _check_spectral_history(r, vid, x, y, protected)
    return r


def _is_prefix(old, new):
    return len(new) >= len(old) and new[:len(old)] == old


def _check_spectral_history(r, vid, x, y, protected):
    """D7: spectral history is append-only under a protected transition.

    Protected (memory-preserving): existing SPECTRAL_MEMORY and Spectral_Signature
    entries may not change (new entries may be appended), Chemical_Ref may not change.
    Color_Projection is a derived projection and may change.
    Every spectral change is reported, so nothing is silent.
    """
    sx, sy = x["SPECTRAL_FIELD"], y["SPECTRAL_FIELD"]
    histories = (("SPECTRAL_MEMORY", x["SPECTRAL_MEMORY"], y["SPECTRAL_MEMORY"]),
                 ("SPECTRAL_FIELD.Spectral_Signature", sx["Spectral_Signature"], sy["Spectral_Signature"]))
    for name, old, new in histories:
        if old == new:
            continue
        if not _is_prefix(old, new):
            if protected:
                r.err("E_SPECTRAL_HISTORY_REWRITTEN", f"{vid}.{name}",
                      "existing entries changed under a protected transition (append-only)")
            else:
                r.warn("W_SPECTRAL_CHANGED", f"{vid}.{name}", "rewritten under a non-preserving tau (allowed)")
        else:
            r.warn("W_SPECTRAL_APPENDED", f"{vid}.{name}", f"{len(new) - len(old)} entr(y/ies) appended")
    if sx["Chemical_Ref"] != sy["Chemical_Ref"]:
        if protected:
            r.err("E_SPECTRAL_HISTORY_REWRITTEN", f"{vid}.SPECTRAL_FIELD.Chemical_Ref",
                  "changed under a protected transition")
        else:
            r.warn("W_SPECTRAL_CHANGED", f"{vid}.SPECTRAL_FIELD.Chemical_Ref", "changed under a non-preserving tau")
    if sx["Color_Projection"] != sy["Color_Projection"]:
        r.warn("W_SPECTRAL_CHANGED", f"{vid}.SPECTRAL_FIELD.Color_Projection", "derived projection changed")


# ---------- snapshot envelope (D1) ----------

ENVELOPE_KEYS = ("schema_id", "schema_version", "voxels")


def validate_snapshot(env, symmetry="DIRECTED_ALLOWED", edge_contract=DEFAULT_EDGE_CONTRACT) -> Report:
    """D1: a snapshot carries the schema identity; VOXEL_UNIT stays the literal 1.
    Unknown schema versions are rejected (fail-closed)."""
    r = Report()
    if not _obj(r, "snapshot", env, ENVELOPE_KEYS):
        return r
    if env["schema_id"] != SPEC_ID:
        r.err("E_SCHEMA", "snapshot.schema_id", f"must be {SPEC_ID}")
    if env["schema_version"] != SCHEMA_VERSION:
        r.err("E_SCHEMA", "snapshot.schema_version", f"must be {SCHEMA_VERSION!r}")
    sub = validate_network(env["voxels"], symmetry, edge_contract)
    r.errors += sub.errors
    r.warnings += sub.warnings
    return r
