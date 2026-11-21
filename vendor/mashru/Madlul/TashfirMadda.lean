/-
  Madlul/TashfirMadda.lean — جسرُ المعلومة المعمَّم: طيُّ وفكُّ Madlul.Jamad.Madda (معلومةٌ سابقةٌ حقيقيّة عن
  الجماد: الحقيقة وثلاثُ كثافاتٍ وعتبتا الذوب والغليان) بآلةٍ واحدة، لا حلولًا متفرّقة.

  السند: طلب المالك 2026-10-17 22:26 (ردًّا على «ما بقي باسمه» في جوابي عن المقترح ١ — جسر المعلومة/المفاهيم
  بالنمط المعمَّم): «ابدا بالجسر اعمل lean». البادئُ هنا بنيةُ معلوماتٍ سابقةٍ حقيقيّة (لا تعدادًا تافهًا):
  Madlul.Jamad.Madda، ستّةُ حقولٍ (الحقيقةُ، وثلاثُ كثافاتٍ اختياريّة، وعتبتا ذوبٍ وغليانٍ اختياريّتان من Int).

  **الأداة.** ليس هنا حاملٌ مقيَّدُ المدى كحوامل SLGE (مخرج/حامل/خانة محدودةٌ بعدد المخارج والحركات)؛ حقولُ Madda
  أعدادٌ طليقةٌ (كثافةُ الذهب تسعةَ عشرَ مليونًا، لا 116). فالآلةُ المعادُ استعمالُها هنا ليست حدودَ السلّم
  (carrierEnc/cellEnc/sylEnc) بل لبنتُها العامّةُ تحتها: `SLGE.mixEnc`/`SLGE.mixDec` نفسُها (SLGE/Core.lean،
  معلَنةٌ، لا مُعدَّلة)، بنصّها: `mixEnc B C o k₁ k₂ := (o*B+k₁)*C+k₂`، بلا قيدٍ على `o` وقيدٌ وحيدٌ `k₁<B ∧ k₂<C` —
  وهي ذاتُ الآلة التي قامت عليها cellEnc وsylEnc، مستعملةً هنا مباشرةً على حقول Madda بدل إعادة بنائها.
  السَّقفُ `BOUND` (= 2^32) تعيينٌ منّي لا نصٌّ من المالك ولا من مصدر: سَقفٌ عمليٌّ لحقول الكثافة والحرارة بعد
  تحويلها، تكفيه كثافةُ الذهب الموثَّقة (19,283,000 في Jamad.lean) بمراحل.

  **الصورة.** `optNatEnc`/`optNatDec`: Option Nat ↔ Nat بلا شرط (غياب↦0، حضورٌ n↦n+1). `zigzag`/`unzigzag`:
  Int ↔ Nat بلا شرط (الزوجُ لغير السالب، الفردُ للسالب). `optIntEnc`/`optIntDec`: تركيبُهما على Option Int بلا
  شرط. `maddaEnc`/`maddaDec`: الستّةُ حقولًا بثلاث طبقاتٍ من mixEnc (الحقيقةُ في الطبقة الأخيرة غيرُ مقيَّدة،
  والخمسةُ الباقيةُ مقيَّدةٌ بـBOUND بعد التحويل). والطيُّ هنا **غيرُ مشروطٍ على بنية Madda نفسِها** (بخلاف
  TashfirSullam حيث الحاملُ الخامّ يحتاج شرط صحّةٍ قبل الفكّ): شرطُ `Sahih` شرطٌ على **بقاء القيم تحت BOUND**
  لا على شكل Madda، وهو مستوفًى فعلًا في شواهد Jamad.lean الستّة كلِّها.

  ما يُبرهن هنا: جولاتُ الطيّ لكلّ محوّلٍ (optNat، zigzag، optInt) بلا شرط؛ وmadda_dec_enc على كامل Madda بشرط
  البقاء تحت BOUND، نقلًا مباشرًا لـ`SLGE.mixDec_enc` ثلاثَ مرّات؛ وTayy Madda Nat (Subtype على Sahih، كما فعلت
  TashfirSullam بـSahih السلّم)؛ وعلى الشاهد: الستّةُ موادّ المودَعة في Jamad.lean (ماء، حديد، ذهب، رصاص، زئبق،
  ملح) تحت BOUND فيطويها الطيُّ ويفكّها بعينها.

  مؤجَّلٌ: Madlul.Wiratha.Khawass (قابليّاتُها `qab : List QabHaraka` تحتاج ترميزَ قوائم لم يُبنَ هنا)، وكلُّ
  جداول المعلومات السابقة الأخرى (alaqat، hawass، awwaliyyat، azmina، makan، mirsat، isnad) — مهمّةٌ تالية.
