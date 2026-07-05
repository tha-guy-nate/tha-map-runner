# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.12] - 2026-07-05
### Fixed
- `__init__.py` `__version__` was stale at `0.2.10` while `pyproject.toml` and PyPI were already at `0.2.11` — now back in sync.
### Changed
- `publish.yml` and `auto-assign-pr.yml` now call the reusable `python-publish.yml`/`auto-assign-pr.yml` workflows in `tha-github-workflows` instead of maintaining standalone copies. PR auto-assign now assigns the PR author (was previously hardcoded to always assign `tha-guy-nate`).

## [0.2.11] - 2026-07-04
### Fixed
- Added missing `keywords` to `pyproject.toml` (PyPI search had none) and fixed the README's opening line to lead with the family-standard "A Tabular Helper API library that..." description instead of a divergent one-off wording.

## [0.2.10] - 2026-07-04
### Fixed
- `__init__.py` `__version__` was stale at `0.2.8` while `pyproject.toml` and PyPI were already at `0.2.9` — now back in sync.
- Test coverage gap in `resolve_path`: added a test covering nested list-of-lists path traversal. Coverage is now 100%.

## [0.2.9] - 2026-06-27
### Changed
- Enabled mypy strict mode for comprehensive type checking.

## [0.2.8] - 2026-06-16
### Added
- Python 3.13 and 3.14 classifier and CI support.
### Changed
- Standardized CI and publish workflows.
- Bumped minimum dev dependency floors (pytest ≥ 9.1.0, ruff ≥ 0.15.17, mypy ≥ 2.1.0).
- Added Dependabot for automated updates.

## [0.2.7] - 2026-06-05
### Added
- List traversal in `resolve_path` for indexing into nested lists within a mapped value.

## [0.2.6] - 2026-06-05
### Added
- `expand_rows` for one-to-many fan-out joins from a single source column.

## [0.2.5] - 2026-06-01
### Changed
- Updated `enrich_from_ddb` to consume the normalized tha-aws-runner 0.1.6 fetch result shape.
- Switched to `uv publish`.

## [0.2.4] - 2026-05-31
### Fixed
- Error records from DynamoDB are treated as no-match in `enrich_from_ddb` instead of being enriched.

## [0.2.3] - 2026-05-30
### Changed
- `enrich_from_ddb` now supports per-row table routing via `table_name_col`.

## [0.2.1] - 2026-05-30
### Added
- `enrich_from_ddb` for enriching rows with DynamoDB fetch results.

## [0.2.0] - 2026-05-17
### Added
- `how="inner"` and `how="anti"` join modes to `enrich_rows`.

## [0.1.2] - 2026-05-16
### Added
- `py.typed` marker for PEP 561 typed package support.

## [0.1.1] - 2026-05-15
### Added
- `ThaMap` class for structured dict/JSON enrichment with left/inner/anti join semantics.

## [0.1.0] - 2026-05-12
### Added
- Initial release.
