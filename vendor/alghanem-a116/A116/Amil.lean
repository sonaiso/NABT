import A116.Qism
import A116.Tarkib
import A116.Pause

/-!
# العاملُ والمعمول على حامل/حالة/موضع، والعلاماتُ الأصليّةُ والفرعيّة، والنِّسَبُ الثلاث (ADR ٧٠، أمرُ المالك)

المراسي (شرحُ ابن عقيل المختوم `corpora/ibn-aqil/`، س406–418؛ والكتابُ س234–240):

* س406–407: «فارفع بضمٍّ وانصبن فتحًا وجرّ كسرًا … واجزم بتسكين، وغيرُ ما ذُكر ينوب» — **الأصليّةُ** أربعُ حركات،
  و**الفرعيّةُ** نائبةٌ عنها (س412: «وما عدا ذلك يكون نائبًا عنه»).
* س409–410: الرفعُ والنصبُ مشتركان، والجرُّ للأسماء، والجزمُ للأفعال.
* س336–341: المعربُ «متأثّرٌ بالعامل».

## على الخانات

العاملُ لا يمسّ إلّا **موضعًا** واحدًا: حالةَ الخانة الأخيرة (`Ledger.mahallAt` من قبل)؛ فالعلامةُ الأصليّةُ
حالةٌ من الأربع على حامل الآخر، والفرعيّةُ حاملٌ (واو/ألف/ياء) أو حاملٌ وحالة (ان/ين/ون). والوقفُ يمحو
الأصليّة (`Pause.pause`) ولا يمحو حاملَ الفرعيّة.

## ما يُبرهَن

1. قسمةُ العلامات: أصليّةٌ أو فرعيّة (`mark_partition`)؛ الصنفُ الصحيح (اسمًا وفعلًا) أصليُّ العلامات كلِّها
   (`sahih_asliyya`)، والأسماءُ الستّة والمثنّى وجمعا السلامة والأمثلةُ الخمسة فرعيّةٌ أو نائبةٌ في كلّ حالة
   (`naib_classes`)؛ وعددُ أزواج (صنف، حالة) النائبة من الـ45 (`naib_count`).
2. العاملُ: أثرُه حالةٌ إعرابيّة (`athar`)؛ الاسمُ لا يُجزم والفعلُ لا يُجرّ (`ism_no_jazm`، `fil_no_jarr`) —
   من جدول `Qism.ending` على س404–405، 409–410.
3. الموضع: `applyMark` يغيّر الخانةَ الأخيرةَ وحدَها (`apply_prefix`، `apply_length`)، والوقفُ يمحو العلامةَ
   الأصليّة (`pause_erases_asliyya`): وقفُ المرفوع = وقفُ المنصوب = وقفُ المجرور.
4. النِّسَبُ الثلاث (ج3، مرساتُها في SLGE `Slge.Nabhani.nisab_three`، `no_tadmin`: إسناديّةٌ وتقييديّةٌ وإضافيّة، لا
   «تضمينيّة»): الفاعليّةُ والابتداءُ إسنادٌ ورفع (`isnad_raf`)، والمفعوليّةُ ومنها **السببيّة** (المفعولُ له)
   تقييدٌ ونصب (`taqyid_nasb`)، والإضافةُ جرٌّ بلا حرف (`idafa_jarr`)، والمجرورُ بالحرف قيد؛ ولا رابعةَ
   (`nisab_three`). و**المسببيّة** ليست نسبةَ إعراب: هي علاقةُ مجازٍ في ج3 (SLGE `Slge.Salsala`) فلا علامةَ
   لها هنا — `MUSABBABIYYA_IS_MAJAZ_NOT_IRAB`.

ما لا يُبرهَن: أنّ هذه علاماتُ العربيّة — ذلك مرويُّ الألفيّة بأسطره؛ Lean يُبرهن خواصَّ الجدول المنقول.
-/

namespace A116.Amil

open A116 A116.Qism

/-! ## ١. العلاماتُ الأصليّة والفرعيّة -/

/-- الأصليّةُ: الحركاتُ الأربع (س406–407). -/
def asliyya : Ending → Bool
  | .damma | .fatha | .kasra | .sukun => true
  | _ => false

/-- الفرعيّةُ بالحرف: واو، ألف، ياء، ان، ين، ون. -/
def harfiyya (e : Ending) : Bool := !asliyya e

theorem mark_partition (e : Ending) : asliyya e = true ∨ harfiyya e = true := by
  cases e <;> simp [asliyya, harfiyya]

theorem asliyya_count : (endings.filter asliyya).length = 4 := by decide
theorem harfiyya_count : (endings.filter harfiyya).length = 7 := by decide

