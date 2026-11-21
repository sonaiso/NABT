import A116.Tarkib

/-!
# المفردُ: اسمٌ وفعلٌ وحرف، والاسمُ كلّيٌّ وجزئيّ، والضميرُ اسمٌ لا حرف (ADR ٨١)

ملاحظةُ المالك (2026-10-16): «الضمير اسمٌ وليس حرفًا، وهو مكوّنٌ من الـ116، وهو اسمٌ وليس أداة. راجع الفرقَ بين
الاسم والحرف: الحرف لا يستقلّ بذاته. راجع النبهانيَّ في الكلّيّ والجزئيّ بعمق.»

## السند (منقولٌ بلفظه، لا مُعاد الصوغ)

* الشخصيّة ج3، «المفرد»: «اللفظ المفرد إمّا أن لا يستقلّ بمعناه، وإمّا أن يستقلّ بمعناه؛ فإن كان لا يستقلّ
  بمعناه فهو الحرف … وإن كان يستقلّ بمعناه … فإن دلّ بهيئته … على أحد الأزمنة الثلاثة … فهو الفعل … وإن لم
  يدلّ بهيئته على أحد الأزمنة فهو الاسم».
* ج3، «الاسم»: «إمّا أن يكون كلّيًّا وإمّا أن يكون جزئيًّا؛ لأنّه إن كان بحيث يصحّ أن يشترك في مفهومه كثيرون …
  فهو الكلّيّ … وأمّا الجزئيّ فهو الذي لم يشترك في معناه كثيرون، مثل زيد علمًا على رجل، ومثل الضمائر كهو وهي».
* ج3: «وأمّا الجزئيّ فهو نوعان علمٌ وضمير؛ … إن استقلّ اللفظ بالدلالة، أي كان لا يفتقر إلى شيءٍ يفسّره، فهو
  العلم … وإن لم يستقلّ، بأن كان يفتقر إلى شيءٍ يفسّره، فهو المضمر … والفرقُ بينه وبين الحرف أنّ الحرف لا
  يستقلّ بمعناه أصلًا، ولا يُفهم معناه إلّا بوجود لفظٍ متعلّقٍ معناه بمعناه. وأمّا الضمير فهو مستقلٌّ بمعناه
  أصلًا … وإنّما هو يفتقر إلى التفسير فقط؛ ولذلك كان الضميرُ اسمًا، وهو مغايرٌ للحرف».
* شرحُ ابن عقيل المختوم س209–211: «إن دلّت على معنًى في نفسها غيرَ مقترنةٍ بزمانٍ فهي الاسم … وإن لم تدلّ على
  معنًى في نفسها بل في غيرها فهي الحرف»؛ وس738: «المضمراتُ كلُّها مبنيّةٌ لشبهها بالحروف» — شبهٌ لا هويّة.

## ما يُبرهَن

١. **القسمةُ ثلاثيّةٌ بالاستقلال ثمّ الهيئة** (`qismOf`): الحرفُ ⟺ لا استقلال (`harf_iff`).
٢. **حاجتان لا حاجة واحدة** (`Haja`): حاجةُ الحرف **تعلّقٌ** في معناه، وحاجةُ الضمير **تفسيرٌ** فقط
   (`harf_taalluq`، `damir_haja`) — فالحاجتان مختلفتان، والحاجةُ إلى المفسِّر لا تغيّر القسم أبدًا
   (`mufassir_la_yughayyir`).
٣. **الضميرُ اسمٌ جزئيّ** (`damir_ism`، `damir_ne_harf`، `damir_juzi`)، والشبهُ بالحرف لا يجعله حرفًا
   (`shabah_la_yuhawwil`).
٤. **الضميرُ من الـ116**: كلمةُ الضمير خاناتٌ كسائر الكلمات وترخيصُها ترخيصُ خاناتها (`damir_min_116`)،
   والقسمُ ليس في الخانات (`Tarkib.licence_blind_to_qism`).
٥. **الفرقُ يحمل الإسناد**: «هو قائم» إسنادٌ لأنّ الضمير اسم، ولو كان حرفًا لما كان (`damir_musnad_ilayh`).

ما لا يُبرهَن: أنّ هذه صفاتُ ألفاظٍ بأعيانها — الصفاتُ مدخلٌ يُروى (QAC، الكتاب، الشرح)، لا تقرؤه البوّابة
(`MUFRAD_SIFAT_ARE_INPUT`)؛ والإشارةُ والموصول لم يذكرهما نصُّ ج3 في قسمة الجزئيّ (`ISHARA_MAWSUL_NOT_IN_J3_DIVISION`).
-/

namespace A116.Mufrad

open A116 A116.Tarkib A116.NizamLine

/-- صفاتُ اللفظ المفرد في قسمة ج3. -/
structure Sifat where
  /-- يستقلّ بمعناه (لا يتعلّق معناه بمعنى لفظٍ آخر). -/
  istiqlal : Bool
  /-- يدلّ بهيئته على أحد الأزمنة الثلاثة. -/
  zamanHaya : Bool
  /-- يصحّ أن يشترك في مفهومه كثيرون. -/
  shirka : Bool
  /-- يفتقر إلى شيءٍ يفسّره. -/
  mufassir : Bool
  deriving DecidableEq, Repr

/-- **القسمة**: لا استقلال ← حرف؛ استقلالٌ بزمانٍ في الهيئة ← فعل؛ وإلّا اسم. -/
def qismOf (s : Sifat) : Qism :=
  if s.istiqlal then (if s.zamanHaya then .fil else .ism) else .harf

/-- أنواعُ الاسم: الكلّيّ، والجزئيّ نوعان: علمٌ وضمير. -/
inductive Ism where
  | kulli | alam | damir
  deriving DecidableEq, Repr

