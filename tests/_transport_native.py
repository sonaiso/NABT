"""Portable discovery versus mandatory native transport conformance."""
from functools import wraps
import os
from pathlib import Path
import unittest

BIN = Path(__file__).resolve().parents[1] / "formal/.lake/build/bin"


def require_native(*names):
    missing = [name for name in names if not (BIN / name).is_file()]
    if missing:
        message = "Native transport prerequisites missing: " + ", ".join(missing)
        if os.environ.get("NABT_REQUIRE_NATIVE_TRANSPORT") == "1":
            raise AssertionError(message)
        raise unittest.SkipTest(message + "; mandatory native gate sets NABT_REQUIRE_NATIVE_TRANSPORT=1")


def native_test(*names):
    def decorate(function):
        @wraps(function)
        def checked(*args, **kwargs):
            require_native(*names)
            return function(*args, **kwargs)
        return checked
    return decorate
