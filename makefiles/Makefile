SHELL    := /bin/bash
RUN      := python run.py

CIRCUITS := differentiating-opamp integrating-opamp noninverting-opamp inverting-opamp
EXPATH   := /home/simon/projects/eoi-document-generator/libs/ltspice-runner/example

SVG_FILES := $(patsubst %,build/%/schematic.svg,$(CIRCUITS))
SIM_STAMPS := $(patsubst %,build/%/.sim.stamp,$(CIRCUITS))

.PHONY: all svg sim plots report clean

all: svg sim plots report

# ── Schematics ────────────────────────────────────────────────────────────────
svg: $(SVG_FILES)

build/%/schematic.svg: $(EXPATH)/%.asc run.py
	@mkdir -p $(@D)
	$(RUN) svg --circuit $*

# ── Simulations ───────────────────────────────────────────────────────────────
# One stamp per circuit so `make -j` can simulate them in parallel.
sim: $(SIM_STAMPS)

build/%/.sim.stamp: $(EXPATH)/%.asc run.py
	@mkdir -p $(@D)
	$(RUN) sim --circuit $*
	@touch $@

# Ad-hoc single-circuit raw: export .asc → .net → .raw (circuit-named, flat in build/).
build/%.net: $(EXPATH)/%.asc
	ltspice-runner export $< --build-dir build

build/%.raw: build/%.net
	ltspice-runner batch $<

# ── Plots ─────────────────────────────────────────────────────────────────────
plots: build/.plots.stamp

build/.plots.stamp: $(SVG_FILES) $(SIM_STAMPS)
	$(RUN) plots
	@touch $@

# ── Report ────────────────────────────────────────────────────────────────────
REPORTS := build/opamp-examples.md build/opamp-examples-plain.md

report: $(REPORTS)

$(REPORTS): build/.plots.stamp
	$(RUN) report

# ── Housekeeping ──────────────────────────────────────────────────────────────
clean:
	rm -rf build
