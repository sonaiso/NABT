/-
  Aql/Idaa.lean — بوّابة الإيداع: ما يدخل الموسوعة من كتابٍ مرفوع، وبأيّ وسمٍ، وعلى أيّ سند.

  السند:
  * الدستور م2: «مبرهن» لمبرهنة Lean باسمها وحدها.
  * الدستور م9: لا ختم مودَع جديد إلّا بإذن المالك.
  * الدستور م12: لا مودَع بلا نوع (واقعٌ مختوم، وضع، معلومات سابقة، مرجع محجوب).
  * الدستور م17: Lean يبرهن خواصّ المرويّ المودَع، لا اللغة.
  * ج3 729: طريق معرفة اللغة الرواية الصحيحة، تواترًا أو آحادًا، «ولا طريق غيرهما».
    - المتواتر قاطع «لا يقبل التشكيك».
    - الآحاد «طريق تحصيل الظنّ به»، كالمرويّ عن الخليل والأصمعي.
    - «وأمّا العقل فلا ينفع في معرفة اللغة».

  ما يُبرهن:
  ١. لا يُنتج مودَعٌ، أيًّا كان نوعه، أصلًا موسومًا «مبرهن» أو «مبرهن على الشاهد».
  ٢. للأصل من المودَع وجهان لا يختلطان:
     - الحكاية («المودَع يقول كذا في موضع كذا») تطابَق على النصّ المختوم؛
     - المضمون («اللفظ موضوع لكذا») مرتبته من درجة الخبر: الآحاد ظنّيّ، والمتواتر قطعيّ.
  ٣. «التنظيف» الذي يجمع صورتين مختلفتين في صورة واحدة ليس طيًّا معتبرًا (شاهده التطويل).
  ٤. الأصل لا يُقبل إلّا إن كان سنده يبدأ ببصمة مودَعٍ مسجَّل غيرِ فارغة.
  بلا sorry ولا axiom ولا native_decide.
-/
import Aql.Aqliyya
import Aql.Mawsua

namespace Idaa

open Mawsua

/-! ## ١. نوع المودَع وسقف وسمه -/

/-- أنواع المودَع (الدستور م12). -/
inductive Naw | waqiMakhtum | wad | maalumatSabiqa | marjaMahjub
deriving DecidableEq, Repr

/-- سقف وسم الحكاية عن المودَع: أعلاه «مطابق» (موضعٌ في نصٍّ مختوم)؛ فالبرهان لا يأتي من كتاب. -/
def sakf : Naw → Wasm
  | .waqiMakhtum | .wad | .maalumatSabiqa => .mutabaq
  | .marjaMahjub => .maqis

def qaydMudaa (n : Naw) (w : Wasm) : Wasm :=
  if w.quwwa ≤ (sakf n).quwwa then w else sakf n

theorem qaydMudaa_la_yarfa (n : Naw) (w : Wasm) : (qaydMudaa n w).quwwa ≤ w.quwwa := by
  cases n <;> cases w <;> decide

/-- لا مودَع يُنتج «مبرهن» ولا «مبرهن على الشاهد»، مهما أعلن المُدخِل (الدستور م2). -/
theorem la_burhan_min_mudaa (n : Naw) (w : Wasm) :
    (qaydMudaa n w).quwwa < Wasm.mubarhanShahid.quwwa := by
  cases n <;> cases w <;> decide

/-! ## ٢. الحكاية والمضمون (ج3 729) -/

/-- درجة الخبر عن الوضع. -/
inductive Daraja | mutawatir | ahad deriving DecidableEq, Repr

/-- وجها الأصل اللغويّ: ما يحكيه المودَع، وما يتضمّنه من حكمٍ على الوضع. -/
inductive Wajh | hikaya | madmun deriving DecidableEq, Repr

/-- مرتبة المضمون من درجة خبره: المتواتر قاطع، والآحاد ظنّيّ. -/
def martabaMadmun : Daraja → Aql.Martaba
  | .mutawatir => .qati
  | .ahad => .zanni

/-- المرويّ عن واحدٍ كالخليل أو الأصمعي ظنّيّ المضمون، ولو صحّت حكايته (ج3 729). -/
theorem ahad_zanni : martabaMadmun .ahad = .zanni := rfl

/-- فلا يصحّ «كلّ أصلٍ لغويّ قطعيّ»: للمضمون اللغويّ مرتبتان بحسب الخبر. -/
theorem laysa_kull_lughawi_qati : ¬ ∀ d : Daraja, martabaMadmun d = .qati := by
  intro h
  exact absurd (h .ahad) (by decide)

/-! ## ٣. لا «تنظيف» يجمع صورتين -/

/-- تنظيفٌ يحذف التطويل (ـ). -/
def hadhfTatwil (s : List Char) : List Char := s.filter (· != 'ـ')

/-- «بـاب» و«باب» صورتان مختلفتان في المودَع، يجمعهما الحذف في صورة واحدة. -/
theorem tatwil_yajma :
    hadhfTatwil ['ب', 'ـ', 'ا', 'ب'] = hadhfTatwil ['ب', 'ا', 'ب'] ∧
    ['ب', 'ـ', 'ا', 'ب'] ≠ ['ب', 'ا', 'ب'] := by decide

