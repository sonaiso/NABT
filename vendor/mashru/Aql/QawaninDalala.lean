/-
  Aql/QawaninDalala.lean — القوانين الأولى للدلالة في القاعدة، وفق منهج النبهاني (قرار المالك، 15 أكتوبر 2026).

  السند ج3 737 («تقسيم اللفظ باعتبار الدال وحده»):
  * المطابقة «دلالة اللفظ على تمام مسمّاه، كدلالة الإنسان على الحيوان الناطق».
  * التضمّن «دلالة اللفظ على جزء المسمّى، كدلالة الإنسان على الحيوان فقط، أو على الناطق فقط».
  * الالتزام «دلالة اللفظ على لازمه، كدلالة الأسد على الشجاعة»؛ «والمعتبر باللزوم هو اللزوم الذهني»؛
    «وهذا اللزوم شرط وليس بموجب … السبب هو إطلاق اللفظ، واللزوم شرط».
  وج3 729: اللغة تُعرف بالنقل لا بالعقل — فالوضع والجزء واللزوم أصولٌ مودَعة (الرتبة صفر)، لا نتائج.
  وج3 1028 (المنطوق): حمل الخطاب «أوّلًا على الحقيقة الشرعية … حمل على الحقيقة العرفية … حمل على الحقيقة
  اللغوية … فإن لم يكن كذلك كان مشتركًا لا يترجّح إلّا بقرينة، فإن تعذّرت الحقائق الثلاث حمل على المجازي».

  البناء:
  * `Qadiyya`: القضايا الأولى على معرّفات (أرقام مواضع في المودَع)، لا على الألفاظ نفسها.
  * ثلاثة قوانين دلالة + قانون تعدية الاحتواء (بنية المودَع). كلّ قانون في المخزن مثالٌ لأحد هذه، يفحصه `shakl`.
  * `tafsir`: قراءة القضايا في نموذج Madlul/Dalala.lean؛ و`salama`: كلّ مرخَّصٍ بهذه القوانين صادقٌ في النموذج
    متى صدقت أصوله. فالقوانين سليمة بالنسبة إلى التعريفات (لا «برهانٌ على اللغة»، الدستور م17).
  * التدرّج: قوانين الدلالة الثلاثة متدرّجة تدرّجًا صارمًا؛ ومع التعدية تدرّجًا ضعيفًا — فالرتبة صفر أصولٌ أبدًا.
  * شواهد ج3 737 بالفاحص نفسه (مبرهن على الشاهد)، وحملُ الخطاب (ج3 1028) دالّةً مبرهنةَ الخواصّ.
  أعيد هنا بناءُ ما اقترحه المالك في qawanin_madlul_v17 (SLGE/Qarar.lean) على قاعدتنا، ولم يُنقل نصًّا.
  بلا sorry ولا axiom ولا native_decide.
-/
import Aql.Qaida
import Madlul.Dalala

namespace QawaninDalala
open Qaida Dalala

/-! ## ١. القضايا الأولى ورتبها -/

inductive Qadiyya
  | wad (l m : Nat)        -- اللفظ l موضوعٌ للمعنى m (خبر وضعٍ بشاهده)
  | juz (j m : Nat)        -- المعنى j جزءٌ من المعنى m
  | kharij (k m : Nat)     -- المعنى k خارجٌ عن المعنى m
  | luzum (m k : Nat)      -- k لازمٌ ذهنيٌّ لـ m (جدول اللزوم)
  | mutabaqa (l m : Nat)   -- L يدلّ على m مطابقةً
  | tadammun (l j : Nat)   -- L يدلّ على j تضمّنًا
  | iltizam (l k : Nat)    -- L يدلّ على k التزامًا
  | fi (c p : Nat)         -- العنوان c داخل العنوان p (بنية المودَع)
  | taht (z p : Nat)       -- الزوج z مذكورٌ تحت العنوان p (بنية المودَع)
deriving DecidableEq, Repr

/-- الرتبة: ما يُنقل عن الواضع وبنية المودَع في الصفر؛ المطابقة أولى؛ التضمّن والالتزام ثانية. -/
def rutba : Qadiyya → Nat
  | .wad .. | .juz .. | .kharij .. | .luzum .. | .fi .. => 0
  | .mutabaqa .. | .taht .. => 1
  | .tadammun .. | .iltizam .. => 2