/-- الأصلُ الذي يُقاس عليه: الاسمُ الصحيح والفعلُ الصحيح. -/
def asl (c : Cls) : Cls := if isIsm c then .iSahih else .fSahih

/-- النيابةُ (س412): آخرُ الصنف في الحالة يخالف آخرَ أصله فيها. -/
def naib (c : Cls) (i : Irab) : Bool := ending c i != ending (asl c) i

/-- الصنفُ الصحيح اسمًا وفعلًا: علاماتُه أصليّةٌ كلُّها ولا نيابةَ فيه. -/
theorem sahih_asliyya :
    irabs.all (fun i =>
      (ending .iSahih i).all asliyya && (ending .fSahih i).all asliyya &&
      !naib .iSahih i && !naib .fSahih i) = true := by
  decide

/-- الأسماءُ الستّة والمثنّى وجمعُ المذكّر السالم والأمثلةُ الخمسة: نائبةٌ في كلّ حالةٍ لها. -/
theorem naib_classes :
    [Cls.iSitta, .iMuthanna, .iJamM, .fKhamsaA, .fKhamsaW, .fKhamsaY].all (fun c =>
      irabs.all fun i => !(ending c i).isSome || naib c i) = true := by
  decide

/-- النائبُ بحركةٍ أصليّة: جمعُ المؤنّث (الكسرةُ عن الفتحة) والممنوعُ (الفتحةُ عن الكسرة). -/
theorem naib_by_haraka :
    naib .iJamF .nasb = true ∧ ending .iJamF .nasb = some .kasra ∧
    naib .iMamnu .jarr = true ∧ ending .iMamnu .jarr = some .fatha := by
  decide

/-- أزواجُ (صنف، حالة) النائبة من الخمسة والأربعين. -/
theorem naib_count : (pairs.filter fun p => naib p.1 p.2).length = 32 := by decide

/-! ## ٢. العاملُ وأثرُه -/

/-- العواملُ بأثرها: الابتداءُ والفعلُ يرفعان، والناصبُ ينصب، والجارُّ يجرّ، والجازمُ يجزم. -/
inductive Amil where
  | ibtida | fil | nasib | jarr | jazim
  deriving DecidableEq, Repr

def athar : Amil → Irab
  | .ibtida | .fil => .raf
  | .nasib => .nasb
  | .jarr => .jarr
  | .jazim => .jazm

/-- آخرُ المعمول من صنفه وعامله. -/
def mamul (c : Cls) (a : Amil) : Option Ending := ending c (athar a)

/-- الاسمُ لا يُجزم (س410). -/
theorem ism_no_jazm : classes.all (fun c => !isIsm c || (mamul c .jazim).isNone) = true := by decide

/-- الفعلُ لا يُجرّ (س410). -/
theorem fil_no_jarr : classes.all (fun c => isIsm c || (mamul c .jarr).isNone) = true := by decide

/-- الرفعُ والنصبُ مشتركان (س409): لكلّ صنفٍ آخرٌ مرفوعٌ وآخرٌ منصوب. -/
theorem raf_nasb_shared :
    classes.all (fun c => (mamul c .fil).isSome && (mamul c .nasib).isSome) = true := by
  decide

/-! ## ٣. الموضع: العلامةُ في الخانة الأخيرة، والوقفُ يمحو الأصليّة -/

def harakaOf : Ending → Option Haraka
  | .damma => some .damma | .fatha => some .fatha | .kasra => some .kasra | .sukun => some .sukun
  | _ => none

/-- وضعُ علامةٍ أصليّةٍ على الخانة الأخيرة؛ الفرعيّةُ تحتاج حاملًا فلا تُوضع هنا. -/
def applyMark (w : List Cell) (h : Haraka) : List Cell :=
  match w.getLast? with
  | none => []
  | some c => w.dropLast ++ [⟨c.carrier, h⟩]

theorem applyMark_snoc (v : List Cell) (c : Cell) (h : Haraka) :
    applyMark (v ++ [c]) h = v ++ [⟨c.carrier, h⟩] := by
  simp [applyMark]

theorem apply_prefix (w : List Cell) (h : Haraka) (hw : w ≠ []) :
    (applyMark w h).dropLast = w.dropLast := by
  unfold applyMark
  cases hl : w.getLast? with
  | none => exact absurd (List.getLast?_eq_none_iff.1 hl) hw
  | some c => simp

theorem apply_length (w : List Cell) (h : Haraka) (hw : w ≠ []) :
    (applyMark w h).length = w.length := by
  unfold applyMark
  cases hl : w.getLast? with
  | none => exact absurd (List.getLast?_eq_none_iff.1 hl) hw
  | some c =>
    simp only [List.length_append, List.length_dropLast, List.length_singleton]
    have : 0 < w.length := List.length_pos_iff.2 hw
    omega

