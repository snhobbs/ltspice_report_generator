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

PROJECT_NAME = "ql01"
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
            slug="ql01",
            name="QL01",
            asc="/home/simon/projects/ql01/spice/2024-12-05_S6968_ATIAdoneBiasCompensated.asc",
            input_node="N025",
            input_node_minus="N023",
            output_node="OUT3",
            input_source="I1",
            plots=make_plots("OUT", "I1"),
            suite_instance=PhotoreceiverStandardSuite.from_specs(
                secondary_gain=1,
                transimpedance=10e6,
                output_range=(-10, 10),
                bandwidth=(0, 1e6),
                pulse_width=10e-6,
            ),
        ),
        CircuitConfig(
            slug="ql01-fet-comparison",
            name="QL01",
            asc="/home/simon/projects/ql01/spice/1uATIAcandidateCPH3910vsBF862_stripped.asc",
            input_node_minus="OUT1",
            input_node="N001",
            output_node="OUT3",
            input_source="I1",
            plots=make_plots("OUT", "I1"),
            suite_instance=PhotoreceiverStandardSuite.from_specs(
                secondary_gain=1,
                transimpedance=10e6,
                output_range=(-10, 10),
                bandwidth=(0, 1e6),
                pulse_width=10e-6,
            ),
        ),
    ],
)


cli = make_cli(config, output_makefile="Makefile.ql01", script="run_ql01.py")

if __name__ == "__main__":
    cli()
