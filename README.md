# MaMeeFarm Data License

This repository issues **verifiable JSON-LD license records** for MaMeeFarm datasets.

The system reads metadata JSON files from a public data archive and produces
license records that are cryptographically linked to the exact file contents
using **SHA-256 hashing** and **timestamped commits**.

The purpose of this repository is to create a transparent and verifiable
licensing layer for MaMeeFarm data while preserving the integrity of the
original archive.

---

## Repository Scope

This repository performs the following functions:

- Generate JSON-LD license records
- Link license records to exact source files using SHA-256 hashing
- Maintain an append-only licensing history
- Provide verifiable provenance for dataset usage rights

This repository **does not host the original dataset**.  
It only produces license records derived from archived metadata.

---

## Source and Output

Source archive  
MaMeeFarm public dataset archive

Output licenses  
`licenses/output/*.license.jsonld`

License templates  
`licenses/templates/*`

Each generated license record references the exact source metadata file
through a cryptographic hash.

---

## License Generation Workflow

1. A GitHub Action runs on schedule or manually.

2. The script fetches metadata JSON files from the archive repository.

3. For each metadata file:

   - Compute SHA-256 digest of the exact file contents
   - Determine license eligibility according to metadata fields
   - Generate a JSON-LD license record referencing the file hash

4. The generated license record is written to:

licenses/output/<file>.license.jsonld

5. GitHub Actions commits the generated license records back to this repository.

---

## Repository Structure

licenses/
 ├─ output/
 │   └─ *.license.jsonld
 │
 ├─ templates/
 │   └─ license templates
 │
scripts/
 └─ make_license_from_archive.py

Description:

licenses/output/  
Generated JSON-LD license records.

licenses/templates/  
License structure templates used by the generator.

scripts/  
License generation scripts.

---

## Data Continuity Policy

This repository follows a strict **append-only record policy**.

Existing license records are **never modified** and **never removed**.

When new information becomes available, the system creates new license
records rather than altering historical entries.

This ensures:

- Historical continuity
- Verifiable provenance
- Immutable licensing history

---

## Verification Model

Each license record is cryptographically linked to the source metadata file.

Verification chain:

Archive Metadata JSON  
↓  
SHA-256 Digest  
↓  
JSON-LD License Record  
↓  
Git Commit Timestamp  

This structure allows independent verification of:

- data origin
- file integrity
- license attribution

---

## Run locally

To run the license generation script locally:

python -m pip install -U requests  
python scripts/make_license_from_archive.py

The script will:

- Fetch metadata JSON files from the archive repository
- Compute SHA-256 hashes of the exact file contents
- Generate JSON-LD license records
- Write license files to licenses/output/<file>.license.jsonld

---

## Protocol Context

This repository represents the **Licensing Layer** within the  
**DGCP (Data Governance & Continuous Proof) framework**.

DGCP defines a structure for:

- verifiable datasets
- continuous evidence generation
- transparent data provenance

Within this framework, the role of this repository is to provide
cryptographically verifiable license records derived from archived data
without altering the original dataset.

DGCP™ | MMFARM-POL-2025
