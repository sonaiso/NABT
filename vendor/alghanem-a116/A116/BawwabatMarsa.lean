import A116.Bawwabat
import A116.Istiqama
import A116.Ihala

/-!
# البوّاباتُ على مرساتَي «الآن» و«هنا» (ADR ٩١، أمرُ المالك 2026-10-17)

نصُّ المالك: «الربط مع (الآن) والربط مع (هنا) مع ADR ٩٠».

## السند (الأسطرُ 1-based)

شرحُ ابن عقيل المختوم:
* س6470: «والفاء للترتيب باتصال ... وثم للترتيب بانفصال».
* س6471–6472: «تدلّ الفاء على تأخّر المعطوف عن المعطوف عليه متّصلًا به، وثمّ على تأخّره عنه منفصلًا أي متراخيًا عنه».
* س1019–1020: «يُشار إلى المكان القريب بهنا… ويُشار إلى البعيد على رأي المصنّف بهناك وهنالك».
* س1314: «الآن بمعنى هذا الوقت».

الشخصيّة ج3 المختومة، س373: ما يدلّ على الزمان «بذاته كالصبوح، والغبوق، وأمس، والآن، وغداً».

## ما يُبنى

في ADR ٩٠ كانت رتبةُ الفاء وثمّ مُدخَلًا (`RUTBA_IS_INPUT`). وهنا تُحسب من موضعَي الحدثين في إطارٍ واحد، بنسبة
`Malumat.nisba` (ADR ٨٧):
* **الآن**: الفاءُ صادقةُ الرتبة ⟺ الثاني بعد الأوّل ومسافتُه لا تجاوز حدَّ الاتّصال، وثمّ ⟺ بعده ومسافتُه تجاوزه.
  والمعُ والعكسُ كذبٌ فيهما، والواو لا تقرأ الرتبة. ولا رتبةَ بلا موضعين، ولا بين إطارين: «لا حكم» لا كذب.
* **هنا**: «هذا»/«هنا» صادقٌ ⟺ المشارُ إليه قريبٌ من المتكلّم في إطار «هنا»، و«ذلك»/«هناك» ⟺ بعيد. والقربُ والبعدُ
  بالكاف (`Ihala.rutbaIshara`)، فقانونُ «هنا/هناك/هنالك» هو قانونُ «ذا/ذاك/ذلك» بعينه. ولا قربَ في إطار «الآن».

وكلاهما لا يتغيّر بنقل المرساة: الحكمُ لا يحتاج إحداثيًّا من العالم.

وما لا يُبرهَن: مقدارُ حدّ الاتّصال وحدّ القرب. هما مُدخَلان مسمّيان (`ITTISAL_HADD_IS_INPUT`، `QURB_HADD_IS_INPUT`).
-/

namespace A116.BawwabatMarsa

open A116.Atf A116.Bawwabat A116.Malumat

/-! ## الآن: رتبةُ الفاء وثمّ من النسبة -/

/-- رتبةُ الأداة من موضعَي الحدثين. `ittisal` حدُّ الاتّصال. لا رتبةَ بلا موضعين في إطارٍ واحد. -/
def rutba (h : Harf) (ittisal : Nat) : Option Mawqi → Option Mawqi → Q
  | some a, some c =>
    match nisba a c with
    | none => none
    | some .qabl =>
      match h with
      | .fa => some (decide (c.qadr - a.qadr ≤ (ittisal : Int)))
      | .thumma => some (decide ((ittisal : Int) < c.qadr - a.qadr))
      | _ => none
    | some _ =>
      match h with
      | .fa | .thumma => some false
      | _ => none
  | _, _ => none

/-- البوّابةُ على المرساة: عملُ ADR ٩٠ برتبةٍ محسوبة. -/
def amalM (b : Bawwaba) (ittisal : Nat) (a c : Q) (pa pc : Option Mawqi) : Natija :=
  amal b a c (rutba b.harf ittisal pa pc)

