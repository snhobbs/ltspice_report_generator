# simulation-reporter

Meta tool aimed at simplifying making reports about ltspice simulations easier.

## Tools

- [ltspice-runner](https://github.com/snhobbs/ltspice-runner) — simulation runner
- [ltspice_to_svg](https://github.com/snhobbs/ltspice_to_svg) — schematic export to svg
- [ltspice](https://github.com/DongHoonPark/ltspice_pytool) — Simulation raw file parser

## Components

- Standard test suites: Simulation sets with plot sets
  - Voltage Amplifiers
  - TIAs
  - Photoreceivers
  - Power Supplies
  - Current Supplies

- Plotting Tools: Style and standard plotting types
  - Noise analysis
  - DC Operating point
  - AC Sweep
  - Parameter sweeps
  - Step response

- Makefiles: Example make files for standard report styles, one for each Test suite type

## Built-in suites

| Name             | Simulations                          |
| ---------------- | ------------------------------------ |
| `opamp_standard` | step response, AC sweep, noise sweep |