/-- الوقفُ يمحو العلامةَ الأصليّة: وقفُ المرفوع ووقفُ المنصوب ووقفُ المجرور واحد. -/
theorem pause_erases_asliyya (w : List Cell) (h h' : Haraka) :
    Pause.pause (applyMark w h) = Pause.pause (applyMark w h') := by
  unfold applyMark
  cases w.getLast? with
  | none => rfl
  | some c => rw [Pause.pause_snoc, Pause.pause_snoc]

/-- الوقفُ على المعمول هو الوقفُ على أصله بلا علامة. -/
theorem pause_forgets_amil (w : List Cell) (h : Haraka) (hw : w ≠ []) :
    Pause.pause (applyMark w h) = Pause.pause w := by
  rcases List.eq_nil_or_concat w with rfl | ⟨v, c, rfl⟩
  · exact absurd rfl hw
  · rw [List.concat_eq_append, applyMark_snoc, Pause.pause_snoc, Pause.pause_snoc]

/-! ## ٤. النِّسَبُ الثلاث -/

inductive Nisba where
  | isnadiyya | taqyidiyya | idafiyya
  deriving DecidableEq, Repr

/-- مواضعُ المعمول بأسمائها، كلٌّ بعامله. -/
inductive Mawdi where
  | mubtada | fail | maful | mafulLahu | majrurBiHarf | mudafIlayh
  deriving DecidableEq, Repr

def amilOf : Mawdi → Amil
  | .mubtada => .ibtida
  | .fail => .fil
  | .maful | .mafulLahu => .nasib
  | .majrurBiHarf | .mudafIlayh => .jarr

def nisbaOf : Mawdi → Nisba
  | .mubtada | .fail => .isnadiyya
  | .maful | .mafulLahu | .majrurBiHarf => .taqyidiyya
  | .mudafIlayh => .idafiyya

/-- الإسنادُ رفعٌ: الفاعليّةُ والابتداء. -/
theorem isnad_raf (m : Mawdi) (h : nisbaOf m = .isnadiyya) : athar (amilOf m) = .raf := by
  cases m <;> simp_all [nisbaOf, amilOf, athar]

/-- التقييدُ نصبٌ أو جرٌّ بحرف: المفعوليّةُ والسببيّةُ (المفعولُ له) والمجرورُ بالحرف. -/
theorem taqyid_nasb (m : Mawdi) (h : nisbaOf m = .taqyidiyya) :
    athar (amilOf m) = .nasb ∨ (athar (amilOf m) = .jarr ∧ m = .majrurBiHarf) := by
  cases m <;> simp_all [nisbaOf, amilOf, athar]

/-- الإضافةُ جرٌّ بلا حرف. -/
theorem idafa_jarr (m : Mawdi) (h : nisbaOf m = .idafiyya) : athar (amilOf m) = .jarr ∧ m = .mudafIlayh := by
  cases m <;> simp_all [nisbaOf, amilOf, athar]

/-- السببيّةُ مفعولٌ له: تقييدٌ ونصب، والمسببيّةُ لا موضعَ إعرابٍ لها هنا. -/
theorem sababiyya : nisbaOf .mafulLahu = .taqyidiyya ∧ athar (amilOf .mafulLahu) = .nasb := by decide

/-- لا رابعةَ: كلُّ موضعٍ في واحدةٍ من الثلاث. -/
theorem nisab_three (m : Mawdi) :
    nisbaOf m = .isnadiyya ∨ nisbaOf m = .taqyidiyya ∨ nisbaOf m = .idafiyya := by
  cases m <;> simp [nisbaOf]

/-- الإسنادُ في التركيب (`Tarkib.Isnad`) يحتاج موضعًا إسناديًّا مرفوعًا: المبتدأُ أو الفاعل. -/
theorem isnad_has_raf_slot : ∃ m, nisbaOf m = .isnadiyya ∧ athar (amilOf m) = .raf :=
  ⟨.fail, rfl, rfl⟩

/-- الشاهدُ على الخانات: «زَيْدٌ» مرفوعًا ومنصوبًا ومجرورًا يقف على «زَيْدْ». -/
theorem zayd_pause :
    let z := [Ladder.atom 'ز' .fatha, Ladder.atom 'ي' .sukun, Ladder.atom 'د' .damma]
    Pause.pause (applyMark z .fatha) = Pause.pause z ∧ Pause.pause (applyMark z .kasra) = Pause.pause z := by
  exact ⟨pause_forgets_amil _ _ (by simp), pause_forgets_amil _ _ (by simp)⟩

end A116.Amil