/-- **نقلُ «الآن» لا يغيّر الرتبة.** -/
theorem rutba_shift (h : Harf) (it : Nat) (i : Itar) (a c k : Int) :
    rutba h it (some ⟨i, a + k⟩) (some ⟨i, c + k⟩) = rutba h it (some ⟨i, a⟩) (some ⟨i, c⟩) := by
  have e : c + k - (a + k) = c - a := by omega
  simp only [rutba, nisba_shift, e]

/-- **لا رتبةَ بين إطارين**: الهجريُّ والميلاديّ، أو «الآن» و«هنا». -/
theorem rutba_itarayn (h : Harf) (it : Nat) (a c : Mawqi) (hne : a.itar ≠ c.itar) :
    rutba h it (some a) (some c) = none := by
  simp [rutba, la_nisba_bayna_itarayn a c hne]

/-- **ولا رتبةَ بلا موضع**: الغيابُ «لا حكم». -/
theorem rutba_ghiyab (h : Harf) (it : Nat) (p : Option Mawqi) :
    rutba h it none p = none ∧ rutba h it p none = none := by
  cases p <;> simp [rutba]

/-- **الفاءُ وثمّ لا تصدقان معًا** على حدثين واحدين: الاتّصالُ والانفصالُ متقابلان. -/
theorem fa_thumma_la_yajtamian (it : Nat) (pa pc : Option Mawqi) :
    ¬ (rutba .fa it pa pc = some true ∧ rutba .thumma it pa pc = some true) := by
  rintro ⟨h1, h2⟩
  rcases pa with _ | a <;> rcases pc with _ | c
  · simp [rutba] at h1
  · simp [rutba] at h1
  · simp [rutba] at h1
  · simp only [rutba] at h1 h2
    cases hn : nisba a c with
    | none => simp [hn] at h1
    | some r =>
      cases r with
      | qabl =>
        simp only [hn, Option.some.injEq, decide_eq_true_eq] at h1 h2
        omega
      | maa => simp [hn] at h1
      | bad => simp [hn] at h1

/-- الشاهدُ لكلّ «آن»: «جاء زيدٌ أمسِ فعمرٌو اليومَ» صادقُ الرتبة، و«ثمّ» كاذبتُها بحدّ اتّصالٍ يومًا. -/
theorem ams_yawm (n : Int) :
    rutba .fa 1 (some ⟨.alAn, -1 + n⟩) (some ⟨.alAn, 0 + n⟩) = some true ∧
    rutba .thumma 1 (some ⟨.alAn, -1 + n⟩) (some ⟨.alAn, 0 + n⟩) = some false := by
  rw [rutba_shift, rutba_shift]; decide

/-- والعكسُ كاذب: «جاء زيدٌ اليومَ فعمرٌو أمسِ». -/
theorem yawm_ams (n : Int) :
    rutba .fa 1 (some ⟨.alAn, 0 + n⟩) (some ⟨.alAn, -1 + n⟩) = some false := by
  rw [rutba_shift]; decide

/-- «ثمّ» مع التراخي: «خرج زيدٌ أمسِ ثمّ عمرٌو غدًا» صادقةُ الرتبة، والفاءُ كاذبتُها. -/
theorem ams_ghad (n : Int) :
    rutba .thumma 1 (some ⟨.alAn, -1 + n⟩) (some ⟨.alAn, 1 + n⟩) = some true ∧
    rutba .fa 1 (some ⟨.alAn, -1 + n⟩) (some ⟨.alAn, 1 + n⟩) = some false := by
  rw [rutba_shift, rutba_shift]; decide

/-- **الواو لمطلق الجمع** (س6458): حدثان معًا صادقان بالواو، والفاءُ كاذبةٌ بهما. -/
theorem wa_maa_fa_kadhib (n : Int) (it : Nat) :
    amalM ⟨.wa, .ithbat, true⟩ it (some true) (some true)
        (some ⟨.alAn, n⟩) (some ⟨.alAn, n⟩) = .qima (some true) ∧
    amalM ⟨.fa, .ithbat, true⟩ it (some true) (some true)
        (some ⟨.alAn, n⟩) (some ⟨.alAn, n⟩) = .qima (some false) := by
  simp [amalM, amal, rutba, nisba, cmpInt, shartSiyaq, wa]

