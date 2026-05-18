from pathlib import Path

from simulation_reporter.config import (
    CircuitConfig,
    Config,
    PathsConfig,
    PlotConfig,
    ProjectConfig,
    ReportConfig,
)
from simulation_reporter.suites import AmplifierStandardSuite
from run_common import make_cli

# ── Config ────────────────────────────────────────────────────────────────────

PROJECT_NAME = "la-22"
BUILD_DIR = "build-amp"
HUGO_ROOT = "../hugo-site"
LIB_DIR = "/home/simon/projects/labamps/spice"


def make_plots(input_node: str, output_node: str) -> list:
    IN, OUT = f"V({input_node})", f"V({output_node})"
    return [
        PlotConfig(label="op", title="Operating Point"),
        PlotConfig(label="step_response", title="Step Response", vars=[IN, OUT]),
        PlotConfig(label="fast_step_response", title="Step Response (Fast)", vars=[IN, OUT]),
        PlotConfig(label="ac_sweep", title="AC Sweep", vars=[OUT, "gain"], db=True),
        PlotConfig(label="noise", filename="noise_output", title="Output Noise", vars=["V(onoise)"]),
        PlotConfig(label="noise", filename="noise_gain", title="Noise Gain", vars=["gain"]),
        PlotConfig(label="noise", filename="noise_combined", title="Noise Sources",
                   vars=["V(R8)", "V(J1)", "V(J2)", "V(onoise)"]),
        PlotConfig(label="dc_sweep", title="DC Transfer", vars=[IN, OUT]),
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
            slug="la-22-THS4631",
            name="La 22 THS4631",
            asc="/home/simon/projects/labamps/spice/labampTHS4631_11nsHacked2024-03-05.asc",
            input_node="N011",
            output_node="OUT",
            input_source="V5",
            lib_dir=LIB_DIR,
            plots=make_plots("N011", "OUT"),
            suite_instance=AmplifierStandardSuite.from_specs(
                bandwidth=(1000, 30e6),
                output_range=(-10, 10),
                gain=100,
            ),
        ),
        CircuitConfig(
            slug="la-22-built",
            name="La 22 As Built",
            asc="/home/simon/projects/labamps/spice/labampAsBuilt.asc",
            input_node="N009",
            output_node="OUT",
            input_source="V5",
            lib_dir=LIB_DIR,
            plots=make_plots("N009", "OUT"),
            suite_instance=AmplifierStandardSuite.from_specs(
                bandwidth=(1000, 30e6),
                output_range=(-10, 10),
                gain=100,
            ),
        ),
    ],
)


cli = make_cli(config, output_makefile="Makefile.amp", script="run_amp.py")

if __name__ == "__main__":
    cli()
