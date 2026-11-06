PYTHON ?= python3
TOOLKIT = PYTHONPATH=tools/src $(PYTHON) -m handbook_toolkit

.PHONY: check full test verify verify-full clean

## Fast checks: suitable for every commit.
check: test verify

## Full checks: required before review and before a gate.
full: check verify-full

test:
	$(PYTHON) -m unittest discover -s tools/tests -v

verify:
	$(TOOLKIT) --root . verify

verify-full:
	$(TOOLKIT) --root . verify --full

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
