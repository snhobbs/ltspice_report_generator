import sys
from pathlib import Path

import click
from simulation_reporter.config import (
    CircuitConfig,
    Config,
    PathsConfig,
    PlotConfig,
    ProjectConfig,
    ReportConfig,
)
from simulation_reporter import pipeline

# ── Config ────────────────────────────────────────────────────────────────────

COMMON_PLOTS = [
    PlotConfig(label="step_response", title="Step Response", vars=["V(IN)", "V(OUT)"]),
    PlotConfig(label="ac_sweep", title="AC Sweep", vars=["V(OUT)"], db=True),
    PlotConfig(label="noise", title="Noise"),
]

EXPATH = Path("/home/simon/projects/eoi-document-generator/libs/ltspice-runner/example")

config = Config(
    project=ProjectConfig(
        name="opamp-examples",
        title="Opamp Circuit Simulation Examples",
        date="2026-05-17",
        paths=PathsConfig(
            build="build",
            report="build/opamp-examples.md",
            hugo_root="../hugo-site",
        ),
        reports=[
            ReportConfig(template="hugo",  path="build/opamp-examples.md"),
            ReportConfig(template="plain", path="build/opamp-examples-plain.md"),
        ],
    ),
    circuits=[
        CircuitConfig(
            slug="differentiating-opamp",
            name="Differentiating Opamp",
            asc=str(EXPATH / "differentiating-opamp.asc"),
            input_node="IN",
            output_node="OUT",
            test_suite="opamp_standard",
            plots=COMMON_PLOTS,
        ),
        CircuitConfig(
            slug="integrating-opamp",
            name="Integrating Opamp",
            asc=str(EXPATH / "integrating-opamp.asc"),
            input_node="IN",
            output_node="OUT",
            test_suite="opamp_standard",
            plots=COMMON_PLOTS,
        ),
        CircuitConfig(
            slug="noninverting-opamp",
            name="Non-Inverting Opamp",
            asc=str(EXPATH / "noninverting-opamp.asc"),
            input_node="IN",
            output_node="OUT",
            test_suite="opamp_standard",
            plots=COMMON_PLOTS,
        ),
        CircuitConfig(
            slug="inverting-opamp",
            name="Inverting Opamp",
            asc=str(EXPATH / "inverting-opamp.asc"),
            input_node="IN",
            output_node="OUT",
            test_suite="opamp_standard",
            plots=COMMON_PLOTS,
        ),
    ],
)

# ── CLI ───────────────────────────────────────────────────────────────────────


@click.group()
def cli():
    pass


@cli.command()
@click.option("--circuit", default=None, metavar="SLUG")
def svg(circuit):
    pipeline.svg(config, circuit_slug=circuit)


@cli.command()
@click.option("--circuit", default=None, metavar="SLUG")
def sim(circuit):
    pipeline.sim(config, circuit_slug=circuit)


@cli.command()
@click.option("--circuit", default=None, metavar="SLUG")
def plots(circuit):
    pipeline.plots(config, circuit_slug=circuit)


@cli.command()
def report():
    pipeline.report(config)


if __name__ == "__main__":
    cli()
