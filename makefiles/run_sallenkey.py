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

PROJECT_NAME = "sallenkey"
BUILD_DIR = f"build-{PROJECT_NAME}"
HUGO_ROOT = "../hugo-site"


def make_plots(input_node: str, output_node: str) -> list:
    IN, OUT = f"V({input_node})", f"V({output_node})"
    return [
        PlotConfig(label="op", title="Operating Point"),
        PlotConfig(
            label="step_response", title="Step Response", vars=[IN], right_vars=[OUT]
        ),
        PlotConfig(
            label="fast_step_response",
            title="Step Response (Fast)",
            vars=[IN],
            right_vars=[OUT],
        ),
        PlotConfig(
            label="ac_sweep",
            title="AC Sweep",
            vars=[IN],
            right_vars=[OUT, "gain"],
            db=True,
        ),
        PlotConfig(
            label="noise",
            filename="noise_output",
            title="Output Noise",
            vars=["V(onoise)"],
        ),
        PlotConfig(
            label="noise", filename="noise_gain", title="Noise Gain", vars=["gain"]
        ),
        PlotConfig(
            label="noise",
            filename="noise_combined",
            title="Noise Sources",
            vars=["V(R6)", "V(U1)", "V(onoise)"],
        ),
        PlotConfig(label="dc_sweep", title="DC Transfer", vars=[IN], right_vars=[OUT]),
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
            slug="sallenkey-dc-1meg",
            name="DC-1MHz Sallen Key",
            asc="/home/simon/projects/noiseFilters/spice/1MHzSallenKeyGauss12_hacked2nice.asc",
            input_node="N012",
            output_node="OUT",
            input_source="V3",
            plots=make_plots("N012", "OUT"),
            suite_instance=AmplifierStandardSuite.from_specs(
                bandwidth=(100, 1e6),
                output_range=(-10, 10),
                gain=1,
            ),
        ),
        CircuitConfig(
            slug="sallenkey-dc-10meg",
            name="DC-10MHz Sallen Key",
            asc="/home/simon/projects/noiseFilters/spice/10MHzSallenKeyGauss12.asc",
            input_node="N012",
            output_node="OUT",
            input_source="V3",
            plots=make_plots("N012", "OUT"),
            suite_instance=AmplifierStandardSuite.from_specs(
                bandwidth=(100, 10e6),
                output_range=(-10, 10),
                gain=1,
            ),
        ),
        CircuitConfig(
            slug="sallenkey-dc-3meg",
            name="DC-3MHz Sallen Key",
            asc="/home/simon/projects/noiseFilters/spice/3MHzSallenKeyGauss12_hacked2nice.asc",
            input_node="N012",
            output_node="OUT",
            input_source="V3",
            plots=make_plots("N012", "OUT"),
            suite_instance=AmplifierStandardSuite.from_specs(
                bandwidth=(100, 10e6),
                output_range=(-10, 10),
                gain=1,
            ),
        ),
    ],
)


cli = make_cli(
    config, output_makefile=f"Makefile.{PROJECT_NAME}", script=f"run_{PROJECT_NAME}.py"
)

if __name__ == "__main__":
    cli()
