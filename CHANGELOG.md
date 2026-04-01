# Changelog

All notable changes to this project will be documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

## [alpha.0.1.0] - 2026-March-27
### Added
- Initial release
- NDPI to BIDS conversion via `ndpi2bids.py`
- OME-TIFF conversion support via `--convert` (requires bfconvert)
- JSON sidecar generation from stain templates
- `--dry_run` and `--force` flags


## [Released] 

## [0.1.0] - 2026-March-31
### Added
- Initial repository setup and population: Boutiques descriptor, Python environment, Dockerfile, README, templates, and LICENSE (`ff71c04`, 2026-03-26)
- NDPI to BIDS conversion via `ndpi2bids.py` with JSON sidecar generation from stain templates
- OME-TIFF conversion support via `--convert` (requires bfconvert)
- `--dry_run` and `--force` operational flags
- Template-based metadata loading from `stain-AT8_BF.json`
- `--meta KEY=VALUE` CLI option to override template metadata values
- NDPI header extraction for: Manufacturer, ManufacturersModelName, PixelSize, Magnification, Compression, BitsPerPixel, DateAcquired, ScanTimeSeconds, FocusTimeSeconds, Software
- Mandatory BIDS root files auto-created: `.bidsignore`, `dataset_description.json`, `CITATION.cff`, `README`
- Hardcoded NumericalAperture fallback
- NDPI file removed after successful OME-TIFF conversion to avoid data duplication
- `participants.json` template with updated keys
- Boutiques descriptor (`boutiques/ndpi2bids.json`)
- Change version to 0.1.0

### Changed
- Repository reorganization: templates moved inside `ndpi2bids/` package (`318678`, 2026-03-27)
- `stain-AT8_BF.json`: updated default key values (`04c75e8`, 2026-03-31)
- README: updated repository structure and badges (`bc6f5ab`, 2026-03-31)

### Fixed
- Dockerfile: removed non-existent `kiki` dependency, switched to `pip install` with `pyproject.toml` (`21fda90`, 2026-03-31)
- Fixed `build-backend` in `pyproject.toml` to `setuptools.build_meta`

## [0.1.1] - 2026-April-1
