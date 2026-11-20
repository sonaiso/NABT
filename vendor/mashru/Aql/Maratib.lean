/-
  Aql/Maratib.lean — مراتب المخرج الثلاث (الدستور م15–م17)، على قضايا الدلالة الأولى.

  السند: الدستور م15: «ثلاثُ مراتبَ للمخرج لا مرتبتان: من حيث هي (ما تدلّ عليه الصورةُ والنسبةُ بوضعها) /
  معلومة (معنًى مفهومٌ لفظًا لا شاهدَ مودَعًا لواقعه) / مفهوم (معنًى له واقعٌ مودَعٌ مشهود)»؛
  م16: «لا مفهوم بلا واقعٍ مودَع … ولا يرفع التكرارُ في النصّ معلومةً إلى مفهوم»؛
  م17: «مرتبةُ من حيث هي تُحسب من الصورة والنسبة وحدهما: لا معاملَ لقصد المتكلّم ولا لتوقّع السامع».
  ج1 (العقلية): «المفاهيمُ معاني الأفكار لا معاني الألفاظ … وما عدا ذلك مجرّدُ معلومات».
  ومقترح المالك (qawanin_madlul_v17، SLGE/Shajara.lean): الشاهد موضعٌ في مودَعٍ مختوم، لا Bool؛ أعيد بناؤه هنا.

  البناء:
  * قضايا الدلالة والبنية كلُّها «من حيث هي»: دالّتها لا تأخذ قصدًا ولا سامعًا (م17).
  * المعاني المذكورة في القضيّة تُرتَّب كلٌّ بشواهد واقعه: «مفهوم» لا يُبنى إلّا على قائمة شواهد غير خالية
    (في المُنشئ نفسه، م16)؛ وإلّا «معلومة».
  * الشاهد لا يُعتبر إلّا إن كانت بصمته لمودَعٍ من نوع «واقع مختوم» (الدستور م12): المعجم لا يصنع مفهومًا؛ وببصمةِ قيدٍ غيرِ
    فارغة (سُدّ 2026-10-19 بإذن المالك: «""» بادئةُ كلّ بصمة، فقيدٌ فارغٌ من نوع «واقع مختوم» كان يُعتبر كلَّ شاهد؛ و`waqi_yarfa`
    أُضعفت بالضرورة بفرض `hne`، لأنّ صيغتها القديمة عند `b = ""` كانت هي شاهدَ الثغرة).
  * الفهرس يعدّ الثلاث كلّها.
  بلا sorry ولا axiom ولا native_decide.
-/
import Aql.QawaninDalala
import Aql.Idaa

namespace Maratib
open QawaninDalala

/-- شاهد الواقع: موضعٌ في مودَع، ببصمته. -/
structure ShahidWaqi where
  basma : String
  mawdi : Nat
deriving DecidableEq, Repr

/-- المخرج بمراتبه الثلاث. «مفهوم» يحمل شواهده وبرهان عدم خلوّها. -/
inductive Mukhraj
  | minHaythuHiya (p : Qadiyya)
  | maaluma (m : Nat)
  | mafhum (m : Nat) (sh : List ShahidWaqi) (h : sh ≠ [])

def Mukhraj.ism : Mukhraj → String
  | .minHaythuHiya _ => "من حيث هي"
  | .maaluma _ => "معلومة"
  | .mafhum .. => "مفهوم"

/-! ## ١. من حيث هي: من القضيّة وحدها -/

/-- مرتبة القضيّة: لا تأخذ متكلّمًا ولا سامعًا ولا مرادًا (م17). -/
def martabatQadiyya (p : Qadiyya) : Mukhraj := .minHaythuHiya p

theorem qadiyya_min_haythu_hiya (p : Qadiyya) : (martabatQadiyya p).ism = "من حيث هي" := rfl

/-! ## ٢. المعاني: معلومة أو مفهوم بشواهد الواقع -/

/-- الشواهد المعتبرة: ما كانت بصمته لمودَعٍ مسجَّلٍ من نوع «واقع مختوم» ببصمةٍ **غيرِ فارغة** (الفارغةُ بادئةُ كلّ بصمة؛
    سُدّ بإذن المالك 2026-10-19 16:16). -/
