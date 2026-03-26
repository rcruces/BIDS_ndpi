# BIDS microscopy: ndpi

Convert whole-slide images in `.ndpi` format to [Brain Imaging Data Structure (BIDS) microscopy](https://bids-specification.readthedocs.io/en/stable/modality-specific-files/microscopy.html) compliant datasets.

---

## Overview

`BIDS_ndpi` automates the conversion of Hamamatsu `.ndpi` whole-slide microscopy images into a BIDS-compliant directory structure, generating the required JSON sidecars, `participants.tsv`, and metadata files along the way.

---

## Repository structure

```
BIDS_ndpi/
├── README.md
├── Dockerfile
├── environment.yml
├── CITATION.cff
├── .gitignore
├── ndpi2bids/
│   ├── __init__.py
│   ├── ndpi2bids.json          # Boutique descriptor 
│   └── ndpi2bids.py            # Main conversion script
└── templates/
    ├── stain-AT8_BF.json       # Stain-specific JSON sidecar template
    ├── participants.json       # Participants metadata template
    └── participants_description.json
```

---

## Requirements

- Docker (recommended), **or**
- [Pixi](https://pixi.sh) / conda with the provided `environment.yml`

---

## Quick start

### With Docker

```bash
# Build the image
docker build -t bids_ndpi .

# Run conversion
docker run --rm \
  -v /path/to/ndpi/files:/input \
  -v /path/to/output:/output \
  bids_ndpi \
  python ndpi2bids/ndpi2bids.py --input /input --output /output
```

### With conda / pixi

```bash
# Create environment
conda env create -f environment.yml
conda activate bids_ndpi

# Run conversion
python ndpi2bids/ndpi2bids.py --input /path/to/ndpi --output /path/to/bids
```

---

## Usage

```bash
python ndpi2bids/ndpi2bids.py [OPTIONS]

Mandatory arguments:
  --ndpi_path  PATH   Path to raw Hamamatsu .ndpi file             [required]
  --bids       PATH   Path to the root of the BIDS dataset         [required]
  --sub        LABEL  Subject ID (e.g., PX067)                     [required]
  --stain      LABEL  Stain entity (e.g., AT8)                     [required]
  --suffix     LABEL  BIDS suffix (e.g., BF)                       [required]

Optional BIDS entities:
  --ses        LABEL  Session ID
  --sample     LABEL  Sample ID (e.g., NP24709)
  --acq        LABEL  Acquisition label
  --run        INDEX  Run index
  --chunk      LABEL  Chunk label (e.g., A3)
  --template   PATH   JSON template for metadata (overrides defaults)

Operational flags:
  --convert           Convert NDPI to OME-TIFF via bfconvert
  --force             Overwrite existing BIDS files and sidecars
  --dry_run           Print the intendet output.
```

## Example
```bash
python ndpi2bids/ndpi2bids.py \
  --ndpi_path /data/raw/PX067_AT8.ndpi \
  --bids      /data/bids \
  --sub       S001 \
  --stain     AT8 \
  --suffix    BF \
  --ses       01 \
  --sample    NP24709A1 \
  --convert
```

---

## Templates

JSON templates in `./templates/` define stain-specific metadata injected into BIDS sidecars.

| File | Purpose |
|------|---------|
| `stain-AT8_BF.json` | Sidecar template for AT8 brightfield staining |
| `participants.json` | Column definitions for `participants.tsv` |
| `participants_description.json` | Dataset-level participant metadata |

To add a new stain, copy an existing template and update the fields, then pass it via `--template`.

---

## BIDS output structure

```
output/
├── dataset_description.json
├── participants.tsv
├── participants.json
├── README
└── sub-<label>/
    └── ses-<label>/
        └── micr/
            ├── sub-<label>_ses-<label>_stain-AT8_BF.ndpi
            └── sub-<label>_ses-<label>_stain-AT8_BF.json
```

---

## Citation

If you use this tool, please cite it using the metadata in [`CITATION.cff`](./CITATION.cff).

---

## License

MIT License — see `LICENSE` for details.