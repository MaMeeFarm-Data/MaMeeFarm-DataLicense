# Fetch JSON files from the public TikTok archive repo and issue JSON-LD licenses.
import os, json, hashlib
from pathlib import Path
from datetime import datetime, timezone
import requests

# ------- Config -------
ARCHIVE_REPO   = os.environ.get("ARCHIVE_REPO", "MaMeeFarm-Data/MaMeeFarm-TikTok-Archive")
ARCHIVE_BRANCH = os.environ.get("ARCHIVE_BRANCH", "main")
DATA_PREFIX    = "data/"
RAW_BASE = f"https://raw.githubusercontent.com/{ARCHIVE_REPO}/{ARCHIVE_BRANCH}/"

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "licenses" / "output"
TPL_DIR = ROOT / "licenses" / "templates"
STATE   = ROOT / ".state"; STATE.mkdir(exist_ok=True)
SEEN    = STATE / "seen_output.json"
OUT_DIR.mkdir(parents=True, exist_ok=True)

ISSUER = "MaMeeFarm Data Cooperative"
HOLDER = "MaMeeFarm"

def _http_json(url: str):
    r = requests.get(url, timeout=30, headers={"Accept":"application/json"})
    r.raise_for_status()
    return r.json()

def list_archive_files():
    # Use Git trees API (recursive listing)
    url = f"https://api.github.com/repos/{ARCHIVE_REPO}/git/trees/{ARCHIVE_BRANCH}?recursive=1"
    tree = _http_json(url).get("tree", [])
    return [n["path"] for n in tree if n.get("type") == "blob" and n["path"].startswith(DATA_PREFIX) and n["path"].endswith(".json")]

def load_seen():
    if SEEN.exists():
        try: return json.loads(SEEN.read_text(encoding="utf-8"))
        except Exception: return {}
    return {}

def save_seen(s): SEEN.write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")

def pick_template(rec: dict):
    rights = rec.get("rights", {})
    audio  = (rights.get("audio_source") or "").lower()
    allow  = bool(rights.get("upload_to_ipfs"))
    if allow and audio in ("original","none","no-music","my-voice"):
        return (TPL_DIR / "cc-by-4.0.jsonld", "CC-BY-4.0")
    return (TPL_DIR / "metadata-only.jsonld", None)

def build_license(path_in_archive: str):
    raw_url = RAW_BASE + path_in_archive
    rec      = requests.get(raw_url, timeout=30).json()
    digest   = hashlib.sha256(requests.get(raw_url, timeout=30).content).hexdigest()

    tpl_path, spdx = pick_template(rec)
    tpl = json.loads(Path(tpl_path).read_text(encoding="utf-8"))

    content_url = raw_url
    lic = {
        "@context": tpl["@context"],
        "@type": tpl["@type"],
        "name": tpl["name"],
        "license": tpl["license"],
        "spdxId": spdx or tpl.get("spdxId",""),
        "issuedBy": ISSUER,
        "holder": HOLDER,
        "issuedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "usageInfo": tpl.get("usageInfo",""),
        "conditionsOfAccess": tpl.get("conditionsOfAccess",""),
        "dataFile": {
            "name": path_in_archive.split("/")[-1],
            "contentUrl": content_url,
            "hashSHA256": digest
        },
        "data:title": rec.get("title"),
        "data:tiktok_url": rec.get("tiktok_url"),
        "data:posted_at": rec.get("posted_at"),
        "data:author": rec.get("author")
    }

    safe_name = path_in_archive.replace("/", "_")
    out = OUT_DIR / f"{safe_name}.license.jsonld"
    out.write_text(json.dumps(lic, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[ok] {out}")
    return out.name

def main():
    files = list_archive_files()
    if not files:
        print("[info] no data files found in archive")
        return
    seen = load_seen()
    new = 0
    for p in sorted(files):
        key = p
        out_name = f"{p.replace('/', '_')}.license.jsonld"
        if seen.get(key) == out_name and (OUT_DIR / out_name).exists():
            continue
        out_file = build_license(p)
        seen[key] = out_file
        new += 1
    save_seen(seen)
    print(f"[done] generated={new}, total={len(seen)}")

if __name__ == "__main__":
    main()
