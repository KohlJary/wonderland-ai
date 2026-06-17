"""Wiring-diff: reverse-adapt built code → diff vs the intended diagram (P21 d).

The hollow-verify payoff. The first LDR pilot shipped front-end components
that existed as files but were never mounted into the app — every layer
"verified" in isolation, the composed product was empty. A diagram node
records INTENT ("the dashboard renders a WeatherCard"); this module reads
the built code, reverse-adapts each component to find what it actually
renders/imports, and reports each node as:

  - ``wired``     — built AND referenced (imported or rendered) by something
                    other than its own definition. The component is hooked up.
  - ``orphaned``  — built (a file defines it) but NOTHING references it. The
                    hollow build: it passes its own unit test and ships
                    nothing the user can see. THIS is the class to catch.
  - ``missing``   — the diagram intends it, no file defines it. Not built.

UI nodes drive the structural check (React component composition, via the
vendored Ophanic reverse-adapter + a JSX-tag fallback). DB-layer nodes get a
lighter presence check (is the table/model named anywhere in the backend?).

Deterministic + read-only. Surfaced to Caterpillar as the ``verify_wiring``
review tool — the verification half of the build-against-contract loop (c).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from wonderland.diagrams.models import LAYER_DB, LAYER_UI
from wonderland.diagrams.registry import DiagramRegistry

STATUS_WIRED = "wired"
STATUS_ORPHANED = "orphaned"
STATUS_MISSING = "missing"
STATUS_PRESENT = "present"  # db-layer: table/model found in backend

_FRONTEND_EXT = {".tsx", ".jsx", ".ts", ".js"}
_BACKEND_EXT = {".py", ".sql", ".ts", ".js"}
_SKIP_DIRS = {"node_modules", ".git", "dist", "build", "__pycache__", ".venv"}
# JSX component tags are Capitalised; HTML tags are lowercase.
_JSX_TAG_RE = re.compile(r"<([A-Z][A-Za-z0-9_]*)")
_IMPORT_RE = re.compile(r"\bimport\b[^;\n]*")
_IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
# Framework-mounted entry points: never "orphaned" even if nothing in the
# repo imports them (main.tsx / the bundler mounts them).
_ENTRY_NAMES = {"App", "Main", "Root", "Index", "Layout"}


@dataclass(frozen=True)
class WiringFinding:
    node: str
    layer: str
    status: str
    detail: str

    @property
    def is_problem(self) -> bool:
        return self.status in (STATUS_ORPHANED, STATUS_MISSING)


def _iter_files(project_root: Path, src_dirs, exts) -> list[Path]:
    out: list[Path] = []
    for sd in src_dirs:
        base = project_root / sd
        if not base.is_dir():
            continue
        for f in base.rglob("*"):
            if not f.is_file() or f.suffix.lower() not in exts:
                continue
            if _SKIP_DIRS & set(f.parts):
                continue
            if ".test." in f.name or ".spec." in f.name:
                continue
            out.append(f)
    return out


def _rendered_refs(text: str) -> set[str]:
    """Components this source renders. Reverse-adapt via the Ophanic React
    parser (structural), then union a raw JSX-tag scan (robust fallback for
    code the layout parser can't model)."""
    refs: set[str] = set()
    try:
        from wonderland.diagrams._ophanic.adapters.react_reverse import (
            parse_react,
        )
        from wonderland.diagrams._ophanic.models import NodeType

        doc = parse_react(text)

        def walk(node) -> None:
            if node.type == NodeType.COMPONENT_REF and node.name:
                refs.add(node.name)
            for child in node.children:
                walk(child)

        for bp in doc.breakpoints:
            walk(bp.root)
    except Exception:  # noqa: BLE001 — best-effort; the regex covers us
        pass
    for m in _JSX_TAG_RE.finditer(text):
        refs.add(m.group(1))
    return refs


def _imported_names(text: str) -> set[str]:
    """Identifiers pulled in by import statements — the other way a
    component gets referenced (a router importing a page)."""
    names: set[str] = set()
    for m in _IMPORT_RE.finditer(text):
        # Drop the module path, keep the bound identifiers.
        head = m.group(0).split(" from ")[0]
        for ident in _IDENT_RE.findall(head):
            if ident not in ("import", "from", "as", "type"):
                names.add(ident)
    return names


def _defined_component(path: Path, text: str) -> str | None:
    """The component a frontend file defines: its CapitalCase filename stem
    (React convention) or an exported Capitalised function/const/class."""
    stem = path.stem
    if stem[:1].isupper():
        return stem
    m = re.search(
        r"\b(?:export\s+)?(?:default\s+)?(?:function|const|class)\s+"
        r"([A-Z][A-Za-z0-9_]*)",
        text,
    )
    return m.group(1) if m else None


def verify_wiring(
    project_root: Path,
    *,
    diagram_slug: str | None = None,
    src_dirs: tuple[str, ...] = ("src", "frontend", "app", "client"),
    backend_dirs: tuple[str, ...] = ("src", "backend", "server", "api"),
) -> list[WiringFinding]:
    """Diff built code against the intended diagram(s). ``diagram_slug``
    limits to one diagram; otherwise every diagram is checked."""
    registry = DiagramRegistry(project_root)
    slugs = [diagram_slug] if diagram_slug else registry.list_slugs()

    # ---- frontend reference graph (built once) ----
    fe_files = _iter_files(project_root, src_dirs, _FRONTEND_EXT)
    defined: dict[str, Path] = {}
    file_owner: dict[Path, str | None] = {}
    file_text: dict[Path, str] = {}
    for f in fe_files:
        txt = f.read_text(encoding="utf-8", errors="ignore")
        file_text[f] = txt
        owner = _defined_component(f, txt)
        file_owner[f] = owner
        if owner:
            defined.setdefault(owner, f)
    referenced: dict[str, set[Path]] = {}
    for f in fe_files:
        owner = file_owner[f]
        refs = _rendered_refs(file_text[f]) | _imported_names(file_text[f])
        for name in refs:
            if name != owner:
                referenced.setdefault(name, set()).add(f)

    # ---- backend text (for db-layer presence) ----
    be_text = ""
    if any(registry.read(s) and registry.read(s).layer == LAYER_DB for s in slugs):
        be_files = _iter_files(project_root, backend_dirs, _BACKEND_EXT)
        be_text = "\n".join(
            f.read_text(encoding="utf-8", errors="ignore") for f in be_files
        ).lower()

    findings: list[WiringFinding] = []
    for slug in slugs:
        diagram = registry.read(slug)
        if diagram is None:
            continue
        for node in diagram.nodes:
            nm = node.name
            if diagram.layer == LAYER_DB:
                # Presence check: is the table/entity named in the backend?
                hay = be_text
                hit = nm.lower() in hay or _snake(nm) in hay
                findings.append(
                    WiringFinding(
                        nm, diagram.layer,
                        STATUS_PRESENT if hit else STATUS_MISSING,
                        f"{nm}: {'found' if hit else 'NOT found'} in backend",
                    )
                )
                continue
            # UI node.
            if nm not in defined:
                findings.append(WiringFinding(
                    nm, diagram.layer, STATUS_MISSING,
                    f"{nm}: no component defines it under {list(src_dirs)}",
                ))
            elif nm in _ENTRY_NAMES or referenced.get(nm):
                n = len(referenced.get(nm, ()))
                findings.append(WiringFinding(
                    nm, diagram.layer, STATUS_WIRED,
                    f"{nm}: defined ({defined[nm].name}) + referenced by "
                    f"{n} file(s)" if n else f"{nm}: entry component",
                ))
            else:
                findings.append(WiringFinding(
                    nm, diagram.layer, STATUS_ORPHANED,
                    f"{nm}: defined in {defined[nm].name} but NEVER imported "
                    f"or rendered — hollow build, not wired into the app",
                ))
    return findings


def _snake(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def format_findings(findings: list[WiringFinding]) -> str:
    if not findings:
        return "verify_wiring: no diagram nodes to check."
    problems = [f for f in findings if f.is_problem]
    lines = []
    for f in findings:
        mark = "✗" if f.is_problem else "✓"
        lines.append(f"  {mark} [{f.status}] {f.detail}")
    head = (
        f"verify_wiring: {len(problems)} problem(s) of {len(findings)} nodes"
        if problems
        else f"verify_wiring: all {len(findings)} nodes wired/present"
    )
    return head + "\n" + "\n".join(lines)


__all__ = [
    "WiringFinding",
    "verify_wiring",
    "format_findings",
    "STATUS_WIRED",
    "STATUS_ORPHANED",
    "STATUS_MISSING",
    "STATUS_PRESENT",
]
