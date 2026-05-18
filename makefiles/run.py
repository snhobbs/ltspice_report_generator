from pathlib import Path

from simulation_reporter.config import (
    CircuitConfig,
    Config,
    PathsConfig,
    PlotConfig,
    ProjectConfig,
    ReportConfig,
)
from simulation_reporter.suites import OpampStandardSuite
from run_common import make_cli

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
            input_source="VIN",
            plots=COMMON_PLOTS,
            suite_instance=OpampStandardSuite(),
        ),
        CircuitConfig(
            slug="integrating-opamp",
            name="Integrating Opamp",
            asc=str(EXPATH / "integrating-opamp.asc"),
            input_node="IN",
            output_node="OUT",
            input_source="VIN",
            plots=COMMON_PLOTS,
            suite_instance=OpampStandardSuite(),
        ),
        CircuitConfig(
            slug="noninverting-opamp",
            name="Non-Inverting Opamp",
            asc=str(EXPATH / "noninverting-opamp.asc"),
            input_node="IN",
            output_node="OUT",
            input_source="VIN",
            plots=COMMON_PLOTS,
            suite_instance=OpampStandardSuite(),
        ),
        CircuitConfig(
            slug="inverting-opamp",
            name="Inverting Opamp",
            asc=str(EXPATH / "inverting-opamp.asc"),
            input_node="IN",
            output_node="OUT",
            input_source="VIN",
            plots=COMMON_PLOTS,
            suite_instance=OpampStandardSuite(),
        ),
    ],
)

cli = make_cli(config, output_makefile="Makefile", script="run.py")

if __name__ == "__main__":
    cli()