-/
import SLGE.Core
import Aql.Mawsua
import Madlul.Jamad

set_option autoImplicit false

namespace Madlul.TashfirMadda

open Mawsua Madlul.Jamad

/-- غياب↦0، حضورٌ n↦n+1 — بلا شرط. -/
def optNatEnc : Option Nat → Nat
  | none => 0
  | some n => n + 1

def optNatDec : Nat → Option Nat
  | 0 => none
  | n + 1 => some n

theorem optNat_dec_enc (x : Option Nat) : optNatDec (optNatEnc x) = x := by
  cases x <;> rfl

/-- زِكزاكُ الصحيح على مُنشِئَي Int نفسِهما (ofNat/negSucc) — بلا شرط، على كلّ Int. -/
def zigzag : Int → Nat
  | .ofNat n => 2 * n
  | .negSucc n => 2 * n + 1

def unzigzag (k : Nat) : Int :=
  if k % 2 = 0 then Int.ofNat (k / 2) else Int.negSucc (k / 2)

theorem zigzag_unzigzag (z : Int) : unzigzag (zigzag z) = z := by
  cases z with
  | ofNat n =>
    have h1 : (2 * n) % 2 = 0 := by omega
    have h2 : (2 * n) / 2 = n := by omega
    simp only [zigzag, unzigzag, h1, h2, ite_true]
  | negSucc n =>
    have h1 : (2 * n + 1) % 2 = 1 := by omega
    have h2 : (2 * n + 1) / 2 = n := by omega
    simp only [zigzag, unzigzag, h1, h2]
    omega

/-- Option Int ↔ Nat، بتركيب الزِّكزاك مع محوّل Option — بلا شرط. -/
def optIntEnc : Option Int → Nat
  | none => 0
  | some z => zigzag z + 1

def optIntDec : Nat → Option Int
  | 0 => none
  | n + 1 => some (unzigzag n)

theorem optInt_dec_enc (x : Option Int) : optIntDec (optIntEnc x) = x := by
  cases x with
  | none => rfl
  | some z => simp [optIntEnc, optIntDec, zigzag_unzigzag]

/-- السَّقفُ العمليّ (تعيينٌ منّي): يكفي كثافةَ الذهب الموثَّقة (19,283,000) بمراحل. -/
def BOUND : Nat := 2 ^ 32

theorem bound_pos : 0 < BOUND := by decide

/-- شرطُ صحّة الترميز (لا على بنية Madda): الحقولُ الخمسةُ بعد التحويل تحت BOUND. -/
def Sahih (m : Madda) : Prop :=
  optNatEnc m.kJamid < BOUND ∧ optNatEnc m.kSail < BOUND ∧ optNatEnc m.kBukhar < BOUND ∧
  optIntEnc m.dhawb < BOUND ∧ optIntEnc m.ghalayan < BOUND

/-- الطيُّ: ثلاثُ طبقاتٍ من `SLGE.mixEnc`، الحقيقةُ في الأعمق (غيرُ مقيَّدة). -/
def maddaEnc (m : Madda) : Nat :=
  let l1 := SLGE.mixEnc BOUND BOUND m.haqiqa (optNatEnc m.kJamid) (optNatEnc m.kSail)
  let l2 := SLGE.mixEnc BOUND BOUND l1 (optNatEnc m.kBukhar) (optIntEnc m.dhawb)
  SLGE.mixEnc BOUND BOUND l2 (optIntEnc m.ghalayan) 0

