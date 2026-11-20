-- مولَّدٌ بـ`tools/gen_tashkil.py`؛ لا يُحرَّر باليد (ADR ١٠٣).

namespace A116.TashkilData

/-- عددُ الهياكل في المعجم، وعددُ ما له صورةٌ واحدة. -/
def haykalCount : Nat := 49412
def wahidCount : Nat := 39154

/-- صفوفُ الشواهد: (الهيكل، صورُه). -/
def shawahid : List (String × List String) := [
  ("كتب", ["كَتَبَ", "كُتُبٌ", "كُتُبٍ", "كُتُبِ", "كُتِبَ"]),
  ("قال", ["قَالَ"]),
  ("علم", ["عَلَمٌ", "عَلَمِ", "عَلَّمَ", "عَلِمَ", "عُلِمَ", "عِلْمٌ", "عِلْمٍ", "عِلْمَ", "عِلْمُ", "عِلْمِ"]),
  ("الكتاب", ["الْكِتَابَ", "الْكِتَابُ", "الْكِتَابِ"]),
  ("والله", ["وَاللَّهُ", "وَاللَّهِ"])
]

/-- القياسُ المسجَّل (`docs/tashkil/result.json`): (البسط، المقام). -/
def muayyan : Nat × Nat := (28552, 106775)
def muhtamal : Nat × Nat := (55547, 106775)
def laHukm : Nat × Nat := (22676, 106775)
def exact : Nat × Nat := (17714, 28552)
def inSet : Nat × Nat := (39813, 55547)
def coreMuayyan : Nat × Nat := (50494, 106775)
def coreExact : Nat × Nat := (41297, 50494)

end A116.TashkilData