/-! ## ٢. القوانين -/

def qMutabaqa (l m : Nat) : Qanun Qadiyya := ⟨"مطابقة-من-الوضع", [.wad l m], .mutabaqa l m⟩
def qTadammun (l m j : Nat) : Qanun Qadiyya := ⟨"تضمّن-من-الجزء", [.mutabaqa l m, .juz j m], .tadammun l j⟩
def qIltizam (l m k : Nat) : Qanun Qadiyya :=
  ⟨"التزام-من-اللزوم", [.mutabaqa l m, .kharij k m, .luzum m k], .iltizam l k⟩
def qTadiya (z c p : Nat) : Qanun Qadiyya := ⟨"تعدية-الاحتواء", [.taht z c, .fi c p], .taht z p⟩

/-- هيئة القانون: مثالٌ لأحد القوانين الأربعة بعينه، أو مرفوض. -/
def shakl (r : Qanun Qadiyya) : Bool :=
  match r.muqaddimat with
  | [.wad l m] => decide (r = qMutabaqa l m)
  | [.mutabaqa l m, .juz j _] => decide (r = qTadammun l m j)
  | [.mutabaqa l m, .kharij k _, .luzum _ _] => decide (r = qIltizam l m k)
  | [.taht z c, .fi _ p] => decide (r = qTadiya z c p)
  | _ => false

theorem shakl_sahih (r : Qanun Qadiyya) (h : shakl r = true) :
    (∃ l m, r = qMutabaqa l m) ∨ (∃ l m j, r = qTadammun l m j) ∨
    (∃ l m k, r = qIltizam l m k) ∨ (∃ z c p, r = qTadiya z c p) := by
  unfold shakl at h
  split at h
  · exact Or.inl ⟨_, _, of_decide_eq_true h⟩
  · exact Or.inr (Or.inl ⟨_, _, _, of_decide_eq_true h⟩)
  · exact Or.inr (Or.inr (Or.inl ⟨_, _, _, of_decide_eq_true h⟩))
  · exact Or.inr (Or.inr (Or.inr ⟨_, _, _, of_decide_eq_true h⟩))
  · cases h

theorem shakl_qawanin : ∀ l m j k z c p, shakl (qMutabaqa l m) = true ∧ shakl (qTadammun l m j) = true ∧
    shakl (qIltizam l m k) = true ∧ shakl (qTadiya z c p) = true := by
  intro l m j k z c p
  simp [shakl, qMutabaqa, qTadammun, qIltizam, qTadiya]

/-! ## ٣. التدرّج -/

/-- قاعدةٌ كلُّ قوانينها على الهيئة متدرّجةٌ ضعيفًا: فالرتبة صفر (الوضع، الجزء، اللزوم، البنية) أصولٌ أبدًا. -/
theorem shakl_mutadarrija (q : Qaida.Qaida Qadiyya) (hq : ∀ r ∈ q.qawanin, shakl r = true) :
    MutadarrijaDaifa q rutba := by
  intro r hr
  rcases shakl_sahih r (hq r hr) with ⟨l, m, rfl⟩ | ⟨l, m, j, rfl⟩ | ⟨l, m, k, rfl⟩ | ⟨z, c, p, rfl⟩ <;>
    simp [qMutabaqa, qTadammun, qIltizam, qTadiya, rutba]

/-- قوانين الدلالة الثلاثة وحدها متدرّجة تدرّجًا صارمًا. -/
theorem dalala_mutadarrija (q : Qaida.Qaida Qadiyya)
    (hq : ∀ r ∈ q.qawanin, (∃ l m, r = qMutabaqa l m) ∨ (∃ l m j, r = qTadammun l m j) ∨ (∃ l m k, r = qIltizam l m k)) :
    Mutadarrija q rutba := by
  intro r hr
  rcases hq r hr with ⟨l, m, rfl⟩ | ⟨l, m, j, rfl⟩ | ⟨l, m, k, rfl⟩ <;>
    simp [qMutabaqa, qTadammun, qIltizam, rutba]

