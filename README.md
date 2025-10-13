# MaMeeFarm Data License

This repository issues **verifiable JSON-LD licenses** for MaMeeFarm data.
It reads TikTok metadata JSON files from the public archive repository and
produces signed (by timestamp + hash) license records.

- Source archive: `MaMeeFarm-Data/MaMeeFarm-TikTok-Archive`
- Output licenses: `licenses/output/*.license.jsonld`
- Templates: `licenses/templates/*`

## How it works
1. GitHub Action runs on schedule or manually.
2. The script fetches `data/*.json` from the archive repo (public, no token).
3. For each JSON:
   - Compute SHA-256 digest of the exact file contents.
   - Decide license:
     - **CC BY 4.0** if `rights.upload_to_ipfs == true` and `audio_source` is one of:
       `original`, `none`, `no-music`, `my-voice`
     - otherwise **Metadata-Only**.
   - Emit JSON-LD to `licenses/output/<file>.license.jsonld`.
4. The Action commits the new licenses back to this repo.

## Run locally
```bash
python -m pip install -U requests
python scripts/make_license_from_archive.py
