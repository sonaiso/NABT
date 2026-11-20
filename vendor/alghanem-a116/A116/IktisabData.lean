import A116.Iktisab

/-! مولَّدٌ بـ`tools/gen_iktisab.py` (ADR ١٢٣) — لا يُحرَّر باليد. البرامجُ كما اكتسبها المتعلّم. -/

namespace A116.IktisabData

open A116.Iktisab

/-- `naqis`: اكتُسب من الأمثلة المضادّة: `and(v0, xor(v0, v1))`. -/
def naqis : Ibara := (.wa (.var 0) (.xor (.var 0) (.var 1)))

/-- `batt_qima` (bila_maktaba): `or(v1, and(v3, xor(v0, v2)))`. -/
def batt_qima_bila_maktaba : Ibara := (.aw (.var 1) (.wa (.var 3) (.xor (.var 0) (.var 2))))

/-- `batt_qima` (bil_maktaba): `or(v1, naqis(v3, v0))`. -/
def batt_qima_bil_maktaba : Ibara := (.aw (.var 1) (subst naqis [(.var 3), (.var 0)]))

/-- `batt_maalum` (bila_maktaba): `or(v0, v2)`. -/
def batt_maalum_bila_maktaba : Ibara := (.aw (.var 0) (.var 2))

/-- `batt_maalum` (bil_maktaba): `or(v0, v2)`. -/
def batt_maalum_bil_maktaba : Ibara := (.aw (.var 0) (.var 2))

/-- `taarud` (bila_maktaba): `and(v0, and(v2, xor(v1, v3)))`. -/
def taarud_bila_maktaba : Ibara := (.wa (.var 0) (.wa (.var 2) (.xor (.var 1) (.var 3))))

/-- `taarud` (bil_maktaba): `and(v0, and(v2, xor(v1, v3)))`. -/
def taarud_bil_maktaba : Ibara := (.wa (.var 0) (.wa (.var 2) (.xor (.var 1) (.var 3))))

end A116.IktisabData
