# scripts/v2/make_license_from_archive.py
# Platform-agnostic license generator (v2) — append-only outputs
# DGCP™ | MMFARM-POL-2025

import os, json, hashlib
from pathlib import Path
from datetime import datetime, timezone
import requests

# ------- Config (Platform-Agnostic) -------
ARCHIVE_REPO   = os.environ.get("ARCHIVE_REPO", "MaMeeFarm-Data/MaMeeFarm-DataArchive")
ARCHIVE_BRANCH = os.environ.get("ARCHIVE_BRANCH", "main")
DATA_PREFIX    = os.environ.get("DATA_PREFIX", "data/")

RAW_BASE = f"https://raw.githubusercontent.com/{ARCHIVE_REPO}/{ARCHIVE_BRANCH}/"
TREE_API = f"https://api.github.com/repos/{ARCHIVE_REPO}/git/trees/{ARCHIVE_BRANCH}?recursive=1"

ROOT    = Path(__file__).resolve().parents[2]  # repo root
OUT_DIR = ROOT / "licenses" / "output_v2"
TPL_DIR = ROOT / "licenses" / "templates"
STATE   = ROOT / ".state"
SEEN    = STATE / "seen_output_v2.json"

STATE.mkdir(exist_ok=True)
OUT_DIR.mkdir(parents=True, exist_ok=True)

ISSUER    = os.environ.get("LICENSE_ISSUER", "MaMeeFarm Data Cooperative")
HOLDER    = os.environ.get("LICENSE_HOLDER", "MaMeeFarm")
POLICY_ID = os.environ.get("LICENSE_POLICY_ID", "MMFARM-POL-2025")

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

SESSION = requests.Session()
SESSION.headers.update({
    "Accept": "application/json",
    "User-Agent": "MaMeeFarm-DataLicense-v2 (DGCP)"
})
if GITHUB_TOKEN:
    SESSION.headers.update({"Authorization": f"Bearer {GITHUB_TOKEN}"})


def _http_json(url: str) -> dict:
    r = SESSION.get(url, timeout=30)
    r.raise_for_status()
    return r.json()


def _http_bytes(url: str) -> bytes:
    r = SESSION.get(url, timeout=30)
    r.raise_for_status()
    return r.content


def list_archive_files():
    tree = _http_json(TREE_API).get("tree", [])
    return [
        n["path"] for n in tree
        if n.get("type") == "blob"
        and n.get("path", "").startswith(DATA_PREFIX)
        and n.get("path", "").endswith(".json")
    ]


def load_seen():
    # map: { "<path_in_archive>": "<sha256_hex_latest>" }
    if SEEN.exists():
        try:
            return json.loads(SEEN.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_seen(s):
    SEEN.write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")


def _rights_bool(rights: dict, *keys: str) -> bool:
    for k in keys:
        v = rights.get(k)
        if isinstance(v, bool):
            return v
        if isinstance(v, str) and v.strip().lower() in ("true", "yes", "1"):
            return True
    return False


def pick_template(rec: dict):
    """
    Platform-agnostic rule:
    - Prefer CC BY 4.0 only when explicit public release flag is true
      AND audio_source indicates creator-owned/clean audio.
    - Otherwise Metadata-Only.
    Backward compatible with older keys if present.
    """
    rights = rec.get("rights", {}) if isinstance(rec.get("rights", {}), dict) else {}
    public_release = _rights_bool(rights, "public_release", "publish_publicly", "upload_to_ipfs")
    audio_source = (rights.get("audio_source") or rights.get("audioOrigin") or "").lower()

    if public_release and audio_source in ("original", "none", "no-music", "my-voice", "self"):
        return (TPL_DIR / "cc-by-4.0.jsonld", "CC-BY-4.0")

    return (TPL_DIR / "metadata-only.jsonld", "")


def issued_at_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def build_license(path_in_archive: str):
    raw_url = RAW_BASE + path_in_archive

    raw_bytes = _http_bytes(raw_url)
    digest = hashlib.sha256(raw_bytes).hexdigest()

    try:
        rec = json.loads(raw_bytes.decode("utf-8"))
    except Exception:
        rec = {}

    tpl_path, spdx = pick_template(rec)
    tpl = json.loads(Path(tpl_path).read_text(encoding="utf-8"))

    # Platform-agnostic metadata extraction (best-effort)
    title = rec.get("title") or rec.get("name") or rec.get("caption")
    source_url = rec.get("source_url") or rec.get("url") or rec.get("permalink")
    created_at = rec.get("created_at") or rec.get("posted_at") or rec.get("timestamp")
    creator = rec.get("creator") or rec.get("author") or rec.get("owner")

    lic = {
        "@context": tpl.get("@context", []),
        "@type": tpl.get("@type", "LicenseDocument"),
        "name": tpl.get("name", "MaMeeFarm Data License Record"),
        "license": tpl.get("license", ""),
        "spdxId": spdx or tpl.get("spdxId", ""),
        "policyId": POLICY_ID,
        "issuedBy": ISSUER,
        "holder": HOLDER,
        "issuedAt": issued_at_utc(),
        "usageInfo": tpl.get("usageInfo", ""),
        "conditionsOfAccess": tpl.get("conditionsOfAccess", ""),
        "dataFile": {
            "name": path_in_archive.split("/")[-1],
            "contentUrl": raw_url,
            "hashSHA256": digest
        },
        "data:title": title,
        "data:source_url": source_url,
        "data:created_at": created_at,
        "data:creator": creator
    }

    # Append-only output: one file per source+hash (no overwrite)
    safe_name = path_in_archive.replace("/", "_")
    out_name = f"{safe_name}.{digest[:12]}.license.jsonld"
    out_path = OUT_DIR / out_name

    if not out_path.exists():
        out_path.write_text(json.dumps(lic, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[ok] {out_path}")

    return digest, out_name


def main():
    files = list_archive_files()
    if not files:
        print("[info] no metadata files found in archive")
        return

    seen = load_seen()
    generated = 0

    for p in sorted(files):
        prev_hash = seen.get(p, "")
        if prev_hash:
            expected = OUT_DIR / f"{p.replace('/', '_')}.{prev_hash[:12]}.license.jsonld"
            if expected.exists():
                continue

        new_hash, out_name = build_license(p)
        seen[p] = new_hash
        generated += 1

    save_seen(seen)
    print(f"[done] generated={generated}, tracked={len(seen)}")


if __name__ == "__main__":
    main()
