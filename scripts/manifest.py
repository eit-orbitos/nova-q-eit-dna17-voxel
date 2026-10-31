"""Create or verify MANIFEST.sha256 (cross-platform, stdlib only).

    python scripts/manifest.py write    # after any change
    python scripts/manifest.py verify   # exit 1 on any mismatch
Hashes are never typed by hand.

.github/ is excluded: GitHub forbids automated commits to workflow files, so they are
created by hand in the web editor and cannot be byte-pinned. They remain visible in the
repository history and in every Actions log.
"""
import hashlib
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAME = "MANIFEST.sha256"
SKIP_DIRS = {".git", ".github", "__pycache__", ".venv", "dist", "build"}


def files():
    out = []
    for d, dirs, fs in os.walk(ROOT):
        dirs[:] = sorted(x for x in dirs if x not in SKIP_DIRS and not x.endswith(".egg-info"))
        for f in sorted(fs):
            rel = os.path.relpath(os.path.join(d, f), ROOT).replace(os.sep, "/")
            if rel != NAME and not f.endswith(".pyc"):
                out.append(rel)
    return sorted(out)


def sha(rel):
    with open(os.path.join(ROOT, rel), "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def main(mode):
    path = os.path.join(ROOT, NAME)
    if mode == "write":
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            for rel in files():
                fh.write(f"{sha(rel)}  {rel}\n")
        print(f"wrote {len(files())} entries")
        return 0
    listed = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            h, rel = line.rstrip("\n").split("  ", 1)
            listed[rel] = h
    bad = [r for r, h in listed.items() if not os.path.exists(os.path.join(ROOT, r)) or sha(r) != h]
    extra = sorted(set(files()) - set(listed))
    for r in bad:
        print("MISMATCH", r)
    for r in extra:
        print("NOT IN MANIFEST", r)
    print(f"{len(listed) - len(bad)}/{len(listed)} match, {len(extra)} unlisted")
    return 1 if bad or extra else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "verify"))
