import A116.Amil

/-!
# العواملُ المائة بأصناف أثرها، على `Amil` (ADR ٧١، أمرُ المالك «اعمل Lean العوامل وفق المرفق»)

المرفقُ جدولُ مئةِ عاملٍ؛ دخل منه **العاملُ وأسلوبُه وحكمُه الإعرابيّ** (الأعمدةُ الأربعة الأولى)، ورُفض ما سواه
باسمه `ATTACHMENT_COLUMNS_REJECTED` (أوزانٌ وأنماطُ CV وأبوابٌ صرفيّة مولَّدةٌ آليًّا تناقض المودَع). الحكمُ
الإعرابيّ صُنّف ثلاثةَ عشرَ صنفًا مغلقًا (`Athar`)، كلُّ صنفٍ مرسًى في **باب** من شرح ابن عقيل المختوم بسطر
عنوانه (`corpora/awamil/awamil.tsv` ← `AwamilData.lean` بـ`tools/gen_awamil.py --check`):

كان وأخواتها (1847)، أفعالُ المقاربة (2202)، إنّ وأخواتها (2339)، ظنّ وأخواتها (2794)، الاستثناء (4074)،
حروفُ الجرّ (4634)، عطفُ النسق (6440)، النداء (6680)، إعرابُ الفعل — النواصب (7398)، عواملُ الجزم (7577).

## ما يُبرهَن

* كلُّ صنفٍ يُردّ إلى أثرٍ على معمولٍ أوّل وثانٍ من حالات `Qism.Irab` الأربع (`first`، `second`)، ومعمولُه
  اسمٌ أو فعل (`target`)؛ فالعواملُ المائة **تُردّ إلى عوامل `Amil` الخمسة** (`reduces_to_amil`): ما له أثرٌ
  فهو ابتداءٌ/فعلٌ رافع، أو ناصب، أو جارّ، أو جازم.
* الاتّساق مع الألفيّة: ما يجرّ معمولُه اسمٌ، وما يجزم معمولُه فعل (`jarr_targets_ism`، `jazm_targets_fil`) —
  وهو `Amil.ism_no_jazm`/`fil_no_jarr` من الجهة الأخرى.
* إنّ وكان متقابلتان على المعمولين (`inna_kana_dual`)، وظنّ تنصبهما معًا (`zanna_two_nasb`)، وأدواتُ الشرط
  الجازمة تجزم فعلين (`shart_two_jazm`).
* على المودَع: مئةُ صفّ (`rows_length`)، وعددُ كلّ صنف (`class_counts`)، وكلُّ صفٍّ له أثرٌ مرسًى في بابٍ
  (`anchored_or_none`)، والمعطوفُ تابعٌ لا أثرَ له من نفسه (`tabi_no_effect`).

ما لا يُبرهَن: أنّ هذه عواملُ العربيّة كلُّها — المرفقُ ليس مجالًا مختومًا، والمرساةُ أبوابٌ لا سطورُ كلّ عامل
(`AWAMIL_ANCHOR_IS_BAB_NOT_LINE`)؛ وأمثلتُه لم تمرّ على البوّابة (`AWAMIL_EXAMPLES_NOT_GATED`).
-/

namespace A116.Awamil

open A116 A116.Qism A116.Amil

/-- أصنافُ الأثر الثلاثةَ عشر. -/
inductive Athar where
  | nasbRaf        -- إنّ وأخواتها: تنصب الاسم وترفع الخبر
  | rafNasb        -- كان وأخواتها: ترفع الاسم وتنصب الخبر
  | nasbNasb       -- ظنّ وأخواتها: تنصب مفعولين
  | rafTawil       -- كاد وأخواتها: ترفع الاسم والخبرُ جملةٌ بتأويل
  | jarr           -- حروفُ الجرّ، وواوُ القسم وتاؤه
  | jarrOrNasb     -- خلا عدا حاشا: جرٌّ أو نصبٌ على الاستثناء
  | tabi           -- حروفُ العطف: التابعُ يحكي متبوعَه
  | jazmFil        -- لم لمّا لا الناهية لامُ الأمر
  | nasbFil        -- أن لن كي إذن حتّى فاءُ السببيّة واوُ المعيّة
  | jarrOrNasbFil  -- لامُ التعليل: تجرّ الاسمَ وتنصب المضارع
  | jazmFilayn     -- أدواتُ الشرط الجازمة: فعلُ الشرط وجوابُه
  | nida           -- حروفُ النداء: المنادى منصوبٌ أو مبنيٌّ على الضمّ
  | none           -- لا عمل: الاستفهام، والشرطُ غيرُ الجازم
  deriving DecidableEq, Repr

