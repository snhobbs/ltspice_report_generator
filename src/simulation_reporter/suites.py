from __future__ import annotations

import importlib.util
from dataclasses import dataclass, field
from pathlib import Path

from .config import CircuitConfig

from ltspice_runner import (
    AC,
    ACSource,
    Constant,
    CurrentSource,
    DC,
    Noise,
    OperatingPoint,
    Pulse,
    SimulationCase,
    Transient,
    VoltageSource,
)


@dataclass
class OpampStandardSuite:
    pulse_amplitude: str = "1"
    pulse_rise: str = "10n"
    pulse_fall: str = "10n"
    pulse_width: str = "1m"
    pulse_period: str = "2m"
    tran_stop: str = "2m"
    tran_ceiling: str = ""
    ac_points: int = 200
    ac_start_freq: str = "1"
    ac_stop_freq: str = "10meg"
    noise_points: int = 200
    noise_start_freq: str = "1"
    noise_stop_freq: str = "10meg"

    def suite(
        self,
        input_source: str,
        input_node: str,
        output_node: str,
        input_node_minus: str = "0",
    ) -> list[SimulationCase]:
        return [
            SimulationCase(
                VoltageSource(
                    input_source,
                    input_node,
                    input_node_minus,
                    Pulse(
                        "0",
                        self.pulse_amplitude,
                        rise=self.pulse_rise,
                        fall=self.pulse_fall,
                        width=self.pulse_width,
                        period=self.pulse_period,
                    ),
                ),
                Transient(self.tran_stop, step_ceiling=self.tran_ceiling),
                label="step_response",
            ),
            SimulationCase(
                VoltageSource(
                    input_source, input_node, input_node_minus, ACSource("1")
                ),
                AC(
                    points=self.ac_points,
                    start_freq=self.ac_start_freq,
                    stop_freq=self.ac_stop_freq,
                ),
                label="ac_sweep",
            ),
            SimulationCase(
                VoltageSource(
                    input_source, input_node, input_node_minus, Constant("0")
                ),
                Noise(
                    output=output_node,
                    source=input_source,
                    points=self.noise_points,
                    start_freq=self.noise_start_freq,
                    stop_freq=self.noise_stop_freq,
                ),
                label="noise",
            ),
        ]


