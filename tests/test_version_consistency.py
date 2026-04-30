"""Asegura que la versión es la misma en __init__.py, pyproject.toml,
publiccode.yml y la entrada superior del CHANGELOG.

This test guards against version drift across the canonical files that
ship v0.6.0 (and beyond). Dates are NOT compared — only the semver string.
"""
from __future__ import annotations

from pathlib import Path

import yaml

import venturalitica


REPO_ROOT = Path(__file__).resolve().parent.parent


def _read_pyproject_version() -> str:
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    for line in text.splitlines():
        if line.strip().startswith("version ="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise RuntimeError("version not found in pyproject.toml")


def _read_publiccode_version() -> str:
    data = yaml.safe_load((REPO_ROOT / "publiccode.yml").read_text(encoding="utf-8"))
    return str(data["softwareVersion"])


def _read_changelog_top_version() -> str:
    text = (REPO_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("## ["):
            return line.split("[", 1)[1].split("]", 1)[0]
    raise RuntimeError("no versioned heading in CHANGELOG.md")


def test_version_matches_across_files():
    pkg = venturalitica.__version__
    pyproject = _read_pyproject_version()
    publiccode = _read_publiccode_version()
    changelog = _read_changelog_top_version()
    assert pkg == pyproject == publiccode == changelog, (
        f"version drift: __init__={pkg}, pyproject={pyproject}, "
        f"publiccode={publiccode}, changelog={changelog}"
    )
