import logging
import sys

import click

from .config import load_config
from .pipeline import svg as _svg, sim as _sim, plots as _plots, report as _report
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
def cli():
    _setup_logging()


@cli.command()
@click.option("--circuit", default=None, metavar="SLUG", help="Limit to one circuit")
def svg(circuit):
    """Generate schematic SVGs from .asc files."""
    _run(_svg, load_config(), circuit_slug=circuit)


@cli.command()
@click.option("--circuit", default=None, metavar="SLUG", help="Limit to one circuit")
@click.option("--ltspice", default=DEFAULT_LTSPICE, show_default=True)
def sim(circuit, ltspice):
    """Run LTspice simulations and write .raw files to the build directory."""
    _run(_sim, load_config(), circuit_slug=circuit, ltspice_cmd=ltspice)


@cli.command()
@click.option("--circuit", default=None, metavar="SLUG", help="Limit to one circuit")
def plots(circuit):
    """Generate PNG plots from simulation .raw files."""
    _run(_plots, load_config(), circuit_slug=circuit)


@cli.command()
def report():
    """Compile Hugo markdown report by rendering report_template.md.j2 via Jinja2."""
    _report(load_config())


@cli.command(name="all")
@click.option("--ltspice", default=DEFAULT_LTSPICE, show_default=True)
def run_all(ltspice):
    """Run svg, sim, plots, and report in sequence."""
    config = load_config()
    _svg(config)
    _sim(config, ltspice_cmd=ltspice)
    _plots(config)
    _report(config)


def _run(fn, config, **kwargs):
    try:
        fn(config, **kwargs)
    except ValueError as e:
        raise click.ClickException(str(e))
