import logging
import sys
from pathlib import Path

import click

from .config import load_config
from .pipeline import svg as _svg, sim as _sim, plots as _plots, report as _report
from .suites import load_suite
from ltspice_runner.runner import DEFAULT_LTSPICE


def _setup_logging() -> None:
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    fmt = logging.Formatter("%(message)s")

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.INFO)
    stdout_handler.addFilter(lambda r: r.levelno < logging.WARNING)
    stdout_handler.setFormatter(fmt)

    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.WARNING)
    stderr_handler.setFormatter(fmt)

    root.addHandler(stdout_handler)
    root.addHandler(stderr_handler)


@click.group()
@click.option(
    "--config", "config_path",
    type=click.Path(path_type=Path),
    default=None,
    metavar="FILE",
    help="Path to project.toml (default: ./project.toml)",
)
@click.option(
    "--script", "script_path",
    type=click.Path(path_type=Path),
    default=None,
    metavar="FILE",
    help="Python file defining suite() and optionally plot()",
)
@click.pass_context
def cli(ctx, config_path, script_path):
    _setup_logging()
    ctx.ensure_object(dict)
    ctx.obj["config_path"] = config_path
    ctx.obj["script_path"] = Path(script_path).resolve() if script_path else None


@cli.command()
@click.option("--circuit", default=None, metavar="SLUG", help="Limit to one circuit")
@click.pass_context
def svg(ctx, circuit):
    """Generate schematic SVGs from .asc files."""
    _run(_svg, load_config(ctx.obj["config_path"]), circuit_slug=circuit)


@cli.command()
@click.option("--circuit", default=None, metavar="SLUG", help="Limit to one circuit")
@click.option("--ltspice", default=DEFAULT_LTSPICE, show_default=True)
@click.pass_context
def sim(ctx, circuit, ltspice):
    """Run LTspice simulations and write .raw files to the build directory."""
    _, suite_fn = _load_script(ctx)
    _run(_sim, load_config(ctx.obj["config_path"]),
         circuit_slug=circuit, ltspice_cmd=ltspice, suite_fn=suite_fn)


@cli.command()
@click.option("--circuit", default=None, metavar="SLUG", help="Limit to one circuit")
@click.pass_context
def plots(ctx, circuit):
    """Generate PNG plots from simulation .raw files."""
    plot_fn, _ = _load_script(ctx)
    _run(_plots, load_config(ctx.obj["config_path"]),
         circuit_slug=circuit, plot_fn=plot_fn)


@cli.command()
@click.option("--hugo-root", type=click.Path(path_type=Path), default=None,
              metavar="DIR", help="Hugo site root (overrides project.toml)")
@click.pass_context
def report(ctx, hugo_root):
    """Compile Hugo markdown report by rendering the Jinja2 template."""
    _report(load_config(ctx.obj["config_path"]),
            hugo_root=Path(hugo_root).resolve() if hugo_root else None)


@cli.command(name="all")
@click.option("--ltspice", default=DEFAULT_LTSPICE, show_default=True)
@click.option("--hugo-root", type=click.Path(path_type=Path), default=None, metavar="DIR")
@click.pass_context
def run_all(ctx, ltspice, hugo_root):
    """Run svg, sim, plots, and report in sequence."""
    plot_fn, suite_fn = _load_script(ctx)
    config = load_config(ctx.obj["config_path"])
    _svg(config)
    _sim(config, ltspice_cmd=ltspice, suite_fn=suite_fn)
    _plots(config, plot_fn=plot_fn)
    _report(config, hugo_root=Path(hugo_root).resolve() if hugo_root else None)


def _load_script(ctx) -> tuple[callable | None, callable | None]:
    """Return (plot_fn, suite_fn) from --script, or (None, None) if not given."""
    script_path = ctx.obj.get("script_path")
    if script_path is None:
        return None, None
    # pass a dummy circuit dict — script overrides the whole suite
    suite_fn, plot_fn = load_suite(None, script_path)
    return plot_fn, suite_fn


def _run(fn, config, **kwargs):
    try:
        fn(config, **kwargs)
    except ValueError as e:
        raise click.ClickException(str(e))
