import A116.QiraaMadlul
import A116.Haqaiq

/-!
# قارئا الجنس والحمل في السلسلة (ADR ١١٤، أمرُ المالك 2026-10-19)

أمرُ المالك (2026-10-19 01:01 بتوقيت عمّان): «أبني أوّلًا قارئ الجنس بالمقاييس والمخصَّص، وقارئ الحمل بالوضع واللسان،
وأسجّلهما في التسجيل نفسه قبل أيّ قياس … نفذ وفق الدستور وفق افضل الممارسات».

## ما يُبنى (والمعجمُ مُعامِلٌ: مودَعاتُه في `tools/gen_silsila.py`، وهنا الدوالّ ومبرهناتُها)

* **الجذرُ من هيكل الكلمة** (`judhurOf`): الكلمةُ بلا أداة التعريف (`tajrid`) هيكلًا (`QiraaMadlul.haykal`)، فجذورُها
  في معجم الهياكل (هياكلُ ابن فارس في «مقاييس اللغة» المختومة). و`tajrid` هو `QiraaMadlul.stripAl` ومعه قاعدةٌ معلَنة
  للشمسيّة ابتداءً: «ءَ» ثمّ ساكنٌ يليه مثلُه (`RULE_AL_SHAMSI_IBTIDA`، تعيينُ البنّاء).
* **الجنس** (`ajnasOf`): أزواجُ (جذر، جنس) المودَعة لجذورٍ من الطبقة التي دونه — وعلى جذور الهيكل بـ`stripAl` هو
  `QiraaMadlul.jinsCands` بعينه مع الجذر (`kutub_iff`). والجنسُ في الأداة كتابُ «المخصَّص» الذي ذُكر فيه الجذر.
* **الحمل** (`hamlOf`): جذورُ الوضع للفظ (مفتاحُه خاناتُه) المقيّدةُ بجذور ما دونه، ولكلٍّ نوعُ حقيقته من
  `Haqaiq.haml` بلا قرينة: المنقولُ المودَع شرعيٌّ أو عرفيّ، وإلّا لغويّ (الأصلُ عدمُ النقل، ج3 س448 بترقيم الغانم). ولا مجازَ هنا:
  لا مجازَ بلا قرينةٍ مانعة (`Haqaiq.majaz_bi_qarina`)، ولا قرينةَ مودَعة.

## ما يُبرهن (لكلّ معجمٍ وكلمة)

لا جنسَ من خارج المودَع ولا من غير جذور ما دونه، والقيدُ يقطع ولا يزيد؛ ولا حملَ بلا وضعٍ للّفظ، ولا شرعيّةَ ولا عرفيّةَ
بلا نقلٍ مودَع، وما ليس في المنقول لغويّ.
-/

namespace A116.SilsilaQurra

open A116

/-! ## ١. الجذرُ من الهيكل -/

/-- الحروفُ الشمسيّة الأربعةَ عشر (تُدغم فيها لامُ التعريف). تعيينُ البنّاء من المشهور؛ ولا سطرَ مختومًا له هنا. -/
def shamsi : List Char := "تثدذرزسشصضطظلن".toList

/-- الكلمةُ بلا أداة التعريف: «ءَ» ثمّ **حرفٌ شمسيٌّ** ساكنٌ يليه مثلُه (الشمسيّةُ ابتداءً)، وإلّا `QiraaMadlul.stripAl`.
فـ«ءَيْيَاْمِ» (أَيَّامٍ) لا تُجرَّد (ضبطه المراجع)، و«ءَنْنَ» (أَنَّ) تُجرَّد خانةً كـ«ءَنْنَاْسُ» (`SHAMSI_COLLISION`). -/
def tajrid : List Cell → List Cell
  | c :: d :: e :: rest =>
    if c == ⟨Ladder.carrierOf 'ء', .fatha⟩ && d.haraka == .sukun && d.carrier == e.carrier &&
        shamsi.contains (Field112.carrierChar d.carrier) then e :: rest
    else QiraaMadlul.stripAl (c :: d :: e :: rest)
  | w => QiraaMadlul.stripAl w

/-- جذورُ الكلمة في معجم الهياكل بهيكلها بلا أداة. -/
def judhurOf (hy : List (String × List String)) (w : List Cell) : List String :=
  ((hy.find? (·.1 == QiraaMadlul.haykal (tajrid w))).map (·.2)).getD []

