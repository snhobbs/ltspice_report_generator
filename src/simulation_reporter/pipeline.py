from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path

import jinja2
import matplotlib

matplotlib.use("Agg")
logging.getLogger("matplotlib").setLevel(logging.ERROR)

from ltspice_runner import Netlist, plot_raw
from ltspice_runner import run_simulations as _ltspice_run
from ltspice_runner.runner import DEFAULT_LTSPICE, export_netlist

from .config import (
    PACKAGE_DIR,
    Config,
    CircuitConfig,
    PlotConfig,
    ProjectConfig,
    ReportConfig,
    filter_circuits,
    resolve,
)
from .suites import load_suite_from_script

logger = logging.getLogger(__name__)


# ── SVG export ────────────────────────────────────────────────────────────────


def svg(config: Config, circuit_slug: str | None = None) -> None:
    build_base = resolve(config.project.paths.build)
    ltspice_to_svg = config.project.paths.ltspice_to_svg
    for c in filter_circuits(config.circuits, circuit_slug):
        _export_svg(
            ltspice_to_svg,
            resolve(c.asc),
            build_base / c.slug / "schematic.svg",
            c.name,
        )


def _export_svg(ltspice_to_svg: str, asc_path: Path, out_path: Path, name: str) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info("svg  %s", name)
    result = subprocess.run(
        [ltspice_to_svg, str(asc_path), "-o", str(out_path)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        logger.error("  ERROR: %s", result.stderr.strip())
    else:
        logger.info("  -> %s", out_path)


# ── Netlist export ────────────────────────────────────────────────────────────


def netlist(
    config: Config,
    circuit_slug: str | None = None,
    ltspice_cmd: str = DEFAULT_LTSPICE,
) -> None:
    for c in filter_circuits(config.circuits, circuit_slug):
        asc_path = resolve(c.asc)
        logger.info("netlist  %s", c.name)
        try:
            net_path = export_netlist(asc_path, ltspice_cmd=ltspice_cmd)
            logger.info("  -> %s", net_path)
        except RuntimeError as e:
            logger.error("  ERROR: %s", e)


# ── Simulation ────────────────────────────────────────────────────────────────


def sim(
    config: Config,
    circuit_slug: str | None = None,
    ltspice_cmd: str = DEFAULT_LTSPICE,
    suite_fn: callable | None = None,
    case_label: str | None = None,
) -> None:
    build_base = resolve(config.project.paths.build)
    for c in filter_circuits(config.circuits, circuit_slug):
        _simulate(c, build_base / c.slug, ltspice_cmd, suite_fn, case_label=case_label)


def _saves_from_plots(plots: list[PlotConfig]) -> dict[str, list[str]]:
    """Derive per-label save lists from PlotConfig vars, skipping computed names."""
    from collections import defaultdict

    acc: defaultdict[str, set[str]] = defaultdict(set)
    for p in plots:
        for var in p.vars + p.right_vars:
            # if var.upper().startswith(("V(", "I(")):
            acc[p.raw_stem].add(var)
    return {label: sorted(vs) for label, vs in acc.items()}


def _simulate(
    c: CircuitConfig,
    build_dir: Path,
    ltspice_cmd: str,
    suite_fn: callable | None,
    case_label: str | None = None,
) -> None:
    asc_path = resolve(c.asc)
    build_dir.mkdir(parents=True, exist_ok=True)
    lib_dir = resolve(c.lib_dir) if c.lib_dir else None
    logger.info("sim  %s", c.name)
    try:
        net_path = asc_path.with_suffix(".net")
        if not net_path.exists():
            # Fallback for direct invocation outside Make
            net_path = export_netlist(asc_path, ltspice_cmd=ltspice_cmd)
        suite = suite_fn(c.input_node, c.output_node) if suite_fn else c.suite()
        if case_label is not None:
            suite = [case for case in suite if case.label == case_label]
        _ltspice_run(
            Netlist.from_file(net_path),
            suite,
            build_dir,
            lib_dir=lib_dir,
            ltspice_cmd=ltspice_cmd,
            saves=_saves_from_plots(c.plots),
        )
        logger.info("  -> %s", build_dir)
    except RuntimeError as e:
        logger.error("  ERROR: %s", e)


# ── Plots ─────────────────────────────────────────────────────────────────────


def plots(
    config: Config,
    circuit_slug: str | None = None,
    plot_fn: callable | None = None,
    plot_stem: str | None = None,
) -> None:
    build_base = resolve(config.project.paths.build)
    for c in filter_circuits(config.circuits, circuit_slug):
        build_dir = build_base / c.slug
        build_dir.mkdir(parents=True, exist_ok=True)
        existing_dir = resolve(c.existing_sim_dir) if c.existing_sim_dir else None
        for plot_def in c.plots:
            if plot_stem is not None and plot_def.stem != plot_stem:
                continue
            _plot(
                c=c,
                plot_def=plot_def,
                build_dir=build_dir,
                existing_dir=existing_dir,
                plot_fn=plot_fn,
            )


def _plot(
    c: CircuitConfig,
    plot_def: PlotConfig,
    build_dir: Path,
    existing_dir: Path | None,
    plot_fn: callable | None = None,
) -> None:
    stem = plot_def.stem
    raw_path = _find_raw(plot_def.raw_stem, build_dir, existing_dir)
    if raw_path is None:
        logger.info("  skip %s / %s: no .raw file", c.name, stem)
        return
    png_path = build_dir / f"{stem}.png"
    title = plot_def.title or plot_def.label.replace("_", " ").title()
    logger.info("plot %s / %s", c.name, stem)
    try:
        if plot_fn is not None:
            plot_fn(plot_def, raw_path, png_path)
        elif plot_def.vars:
            plot_raw(
                raw_path,
                variables=plot_def.vars,
                right_vars=plot_def.right_vars or None,
                output_path=png_path,
                title=title,
                db=plot_def.db,
            )
        else:
            logger.debug("  skip %s / %s: no vars and no plot script", c.name, stem)
            return
        logger.info("  -> %s", png_path)
    except Exception as e:
        logger.error("  ERROR: %s", e)


def _find_raw(label: str, build_dir: Path, existing_dir: Path | None) -> Path | None:
    p = build_dir / f"{label}.raw"
    if p.exists():
        return p
    if existing_dir:
        p = existing_dir / f"{label}.raw"
        if p.exists():
            return p
    return None


# ── Report ────────────────────────────────────────────────────────────────────


def report(config: Config, hugo_root: Path | None = None) -> None:
    proj = config.project
    project_name = proj.name
    build_base = resolve(proj.paths.build)

    if hugo_root is None:
        hugo_root = resolve(proj.paths.hugo_root)

    assets_dir = hugo_root / "assets" / "media" / "uploads" / project_name
    assets_dir.mkdir(parents=True, exist_ok=True)

    simulations = []
    all_written: set[Path] = set()
    for c in config.circuits:
        sim_data, written = _build_simulation(
            c, build_base / c.slug, assets_dir, project_name
        )
        simulations.append(sim_data)
        all_written.update(written)

    _prune(assets_dir, all_written)

    targets = proj.reports or [
        ReportConfig(template=proj.template, path=proj.paths.report)
    ]
    for r in targets:
        path = resolve(r.path)
        _render_report(proj, simulations, path, r.template)
        logger.info("report -> %s", path)


def _build_simulation(
    c: CircuitConfig, build_dir: Path, assets_dir: Path, project_name: str
) -> tuple[dict, set[Path]]:
    slug = c.slug
    written: set[Path] = set()

    svg_dst = assets_dir / slug / "schematic.svg"
    schematic_path = _copy_schematic(
        build_dir / "schematic.svg", assets_dir / slug, project_name, slug
    )
    if schematic_path:
        written.add(svg_dst)

    plots_data = []
    for plot_def in c.plots:
        p = _build_plot(plot_def, build_dir, assets_dir, project_name, c.name, slug)
        if p:
            plots_data.append(p)
            written.add(assets_dir / slug / f"{plot_def.stem}.png")

    return {
        "title": c.name,
        "description": c.description,
        "schematic": schematic_path,
        "schematic_rel": f"{slug}/schematic.svg" if schematic_path else "",
        "plots": plots_data,
    }, written


def _copy_schematic(svg_src: Path, dst_dir: Path, project_name: str, slug: str) -> str:
    if not svg_src.exists():
        return ""
    dst_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(svg_src, dst_dir / "schematic.svg")
    return f"media/uploads/{project_name}/{slug}/schematic.svg"


def _build_plot(
    plot_def: PlotConfig,
    build_dir: Path,
    assets_dir: Path,
    project_name: str,
    circuit_name: str,
    slug: str,
) -> dict | None:
    stem = plot_def.stem
    png_src = build_dir / f"{stem}.png"
    if not png_src.exists():
        return None
    dst = assets_dir / slug / f"{stem}.png"
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(png_src, dst)
    title = plot_def.title or plot_def.label.replace("_", " ").title()
    asset_path = f"media/uploads/{project_name}/{slug}/{stem}.png"
    caption = f"{circuit_name} — {title}"
    return {
        "title": title,
        "caption": caption,
        "path": asset_path,
        "rel_path": f"{slug}/{stem}.png",
        "shortcode": f'{{{{< imgprint src="{asset_path}" caption="{caption}" layout="full" cmd="Resize" opts="1200x q90" >}}}}',
        "description": plot_def.description,
    }


def _prune(base: Path, keep: set[Path]) -> None:
    if not base.exists():
        return
    for f in sorted(base.rglob("*")):
        if f.is_file() and f not in keep:
            logger.info("prune %s", f)
            f.unlink()
    for d in sorted(base.rglob("*"), reverse=True):
        if d.is_dir() and not any(d.iterdir()):
            d.rmdir()


_NAMED_TEMPLATES = {
    "hugo": "report_template.md.j2",
    "plain": "report_template_plain.md.j2",
}


def _render_report(
    proj: ProjectConfig, simulations: list[dict], report_path: Path, template: str = ""
) -> None:
    if template in _NAMED_TEMPLATES:
        loader = jinja2.FileSystemLoader(str(PACKAGE_DIR))
        template_name = _NAMED_TEMPLATES[template]
    elif template:
        tmpl_path = resolve(template)
        loader = jinja2.FileSystemLoader(str(tmpl_path.parent))
        template_name = tmpl_path.name
    else:
        loader = jinja2.FileSystemLoader(str(PACKAGE_DIR))
        template_name = "report_template.md.j2"

    template_data = {
        "report": {
            "title": proj.title,
            "description": proj.description,
            "date": proj.date,
            "part_number": proj.part_number,
            "categories": proj.categories,
            "tags": proj.tags,
        },
        "simulations": simulations,
    }
    env = jinja2.Environment(loader=loader, keep_trailing_newline=True)
    output = env.get_template(template_name).render(**template_data)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(output)