/-- لا وضع ولا جزء ولا لزوم يُستنتج: كلّ ما رتبته صفر مرخَّصٌ أصلًا مودَعًا (ج3 729). -/
theorem naql_la_aql (q : Qaida.Qaida Qadiyya) (hq : ∀ r ∈ q.qawanin, shakl r = true) (A : Qadiyya → Prop)
    (l m : Nat) (h : Murakhkhas q A (.wad l m)) : A (.wad l m) :=
  rutba_sifr_asl_daifa q rutba A (shakl_mutadarrija q hq) h rfl

/-! ## ٤. السلامة بالنسبة إلى نموذج المدلول (Madlul/Dalala.lean) -/

section Tafsir
variable {L α : Type} (W : Wad L α) (Z : Luzum α) (lf : Nat → L) (mn : Nat → Maana α)
  (Fi Taht : Nat → Nat → Prop)

/-- قراءة القضايا في النموذج: المعرّفات إلى ألفاظٍ ومعانٍ، والبنية إلى علاقتين معطاتين. -/
def tafsir : Qadiyya → Prop
  | .wad l m => W.shuhud (lf l) ≠ [] ∧ Sawa (mn m) (W.maana (lf l))
  | .juz j m => Juz (mn j) (mn m)
  | .kharij k m => Kharij (mn k) (mn m)
  | .luzum m k => Z (mn m) (mn k)
  | .mutabaqa l m => Mutabaqa W (lf l) (mn m)
  | .tadammun l j => Tadammun W (lf l) (mn j)
  | .iltizam l k => Iltizam W Z (lf l) (mn k)
  | .fi c p => Fi c p
  | .taht z p => Taht z p

theorem juz_sawa {p m j : Maana α} (hs : Sawa p m) (hj : Juz j p) : Juz j m := by
  obtain ⟨hne, hsub, x, hpx, hjx⟩ := hj
  exact ⟨hne, fun y hy => (hs y).mp (hsub y hy), x, (hs x).mp hpx, hjx⟩

theorem kharij_sawa {p m k : Maana α} (hs : Sawa p m) (hk : Kharij k p) : Kharij k m := by
  obtain ⟨x, hkx, hpx⟩ := hk
  exact ⟨x, hkx, fun hm => hpx ((hs x).mpr hm)⟩

theorem sawa_eq {p m : Maana α} (hs : Sawa p m) : p = m :=
  funext fun x => propext (hs x)

/-- **السلامة:** في قاعدةٍ قوانينها على الهيئة، كلّ قضيّةٍ مرخَّصةٍ صادقةٌ في النموذج متى صدقت أصولها،
    وكانت بنيةُ المودَع تُعدّي الاحتواء. -/
theorem salama (q : Qaida.Qaida Qadiyya) (hq : ∀ r ∈ q.qawanin, shakl r = true)
    (A : Qadiyya → Prop) (hA : ∀ a, A a → tafsir W Z lf mn Fi Taht a)
    (htadiya : ∀ z c p, Taht z c → Fi c p → Taht z p)
    {p : Qadiyya} (h : Murakhkhas q A p) : tafsir W Z lf mn Fi Taht p := by
  induction h with
  | asl ha => exact hA _ ha
  | qanun r hr _ ih =>
    rcases shakl_sahih r (hq r hr) with ⟨l, m, rfl⟩ | ⟨l, m, j, rfl⟩ | ⟨l, m, k, rfl⟩ | ⟨z, c, p, rfl⟩
    · have h1 : tafsir W Z lf mn Fi Taht (.wad l m) := ih (.wad l m) (by simp [qMutabaqa])
      exact h1
    · have h1 : tafsir W Z lf mn Fi Taht (.mutabaqa l m) := ih (.mutabaqa l m) (by simp [qTadammun])
      have h2 : tafsir W Z lf mn Fi Taht (.juz j m) := ih (.juz j m) (by simp [qTadammun])
      simp only [tafsir] at h1 h2 ⊢
      exact ⟨h1.1, juz_sawa h1.2 h2⟩
    · have h1 : tafsir W Z lf mn Fi Taht (.mutabaqa l m) := ih (.mutabaqa l m) (by simp [qIltizam])
      have h2 : tafsir W Z lf mn Fi Taht (.kharij k m) := ih (.kharij k m) (by simp [qIltizam])
      have h3 : tafsir W Z lf mn Fi Taht (.luzum m k) := ih (.luzum m k) (by simp [qIltizam])
      simp only [tafsir] at h1 h2 h3 ⊢
      refine ⟨h1.1, kharij_sawa h1.2 h2, ?_⟩
      rw [← sawa_eq h1.2]; exact h3
    · have h1 : tafsir W Z lf mn Fi Taht (.taht z c) := ih (.taht z c) (by simp [qTadiya])
      have h2 : tafsir W Z lf mn Fi Taht (.fi c p) := ih (.fi c p) (by simp [qTadiya])
      simp only [tafsir] at h1 h2 ⊢
      exact htadiya z c p h1 h2

