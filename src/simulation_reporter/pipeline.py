import logging
import shutil
import subprocess
from pathlib import Path

import jinja2
import matplotlib
matplotlib.use("Agg")

from ltspice_runner import Netlist, plot_raw
from ltspice_runner import run_simulations as _ltspice_run
from ltspice_runner.runner import DEFAULT_LTSPICE

from .config import PACKAGE_DIR, filter_circuits, resolve
from .suites import SUITES

logger = logging.getLogger(__name__)


# ── SVG export ───────────────────────────────────────────────────────────────

def svg(config: dict, circuit_slug: str | None = None) -> None:
    paths = config["project"]["paths"]
    build_base = resolve(paths["build"])
    ltspice_to_svg = paths.get("ltspice_to_svg", "ltspice_to_svg")
    for c in filter_circuits(config["circuits"], circuit_slug):
        _export_svg(ltspice_to_svg, resolve(c["asc"]), build_base / c["slug"] / "schematic.svg", c["name"])


def _export_svg(ltspice_to_svg: str, asc_path: Path, out_path: Path, name: str) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info("svg  %s", name)
    result = subprocess.run([ltspice_to_svg, str(asc_path), "-o", str(out_path)], capture_output=True, text=True)
    if result.returncode != 0:
        logger.error("  ERROR: %s", result.stderr.strip())
    else:
        logger.info("  -> %s", out_path)


# ── Simulation ────────────────────────────────────────────────────────────────

def sim(config: dict, circuit_slug: str | None = None, ltspice_cmd: str = DEFAULT_LTSPICE) -> None:
    build_base = resolve(config["project"]["paths"]["build"])
    for c in filter_circuits(config["circuits"], circuit_slug):
        _simulate(c, build_base / c["slug"], ltspice_cmd)


def _simulate(c: dict, build_dir: Path, ltspice_cmd: str) -> None:
    net_path = resolve(c["asc"]).with_suffix(".net")
    if not net_path.exists():
        logger.info("sim  %s: no .net file, skipping", c["name"])
        return
    suite = SUITES[c["test_suite"]](c["input_node"], c["output_node"])
    logger.info("sim  %s", c["name"])
    try:
        _ltspice_run(Netlist.from_file(net_path), suite, build_dir, ltspice_cmd=ltspice_cmd)
        logger.info("  -> %s", build_dir)
    except RuntimeError as e:
        logger.error("  ERROR: %s", e)


# ── Plots ─────────────────────────────────────────────────────────────────────

def plots(config: dict, circuit_slug: str | None = None) -> None:
    build_base = resolve(config["project"]["paths"]["build"])
    for c in filter_circuits(config["circuits"], circuit_slug):
        build_dir = build_base / c["slug"]
        build_dir.mkdir(parents=True, exist_ok=True)
        existing_dir = resolve(c["existing_sim_dir"]) if c.get("existing_sim_dir") else None
        suite = SUITES[c["test_suite"]](c["input_node"], c["output_node"])
        for case in suite:
            _plot(c, case, build_dir, existing_dir)


def _plot(c: dict, case, build_dir: Path, existing_dir: Path | None) -> None:
    raw_path = _find_raw(case.label, build_dir, existing_dir)
    if raw_path is None:
        logger.info("  skip %s/%s: no .raw file", c["slug"], case.label)
        return
    png_path = build_dir / f"{case.label}.png"
    logger.info("plot %s / %s", c["name"], case.label)
    try:
        plot_raw(raw_path, variables=case.plot_vars, output_path=png_path,
                 title=f"{c['name']} — {case.label.replace('_', ' ')}", db=(case.label == "ac_sweep"))
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

def report(config: dict) -> None:
    proj = config["project"]
    paths = proj["paths"]
    project_name = proj["name"]
    build_base = resolve(paths["build"])
    report_path = resolve(paths["report"])
    hugo_root = resolve(paths.get("hugo_root", ".."))

    png_assets_dir = hugo_root / "assets" / "media" / "uploads" / project_name
    svg_static_dir = hugo_root / "static" / "sim" / project_name
    png_assets_dir.mkdir(parents=True, exist_ok=True)
    svg_static_dir.mkdir(parents=True, exist_ok=True)

    simulations = [
        _build_simulation(c, build_base / c["slug"], svg_static_dir, png_assets_dir, project_name)
        for c in config["circuits"]
    ]
    _render_report(proj, simulations, report_path)
    logger.info("report -> %s", report_path)


def _build_simulation(c: dict, build_dir: Path, svg_static_dir: Path,
                      png_assets_dir: Path, project_name: str) -> dict:
    slug = c["slug"]
    suite = SUITES[c["test_suite"]](c["input_node"], c["output_node"])
    schematic_url = _copy_schematic(build_dir / "schematic.svg", svg_static_dir / slug, project_name, slug)
    plots_data = [
        p for case in suite
        if (p := _build_plot(case, build_dir, png_assets_dir, project_name, c["name"], slug))
    ]
    return {"title": c["name"], "description": c.get("description", ""),
            "schematic": schematic_url, "plots": plots_data}


def _copy_schematic(svg_src: Path, dst_dir: Path, project_name: str, slug: str) -> str:
    if not svg_src.exists():
        return ""
    dst_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(svg_src, dst_dir / "schematic.svg")
    return f"/sim/{project_name}/{slug}/schematic.svg"


def _build_plot(case, build_dir: Path, png_assets_dir: Path,
                project_name: str, circuit_name: str, slug: str) -> dict | None:
    png_src = build_dir / f"{case.label}.png"
    if not png_src.exists():
        return None
    dst = png_assets_dir / slug / f"{case.label}.png"
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(png_src, dst)
    label_title = case.label.replace("_", " ").title()
    asset_path = f"media/uploads/{project_name}/{slug}/{case.label}.png"
    caption = f"{circuit_name} — {label_title}"
    return {
        "title": label_title,
        "caption": caption,
        "path": asset_path,
        "shortcode": f'{{{{< imgprint src="{asset_path}" caption="{caption}" layout="full" cmd="Resize" opts="1200x q90" >}}}}',
        "description": "",
    }


def _render_report(proj: dict, simulations: list[dict], report_path: Path) -> None:
    template_data = {
        "report": {
            "title": proj["title"],
            "description": proj.get("description", ""),
            "date": proj.get("date", "2026-01-01"),
            "part_number": proj.get("part_number", ""),
        },
        "simulations": simulations,
    }
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(PACKAGE_DIR)),
        keep_trailing_newline=True,
    )
    output = env.get_template("report_template.md.j2").render(**template_data)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(output)