/-- **الهجريُّ والميلاديُّ في الفاء**: طرفان صادقان، والواو تصدق، والفاءُ «لا حكم» بلا مقابلةٍ مسمّاة. -/
theorem fa_hijri_miladi (a c : Int) (it : Nat) :
    amalM ⟨.wa, .ithbat, true⟩ it (some true) (some true)
        (some ⟨.istilah "الهجري", a⟩) (some ⟨.istilah "الميلادي", c⟩) = .qima (some true) ∧
    amalM ⟨.fa, .ithbat, true⟩ it (some true) (some true)
        (some ⟨.istilah "الهجري", a⟩) (some ⟨.istilah "الميلادي", c⟩) = .qima none := by
  refine ⟨rfl, ?_⟩
  simp only [amalM]
  rw [rutba_itarayn _ _ _ _ (by simp)]
  rfl

/-- و«الآن» و«هنا» لا يتقابلان: لا رتبةَ للفاء بين زمانٍ ومكان. -/
theorem fa_alAn_huna (a c : Int) (it : Nat) :
    amalM ⟨.fa, .ithbat, true⟩ it (some true) (some true)
        (some ⟨.alAn, a⟩) (some ⟨.huna, c⟩) = .qima none := by
  simp only [amalM]
  rw [rutba_itarayn _ _ _ _ (by simp)]
  rfl

/-- الكذبُ يغلب وإن غابت الرتبة: طرفٌ كاذبٌ يكذّب الفاءَ بلا موضع. -/
theorem fa_kadhib_bila_mawqi (it : Nat) (c : Q) :
    amalM ⟨.fa, .ithbat, true⟩ it (some false) c none none = .qima (some false) := by
  cases c with
  | none => rfl
  | some x => cases x <;> rfl

/-! ## هنا: الإشارةُ بالقرب والبعد -/

/-- القربُ في إطار «هنا»: المشارُ إليه من المتكلّم دون حدّ القرب. ولا قربَ في غيره. -/
def qarib (hadd : Nat) (mutakallim mushar : Mawqi) : Q :=
  if mutakallim.itar = .huna ∧ mushar.itar = .huna then
    some (decide ((mushar.qadr - mutakallim.qadr).natAbs ≤ hadd))
  else none

/-- صدقُ الإشارة: صيغةٌ صحيحة، ورتبتُها بالكاف توافق القربَ المحسوب. -/
def ishara (s : Ihala.Sigha) (hadd : Nat) : Option Mawqi → Option Mawqi → Q
  | some u, some m =>
    if Ihala.sahiha s then
      (qarib hadd u m).map (fun q => q == (Ihala.rutbaIshara s == .qurb))
    else none
  | _, _ => none

/-- صيغُ المكان (س1017–1020): «هنا» و«ههنا» للقريب، و«هناك» و«هنالك» للبعيد، بخانات «ذا» بعينها. -/
def huna : Ihala.Sigha := ⟨false, false, false⟩
def hahuna : Ihala.Sigha := ⟨true, false, false⟩
def hunaka : Ihala.Sigha := ⟨false, true, false⟩
def hunalika : Ihala.Sigha := ⟨false, true, true⟩

/-- **قانونُ «هنا» قانونُ «ذا»**: الكافُ للبعد في المكان كما في المشار إليه. -/
theorem huna_ka_dha :
    Ihala.rutbaIshara huna = .qurb ∧ Ihala.rutbaIshara hahuna = .qurb ∧
    Ihala.rutbaIshara hunaka = .bud ∧ Ihala.rutbaIshara hunalika = .bud ∧
    huna = Ihala.dha ∧ hahuna = Ihala.hadha ∧ hunaka = Ihala.dhaka ∧ hunalika = Ihala.dhalika := by
  decide