@dataclass
class AmplifierStandardSuite:
    pulse_amplitude: str = "10m"
    pulse_rise: str = "1n"
    pulse_fall: str = "1n"
    pulse_width: str = "500u"
    pulse_width_fast: str = "5u"
    pulse_period: str = "1m"
    tran_stop: str = "2m"
    tran_stop_fast: str = "50u"
    tran_ceiling: str = ""
    ac_points: int = 200
    ac_start_freq: str = "1"
    ac_stop_freq: str = "100meg"
    noise_points: int = 200
    noise_start_freq: str = "1"
    noise_stop_freq: str = "100meg"
    dc_start: str = "-100m"
    dc_stop: str = "100m"
    dc_step: str = "1m"

    @classmethod
    def from_specs(
        cls,
        bandwidth: tuple[float, float],
        output_range: tuple[float, float],
        gain: float,
        bw_decades_below: float = 1.0,
        bw_decades_above: float = 1.0,
        dc_points: int = 200,
        **overrides,
    ) -> "AmplifierStandardSuite":
        """Derive simulation parameters from bandwidth, output range, and gain.

        bandwidth       : -3 dB bandwidth in Hz
        output_range    : (v_min, v_max) usable output swing in volts
        gain            : voltage gain magnitude
        bw_decades_below: AC/noise start = bandwidth / 10**this
        bw_decades_above: AC/noise stop  = bandwidth * 10**this
        dc_points       : number of DC sweep steps across the input range
        **overrides     : any field name to override after computation
        """
        f_low, f_high = min(bandwidth), max(bandwidth)
        f_low_eff = (
            f_low if f_low > 0 else f_high / 10 ** (bw_decades_below + bw_decades_above)
        )
        t_rise = 0.35 / f_high
        in_swing = (output_range[1] - output_range[0]) / abs(gain)
        pulse_amplitude = in_swing / 2
        pulse_rise = t_rise / 10
        pulse_width = 1 / f_low_eff
        pulse_width_fast = 5.0 / f_high
        pulse_period = 2.0 * pulse_width
        tran_stop = 2.0 * pulse_period  # slow step: 4 full periods of min BW
        tran_stop_fast = 10.0 * pulse_width_fast  # fast step: 10 pulse widths at max BW
        tran_ceiling = tran_stop_fast / 1000
        ac_start = f_low_eff / 10**bw_decades_below
        ac_stop = f_high * 10**bw_decades_above
        dc_start = output_range[0] / abs(gain)
        dc_stop = output_range[1] / abs(gain)
        dc_step = (dc_stop - dc_start) / dc_points

        def _f(v: float) -> str:
            return f"{v:.4g}"

        return cls(
            pulse_amplitude=_f(pulse_amplitude),
            pulse_rise=_f(pulse_rise),
            pulse_fall=_f(pulse_rise),
            pulse_width=_f(pulse_width),
            pulse_width_fast=_f(pulse_width_fast),
            pulse_period=_f(pulse_period),
            tran_stop=_f(tran_stop),
            tran_stop_fast=_f(tran_stop_fast),
            tran_ceiling=_f(tran_ceiling),
            ac_start_freq=_f(ac_start),
            ac_stop_freq=_f(ac_stop),
            noise_start_freq=_f(ac_start),
            noise_stop_freq=_f(ac_stop),
            dc_start=_f(dc_start),
            dc_stop=_f(dc_stop),
            dc_step=_f(dc_step),
            **overrides,
        )

    def suite(
        self,
        input_source: str,
        input_node: str,
        output_node: str,
        input_node_minus: str = "0",
    ) -> list[SimulationCase]:
        return [
            SimulationCase(
                VoltageSource(
                    input_source, input_node, input_node_minus, Constant("0")
                ),
                OperatingPoint(),
                label="op",
            ),
            SimulationCase(
                VoltageSource(
                    input_source,
                    input_node,
                    input_node_minus,
                    Pulse(
                        "0",
                        self.pulse_amplitude,
                        rise=self.pulse_rise,
                        fall=self.pulse_fall,
                        width=self.pulse_width_fast,
                        period=self.pulse_period,
                    ),
                ),
                Transient(self.tran_stop_fast, step_ceiling=self.tran_ceiling),
                label="fast_step_response",
            ),
            SimulationCase(
                VoltageSource(
                    input_source,
                    input_node,
                    input_node_minus,
                    Pulse(
                        "0",
                        self.pulse_amplitude,
                        rise=self.pulse_rise,
                        fall=self.pulse_fall,
                        width=self.pulse_width,
                        period=self.pulse_period,
                    ),
                ),
                Transient(self.tran_stop, step_ceiling=self.tran_ceiling),
                label="step_response",
            ),
            SimulationCase(
                VoltageSource(
                    input_source, input_node, input_node_minus, ACSource("1")
                ),
                AC(
                    points=self.ac_points,
                    start_freq=self.ac_start_freq,
                    stop_freq=self.ac_stop_freq,
                ),
                label="ac_sweep",
            ),
            SimulationCase(
                VoltageSource(
                    input_source, input_node, input_node_minus, Constant("0")
                ),
                Noise(
                    output=output_node,
                    source=input_source,
                    points=self.noise_points,
                    start_freq=self.noise_start_freq,
                    stop_freq=self.noise_stop_freq,
                ),
                label="noise",
            ),
            SimulationCase(
                VoltageSource(
                    input_source, input_node, input_node_minus, Constant("0")
                ),
                DC(
                    source=input_source,
                    start=self.dc_start,
                    stop=self.dc_stop,
                    step=self.dc_step,
                ),
                label="dc_sweep",
            ),
        ]


