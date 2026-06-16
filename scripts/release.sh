#!/usr/bin/env bash
# Release helper for the wonderland package.
#
# Subcommands (run from the repo root):
#   scripts/release.sh bump   <version>   # set pyproject.toml version
#   scripts/release.sh cut    <version>   # release-notes/dev.md -> <version>.md, reset dev.md
#   scripts/release.sh build              # clean dist/ + build sdist+wheel (uv build)
#   scripts/release.sh upload             # twine upload dist/*  (needs PyPI creds)
#   scripts/release.sh all    <version>   # bump + cut + build   (does NOT upload)
#
# Typical flow for a new release:
#   scripts/release.sh all 0.11.0     # prep version + notes + artifacts
#   # ... review, commit, merge ...
#   scripts/release.sh upload         # publish to PyPI
#
# Upload is deliberately a separate, explicit step — publishing is
# irreversible and pulls in your PyPI credentials.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

_die() { echo "error: $*" >&2; exit 1; }
_need_version() { [[ -n "${1:-}" ]] || _die "usage: release.sh $2 <version> (e.g. 0.11.0)"; }

cmd_bump() {
    _need_version "${1:-}" bump
    local v="$1"
    [[ "$v" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || _die "version must be X.Y.Z, got '$v'"
    # Update the [project] version line in pyproject.toml.
    sed -i -E "s/^version = \"[0-9]+\.[0-9]+\.[0-9]+\"/version = \"$v\"/" pyproject.toml
    echo "bumped pyproject.toml version -> $v"
    grep -E '^version = ' pyproject.toml
}

cmd_cut() {
    _need_version "${1:-}" cut
    local v="$1"
    [[ -f release-notes/dev.md ]] || _die "release-notes/dev.md not found"
    [[ ! -f "release-notes/$v.md" ]] || _die "release-notes/$v.md already exists"
    cp release-notes/dev.md "release-notes/$v.md"
    cat > release-notes/dev.md <<'HDR'
# Dev — unreleased

Active changes accumulating toward the next cut. On release, copy this file to `release-notes/<version>.md` and wipe back to header-only.
HDR
    echo "cut release-notes/dev.md -> release-notes/$v.md (dev.md reset to header)"
}

cmd_build() {
    rm -rf dist/
    uv build
    echo "built:"
    ls -1 dist/
}

cmd_upload() {
    [[ -d dist && -n "$(ls -A dist 2>/dev/null)" ]] || _die "dist/ is empty — run 'release.sh build' first"
    twine upload dist/*
}

cmd_all() {
    _need_version "${1:-}" all
    cmd_bump "$1"
    cmd_cut "$1"
    cmd_build
    echo
    echo "Done. Review + commit, then publish with: scripts/release.sh upload"
}

case "${1:-}" in
    bump)   shift; cmd_bump "$@" ;;
    cut)    shift; cmd_cut "$@" ;;
    build)  shift; cmd_build "$@" ;;
    upload) shift; cmd_upload "$@" ;;
    all)    shift; cmd_all "$@" ;;
    *) _die "usage: release.sh {bump|cut|build|upload|all} [version]" ;;
esac
