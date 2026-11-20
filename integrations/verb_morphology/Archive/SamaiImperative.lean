/-
  SamaiImperative.lean — هل تفكّ قوانينُ الابتداء والوصل والوقف جدولَ السماعيّ؟
  حالة الاختبار: أمر الثلاثيّ المجرّد مهموز الفاء (خُذْ، كُلْ، مُرْ في مقابل ائْتِ، ائْذَنْ).
  Lean 4 core (v4.15.0)، بلا Mathlib، بلا sorry، بلا axiom.

  الجدول أدناه مولَّد بسكربت (impv1.py) من مودَع QAC
  (github mustafa0x/quran-morphology)، ولم يُكتب باليد:
    أخذ  ابتداء: الهمزة محذوفة ×11 (خُذُوا 2:63) | وصل بعد و/ف: محذوفة ×11 (فَخُذْ 2:260)
    أكل  ابتداء: محذوفة ×16 (كُلُوا 2:57)        | وصل: محذوفة ×16 (وَكُلَا 2:35)
    أذن  ابتداء: ثابتة ×1 (ائْذَن 9:49)          | وصل: ثابتة ×2 (فَأْذَنُوا 2:279)
    أتى  ابتداء: ثابتة ×14 (ائْتِنَا 6:71)        | وصل: ثابتة ×23 (فَأْتُوا 2:23)
    أمر  وصل: ثابتة ×4 (وَأْمُرْ 7:145)           | ابتداء: لا ورود في المصحف
    أوى  وصل: ثابتة ×1 (فَأْوُوا 18:16)           | ابتداء: لا ورود
  عين المضارع من المودَع نفسه: يَأْخُذُ، يَأْكُلُ، يَأْمُرُ = ضمّ؛ يَأْذَنَ = فتح؛ يَأْتِي، آوِي = كسر.
-/
namespace Ghanem.Samai

inductive Ctx | ibtida | wasl
  deriving DecidableEq, Repr

/-- حركة عين المضارع = حركة همزة الوصل في الابتداء (ضمّ مع الضمّ، وكسر مع غيره). -/
inductive VClass | a | i | u
  deriving DecidableEq, Repr

inductive Root | akhadha | akala | adhina | ata | amara | awa
  deriving DecidableEq, Repr

structure Case where
  root    : Root
  cls     : VClass
  ctx     : Ctx
  dropped : Bool   -- حُذفت الهمزة الأصلية في الأمر؟
  deriving DecidableEq, Repr

open Root VClass Ctx in
def quranTable : List Case :=
  [ ⟨akhadha, u, ibtida, true⟩,  ⟨akhadha, u, wasl, true⟩,
    ⟨akala,   u, ibtida, true⟩,  ⟨akala,   u, wasl, true⟩,
    ⟨adhina,  a, ibtida, false⟩, ⟨adhina,  a, wasl, false⟩,
    ⟨ata,     i, ibtida, false⟩, ⟨ata,     i, wasl, false⟩,
    ⟨amara,   u, wasl,   false⟩,
    ⟨awa,     i, wasl,   false⟩ ]

/-! ### ١. قانون الابتداء يفكّ الابتداء كلّه
    في الابتداء يلتقي «همزة وصل + همزة ساكنة»؛ والحذف يقع إذا كانت حركة الوصل ضمًّا. -/

def ibtidaLaw (c : Case) : Bool := c.cls == .u

theorem ibtida_decoded :
    ∀ c ∈ quranTable, c.ctx = .ibtida → ibtidaLaw c = c.dropped := by decide +kernel

/-! ### ٢. لا دالّة في (الحركة، الموضع) وحدهما تفكّ الجدول كلّه
    أخذ وأمر: كلاهما ضمّ، كلاهما في الوصل، وحكمهما مختلف. -/

theorem no_law_of_class_ctx :
    ¬ ∃ f : VClass → Ctx → Bool, ∀ c ∈ quranTable, f c.cls c.ctx = c.dropped := by
  intro ⟨f, hf⟩
  have h1 := hf ⟨.akhadha, .u, .wasl, true⟩  (by decide)
  have h2 := hf ⟨.amara,   .u, .wasl, false⟩ (by decide)
  simp at h1 h2
  rw [h1] at h2
  exact Bool.noConfusion h2

/-! ### ٣. الدالّة الدنيا: قانون الابتداء + بتٌّ معجميّ واحد
    البتّ: «هل عمّ الحذفُ الوصلَ أيضًا؟» — يُطلب لجذور الضمّ وحدها. -/

def extendsToWasl : Root → Bool
  | .akhadha => true
  | .akala   => true
  | _        => false

def decode (c : Case) : Bool :=
  match c.ctx with
  | .ibtida => c.cls == .u
  | .wasl   => c.cls == .u && extendsToWasl c.root

theorem table_decoded : ∀ c ∈ quranTable, decode c = c.dropped := by decide +kernel

/-- البتّ المعجميّ لا يُستعمل خارج جذور الضمّ: تغييره لجذر غير ضمّيّ لا يغيّر المخرج. -/
theorem lexical_bit_only_for_u (c : Case) (h : c.cls ≠ .u) : decode c = false := by
  cases c with
  | mk r cl cx d =>
    cases cl <;> cases cx <;> simp_all [decode]