end Tafsir

/-! ## ٥. شواهد ج3 737 بالفاحص نفسه: الإنسان 1، الحيوان الناطق 10، الحيوان 11، الناطق 12؛ الأسد 2، معناه 21، الشجاعة 20 -/

def qShahid : Qaida.Qaida Qadiyya :=
  ⟨"دلالة-0.1", [qMutabaqa 1 10, qTadammun 1 10 11, qTadammun 1 10 12, qMutabaqa 2 21, qIltizam 2 21 20]⟩

def aslShahid : Qadiyya → Bool
  | .wad 1 10 | .juz 11 10 | .juz 12 10 | .wad 2 21 | .kharij 20 21 | .luzum 21 20 => true
  | _ => false

theorem shahid_shakl : qShahid.qawanin.all shakl = true := by decide
theorem shahid_mutadarrija : Mutadarrija qShahid rutba := by unfold Mutadarrija; decide

/-- الإنسان يدلّ على الحيوان تضمّنًا: من الوضع ثمّ المطابقة ثمّ الجزء. -/
theorem shahid_tadammun :
    maqbul qShahid aslShahid ⟨.tadammun 1 11, [.asl (.wad 1 10), .qanun 0, .asl (.juz 11 10), .qanun 1]⟩ = true := by
  decide

/-- الأسد يدلّ على الشجاعة التزامًا: بشرط اللزوم. -/
theorem shahid_iltizam :
    maqbul qShahid aslShahid ⟨.iltizam 2 20,
      [.asl (.wad 2 21), .qanun 3, .asl (.kharij 20 21), .asl (.luzum 21 20), .qanun 4]⟩ = true := by
  decide

/-- وبلا لزومٍ مودَع لا التزام: «اللزوم شرط». -/
theorem shahid_la_iltizam_bila_luzum :
    maqbul qShahid aslShahid ⟨.iltizam 2 20, [.asl (.wad 2 21), .qanun 3, .asl (.kharij 20 21), .qanun 4]⟩ = false := by
  decide

/-- ولا تضمّن بلا جزءٍ مودَع، ولا مطابقة لمعنًى لم يوضع له اللفظ. -/
theorem shahid_la_tadammun_bila_juz :
    maqbul qShahid aslShahid ⟨.tadammun 1 20, [.asl (.wad 1 10), .qanun 0, .asl (.juz 20 10), .qanun 1]⟩ = false ∧
    maqbul qShahid aslShahid ⟨.mutabaqa 1 11, [.asl (.wad 1 11), .qanun 0]⟩ = false := by
  decide

/-! ## ٦. حمل الخطاب (ج3 1028): الشرعية ثمّ العرفية ثمّ اللغوية، ثمّ الاشتراك بقرينة، ثمّ المجاز -/

inductive NawHaqiqa | shariyya | urfiyya | lughawiyya deriving DecidableEq, Repr
/-- شهادة المودَع لكلّ حقيقة: نعم، لا، أو غير مصرَّح (لا عالمَ مغلقًا). -/
inductive Shahada | naam | la | ghayr deriving DecidableEq, Repr
inductive Mahmul | haqiqa (n : NawHaqiqa) | mushtarak | majaz | laHukm deriving DecidableEq, Repr

def tartibHaml : List NawHaqiqa := [.shariyya, .urfiyya, .lughawiyya]

/-- الحمل. `sabq`: كثر استعمال الشرعيّ أو العرفيّ حتّى سبق إلى الفهم؛ `qarina`: قرينة ترجّح إحدى الحقائق؛
    `alaqa`: علاقة مجاز مودَعة. -/
