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
    if diagram_slug:
        slugs = [diagram_slug]
    else:
        slugs = registry.list_slugs()
        # Milestone-scope: when a milestone is active (tdd-implement
        # --milestone), only check diagrams whose nodes belong to it. An M1
        # review otherwise flags every M2-M4 surface (dashboard cards,
        # weather/news caches) as "missing" — true that they're unbuilt, but
        # noise that buries the findings that matter for THIS milestone.
        scoped = _milestone_scoped_slugs(project_root, registry, slugs)
        if scoped is not None:
            slugs = scoped

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


def _milestone_scoped_slugs(project_root, registry, slugs):
    """Diagram slugs whose nodes belong to the active milestone (its
    goal/done-when names at least one). Returns None when no milestone is
    active (→ caller checks everything). Mirrors the diagram seed scoping so
    review-relevance and seed-relevance agree."""
    try:
        from wonderland.workflow import get_active_milestone_scope

        scope = get_active_milestone_scope()
    except Exception:  # noqa: BLE001
        return None
    if scope is None or not getattr(scope, "slug", None):
        return None
    try:
        from wonderland.diagrams.linking import _distinctive_tokens, _title_tokens
        from wonderland.milestone import MilestoneRegistry
    except Exception:  # noqa: BLE001
        return None
    mtokens = None
    for rec in MilestoneRegistry(project_root).list_milestones():
        if rec.slug == scope.slug:
            try:
                mtokens = _title_tokens(rec.path.read_text(encoding="utf-8"))
            except OSError:
                return None
            break
    if mtokens is None:
        return None
    kept = []
    for slug in slugs:
        diagram = registry.read(slug)
        if diagram is None:
            continue
        if any(
            (dt := _distinctive_tokens(n.name)) and dt <= mtokens
            for n in diagram.nodes
        ):
            kept.append(slug)
    return kept


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


@dataclass(frozen=True)
class HollowBuild:
    """A diagram node a DONE ticket claims to build, that the built code
    doesn't actually contain — a confirmed hollow build."""

    node: str
    layer: str
    status: str  # missing | orphaned
    done_tickets: tuple[str, ...]

    def summary(self) -> str:
        return (
            f"{self.node} [{self.status}] — ticket(s) "
            f"{list(self.done_tickets)} marked DONE but the component is not "
            f"in the built code"
        )


def find_hollow_builds(
    project_root: Path,
    *,
    feature_slug: str | None = None,
    include_in_progress: bool = False,
) -> list[HollowBuild]:
    """The (b)+(d) cross-reference. A node is a CONFIRMED hollow build when a
    ticket is linked to it that CLAIMS the work is shipping (the build-tracker
    says "this was built") yet ``verify_wiring`` reports it ``missing``/
    ``orphaned`` (the code says it isn't there). The intersection is precise
    where either signal alone is noisy: it ignores inlined chrome and
    naming-divergent components, because those have no claiming ticket.

    ``include_in_progress`` widens "claims shipping" from DONE-only to also
    IN_PROGRESS. The M8 auto-approve gate needs this: at gate time the
    feature's tickets are still IN_PROGRESS (M7 finished, the accept hasn't
    marked them DONE yet), so a DONE-only check sees nothing and the hollow
    build slips through to be marked done. Post-hoc analysis keeps the
    default (DONE only).

    Scoped to one feature's tickets when ``feature_slug`` is given (M8
    reviews per feature). Pure read-side."""
    from wonderland.diagrams.links import DiagramLinks
    from wonderland.ticket_lifecycle import TicketState, get_state as tstate

    claims_states = {TicketState.DONE}
    if include_in_progress:
        claims_states.add(TicketState.IN_PROGRESS)

    registry = DiagramRegistry(project_root)
    links = DiagramLinks(project_root)
    status_by_node = {
        f.node: f.status for f in verify_wiring(project_root)
    }

    ticket_feature: dict[str, str | None] = {}
    if feature_slug is not None:
        from wonderland.cross_feature import (
            _build_feature_index,
            _parse_ticket_sources,
            _ticket_parent_feature,
        )
        from wonderland.ticket import TicketRegistry

        fslugs, _ = _build_feature_index(project_root)
        for t in TicketRegistry(project_root).list_tickets():
            try:
                ticket_feature[t.slug] = _ticket_parent_feature(
                    _parse_ticket_sources(
                        t.path.read_text(encoding="utf-8")
                    ),
                    fslugs,
                )
            except OSError:
                continue

    out: list[HollowBuild] = []
    for slug in registry.list_slugs():
        diagram = registry.read(slug)
        if diagram is None:
            continue
        for node in diagram.nodes:
            status = status_by_node.get(node.name)
            if status not in (STATUS_MISSING, STATUS_ORPHANED):
                continue
            done = []
            for tslug in links.ticket_slugs_for_node(node.guid):
                if tstate(project_root, tslug) not in claims_states:
                    continue
                if (
                    feature_slug is not None
                    and ticket_feature.get(tslug) != feature_slug
                ):
                    continue
                done.append(tslug)
            if done:
                out.append(HollowBuild(
                    node=node.name, layer=node.layer,
                    status=status, done_tickets=tuple(done),
                ))
    return out


__all__ = [
    "WiringFinding",
    "verify_wiring",
    "format_findings",
    "HollowBuild",
    "find_hollow_builds",
    "STATUS_WIRED",
    "STATUS_ORPHANED",
    "STATUS_MISSING",
    "STATUS_PRESENT",
]
