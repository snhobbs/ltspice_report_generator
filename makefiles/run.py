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

EXPATH = Path("/home/simon/projects/eoi-document-generator/libs/ltspice-runner/example")


def make_plots(input_node: str, output_node: str) -> list:
    IN, OUT = f"V({input_node})", f"V({output_node})"
    return [
        PlotConfig(label="op", title="Operating Point"),
        PlotConfig(
            label="step_response", title="Step Response", vars=[IN], right_vars=[OUT]
        ),
        PlotConfig(
            label="ac_sweep",
            title="AC Sweep",
            vars=[IN],
            right_vars=[OUT, "gain"],
            db=True,
        ),
        PlotConfig(label="noise", title="Noise"),
        PlotConfig(label="dc_sweep", title="DC Transfer", vars=[IN], right_vars=[OUT]),
    ]


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
            ReportConfig(template="hugo", path="build/opamp-examples.md"),
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
            input_source="VIN",
            plots=make_plots("IN", "OUT"),
            suite_instance=AmplifierStandardSuite.from_specs(
                bandwidth=(10, 1e6),
                output_range=(-10, 10),
                gain=10,
            ),
        ),
        CircuitConfig(
            slug="integrating-opamp",
            name="Integrating Opamp",
            asc=str(EXPATH / "integrating-opamp.asc"),
            input_node="IN",
            output_node="OUT",
            input_source="VIN",
            plots=make_plots("IN", "OUT"),
            suite_instance=AmplifierStandardSuite.from_specs(
                bandwidth=(10, 1e6),
                output_range=(-10, 10),
                gain=10,
            ),
        ),
        CircuitConfig(
            slug="noninverting-opamp",
            name="Non-Inverting Opamp",
            asc=str(EXPATH / "noninverting-opamp.asc"),
            input_node="IN",
            output_node="OUT",
            input_source="VIN",
            plots=make_plots("IN", "OUT"),
            suite_instance=AmplifierStandardSuite.from_specs(
                bandwidth=(10, 1e6),
                output_range=(-10, 10),
                gain=10,
            ),
        ),
        CircuitConfig(
            slug="inverting-opamp",
            name="Inverting Opamp",
            asc=str(EXPATH / "inverting-opamp.asc"),
            input_node="IN",
            output_node="OUT",
            input_source="VIN",
            plots=make_plots("IN", "OUT"),
            suite_instance=AmplifierStandardSuite.from_specs(
                bandwidth=(10, 1e6),
                output_range=(-10, 10),
                gain=10,
            ),
        ),
    ],
)

cli = make_cli(config, output_makefile="Makefile", script="run.py")

if __name__ == "__main__":
    cli()