/-- الفكّ: عكسُ الطيّ طبقةً طبقة بـ `SLGE.mixDec`. -/
def maddaDec (n : Nat) : Madda :=
  match SLGE.mixDec BOUND BOUND n with
  | (l2, ghalayan', _) =>
    match SLGE.mixDec BOUND BOUND l2 with
    | (l1, kBukhar', dhawb') =>
      match SLGE.mixDec BOUND BOUND l1 with
      | (haqiqa', kJamid', kSail') =>
        { haqiqa := haqiqa', kJamid := optNatDec kJamid', kSail := optNatDec kSail',
          kBukhar := optNatDec kBukhar', dhawb := optIntDec dhawb', ghalayan := optIntDec ghalayan' }

/-- **الفكُّ يعيد الأصل** تحت شرط الصحّة — نقلٌ مباشرٌ لـ `SLGE.mixDec_enc` ثلاثَ مرّات. -/
theorem madda_dec_enc (m : Madda) (h : Sahih m) : maddaDec (maddaEnc m) = m := by
  obtain ⟨h1, h2, h3, h4, h5⟩ := h
  simp only [maddaDec, maddaEnc,
    SLGE.mixDec_enc BOUND BOUND _ (optIntEnc m.ghalayan) 0 h5 bound_pos,
    SLGE.mixDec_enc BOUND BOUND _ (optNatEnc m.kBukhar) (optIntEnc m.dhawb) h3 h4,
    SLGE.mixDec_enc BOUND BOUND m.haqiqa (optNatEnc m.kJamid) (optNatEnc m.kSail) h1 h2,
    optNat_dec_enc, optInt_dec_enc]

/-- الطيُّ على الحامل المقيَّد بـ`Sahih` (Subtype)، على نمط TashfirSullam.SlgeUnit بعينه. -/
def MaddaUnit : Type := {m : Madda // Sahih m}

noncomputable def fakkOf (code : Nat) : Option MaddaUnit :=
  @dite (Option MaddaUnit) (Sahih (maddaDec code)) (Classical.propDecidable _)
    (fun h => some ⟨maddaDec code, h⟩) (fun _ => none)

theorem fakkOf_tawiOf (u : MaddaUnit) : fakkOf (maddaEnc u.1) = some u := by
  obtain ⟨m, hm⟩ := u
  show fakkOf (maddaEnc m) = some ⟨m, hm⟩
  have heq : maddaDec (maddaEnc m) = m := madda_dec_enc m hm
  unfold fakkOf
  rw [heq, dite_eq_left hm]

noncomputable def tayyMadda : Tayy MaddaUnit Nat where
  tawi := fun u => maddaEnc u.1
  fakk := fakkOf
  fakk_tawi := fakkOf_tawiOf

theorem tayyMadda_la_yudi (u : MaddaUnit) : tayyMadda.fakk (tayyMadda.tawi u) = some u :=
  tayyMadda.fakk_tawi u

/-! ## على الشاهد: الموادّ الستّ المودَعة في Jamad.lean -/

theorem shawahid_sahih :
    Sahih ma ∧ Sahih hadid ∧ Sahih dhahab ∧ Sahih rasas ∧ Sahih zibaq ∧ Sahih milh := by
  unfold Sahih optNatEnc optIntEnc zigzag ma hadid dhahab rasas zibaq milh BOUND
  decide

theorem madda_shawahid_tudi :
    maddaDec (maddaEnc ma) = ma ∧ maddaDec (maddaEnc hadid) = hadid ∧
    maddaDec (maddaEnc dhahab) = dhahab ∧ maddaDec (maddaEnc rasas) = rasas ∧
    maddaDec (maddaEnc zibaq) = zibaq ∧ maddaDec (maddaEnc milh) = milh := by
  obtain ⟨s1, s2, s3, s4, s5, s6⟩ := shawahid_sahih
  exact ⟨madda_dec_enc ma s1, madda_dec_enc hadid s2, madda_dec_enc dhahab s3,
    madda_dec_enc rasas s4, madda_dec_enc zibaq s5, madda_dec_enc milh s6⟩

end Madlul.TashfirMadda
