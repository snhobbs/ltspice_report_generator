from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .config import CircuitConfig

from ltspice_runner import (
    AC,
    ACSource,
    Constant,
    Noise,
    Pulse,
    SimulationCase,
    Transient,
    VoltageSource,
)


def opamp_standard_suite(input_node: str, output_node: str) -> list[SimulationCase]:
    return [
        SimulationCase(
            VoltageSource(
                "VIN",
                input_node,
                "0",
                Pulse("0", "1", rise="10n", fall="10n", width="1m", period="2m"),
            ),
            Transient("2m", step_ceiling="10n"),
            label="step_response",
            plot_vars=[f"V({input_node})", f"V({output_node})"],
        ),
        SimulationCase(
            VoltageSource("VIN", input_node, "0", ACSource("1")),
            AC(points=200, start_freq="1", stop_freq="10meg"),
            label="ac_sweep",
            plot_vars=[f"V({output_node})"],
        ),
        SimulationCase(
            VoltageSource("VIN", input_node, "0", Constant("0")),
            Noise(
                output=output_node,
                source="VIN",
                points=200,
                start_freq="1",
                stop_freq="10meg",
            ),
            label="noise",
            plot_vars=None,
        ),
    ]


SUITES: dict[str, callable] = {
    "opamp_standard": opamp_standard_suite,
}


def load_suite(
    c: "CircuitConfig | None", script_path: Path | None = None
) -> tuple[callable, callable | None]:
    """Return (suite_fn, plot_fn).

    If script_path is given, load it as a module. The script must define
    suite(input_node, output_node) -> list[SimulationCase], and may optionally
    define plot(case, raw_path, output_path) for custom plot rendering.

    Otherwise, look up c.test_suite in the built-in SUITES dict.
    plot_fn is None when using a built-in suite or when the script omits plot().
    """
    if script_path is not None:
        spec = importlib.util.spec_from_file_location("_user_suite", script_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if not hasattr(mod, "suite"):
            raise ValueError(
                f"{script_path}: must define a suite(input_node, output_node) function"
            )
        return mod.suite, getattr(mod, "plot", None)
    return SUITES[c.test_suite], None