def shuhudMutabara (sijill : List (String × Idaa.Naw)) (sh : List ShahidWaqi) : List ShahidWaqi :=
  sh.filter fun s => sijill.any fun b => !b.1.isEmpty && s.basma.startsWith b.1 && b.2 == .waqiMakhtum

def martabatMaana (m : Nat) (sh : List ShahidWaqi) : Mukhraj :=
  if h : sh = [] then .maaluma m else .mafhum m sh h

/-- **لا مفهوم بلا شاهد** (م16): بالبناء. -/
theorem la_mafhum_bila_shahid (m : Nat) (sh : List ShahidWaqi) (sh' : List ShahidWaqi) (h : sh' ≠ [])
    (he : martabatMaana m sh = .mafhum m sh' h) : sh ≠ [] := by
  intro hnil; subst hnil; simp [martabatMaana] at he

theorem mafhum_bishahid (m : Nat) (s : ShahidWaqi) (sh : List ShahidWaqi) :
    martabatMaana m (s :: sh) = .mafhum m (s :: sh) (by simp) := by simp [martabatMaana]

/-- **التكرار لا يرفع:** الدالّة لا تأخذ عدد الورود؛ معنًى بلا شاهد معلومةٌ مهما تكرّر. -/
theorem takrar_la_yarfa (m n : Nat) :
    (List.replicate n (martabatMaana m [])).all (fun x => x.ism == "معلومة") = true := by
  induction n with
  | zero => rfl
  | succ k _ => simp [List.replicate_succ, martabatMaana, Mukhraj.ism]

/-- **المعجم لا يصنع مفهومًا:** شاهدٌ في مودَع «معلومات سابقة» لا يُعتبر، فتبقى المرتبة معلومة. -/
theorem mujam_la_yasna_mafhum (b : String) (sh : List ShahidWaqi)
    (_ : ∀ s ∈ sh, s.basma.startsWith b = true) (m : Nat) :
    martabatMaana m (shuhudMutabara [(b, .maalumatSabiqa)] sh) = .maaluma m := by
  have : shuhudMutabara [(b, .maalumatSabiqa)] sh = [] := by
    simp only [shuhudMutabara, List.filter_eq_nil_iff]
    intro s _
    simp
  rw [this]; rfl

/-- **بلا مودَعٍ من نوع «واقع مختوم» في السجلّ لا مفهوم أصلًا**، أيًّا كانت الشواهد. -/
theorem la_mafhum_bila_waqi (sijill : List (String × Idaa.Naw)) (hs : ∀ b ∈ sijill, b.2 ≠ .waqiMakhtum)
    (m : Nat) (sh : List ShahidWaqi) : martabatMaana m (shuhudMutabara sijill sh) = .maaluma m := by
  have : shuhudMutabara sijill sh = [] := by
    simp only [shuhudMutabara, List.filter_eq_nil_iff]
    intro s _
    simp only [Bool.not_eq_true, List.any_eq_false]
    intro b hb
    have := hs b hb
    cases h : b.2 <;> simp_all
  rw [this]; rfl

/-- وشاهدٌ معتبَرٌ واحد في «واقع مختوم» ببصمةٍ غيرِ فارغة يرفع المعنى إلى مفهوم. -/
theorem waqi_yarfa (b : String) (hne : b ≠ "") (s : ShahidWaqi) (hb : s.basma.startsWith b = true) (m : Nat) :
    (martabatMaana m (shuhudMutabara [(b, .waqiMakhtum)] [s])).ism = "مفهوم" := by
  have he : b.isEmpty = false := by
    cases h : b.isEmpty
    · rfl
    · exact absurd (String.isEmpty_iff.mp h) hne
  simp [shuhudMutabara, he, hb, martabatMaana, Mukhraj.ism]

/-- **البصمةُ الفارغة لا أثرَ لها**: حذفُ القيود الفارغة البصمة من أيّ سجلٍّ لا يغيّر الشواهد المعتبرة — وهي خاصّةُ السدّ. -/
theorem basma_farigha_la_tuthir (sijill : List (String × Idaa.Naw)) (sh : List ShahidWaqi) :
    shuhudMutabara (sijill.filter (·.1 != "")) sh = shuhudMutabara sijill sh := by
  unfold shuhudMutabara
  congr 1
  funext s
  induction sijill with
  | nil => rfl
  | cons b bs ih =>
    by_cases hb : b.1 = ""
    · have h0 : ("" : String).isEmpty = true := by decide
      simp [List.filter, hb, h0, ih]
    · have h1 : b.1.isEmpty = false := by
        cases h : b.1.isEmpty
        · rfl
        · exact absurd (String.isEmpty_iff.mp h) hb
      have hb' : (b.1 != "") = true := bne_iff_ne.mpr hb
      simp only [List.filter_cons, hb', ite_true, List.any_cons, h1, ih]

/-- **الشاهدُ المعتبَر سندُه بصمةٌ غيرُ فارغة**: كلُّ شاهدٍ معتبَر تبدأ بصمتُه ببصمة قيدٍ في السجلّ غيرِ فارغة، نوعُه «واقع
    مختوم» — نظيرُ `Idaa.aslMusajjal_sanad`. -/
theorem shuhudMutabara_sanad (sijill : List (String × Idaa.Naw)) (sh : List ShahidWaqi) (s : ShahidWaqi)
    (h : s ∈ shuhudMutabara sijill sh) :
    s ∈ sh ∧ ∃ b ∈ sijill, b.1 ≠ "" ∧ s.basma.startsWith b.1 = true ∧ b.2 = .waqiMakhtum := by
  unfold shuhudMutabara at h
  obtain ⟨hs, hp⟩ := List.mem_filter.mp h
  obtain ⟨b, hb, hq⟩ := List.any_eq_true.mp hp
  simp only [Bool.and_eq_true, Bool.not_eq_true', beq_iff_eq] at hq
  obtain ⟨⟨he, hst⟩, hn⟩ := hq
  have h0 : ("" : String).isEmpty = true := by decide
  exact ⟨hs, b, hb, (fun hb0 => by rw [hb0, h0] at he; cases he), hst, hn⟩

/-- **الشاهدُ الفارغ لا يُعتبر** (على الشاهد): مع سجلٍّ فيه قيدٌ سليمٌ وآخرُ فارغ، كلاهما «واقع مختوم». -/
theorem shahid_farigh_marfud :
    shuhudMutabara [("abc", .waqiMakhtum), ("", .waqiMakhtum)] [⟨"", 1⟩] = [] := by
  decide +kernel

/-- وعلى الشاهد: شاهدٌ تبدأ بصمتُه ببصمة قيدٍ «واقع مختوم» معتبَر، وما لا تبدأ به لا يُعتبر. -/
theorem shuhudMutabara_shahid :
    shuhudMutabara [("abc", .waqiMakhtum)] [⟨"abcdef", 1⟩, ⟨"abd", 2⟩] = [⟨"abcdef", 1⟩] := by
  decide +kernel

/-- **البصمةُ الفارغة لا تُشهِد**: سجلٌّ كلُّ قيدٍ فيه بصمتُه فارغةٌ أو نوعُه غيرُ «واقع مختوم» لا يرفع معنًى إلى مفهوم، أيًّا
    كانت الشواهد — مع أنّ «""» بادئةُ كلّ بصمة. -/
theorem basma_farigha_la_tushhid (sijill : List (String × Idaa.Naw))
    (hs : ∀ b ∈ sijill, b.1 = "" ∨ b.2 ≠ .waqiMakhtum) (m : Nat) (sh : List ShahidWaqi) :
    martabatMaana m (shuhudMutabara sijill sh) = .maaluma m := by
  have : shuhudMutabara sijill sh = [] := by
    simp only [shuhudMutabara, List.filter_eq_nil_iff]
    intro s _
    simp only [Bool.not_eq_true, List.any_eq_false]
    intro b hb
    rcases hs b hb with h | h
    · have he : ("" : String).isEmpty = true := by decide
      rw [h]; simp [he]
    · cases h2 : b.2 <;> simp_all
  rw [this]; rfl

/-! ## ٣. المعاني المذكورة في القضيّة، والفهرس -/

/-- معرّفات المعاني التي تذكرها القضيّة (الألفاظ والعناوين ليست معانيَ). -/
def maani : Qadiyya → List Nat
  | .wad _ m | .mutabaqa _ m => [m]
  | .juz j m | .kharij j m | .luzum j m => [j, m]
  | .tadammun _ j | .iltizam _ j => [j]
  | .fi .. | .taht .. => []

/-- مخرج القضيّة: هي من حيث هي، ومعانيها كلٌّ بمرتبته. -/
def mukhraj (shuhud : Nat → List ShahidWaqi) (p : Qadiyya) : List Mukhraj :=
  martabatQadiyya p :: (maani p).map fun m => martabatMaana m (shuhud m)

/-- خطوة العدّ. -/
def khatwa (acc : Nat × Nat × Nat) : Mukhraj → Nat × Nat × Nat
  | .minHaythuHiya _ => (acc.1 + 1, acc.2.1, acc.2.2)
  | .maaluma _ => (acc.1, acc.2.1 + 1, acc.2.2)
  | .mafhum .. => (acc.1, acc.2.1, acc.2.2 + 1)

/-- الفهرس يعدّ الثلاث كلّها (م15): (من حيث هي، معلومة، مفهوم). -/
def ihsa (xs : List Mukhraj) : Nat × Nat × Nat := xs.foldl khatwa (0, 0, 0)

theorem khatwa_majmu (acc : Nat × Nat × Nat) (x : Mukhraj) :
    (khatwa acc x).1 + (khatwa acc x).2.1 + (khatwa acc x).2.2 = acc.1 + acc.2.1 + acc.2.2 + 1 := by
  cases x <;> simp [khatwa] <;> omega

theorem foldl_majmu (xs : List Mukhraj) (acc : Nat × Nat × Nat) :
    (xs.foldl khatwa acc).1 + (xs.foldl khatwa acc).2.1 + (xs.foldl khatwa acc).2.2 =
      acc.1 + acc.2.1 + acc.2.2 + xs.length := by
  induction xs generalizing acc with
  | nil => simp
  | cons x xs ih => simp only [List.foldl_cons, List.length_cons]; rw [ih, khatwa_majmu]; omega

/-- لا يضيع مخرجٌ من العدّ. -/
theorem ihsa_majmu (xs : List Mukhraj) : (ihsa xs).1 + (ihsa xs).2.1 + (ihsa xs).2.2 = xs.length := by
  simpa [ihsa] using foldl_majmu xs (0, 0, 0)

theorem khatwa_maana_fst (acc : Nat × Nat × Nat) (m : Nat) (sh : List ShahidWaqi) :
    (khatwa acc (martabatMaana m sh)).1 = acc.1 := by
  unfold martabatMaana; split <;> rfl

/-- في مخرج كلّ قضيّة «من حيث هي» واحدةٌ بالضبط، والباقي معانيها معلومةً أو مفهومًا بعددها. -/
theorem mukhraj_wahid_min_haythu (shuhud : Nat → List ShahidWaqi) (p : Qadiyya) :
    (ihsa (mukhraj shuhud p)).1 = 1 ∧
    (ihsa (mukhraj shuhud p)).2.1 + (ihsa (mukhraj shuhud p)).2.2 = (maani p).length := by
  have h1 : (ihsa (mukhraj shuhud p)).1 = 1 := by
    simp only [ihsa, mukhraj, martabatQadiyya, List.foldl_cons, List.foldl_map]
    suffices h : ∀ (l : List Nat) (acc : Nat × Nat × Nat),
        (l.foldl (fun acc m => khatwa acc (martabatMaana m (shuhud m))) acc).1 = acc.1 by
      rw [h]; rfl
    intro l
    induction l with
    | nil => intro acc; rfl
    | cons m l ih => intro acc; simp only [List.foldl_cons]; rw [ih, khatwa_maana_fst]
  have hm := ihsa_majmu (mukhraj shuhud p)
  simp only [mukhraj, List.length_cons, List.length_map] at hm
  simp only [mukhraj] at h1
  refine ⟨h1, ?_⟩
  simp only [mukhraj]
  omega

end Maratib
