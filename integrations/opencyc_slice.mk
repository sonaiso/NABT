.PHONY: opencyc-slice-native
# The original owners remain mandatory, not mocked, in the public release gate.
opencyc-slice-native: io-gateway-build
	PYTHONPATH=src:. NABT_REQUIRE_OPENCYC_NATIVE=1 $(PYTHON) -B -m unittest tests.test_opencyc_slice -v

check: opencyc-slice-native
