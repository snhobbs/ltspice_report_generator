# QL03

- file: QL03_LM6172_700kHzAsBuilt
- Primary Input: I1 Current Source
- Output Node: out
- TIA Resistor: R16
- Diode Stray Capacitance: C10 (12p default)
- Test Suite: Photoreceiver Standard + Diode Capacitance Sweep

# QL01

- file: QL01E
- Primary Input: I1 Current Source
- Output Node: out3
- TIA Resistor: Rf
- Diode Stray Capacitance: C3 (Cd stepped)
- Diode Series Resistance: Rd (Rs stepped)
- Test Suite: Photoreceiver Standard + Diode Capacitance Sweep

# 7ns SiPM Frontend

- file: SiPM/7nsBroadcomFrontend/spice/BFU520cascodeSiPM_7nsOutputAmp.asc
- Primary Input: I1 Current Source
- Output Node: out3
- TIA Resistor: Rf
- Diode Stray Capacitance: C3 (Cd stepped)
- Diode Series Resistance: Rd (Rs stepped)
- Test Suite: Photoreceiver Standard + Diode Capacitance Sweep
- Status: Incomplete

# Marktech APD

- file: MarktechBFU520CascTIA.asc
- Primary Input: I1 Current Source
- Output Node: out
- TIA Resistor: R16 (default 2K)
- Diode Stray Capacitance: Cs4 (Cs4 default 4.5p)
- Test Suite: Photoreceiver Standard + Diode Capacitance Sweep

## Project Simulations

A project description has a set of spice schematics simulating given sections.
A project report should have the schematic svgs and a set of plots of the output.

The project simulations could be a toml file describing everything that gets compiled into a report. Some plots will be highly specific so will need a python script for simulating and plotting. The python file should be specified in the toml file (or yaml) and built with a makefile so the makefile doesnt need to rerun.

## How to make svg

The following creates a {FILENAME}.svg from a {FILENAME}.asc

```bash
ltspice_to_svg demo.asc
```

## Makefile

The svg export, report compilation, and simulations should be called with a Makefile that lives with the project. Use markdown for the report structure and incorporate them into the eoi_document_generator as pages.
