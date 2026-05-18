import logging
from pathlib import Path

import click
import jinja2
from simulation_reporter import pipeline
from simulation_reporter.config import Config


def _build_circuits_data(config: Config, build: str) -> tuple[list[dict], str | None]:
    parents = {str(Path(c.asc).parent) for c in config.circuits}
    expath = next(iter(parents)) if len(parents) == 1 else None

    data = []
    for c in config.circuits:
        seen: set[str] = set()
        sim_labels: list[str] = []
        for case in c.suite():
            if case.label not in seen:
                seen.add(case.label)
                sim_labels.append(case.label)
        plot_entries = [{"stem": p.stem, "raw_stem": p.raw_stem} for p in c.plots if p.vars]
        asc_name = Path(c.asc).name
        if expath:
            asc_dep = f"$(EXPATH)/{asc_name}"
            net_path = f"$(EXPATH)/{Path(asc_name).with_suffix('.net')}"
        else:
            asc_dep = str(Path(c.asc).resolve())
            net_path = str(Path(c.asc).with_suffix(".net"))
        raw_targets = [f"{build}/{c.slug}/{lbl}.raw" for lbl in sim_labels]
        data.append({
            "slug": c.slug,
            "asc_dep": asc_dep,
            "net_path": net_path,
            "sim_labels": sim_labels,
            "plot_entries": plot_entries,
            "raw_targets_str": " \\\n".join(raw_targets),
        })
    return data, expath


def generate_makefile(config: Config, output_makefile: str, script: str) -> str:
    proj = config.project
    build = proj.paths.build
    circuits_data, expath = _build_circuits_data(config, build)

    join = lambda files: " \\\n    ".join(files)
    svg_files = [f"{build}/{c['slug']}/schematic.svg" for c in circuits_data]
    net_files = [c["net_path"] for c in circuits_data]
    raw_files = [f"{build}/{c['slug']}/{lbl}.raw" for c in circuits_data for lbl in c["sim_labels"]]
    png_files = [f"{build}/{c['slug']}/{e['stem']}.png" for c in circuits_data for e in c["plot_entries"]]

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(Path(__file__).parent)),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )
    render_kwargs = dict(
        script=script,
        build=build,
        output_makefile=output_makefile,
        report_paths=[r.path for r in proj.reports],
        circuits=circuits_data,
        svg_files_str=join(svg_files),
        net_files_str=join(net_files),
        raw_files_str=join(raw_files),
        png_files_str=join(png_files),
    )
    if expath:
        render_kwargs["expath"] = expath
    return env.get_template("Makefile.j2").render(**render_kwargs)


def make_cli(config: Config, output_makefile: str, script: str) -> click.Group:
    @click.group()
    @click.option("--debug", is_flag=True, default=False, help="Enable debug logging.")
    def cli(debug):
        logging.basicConfig(
            level=logging.DEBUG if debug else logging.INFO,
            format="%(levelname)s %(name)s: %(message)s",
        )
        logging.getLogger("matplotlib").setLevel(logging.ERROR)

    @cli.command()
    @click.option("--circuit", default=None, metavar="SLUG")
    def svg(circuit):
        pipeline.svg(config, circuit_slug=circuit)

    @cli.command()
    @click.option("--circuit", default=None, metavar="SLUG")
    def netlist(circuit):
        pipeline.netlist(config, circuit_slug=circuit)

    @cli.command()
    @click.option("--circuit", default=None, metavar="SLUG")
    @click.option("--label", default=None, help="Run only the simulation case with this label.")
    def sim(circuit, label):
        pipeline.sim(config, circuit_slug=circuit, case_label=label)

    @cli.command()
    @click.option("--circuit", default=None, metavar="SLUG")
    @click.option("--stem", default=None, help="Render only the plot with this output stem.")
    def plots(circuit, stem):
        pipeline.plots(config, circuit_slug=circuit, plot_stem=stem)

    @cli.command()
    def report():
        pipeline.report(config)

    @cli.command(name="makefile")
    @click.option("--output", "-o", default="-", metavar="FILE", help="Write to FILE instead of stdout.")
    def makefile_cmd(output):
        content = generate_makefile(config, output_makefile, script)
        if output == "-":
            click.echo(content, nl=False)
        else:
            Path(output).write_text(content)
            click.echo(f"wrote {output}", err=True)

    return cli