/-- **لا جذرَ من خارج المعجم**: كلُّ جذرٍ لصفٍّ هيكلُه هيكلُ الكلمة. -/
theorem judhurOf_mudaa (hy : List (String × List String)) (w : List Cell) (r : String)
    (h : r ∈ judhurOf hy w) : ∃ p ∈ hy, p.1 = QiraaMadlul.haykal (tajrid w) ∧ r ∈ p.2 := by
  unfold judhurOf at h
  cases hf : hy.find? (·.1 == QiraaMadlul.haykal (tajrid w)) with
  | none => simp [hf] at h
  | some p =>
    simp only [hf, Option.map_some, Option.getD_some] at h
    exact ⟨p, List.mem_of_find?_eq_some hf, by simpa using List.find?_some hf, h⟩

/-! ## ٢. الجنس -/

/-- أزواجُ الجنس المودَعة لجذورٍ معطاة. -/
def ajnasOf (aj : List (String × String)) (rs : List String) : List (String × String) :=
  (aj.filter fun a => rs.contains a.1).eraseDups

/-- **لا جنسَ من خارج المودَع، ولا لغير جذور ما دونه**. -/
theorem ajnasOf_mem (aj : List (String × String)) (rs : List String) (p : String × String)
    (h : p ∈ ajnasOf aj rs) : p ∈ aj ∧ p.1 ∈ rs := by
  simp only [ajnasOf, List.mem_eraseDups, List.mem_filter, List.contains_iff_mem] at h
  exact h

/-- **القيدُ يقطع ولا يزيد**: جذورٌ أقلّ لا تُخرج زوجًا ليس في أكثر. -/
theorem ajnasOf_la_yazid (aj : List (String × String)) (rs rs' : List String) (hs : ∀ r ∈ rs, r ∈ rs')
    (p : String × String) (h : p ∈ ajnasOf aj rs) : p ∈ ajnasOf aj rs' := by
  simp only [ajnasOf, List.mem_eraseDups, List.mem_filter, List.contains_iff_mem] at h ⊢
  exact ⟨h.1, hs _ h.2⟩

/-- **الجسرُ إلى `QiraaMadlul`**: على جذور الهيكل بـ`stripAl`، الأجناسُ هي `jinsCands` بعينها. -/
theorem kutub_iff (hy : List (String × List String)) (aj : List (String × String)) (w : List Cell) (g : String) :
    g ∈ QiraaMadlul.jinsCands hy aj w ↔
      ∃ r, (r, g) ∈ ajnasOf aj (((hy.find? (·.1 == QiraaMadlul.haykal (QiraaMadlul.stripAl w))).map (·.2)).getD []) := by
  simp only [QiraaMadlul.jinsCands, ajnasOf, List.mem_eraseDups, List.mem_map, List.mem_filter,
    List.contains_iff_mem]
  constructor
  · rintro ⟨⟨r, g'⟩, ⟨hm, hr⟩, rfl⟩
    exact ⟨r, hm, by simpa using hr⟩
  · rintro ⟨r, hm, hr⟩
    exact ⟨(r, g), ⟨hm, by simpa using hr⟩, rfl⟩

/-! ## ٣. الحمل -/

/-- نوعُ حقيقة اللفظ بلا قرينة: `Haqaiq.haml` بعينه. -/
def nawOf (rows : List Haqaiq.Manqul) (l : String) : Haqaiq.Naw :=
  match Haqaiq.haml rows l none with
  | .haqiqa n => n
  | _ => .lughawiyya

/-- مرشَّحو الحمل: جذورُ الوضع للمفتاح المقيّدةُ بجذور ما دونه، ولكلٍّ نوعُ حقيقة اللفظ. -/
def hamlOf (rows : List Haqaiq.Manqul) (wad : List (String × String)) (l key : String) (rs : List String) :
    List (String × Haqaiq.Naw) :=
  ((wad.filter fun p => p.1 == key && rs.contains p.2).map fun p => (p.2, nawOf rows l)).eraseDups

/-- **لا حملَ بلا وضعٍ للّفظ، ولا لغير جذور ما دونه**. -/
theorem la_haml_bila_wad (rows : List Haqaiq.Manqul) (wad : List (String × String)) (l key : String)
    (rs : List String) (x : String × Haqaiq.Naw) (h : x ∈ hamlOf rows wad l key rs) :
    (key, x.1) ∈ wad ∧ x.1 ∈ rs := by
  simp only [hamlOf, List.mem_eraseDups, List.mem_map, List.mem_filter, Bool.and_eq_true, beq_iff_eq,
    List.contains_iff_mem] at h
  obtain ⟨⟨k, r⟩, ⟨hm, hk, hr⟩, rfl⟩ := h
  simp only at hk
  subst hk
  exact ⟨hm, hr⟩