def haml (s1 s2 s3 : Shahada) (sabq : Bool) (qarina : Option NawHaqiqa) (alaqa : Bool) : Mahmul :=
  let sh : NawHaqiqa → Shahada := fun n => match n with | .shariyya => s1 | .urfiyya => s2 | .lughawiyya => s3
  let naam := tartibHaml.filter (fun n => sh n == .naam)
  match naam with
  | [] => if s1 == .ghayr || s2 == .ghayr || s3 == .ghayr then .laHukm else if alaqa then .majaz else .laHukm
  | [n] => .haqiqa n
  | n :: _ => if sabq then .haqiqa n else
      match qarina with
      | some m => if sh m == .naam then .haqiqa m else .mushtarak
      | none => .mushtarak

/-- **الشرعية أوّلًا** متى شهد لها وسبقت. -/
theorem shariyya_awwalan : ∀ s2 s3 q a, haml .naam s2 s3 true q a = .haqiqa .shariyya := by
  intro s2 s3 q a
  cases s2 <;> cases s3 <;> cases a <;> rcases q with _ | n <;> (try cases n) <;> decide

/-- **حقيقة واحدة مشهودة تُحمل عليها**، أيًّا كان السبق والقرينة. -/
theorem wahida_tuhmal : ∀ sabq q a,
    haml .naam .la .la sabq q a = .haqiqa .shariyya ∧ haml .la .naam .la sabq q a = .haqiqa .urfiyya ∧
    haml .la .la .naam sabq q a = .haqiqa .lughawiyya := by
  intro sabq q a
  cases sabq <;> cases a <;> rcases q with _ | n <;> (try cases n) <;> decide

/-- **لا مجاز قبل استنفاد الحقائق الثلاث:** إن شهد لإحداها فليس مجازًا. -/
theorem la_majaz_qabl_istinfad : ∀ s1 s2 s3 sabq q a, (s1 = .naam ∨ s2 = .naam ∨ s3 = .naam) →
    haml s1 s2 s3 sabq q a ≠ .majaz := by
  intro s1 s2 s3 sabq q a
  cases s1 <;> cases s2 <;> cases s3 <;> cases sabq <;> cases a <;> rcases q with _ | n <;> (try cases n) <;> decide

/-- **غيرُ المصرَّح يوقف:** إن لم تشهد حقيقة وكان في الشهادات «غير مصرَّح» فلا حكم، لا مجاز (الغياب ليس امتناعًا). -/
theorem ghayr_yuqif : ∀ s1 s2 s3 sabq q a, ¬ (s1 = .naam ∨ s2 = .naam ∨ s3 = .naam) →
    (s1 = .ghayr ∨ s2 = .ghayr ∨ s3 = .ghayr) → haml s1 s2 s3 sabq q a = .laHukm := by
  intro s1 s2 s3 sabq q a
  cases s1 <;> cases s2 <;> cases s3 <;> cases sabq <;> cases a <;> rcases q with _ | n <;> (try cases n) <;> decide

/-- **المجاز بعد ثلاث سلبيّات مسمّاة وعلاقة؛ وبلا علاقة لا حكم.** -/
theorem majaz_bad_istinfad : ∀ sabq q, haml .la .la .la sabq q true = .majaz ∧ haml .la .la .la sabq q false = .laHukm := by
  intro sabq q
  cases sabq <;> rcases q with _ | n <;> (try cases n) <;> decide

/-- **الاشتراك:** حقيقتان مشهودتان بلا سبقٍ ولا قرينةٍ لا تترجّح إحداهما. -/
theorem mushtarak_bila_qarina : ∀ a, haml .naam .naam .la false none a = .mushtarak ∧
    haml .naam .naam .la false (some .urfiyya) a = .haqiqa .urfiyya := by
  intro a; cases a <;> decide

/-- الحكم رباعيّ ولا يحذف: كلّ مخرجٍ أحد الأربعة. -/
theorem haml_rubai : ∀ s1 s2 s3 sabq q a, (∃ n, haml s1 s2 s3 sabq q a = .haqiqa n) ∨
    haml s1 s2 s3 sabq q a = .mushtarak ∨ haml s1 s2 s3 sabq q a = .majaz ∨ haml s1 s2 s3 sabq q a = .laHukm := by
  intro s1 s2 s3 sabq q a
  cases h : haml s1 s2 s3 sabq q a
  · exact Or.inl ⟨_, rfl⟩
  · exact Or.inr (Or.inl rfl)
  · exact Or.inr (Or.inr (Or.inl rfl))
  · exact Or.inr (Or.inr (Or.inr rfl))

end QawaninDalala