/-- **نقلُ «هنا» لا يغيّر الإشارة**: المتكلّمُ والمشارُ إليه إذا انتقلا معًا. -/
theorem ishara_shift (s : Ihala.Sigha) (hadd : Nat) (u m k : Int) :
    ishara s hadd (some ⟨.huna, u + k⟩) (some ⟨.huna, m + k⟩) =
      ishara s hadd (some ⟨.huna, u⟩) (some ⟨.huna, m⟩) := by
  have e : m + k - (u + k) = m - u := by omega
  simp only [ishara, qarib, e]

/-- **لا إشارةَ مكانيّةً في إطار «الآن»**: القربُ موضعُ مكانٍ لا وقت. -/
theorem ishara_alAn (s : Ihala.Sigha) (hadd : Nat) (u m : Int) :
    ishara s hadd (some ⟨.huna, u⟩) (some ⟨.alAn, m⟩) = none := by
  simp [ishara, qarib]

/-- الشاهد: المشارُ إليه في موضع المتكلّم، «هذا» صادقٌ و«ذلك» كاذب؛ وعلى عشرةٍ بحدّ قربٍ واحد العكس؛ و«هذالك» لا حكم. -/
theorem shawahid_huna (u : Int) :
    ishara Ihala.hadha 1 (some ⟨.huna, 0 + u⟩) (some ⟨.huna, 0 + u⟩) = some true ∧
    ishara Ihala.dhalika 1 (some ⟨.huna, 0 + u⟩) (some ⟨.huna, 0 + u⟩) = some false ∧
    ishara hunalika 1 (some ⟨.huna, 0 + u⟩) (some ⟨.huna, 10 + u⟩) = some true ∧
    ishara huna 1 (some ⟨.huna, 0 + u⟩) (some ⟨.huna, 10 + u⟩) = some false ∧
    ishara Ihala.hadhalika 1 (some ⟨.huna, 0 + u⟩) (some ⟨.huna, 0 + u⟩) = none := by
  simp only [ishara_shift]; decide

/-- الجمعُ على «هنا»: «هذا زيدٌ وذلك عمرٌو» وزيدٌ قريبٌ وعمرٌو بعيد — صادق؛ وإن قلبتَ المواضعَ كاذب. -/
theorem murakkab_huna :
    amal ⟨.wa, .ithbat, true⟩
      (ishara Ihala.hadha 1 (some ⟨.huna, 0⟩) (some ⟨.huna, 0⟩))
      (ishara Ihala.dhalika 1 (some ⟨.huna, 0⟩) (some ⟨.huna, 10⟩)) none = .qima (some true) ∧
    amal ⟨.wa, .ithbat, true⟩
      (ishara Ihala.hadha 1 (some ⟨.huna, 0⟩) (some ⟨.huna, 10⟩))
      (ishara Ihala.dhalika 1 (some ⟨.huna, 0⟩) (some ⟨.huna, 0⟩)) none = .qima (some false) := by
  decide

/-! ## المراسي -/

/-- (النصّ، السطر 1-based، النصّ بعينه). -/
def marasi : List (String × Nat × String) :=
  [("sharh", 6470, "والفاء للترتيب باتصال ... وثم للترتيب بانفصال"),
   ("sharh", 6471, "تدل الفاء على تأخر المعطوف عن المعطوف عليه متصلا به وثم على تأخره"),
   ("sharh", 6472, "عنه منفصلا أي متراخيا عنه"),
   ("sharh", 1019, "يشار إلى المكان القريب بهنا"),
   ("sharh", 1020, "البعيد على رأى المصنف بهناك وهنالك"),
   ("sharh", 1314, "الآن بمعنى هذا الوقت"),
   ("j3", 373, "وأمس، والآن، وغداً")]

end A116.BawwabatMarsa