/-- **القيدُ يقطع ولا يزيد** في الحمل. -/
theorem hamlOf_la_yazid (rows : List Haqaiq.Manqul) (wad : List (String × String)) (l key : String)
    (rs rs' : List String) (hs : ∀ r ∈ rs, r ∈ rs') (x : String × Haqaiq.Naw)
    (h : x ∈ hamlOf rows wad l key rs) : x ∈ hamlOf rows wad l key rs' := by
  simp only [hamlOf, List.mem_eraseDups, List.mem_map, List.mem_filter, Bool.and_eq_true, beq_iff_eq,
    List.contains_iff_mem] at h ⊢
  obtain ⟨p, ⟨hm, hk, hr⟩, rfl⟩ := h
  exact ⟨p, ⟨hm, hk, hs _ hr⟩, rfl⟩

/-- **لا شرعيّةَ ولا عرفيّةَ بلا نقلٍ مودَع** (من `Haqaiq.la_naql_bila_mawda`). -/
theorem naql_mawda (rows : List Haqaiq.Manqul) (wad : List (String × String)) (l key : String)
    (rs : List String) (x : String × Haqaiq.Naw) (h : x ∈ hamlOf rows wad l key rs)
    (hn : x.2 ≠ .lughawiyya) : Haqaiq.lookup rows l = some x.2 := by
  simp only [hamlOf, List.mem_eraseDups, List.mem_map] at h
  obtain ⟨_, _, rfl⟩ := h
  simp only at hn ⊢
  unfold nawOf at hn ⊢
  cases hh : Haqaiq.haml rows l none with
  | haqiqa n =>
    rw [hh] at hn
    exact Haqaiq.la_naql_bila_mawda rows l n hh hn
  | majaz => rw [hh] at hn; exact absurd rfl hn
  | idmar => rw [hh] at hn; exact absurd rfl hn
  | laHukm => rw [hh] at hn; exact absurd rfl hn

/-- **الأصلُ عدمُ النقل**: ما ليس في المنقول حملُه لغويّ (من `Haqaiq.asl_adam_naql`). -/
theorem asl_lughawi (rows : List Haqaiq.Manqul) (wad : List (String × String)) (l key : String)
    (rs : List String) (hl : Haqaiq.lookup rows l = none) (x : String × Haqaiq.Naw)
    (h : x ∈ hamlOf rows wad l key rs) : x.2 = .lughawiyya := by
  simp only [hamlOf, List.mem_eraseDups, List.mem_map] at h
  obtain ⟨_, _, rfl⟩ := h
  simp [nawOf, Haqaiq.asl_adam_naql rows l hl]

/-! ## ٤. الشاهد: معجمٌ صغيرٌ باليد -/

def hyMithal : List (String × List String) := [("كلب", ["كلب"]), ("شمس", ["شمس"]), ("عين", ["عين", "عون"])]
def ajMithal : List (String × String) :=
  [("كلب", "كتاب السباع"), ("شمس", "كتاب السماء"), ("عين", "كتاب خلق الإنسان"), ("عين", "كتاب المياه")]
def wadMithal : List (String × String) := [("كَ لْ ب", "كلب"), ("صَ لَ اْ ت", "صلو"), ("عَ يْ ن", "عين")]

/-- **الشاهد** (`decide +kernel`): «ءَلْكَلْبُ» هيكلُه «كلب» وجنسُه «كتاب السباع»؛ والشمسيّةُ ابتداءً تُجرَّد («ءَشْشَمْسُ»
← «شمس»)؛ و«عين» جذران وثلاثةُ أجناس مع جذر ما دونه «عين» وحدَه اثنان؛ و«الصلاة» شرعيّةٌ بالمنقول، و«الكلب» لغويّة. -/
theorem shahid :
    judhurOf hyMithal (Itar.k "ءَلْكَلْبُ") = ["كلب"] ∧
    judhurOf hyMithal (Itar.k "ءَشْشَمْسُ") = ["شمس"] ∧
    QiraaMadlul.haykal (tajrid (Itar.k "ءَيْيَاْمِ")) = "ءييام" ∧
    QiraaMadlul.haykal (tajrid (Itar.k "شْشَمْسُ")) = "شمس" ∧
    ajnasOf ajMithal (judhurOf hyMithal (Itar.k "ءَلْكَلْبُ")) = [("كلب", "كتاب السباع")] ∧
    ajnasOf ajMithal ["عين"] = [("عين", "كتاب خلق الإنسان"), ("عين", "كتاب المياه")] ∧
    hamlOf Haqaiq.naql wadMithal "الصلاة" "صَ لَ اْ ت" ["صلو"] = [("صلو", .shariyya)] ∧
    hamlOf Haqaiq.naql wadMithal "الكلب" "كَ لْ ب" ["كلب"] = [("كلب", .lughawiyya)] ∧
    hamlOf Haqaiq.naql wadMithal "الكلب" "كَ لْ ب" ["عين"] = [] := by
  decide +kernel

end A116.SilsilaQurra
