import os
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
from simulation_reporter.suites import AmplifierStandardSuite
from simulation_reporter import pipeline

# ── Config from environment (set by Makefile) ─────────────────────────────────

CIRCUIT = os.environ["CIRCUIT"]
ASC = os.environ["ASC"]
INPUT_NODE = "N009"
OUTPUT_NODE = "OUT"
PROJECT_NAME = os.environ.get("PROJECT_NAME", CIRCUIT)
BUILD_DIR = os.environ.get("BUILD_DIR", "build")
HUGO_ROOT = os.environ.get("HUGO_ROOT", "../hugo-site")
LIB_DIR = os.environ.get("LIB_DIR", "")

PLOTS = [
    PlotConfig(label="op", title="Operating Point"),
    PlotConfig(
        label="step_response",
        title="Step Response",
        vars=[f"V({INPUT_NODE})", f"V({OUTPUT_NODE})"],
    ),
    PlotConfig(
        label="fast_step_response",
        title="Step Response",
        vars=[f"V({INPUT_NODE})", f"V({OUTPUT_NODE})"],
    ),
    PlotConfig(
        label="ac_sweep", title="AC Sweep", vars=[f"V({OUTPUT_NODE})", "gain"], db=True
    ),
    PlotConfig(
        label="noise", filename="noise_output", title="Output Noise", vars=["V(onoise)"]
    ),
    PlotConfig(label="noise", filename="noise_gain", title="Noise Gain", vars=["gain"]),
    PlotConfig(
        label="noise",
        filename="noise_combined",
        title="Noise Sources",
        vars=["V(R8)", "V(J1)", "V(J2)", "V(onoise)"],
    ),
    PlotConfig(
        label="dc_sweep",
        title="DC Transfer",
        vars=[f"V({INPUT_NODE})", f"V({OUTPUT_NODE})"],
    ),
]

config = Config(
    project=ProjectConfig(
        name=PROJECT_NAME,
        title=PROJECT_NAME.replace("-", " ").title(),
        paths=PathsConfig(
            build=BUILD_DIR,
            report=f"{BUILD_DIR}/{PROJECT_NAME}.md",
            hugo_root=HUGO_ROOT,
        ),
        reports=[
            ReportConfig(template="hugo", path=f"{BUILD_DIR}/{PROJECT_NAME}.md"),
            ReportConfig(template="plain", path=f"{BUILD_DIR}/{PROJECT_NAME}-plain.md"),
        ],
    ),
    circuits=[
        CircuitConfig(
            slug=CIRCUIT,
            name=CIRCUIT.replace("-", " ").title(),
            asc=ASC,
            input_node=INPUT_NODE,
            output_node=OUTPUT_NODE,
            input_source="V5",
            lib_dir=LIB_DIR,
            plots=PLOTS,
            suite_instance=AmplifierStandardSuite.from_specs(
                bandwidth=(1000, 30e6),
                output_range=(-10, 10),
                gain=100,
            ),
        ),
    ],
)

# ── CLI ───────────────────────────────────────────────────────────────────────


@click.group()
def cli():
    pass


@cli.command()
def svg():
    pipeline.svg(config)


@cli.command()
def sim():
    pipeline.sim(config)


@cli.command()
def plots():
    pipeline.plots(config)


@cli.command()
def report():
    pipeline.report(config)


if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.DEBUG)
    cli()
