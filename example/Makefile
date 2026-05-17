RUN             = simulation-reporter
HUGO_ROOT       = ../extern/hugo-document-generator/example-site
LTSPICE_EXAMPLE = ../../ltspice_runner/example

CIRCUITS = differentiating-opamp integrating-opamp noninverting-opamp inverting-opamp

SVG_FILES   = $(patsubst %,build/%/schematic.svg,$(CIRCUITS))
REPORT      = build/opamp-examples.md
INSTALL_DST = $(HUGO_ROOT)/content/reports/opamp-examples.md

.PHONY: all svg sim plots report install clean

# Default: build everything and install into the Hugo content tree.
# Run `make sim` separately if you have LTspice and want fresh simulations.
all: $(INSTALL_DST)

# ── Schematic SVGs ────────────────────────────────────────────────────────────
svg: $(SVG_FILES)

build/%/schematic.svg: $(LTSPICE_EXAMPLE)/%.asc
	mkdir -p $(@D)
	$(RUN) svg --circuit $*

# ── LTspice simulations (optional; requires LTspice via wine) ─────────────────
sim: build/.sim.stamp

NET_FILES = $(patsubst %,$(LTSPICE_EXAMPLE)/%.net,$(CIRCUITS))

build/.sim.stamp: $(NET_FILES)
	$(RUN) --script suite.py sim
	touch $@

# ── Plots ─────────────────────────────────────────────────────────────────────
plots: build/.plots.stamp

PLOT_DEPS = $(SVG_FILES)
ifneq ($(wildcard build/.sim.stamp),)
PLOT_DEPS += build/.sim.stamp
endif

build/.plots.stamp: $(PLOT_DEPS)
	$(RUN) --script suite.py plots
	touch $@

# ── Report ────────────────────────────────────────────────────────────────────
report: $(REPORT)

$(REPORT): build/.plots.stamp $(SVG_FILES)
	$(RUN) report --hugo-root $(HUGO_ROOT)

# ── Install into Hugo content tree ────────────────────────────────────────────
install: $(INSTALL_DST)

$(INSTALL_DST): $(REPORT)
	mkdir -p $(@D)
	cp $< $@

# ── Housekeeping ──────────────────────────────────────────────────────────────
clean:
	rm -rf build
	rm -f $(INSTALL_DST)