/-! ### ٤. الصحيحان (Open-Hadith-Data، النسخة المشكولة؛ samai_hadith2.py)
  بصمتا الملفّين (sha256، أوّل 16): البخاري b03f661876fc4089، مسلم 79232c8d7c27fef1.
  عددٌ بمطابقة الكلمة كاملة، مع إخراج الاقتباسات القرآنية (وَأْمُرْ ×3 = 7:199):
    أخذ  ابتداء: محذوفة ×94 (خُذْ، خُذُوا)     | وصل: محذوفة ×51 (فَخُذْ)       | ثابتة: ٠
    أكل  ابتداء: محذوفة ×55 (كُلُوا، كُلْ)     | وصل: محذوفة ×83 (فَكُلْ، وَكُلُوا) | ثابتة: ٠
    أمر  ابتداء: محذوفة ×60 (مُرُوا، مُرْهُ، مُرْ) | ثابتة ×1 (B2929 «فَقَالَ أْمُرْ»: مكتوبة بلا ألف وصل
         ⇒ مقروءة دَرْجًا بما قبلها، فهي وصلٌ عبر الكلمة لا ابتداء؛ نُقلت إلى الوصل وبُيِّن سببه)
    أمر  وصل: محذوفة ×30 (فَمُرْنَا، فَمُرْ، وَمُرُوهُمْ) | ثابتة ×1 (M3336 فَأْمُرْهُ) + B2929
  النتيجة: مُرْ في الابتداء ثابتٌ في الحديث، فقانون الابتداء يصمد على مودَعٍ ثانٍ؛
  لكنّ «بتّ الوصل» لأمر ليس ثابتًا معجميًّا: المصحف يُثبت (٤/٤) والحديث يحذف غالبًا (٣٠/٣٢). -/

open Root VClass Ctx in
def hadithTable : List Case :=
  [ ⟨akhadha, u, ibtida, true⟩, ⟨akhadha, u, wasl, true⟩,
    ⟨akala,   u, ibtida, true⟩, ⟨akala,   u, wasl, true⟩,
    ⟨amara,   u, ibtida, true⟩,
    ⟨amara,   u, wasl,   true⟩, ⟨amara,   u, wasl, false⟩ ]

/-- قانون الابتداء يصمد على الحديث أيضًا. -/
theorem ibtida_decoded_hadith :
    ∀ c ∈ hadithTable, c.ctx = .ibtida → ibtidaLaw c = c.dropped := by decide +kernel

/-- لا دالّةَ أحاديّةَ القيمة في (الجذر، الحركة، الموضع) تفكّ المودَعين معًا:
    أمر/ضمّ/وصل ثابتةٌ في المصحف ومحذوفةٌ في الحديث. -/
theorem no_function_both_corpora :
    ¬ ∃ f : Root → VClass → Ctx → Bool,
      ∀ c ∈ quranTable ++ hadithTable, f c.root c.cls c.ctx = c.dropped := by
  intro ⟨f, hf⟩
  have h1 := hf ⟨.amara, .u, .wasl, false⟩ (by decide)
  have h2 := hf ⟨.amara, .u, .wasl, true⟩  (by decide)
  simp at h1 h2
  rw [h1] at h2
  exact Bool.noConfusion h2

/-- الفكّ الصحيح علاقةٌ مرخِّصة لا دالّة: يُعطي مجموعة المخارج الجائزة.
    كلّها مفردة إلا (أمر، وصل) = {حذف، إثبات}: ترخيصان يُرتَّبان ولا يُحذف أحدهما. -/
def licensed (c : Case) : List Bool :=
  match c.ctx with
  | .ibtida => [c.cls == .u]
  | .wasl   =>
    if c.cls != .u then [false]
    else match c.root with
      | .akhadha => [true]
      | .akala   => [true]
      | .amara   => [true, false]
      | _        => [false]

theorem both_corpora_licensed :
    ∀ c ∈ quranTable ++ hadithTable, c.dropped ∈ licensed c := by decide +kernel

/-- التعدّد محصورٌ في خانة واحدة: كلّ ما سوى (أمر، وصل) مخرجه وحيد. -/
theorem variation_only_amara_wasl (c : Case)
    (h : ¬ (c.root = .amara ∧ c.ctx = .wasl)) : (licensed c).length = 1 := by
  cases c with
  | mk r cl cx d =>
    cases cx <;> cases cl <;> cases r <;> simp_all [licensed]

end Ghanem.Samai

#print axioms Ghanem.Samai.ibtida_decoded_hadith
#print axioms Ghanem.Samai.no_function_both_corpora
#print axioms Ghanem.Samai.both_corpora_licensed
#print axioms Ghanem.Samai.variation_only_amara_wasl
#print axioms Ghanem.Samai.ibtida_decoded
#print axioms Ghanem.Samai.no_law_of_class_ctx
#print axioms Ghanem.Samai.table_decoded
#print axioms Ghanem.Samai.lexical_bit_only_for_u