/-- نوعُ الاسم إن كان اسمًا. -/
def ismOf (s : Sifat) : Option Ism :=
  if qismOf s = .ism then
    some (if s.shirka then .kulli else if s.mufassir then .damir else .alam)
  else none

/-- الجزئيّ: علمٌ أو ضمير. -/
def juzi : Ism → Bool
  | .kulli => false
  | _ => true

/-- **الحاجتان**: تعلّقُ المعنى بلفظٍ آخر (الحرف)، والتفسير (الضمير). -/
inductive Haja where
  | taalluq | tafsir
  deriving DecidableEq, Repr

/-- حاجاتُ المفرد. -/
def haja (s : Sifat) : List Haja :=
  (if s.istiqlal then [] else [.taalluq]) ++ (if s.mufassir then [.tafsir] else [])

/-! ## ١. القسمة -/

theorem harf_iff (s : Sifat) : qismOf s = .harf ↔ s.istiqlal = false := by
  cases hi : s.istiqlal <;> cases hz : s.zamanHaya <;> simp [qismOf, hi, hz]

theorem ism_iff (s : Sifat) : qismOf s = .ism ↔ s.istiqlal = true ∧ s.zamanHaya = false := by
  cases hi : s.istiqlal <;> cases hz : s.zamanHaya <;> simp [qismOf, hi, hz]

/-! ## ٢. الحاجتان -/

/-- حاجةُ الحرف تعلّق. -/
theorem harf_taalluq (s : Sifat) (h : qismOf s = .harf) : Haja.taalluq ∈ haja s := by
  rw [harf_iff] at h
  simp [haja, h]

/-- **الحاجةُ إلى المفسِّر لا تغيّر القسم**: «إنّما هو يفتقر إلى التفسير فقط». -/
theorem mufassir_la_yughayyir (s : Sifat) (b : Bool) :
    qismOf { s with mufassir := b } = qismOf s := rfl

/-! ## ٣. الضمير -/

theorem damir_ism (s : Sifat) (h : ismOf s = some .damir) :
    qismOf s = .ism ∧ s.istiqlal = true := by
  unfold ismOf at h
  split at h
  · rename_i hq
    exact ⟨hq, ((ism_iff s).1 hq).1⟩
  · cases h

theorem damir_ne_harf (s : Sifat) (h : ismOf s = some .damir) : qismOf s ≠ .harf := by
  rw [(damir_ism s h).1]
  decide

/-- **حاجةُ الضمير التفسيرُ وحدَه** — لا تعلّق فيه. -/
theorem damir_haja (s : Sifat) (h : ismOf s = some .damir) : haja s = [.tafsir] := by
  have hi := (damir_ism s h).2
  unfold ismOf at h
  split at h
  · cases hs : s.shirka <;> cases hm : s.mufassir <;> simp_all [haja]
  · cases h

theorem damir_juzi (s : Sifat) (h : ismOf s = some .damir) : s.shirka = false := by
  unfold ismOf at h
  split at h
  · cases hs : s.shirka <;> simp_all
  · cases h

/-- **الشبهُ بالحرف لا يحوّل**: للضمير حاجة (بها شابه الحرف فبُني)، وقسمُه اسمٌ لا حرف. -/
theorem shabah_la_yuhawwil (s : Sifat) (h : ismOf s = some .damir) :
    haja s ≠ [] ∧ qismOf s ≠ .harf := by
  refine ⟨?_, damir_ne_harf s h⟩
  rw [damir_haja s h]
  simp

/-- الحاجتان لا تجتمعان في الضمير ولا تتّحدان. -/
theorem hajatan_mukhtalifatan : Haja.taalluq ≠ Haja.tafsir := by decide

/-! ## ٤. الضميرُ من الـ116 -/

/-- كلمةُ الضمير خاناتٌ من الشبكة، وترخيصُها ترخيصُ خاناتها لا غير. -/
theorem damir_min_116 (c : List Cell) (s : Sifat) :
    tarkibB [⟨c, qismOf s⟩] = strictLineB [c] := rfl

/-! ## ٥. الفرقُ يحمل الإسناد -/

/-- صفاتُ «هو»: مستقلٌّ بلا زمانٍ في الهيئة، لا شركة، يفتقر إلى مفسِّر. -/
def huwa : Sifat := ⟨true, false, false, true⟩
/-- «زيد» علمًا. -/
def zayd : Sifat := ⟨true, false, false, false⟩
/-- «الإنسان». -/
def insan : Sifat := ⟨true, false, true, false⟩
/-- «مِن»: لا يستقلّ بمعناه. -/
def min : Sifat := ⟨false, false, false, false⟩
/-- «قام». -/
def qama : Sifat := ⟨true, true, true, false⟩

theorem shawahid :
    ismOf huwa = some .damir ∧ ismOf zayd = some .alam ∧ ismOf insan = some .kulli ∧
    qismOf min = .harf ∧ qismOf qama = .fil ∧ haja huwa = [.tafsir] ∧ haja min = [.taalluq] := by
  decide

/-- **«هو قائم» إسنادٌ لأنّ الضمير اسم؛ ولو عُدّ حرفًا لما كان إسنادًا** — لأيّ خاناتٍ كانت. -/
theorem damir_musnad_ilayh (c d : List Cell) :
    Isnad [⟨c, qismOf huwa⟩, ⟨d, .ism⟩] ∧ ¬ Isnad [⟨c, .harf⟩, ⟨d, .ism⟩] := by
  refine ⟨Isnad.here _ _ [] (Or.inl ⟨rfl, rfl⟩), shibh_no_isnad _ _ rfl⟩

end A116.Mufrad
