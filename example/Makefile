RUN      = simulation-reporter
ROOT     = ..

CIRCUITS = differentiating-opamp integrating-opamp noninverting-opamp

SVG_FILES   = $(patsubst %,build/%/schematic.svg,$(CIRCUITS))
REPORT      = build/opamp-examples.md
INSTALL_DST = $(ROOT)/content/reports/opamp-examples.md

.PHONY: all svg sim plots report install clean

# Default: SVGs + plots (from existing .raw data) + report in build/.
# Run `make install` to copy the report into the Hugo content tree.
# Run `make sim` separately if you have LTspice and want fresh simulations.
all: $(REPORT)

# ── Schematic SVGs ────────────────────────────────────────────────────────────
svg: $(SVG_FILES)

build/%/schematic.svg: $(ROOT)/ltspice_runner/example/%.asc
	mkdir -p $(@D)
	$(RUN) svg --circuit $*

# ── LTspice simulations (optional; requires LTspice via wine) ─────────────────
# Re-runs if any .net source changes; produces .raw files in build/<circuit>/.
sim: build/.sim.stamp

NET_FILES = $(patsubst %,$(ROOT)/ltspice_runner/example/%.net,$(CIRCUITS))

build/.sim.stamp: $(NET_FILES)
	$(RUN) sim
	touch $@

# ── Plots ─────────────────────────────────────────────────────────────────────
# Rebuilds when SVGs change or when fresh simulations are available.
# Falls back to existing_sim_dir (from project.toml) if no .raw in build/.
plots: build/.plots.stamp

PLOT_DEPS = $(SVG_FILES)
ifneq ($(wildcard build/.sim.stamp),)
PLOT_DEPS += build/.sim.stamp
endif

build/.plots.stamp: $(PLOT_DEPS)
	$(RUN) plots
	touch $@

# ── Report ────────────────────────────────────────────────────────────────────
report: $(REPORT)

$(REPORT): build/.plots.stamp $(SVG_FILES)
	$(RUN) report

# ── Install into Hugo content tree ────────────────────────────────────────────
install: $(INSTALL_DST)

$(INSTALL_DST): $(REPORT)
	cp $< $@

# ── Housekeeping ──────────────────────────────────────────────────────────────
clean:
	rm -rf build
	rm -f $(INSTALL_DST)