/-- فليس للحذف طيٌّ معتبر يُفكّ إلى الأصل: الإيداع يحفظ البايتات كما هي، والتصحيف يوسم ولا يُحذف. -/
theorem la_tanzif_bila_daya : ¬ ∃ t : Tayy (List Char) (List Char), t.tawi = hadhfTatwil :=
  la_tayy_maa_jam hadhfTatwil tatwil_yajma.2 tatwil_yajma.1

/-! ## ٤. لا أصل بلا مودَعٍ مسجَّل -/

/-- الأصل مقبول إن كان له سند، وكان سنده يبدأ ببصمة مودَعٍ في السجلّ **غيرِ فارغة**: الفارغةُ بادئةُ كلّ نصّ، فقيدٌ
    بلا بصمةٍ كان يقبل كلَّ سند (سُدّ بإذن المالك 2026-10-19 16:16؛ الفاحص التنفيذيّ يشترط 64 حرفًا عند القراءة، وهذا
    سدُّه في التعريف نفسِه). وعدمُ الفراغ لا يثبت مطابقةَ البصمة الكاملة (السجلّ `["a"]` يقبل كلّ سندٍ أوّلُه a): حدُّها بنوع
    المعرّف مسألةٌ مستقلّة (توجيهٌ رفعه المالك 2026-10-19 18:02). -/
def aslMusajjal {P : Type} (sanad? : P → Option String) (sijill : List String) (p : P) : Bool :=
  match sanad? p with
  | some s => sijill.any (fun b => !b.isEmpty && s.startsWith b)
  | none => false

theorem aslMusajjal_sanad {P : Type} (sanad? : P → Option String) (sijill : List String) (p : P)
    (h : aslMusajjal sanad? sijill p = true) :
    ∃ s b, sanad? p = some s ∧ b ∈ sijill ∧ b ≠ "" ∧ s.startsWith b = true := by
  unfold aslMusajjal at h
  split at h
  · rename_i s hs
    obtain ⟨b, hb, hsb⟩ := List.any_eq_true.mp h
    simp only [Bool.and_eq_true, Bool.not_eq_true'] at hsb
    exact ⟨s, b, hs, hb, by rintro rfl; exact absurd hsb.1 (by decide), hsb.2⟩
  · cases h

/-- سجلٌّ فارغ لا يُقبل منه أصل: لا معرفة بلا مودَع. -/
theorem sijill_faregh (P : Type) (sanad? : P → Option String) (p : P) :
    aslMusajjal sanad? [] p = false := by
  unfold aslMusajjal; split <;> rfl

/-- **البصمةُ الفارغة لا تُسجِّل**: سجلٌّ كلُّ بصماته فارغةٌ لا يُقبل منه أصل، أيًّا كان السند — مع أنّ «""» بادئةُ كلّ نصّ. -/
theorem basma_farigha_la_tuqbal {P : Type} (sanad? : P → Option String) (sijill : List String)
    (hs : ∀ b ∈ sijill, b = "") (p : P) : aslMusajjal sanad? sijill p = false := by
  unfold aslMusajjal
  split
  · rw [List.any_eq_false]
    intro b hb
    have he : ("" : String).isEmpty = true := by decide
    rw [hs b hb]
    simp [he]
  · rfl

/-- **البصمةُ الفارغة لا أثرَ لها**: حذفُ القيود الفارغة من أيّ سجلٍّ لا يغيّر القبول، أيًّا كان السند — وهي خاصّةُ السدّ. -/
theorem basma_farigha_khamila {P : Type} (sanad? : P → Option String) (sijill : List String) (p : P) :
    aslMusajjal sanad? (sijill.filter (· != "")) p = aslMusajjal sanad? sijill p := by
  unfold aslMusajjal
  split
  · rename_i s _
    induction sijill with
    | nil => rfl
    | cons b bs ih =>
      by_cases hb : b = ""
      · subst hb
        have h0 : ("" : String).isEmpty = true := by decide
        simp [List.filter, h0, ih]
      · have h1 : b.isEmpty = false := by
          cases h : b.isEmpty
          · rfl
          · exact absurd (String.isEmpty_iff.mp h) hb
        have hb' : (b != "") = true := bne_iff_ne.mpr hb
        simp only [List.filter_cons, hb', ite_true, List.any_cons, h1, ih]
  · rfl

/-- **السندُ الفارغ لا يُقبل** (على الشاهد): مع سجلٍّ غير فارغ فيه بصمةٌ سليمةٌ وأخرى فارغة. -/
theorem sanad_farigh_marfud : aslMusajjal (fun _ : Unit => some "") ["abc", ""] () = false := by
  decide +kernel

/-- وعلى الشاهد: سندٌ يبدأ ببصمةٍ مسجَّلةٍ غيرِ فارغة مقبول، وسندٌ لا يبدأ بها مرفوض — فالسدُّ لا يُفرغ القبول. -/
theorem aslMusajjal_shahid :
    aslMusajjal (fun _ : Unit => some "abc@1") ["abc"] () = true ∧
    aslMusajjal (fun _ : Unit => some "abd@1") ["abc"] () = false := by
  decide +kernel

end Idaa