@dataclass
class PhotoreceiverStandardSuite:
    """Suite for transimpedance / photoreceiver circuits with a current input.

    Overall transfer: V_out = transimpedance × I_in × secondary_gain
    The pulse amplitude is set so a half-swing input current produces a
    half-swing output voltage, keeping the output well within its linear range.
    """

    pulse_amplitude: str = "100u"  # A
    pulse_rise: str = "1n"
    pulse_fall: str = "1n"
    pulse_width: str = "500u"
    pulse_width_fast: str = "5u"
    pulse_period: str = "1m"
    pulse_period_fast: str = "1m"
    tran_stop: str = "2m"
    tran_stop_fast: str = "50u"
    tran_ceiling: str = ""
    tran_ceiling_slow: str = ""
    ac_points: int = 200
    ac_start_freq: str = "1"
    ac_stop_freq: str = "100meg"
    noise_points: int = 200
    noise_start_freq: str = "1"
    noise_stop_freq: str = "100meg"
    dc_start: str = "0"
    dc_stop: str = "1m"
    dc_step: str = "5u"

    @classmethod
    def from_specs(
        cls,
        transimpedance: float,
        output_range: tuple[float, float],
        bandwidth: tuple[float, float],
        secondary_gain: float = 1.0,
        bw_decades_below: float = 1.0,
        bw_decades_above: float = 1.0,
        dc_points: int = 200,
        **overrides,
    ) -> "PhotoreceiverStandardSuite":
        """Derive simulation parameters from photoreceiver specifications.

        transimpedance  : TIA gain in V/A (Ω)
        output_range    : (v_min, v_max) usable output swing in volts
        bandwidth       : (f_low, f_high) -3 dB bandwidth in Hz
        secondary_gain  : voltage gain of any stage following the TIA
        bw_decades_below: AC/noise start = min(bandwidth) / 10**this
        bw_decades_above: AC/noise stop  = max(bandwidth) * 10**this
        dc_points       : number of DC sweep steps across the input range
        **overrides     : any field name to override after computation
        """
        f_low, f_high = min(bandwidth), max(bandwidth)
        f_low_eff = (
            f_low if f_low > 0 else f_high / 10 ** (bw_decades_below + bw_decades_above)
        )
        overall_gain = transimpedance * secondary_gain  # V/A
        i_swing = (output_range[1] - output_range[0]) / overall_gain
        pulse_amplitude = i_swing / 2

        t_rise = 0.35 / f_high
        pulse_rise = t_rise / 10

        pulse_width = overrides.pop("pulse_width", 1.0 / f_low_eff)
        pulse_period = overrides.pop("pulse_period", 3 * pulse_width)
        tran_stop = 4 * pulse_width

        pulse_width_fast = 5.0 / f_high
        pulse_period_fast = 3 * pulse_width_fast
        tran_stop_fast = 4 * pulse_width_fast
        # tran_ceiling = tran_stop_fast / 1000

        ac_start = f_low_eff / 10**bw_decades_below
        ac_stop = f_high * 10**bw_decades_above

        dc_start = output_range[0] / overall_gain
        dc_stop = output_range[1] / overall_gain
        dc_step = (dc_stop - dc_start) / dc_points

        def _f(v: float) -> str:
            return f"{v:.4g}"

        return cls(
            pulse_amplitude=_f(pulse_amplitude),
            pulse_rise=_f(pulse_rise),
            pulse_fall=_f(pulse_rise),
            pulse_width=_f(pulse_width),
            pulse_width_fast=_f(pulse_width_fast),
            pulse_period=_f(pulse_period),
            pulse_period_fast=_f(pulse_period_fast),
            tran_stop=_f(tran_stop),
            tran_stop_fast=_f(tran_stop_fast),
            tran_ceiling_slow=_f(pulse_rise * 10),
            tran_ceiling=_f(pulse_rise * 10),
            ac_start_freq=_f(ac_start),
            ac_stop_freq=_f(ac_stop),
            noise_start_freq=_f(ac_start),
            noise_stop_freq=_f(ac_stop),
            dc_start=_f(dc_start),
            dc_stop=_f(dc_stop),
            dc_step=_f(dc_step),
            **overrides,
        )

    def suite(
        self,
        input_source: str,
        input_node: str,
        output_node: str,
        input_node_minus: str = "0",
    ) -> list[SimulationCase]:
        src = lambda waveform: CurrentSource(
            input_source, input_node, input_node_minus, waveform
        )
        pulse_fast = Pulse(
            "0",
            self.pulse_amplitude,
            rise=self.pulse_rise,
            fall=self.pulse_fall,
            width=self.pulse_width_fast,
            period=self.pulse_period_fast,
        )
        pulse_slow = Pulse(
            "0",
            self.pulse_amplitude,
            rise=self.pulse_rise,
            fall=self.pulse_fall,
            width=self.pulse_width,
            period=self.pulse_period,
        )
        return [
            SimulationCase(
                src(Constant("0")),
                OperatingPoint(),
                label="op",
            ),
            SimulationCase(
                src(pulse_fast),
                Transient(self.tran_stop_fast, step_ceiling=self.tran_ceiling),
                label="fast_step_response",
            ),
            SimulationCase(
                src(pulse_slow),
                Transient(self.tran_stop, step_ceiling=self.tran_ceiling_slow),
                label="step_response",
            ),
            SimulationCase(
                src(ACSource("1")),
                AC(
                    points=self.ac_points,
                    start_freq=self.ac_start_freq,
                    stop_freq=self.ac_stop_freq,
                ),
                label="ac_sweep",
            ),
            SimulationCase(
                src(Constant("0")),
                Noise(
                    output=output_node,
                    source=input_source,
                    points=self.noise_points,
                    start_freq=self.noise_start_freq,
                    stop_freq=self.noise_stop_freq,
                ),
                label="noise",
            ),
            SimulationCase(
                src(Constant("0")),
                DC(
                    source=input_source,
                    start=self.dc_start,
                    stop=self.dc_stop,
                    step=self.dc_step,
                ),
                label="dc_sweep",
            ),
        ]


_SUITE_REGISTRY: dict[str, callable] = {
    "opamp_standard": lambda src, i, o: OpampStandardSuite().suite(src, i, o),
    "amplifier_standard": lambda src, i, o: AmplifierStandardSuite().suite(src, i, o),
    "photoreceiver_standard": lambda src, i, o: PhotoreceiverStandardSuite().suite(
        src, i, o
    ),
}


def load_suite_from_script(script_path: Path) -> tuple[callable, callable | None]:
    """Load suite_fn (and optional plot_fn) from a user-supplied .py script."""
    spec = importlib.util.spec_from_file_location("_user_suite", script_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if not hasattr(mod, "suite"):
        raise ValueError(
            f"{script_path}: must define a suite(input_node, output_node) function"
        )
    return mod.suite, getattr(mod, "plot", None)