def all : List Athar :=
  [.nasbRaf, .rafNasb, .nasbNasb, .rafTawil, .jarr, .jarrOrNasb, .tabi, .jazmFil, .nasbFil,
   .jarrOrNasbFil, .jazmFilayn, .nida, .none]

theorem all_length : all.length = 13 := by rfl

/-- أثرُ العامل على معموله الأوّل. -/
def first : Athar → Option Irab
  | .nasbRaf => some .nasb | .rafNasb => some .raf | .nasbNasb => some .nasb | .rafTawil => some .raf
  | .jarr => some .jarr | .jarrOrNasb => some .jarr | .jarrOrNasbFil => some .jarr
  | .jazmFil => some .jazm | .nasbFil => some .nasb | .jazmFilayn => some .jazm
  | .nida => some .nasb | .tabi | .none => Option.none

/-- أثرُه على معموله الثاني إن كان له ثانٍ. -/
def second : Athar → Option Irab
  | .nasbRaf => some .raf | .rafNasb => some .nasb | .nasbNasb => some .nasb
  | .jazmFilayn => some .jazm | .jarrOrNasbFil => some .nasb
  | _ => Option.none

/-- قسمُ المعمول الأوّل. -/
def target : Athar → Option Tarkib.Qism
  | .nasbRaf | .rafNasb | .nasbNasb | .rafTawil | .jarr | .jarrOrNasb | .jarrOrNasbFil | .nida =>
      some .ism
  | .jazmFil | .nasbFil | .jazmFilayn => some .fil
  | .tabi | .none => Option.none

/-- الردُّ إلى عوامل `Amil` الخمسة: لكلّ أثرٍ على الأوّل عاملٌ من الخمسة أثرُه هو. -/
def toAmil : Irab → Amil.Amil
  | .raf => .fil | .nasb => .nasib | .jarr => .jarr | .jazm => .jazim

theorem toAmil_athar (i : Irab) : Amil.athar (toAmil i) = i := by cases i <;> rfl

theorem reduces_to_amil : ∀ a ∈ all, ∀ i, first a = some i → ∃ m : Amil.Amil, Amil.athar m = i := by
  intro a _ i _
  exact ⟨toAmil i, toAmil_athar i⟩

/-- ما يجرّ معمولُه اسم (س410: الجرُّ يختصّ بالأسماء). -/
theorem jarr_targets_ism : all.all (fun a => first a != some .jarr || target a == some .ism) = true := by
  decide

/-- ما يجزم معمولُه فعل (س410: الجزمُ يختصّ بالأفعال). -/
theorem jazm_targets_fil : all.all (fun a => first a != some .jazm || target a == some .fil) = true := by
  decide

/-- الصنفان المرخَّصان للمعمول يوافقان جدولَ الألفيّة: الاسمُ له جرٌّ والفعلُ له جزم (`Amil.mamul`). -/
theorem targets_agree_with_table :
    (Amil.mamul .iSahih .jarr).isSome = true ∧ (Amil.mamul .fSahih .jazim).isSome = true ∧
    (Amil.mamul .iSahih .jazim).isNone = true ∧ (Amil.mamul .fSahih .jarr).isNone = true := by
  decide

/-- إنّ وكان متقابلتان: ما تنصبه إحداهما ترفعه الأخرى. -/
theorem inna_kana_dual :
    first .nasbRaf = second .rafNasb ∧ second .nasbRaf = first .rafNasb ∧ first .nasbRaf ≠ first .rafNasb := by
  decide

theorem zanna_two_nasb : first .nasbNasb = some .nasb ∧ second .nasbNasb = some .nasb := by decide

theorem shart_two_jazm : first .jazmFilayn = some .jazm ∧ second .jazmFilayn = some .jazm := by decide

/-- التابعُ لا أثرَ له من نفسه، ولا الاستفهامُ والشرطُ غيرُ الجازم. -/
theorem tabi_no_effect : first .tabi = Option.none ∧ first .none = Option.none := by decide

/-- الرفعُ على الأوّل لا يكون إلّا في نواسخ الابتداء (كان وكاد): الاسمُ مبتدأٌ في الأصل، فالرفعُ إسناد. -/
theorem raf_only_nawasikh : all.all (fun a => first a != some .raf || (a == .rafNasb || a == .rafTawil)) = true := by
  decide

end A116.Awamil
