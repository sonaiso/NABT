.PHONY: opencyc-slice-native
# The original owners remain mandatory, not mocked, in the public release gate.
opencyc-slice-native: io-gateway-build
	PYTHONPATH=src:. NABT_REQUIRE_OPENCYC_NATIVE=1 $(PYTHON) -B -m unittest tests.test_opencyc_slice tests.test_opencyc_boundary -v

check io-gateway-native: opencyc-slice-native
