TOOLKIT ?= handbook-toolkit
COMMIT ?= $(shell git rev-parse HEAD)
OUTPUT ?= ../dist

.PHONY: check full build

# Fast checks: descriptor, reading order and cross-reference gate.
check:
	$(TOOLKIT) --root . validate-book --full
	$(TOOLKIT) --root . validate-references book.yaml

# Full check: fast checks plus a real six-file local build. Requires Quarto 1.11.9 and pdfinfo.
full: check build

# The build also runs manuscript validation before rendering.
build: check
	$(TOOLKIT) build-book --repo . --commit $(COMMIT) --output $(OUTPUT) --mode chapter
