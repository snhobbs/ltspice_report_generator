from pathlib import Path

from simulation_reporter.config import (
    CircuitConfig,
    Config,
    PathsConfig,
    PlotConfig,
    ProjectConfig,
    ReportConfig,
)
from simulation_reporter.suites import PhotoreceiverStandardSuite
from run_common import make_cli

# ── Config ────────────────────────────────────────────────────────────────────

PROJECT_NAME = "ql03"

BUILD_DIR = f"build-{PROJECT_NAME}"
HUGO_ROOT = "../hugo-site"


def make_plots(output_node: str, input_source: str = "I1") -> list:
    I_IN = f"I({input_source})"
    OUT = f"V({output_node})"
    return [
        PlotConfig(label="op", title="Operating Point"),
        PlotConfig(
            label="step_response", title="Step Response", vars=[I_IN], right_vars=[OUT]
        ),
        PlotConfig(
            label="fast_step_response",
            title="Step Response (Fast)",
            vars=[I_IN],
            right_vars=[OUT],
        ),
        PlotConfig(
            label="ac_sweep",
            title="AC Sweep",
            vars=[I_IN],
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
            vars=["V(R16)", "V(J1)", "V(onoise)"],
        ),
        PlotConfig(
            label="dc_sweep", title="DC Transfer", vars=[I_IN], right_vars=[OUT]
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
            slug="ql03",
            name="QL03",
            asc="/home/simon/projects/ql03/spice/QL03LowCostQuietTIAnoise3.asc",
            input_node="sj",
            output_node="OUT",
            input_source="I1",
            plots=make_plots("OUT", "I1"),
            suite_instance=PhotoreceiverStandardSuite.from_specs(
                secondary_gain=1,
                transimpedance=1e6,
                output_range=(-10, 10),
                bandwidth=(0, 1e6),
                pulse_width=1000e-6,
            ),
        ),
    ],
)


cli = make_cli(
    config, output_makefile=f"Makefile.{PROJECT_NAME}", script=f"run_{PROJECT_NAME}.py"
)

if __name__ == "__main__":
    cli()
