"""Piecewise-linear T(P) for ordinary water at saturation, trained on five NIST rows."""
from decimal import Decimal

SOURCE = "https://www.nist.gov/document/nistir5078-tab1pdf"
# NISTIR 5078, Table 1, pp. 5–6. Convert the published MPa to Pa exactly.
ANCHORS = ((70182, 90), (84608, 95), (101420, 100), (120900, 105), (143380, 110))


def estimate(pressure_pa):
    for (p0, t0), (p1, t1) in zip(ANCHORS, ANCHORS[1:]):
        if p0 <= pressure_pa <= p1:
            return t0 + (pressure_pa - p0) * (t1 - t0) / Decimal(p1 - p0)
    return None


def compare(kind, relations):
    result = {"model": "nist5078.table1.linear.v1", "reference": SOURCE,
              "assumptions": ["ماء نقي في اتزان سائل وبخار", "ضغط مطلق بوحدة باسكال"],
              "occurrence_verified": False}
    if kind != "ماء":
        return dict(result, status="MATERIAL_OUT_OF_SCOPE")
    pressures = [r["target"] for r in relations if r["relation"] == "pressure"]
    temps = [r for r in relations if r["relation"] == "temperature"]
    if not pressures:
        return dict(result, status="NEED_ABSOLUTE_PRESSURE")
    if len(pressures) != 1 or len(temps) > 1:
        return dict(result, status="COMPETING_OR_REPEATED_CONDITIONS")
    expected = estimate(Decimal(pressures[0]))
    if expected is None:
        return dict(result, status="PRESSURE_OUTSIDE_CALIBRATION")
    result["reference_temperature_C"] = str(expected.quantize(Decimal("0.001")))
    if not temps or temps[0]["target"] is None or temps[0]["unit"] is None:
        return dict(result, status="NEED_REPORTED_TEMPERATURE_AND_UNIT")
    temp = Decimal(temps[0]["target"])
    if temps[0]["unit_key"] == "كلفن":
        temp -= Decimal("273.15")
    return dict(result, status="COMPARED_UNDER_ASSUMPTIONS",
                reported_minus_reference_C=str((temp - expected).quantize(Decimal("0.001"))))
