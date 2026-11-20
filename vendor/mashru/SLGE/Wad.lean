import SLGE.Ladder2

/-!
# جبرُ العوامل: الإعرابُ والعواملُ والنواسخ والمعارف — على مودَع «قطر الندى»

**الدورُ (مصحَّح):** هذا جبرٌ في المدلول وحده (الإعرابُ والعواملُ نِسَبٌ ووظائف)، والقطرُ **شاهدٌ** عليه لا مصدرُه — ابنُ هشام، متن قطر الندى (OpenITI ‎0761JamalDinIbnHisham.MatnQatrNada.Shamela0011376-ara1‎).
كلُّ جدولٍ هنا منقولٌ بلفظه من أسطره المذكورة؛ والأسماءُ نصوصٌ لا حواملُ مشكولة (لا تشكيلَ من عندي).

**ما يُبرهَن (على المودَع وجدول الدور المعلَن):**
* **الانغلاق:** كلُّ عاملٍ في المودَع لا يُحدث في معموله إعرابًا خارجَ ما يقبله قسمُه.
* **الاستنفاد:** كلُّ (قسم، إعراب) ممكنٍ يُحدثه عاملٌ ما — لا خانةَ فارغة.
* **العلامةُ تعيّن القسم:** الجرُّ للاسم وحده، والجزمُ للفعل وحده، والحرفُ لا إعرابَ له.
* **النواسخُ ثلاثةٌ لا رابع:** أزواجُ (إعراب الاسم، إعراب الخبر) من {رفع، نصب} أربعة؛ الابتداءُ واحدٌ منها،
  والنواسخُ تستنفد الثلاثةَ الباقية بلا زيادة — وهو قولُ ابن هشام «ثلاثة أنواع» (L169).
* **أقلُّ الكلام:** المشتقُّ من جدول الدور (‎Cat.ifada_pairs‎) يطابق قولَ ابن هشام «وأقلُّ ائتلافه من اسمين … أو فعل واسم» (L73–74).
-/

namespace SLGE
namespace Wad

open Cat

inductive Irab | raf | nasb | jarr | jazm
  deriving DecidableEq, Repr

/-- **أنواع الإعراب أربعة** (L75–77): رفعٌ ونصبٌ في اسمٍ وفعل، وجرٌّ في اسم، وجزمٌ في فعل؛ و«جميعُ الحروف مبنيّة» (L71–72). -/
def irabOf : Kind → List Irab
  | .ism => [.raf, .nasb, .jarr]
  | .fil => [.raf, .nasb, .jazm]
  | .harf => []

def allIrab : List Irab := [.raf, .nasb, .jarr, .jazm]

/-- **العلامةُ تعيّن القسم:** الجرُّ للاسم وحده، والجزمُ للفعل وحده؛ والرفعُ والنصبُ مشتركان؛ والحرفُ بلا إعراب. -/
theorem irab_marks :
    (kinds.filter fun k => (irabOf k).contains .jarr) = [.ism] ∧
    (kinds.filter fun k => (irabOf k).contains .jazm) = [.fil] ∧
    (kinds.filter fun k => (irabOf k).contains .raf) = [.ism, .fil] ∧
    (kinds.filter fun k => (irabOf k).contains .nasb) = [.ism, .fil] ∧
    irabOf .harf = [] ∧
    allIrab.all (fun r => kinds.any fun k => (irabOf k).contains r) = true := by decide

/-- عاملٌ في المودَع: اسمُه، وقسمُه، والسطر، وما يُحدثه في معمولاته (قسمُ المعمول، إعرابُه). -/
structure Amil where
  name : String
  kind : Option Kind   -- ‎none‎: عاملٌ معنويّ
  line : Nat
  eff : List (Kind × Irab)
  deriving Repr

def fam (names : List String) (k : Option Kind) (line : Nat) (eff : List (Kind × Irab)) : List Amil :=
  names.map fun n => ⟨n, k, line, eff⟩

/-- حروفُ الجرّ (L338–339): المشتركُ سبعة، والمختصُّ بالظاهر سبعة. -/
def jarrF : List Amil :=
  fam ["من", "إلى", "عن", "على", "في", "اللام", "الباء"] (some .harf) 338 [(.ism, .jarr)] ++
  fam ["رب", "مذ", "منذ", "الكاف", "حتى", "واو القسم", "تاء القسم"] (some .harf) 339 [(.ism, .jarr)]

/-- الإضافة (L339–342): معنويّةٌ ولفظيّة — المضافُ يجرّ المضافَ إليه. -/
def idafaF : List Amil := fam ["الإضافة المعنوية", "الإضافة اللفظية"] (some .ism) 340 [(.ism, .jarr)]

/-- نواصبُ المضارع (L96–100). -/
def nasbF : List Amil := fam ["لن", "كي", "إذن", "أن"] (some .harf) 96 [(.fil, .nasb)]

/-- جوازمُ فعلٍ واحد (L112–114). -/
def jazm1F : List Amil := fam ["لم", "لما", "لام الطلب", "لا الطلبية"] (some .harf) 112 [(.fil, .jazm)]

/-- جوازمُ فعلين (L115)، بلفظ النصّ (وفيه «إذ» و«إذما» كما رُسما). -/
def jazm2F : List Amil :=
  fam ["إن", "إذ", "إذما", "أي", "أين", "أنى", "أيان", "متى", "مهما", "من", "ما", "حيثما"] none 115
    [(.fil, .jazm), (.fil, .jazm)]

/-- النواسخ، النوعُ الأوّل (L170): ترفع الاسمَ وتنصب الخبر. -/
def kanaF : List Amil :=
  fam ["كان", "أمسى", "أصبح", "أضحى", "ظل", "بات", "مازال", "ما فتئ", "ما انفك", "ما برح", "ما دام"]
    (some .fil) 170 [(.ism, .raf), (.ism, .nasb)]

/-- العاملاتُ عملَ ليس (L181–185). -/
def laysaF : List Amil := fam ["ما الحجازية", "لا النافية", "لات"] (some .harf) 181 [(.ism, .raf), (.ism, .nasb)]

/-- النوعُ الثاني (L187–188): تنصب الاسمَ وترفع الخبر؛ ومثلُها لا النافيةُ للجنس (L201). -/
def innaF : List Amil :=
  fam ["إن", "أن", "لكن", "كأن", "ليت", "لعل"] (some .harf) 187 [(.ism, .nasb), (.ism, .raf)] ++
  fam ["لا النافية للجنس"] (some .harf) 201 [(.ism, .nasb), (.ism, .raf)]

/-- النوعُ الثالث (L208): القلبيّات تنصبهما مفعولين. -/
def zannaF : List Amil :=
  fam ["ظن", "رأى", "حسب", "درى", "خال", "زعم", "وجد", "علم"] (some .fil) 208 [(.ism, .nasb), (.ism, .nasb)]

/-- الفعلُ يرفع الفاعلَ (L219) وينصب المفاعيلَ الخمسة (L267) والحالَ والتمييز والمستثنى (L307–326). -/
def filF : List Amil := fam ["الفعل التام"] (some .fil) 219 [(.ism, .raf), (.ism, .nasb)]

/-- ما يعمل عملَ فعله سبعة (L347–372). -/
def amalF : List Amil :=
  fam ["اسم الفعل", "المصدر", "اسم الفاعل", "المثال", "اسم المفعول", "الصفة المشبهة", "اسم التفضيل"]
    (some .ism) 347 [(.ism, .raf), (.ism, .nasb)]

/-- العاملان المعنويّان: الابتداءُ (المبتدأُ والخبر مرفوعان، L152)، والتجرّدُ (يُرفع المضارعُ خاليًا من ناصبٍ وجازم، L96). -/
def manawiF : List Amil :=
  [⟨"الابتداء", none, 152, [(.ism, .raf), (.ism, .raf)]⟩, ⟨"التجرد", none, 96, [(.fil, .raf)]⟩]

def awamil : List Amil :=
  jarrF ++ idafaF ++ nasbF ++ jazm1F ++ jazm2F ++ kanaF ++ laysaF ++ innaF ++ zannaF ++ filF ++ amalF ++ manawiF

/-- **المودَعُ كما نُقل:** 14 جارًّا، وإضافتان، و4 نواصب، و4 جوازم لفعل، و12 لفعلين، و11 من كان،
و3 كليس، و7 كإنّ، و8 قلبيّات، والفعل، و7 تعمل عملَ فعلها، ومعنويّان — 75 مدخلًا. -/
theorem awamil_table :
    jarrF.length = 14 ∧ idafaF.length = 2 ∧ nasbF.length = 4 ∧ jazm1F.length = 4 ∧ jazm2F.length = 12 ∧
    kanaF.length = 11 ∧ laysaF.length = 3 ∧ innaF.length = 7 ∧ zannaF.length = 8 ∧ filF.length = 1 ∧
    amalF.length = 7 ∧ manawiF.length = 2 ∧ awamil.length = 75 := by decide

/-- **الانغلاق:** لا عاملَ يُحدث في معموله إعرابًا لا يقبله قسمُه. -/
theorem closure : awamil.all (fun a => a.eff.all fun (k, r) => (irabOf k).contains r) = true := by decide

/-- **الاستنفاد:** كلُّ (قسم، إعراب) يقبله القسمُ يُحدثه عاملٌ من المودَع. -/
theorem exhaust : kinds.all (fun k => (irabOf k).all fun r =>
    awamil.any fun a => a.eff.contains (k, r)) = true := by decide

/-- **الحرفُ لا يكون معمولًا ولا تُعرَب كلمتُه، ويعمل:** الجرُّ والنصبُ والجزمُ وإنّ وأخواتُها من الحروف. -/
theorem harf_governs : (awamil.all fun a => a.eff.all fun (k, _) => k != .harf) = true ∧
    (awamil.filter fun a => a.kind == some .harf).length = 32 := by decide

/-! ## النواسخُ ثلاثةٌ لا رابع -/

/-- أزواجُ الجملة الاسميّة: (إعرابُ الاسم/المبتدأ، إعرابُ الخبر). -/
def pairOf (a : Amil) : Option (Irab × Irab) :=
  match a.eff with
  | [(.ism, r1), (.ism, r2)] => some (r1, r2)
  | _ => none

def rn : List Irab := [.raf, .nasb]

def nawasikh : List Amil := kanaF ++ laysaF ++ innaF ++ zannaF

/-- **الأزواجُ الممكنة أربعة؛ الابتداءُ أحدُها؛ والنواسخُ تُحدث الثلاثةَ الباقية بعينها — فلا رابع.** -/
theorem nawasikh_three :
    ((rn.flatMap fun a => rn.map fun b => (a, b)).filter fun p =>
        nawasikh.any fun n => pairOf n == some p) = [(.raf, .nasb), (.nasb, .raf), (.nasb, .nasb)] ∧
    pairOf ⟨"الابتداء", none, 152, [(.ism, .raf), (.ism, .raf)]⟩ = some (.raf, .raf) ∧
    (nawasikh.all fun n => pairOf n != some (.raf, .raf)) = true ∧
    (nawasikh.all fun n => match pairOf n with | some (a, b) => rn.contains a && rn.contains b | none => false) = true := by
  decide

/-! ## أقلُّ الكلام: المشتقُّ يطابق المودَع -/

/-- قولُ ابن هشام (L73–74): «وأقلُّ ائتلافه من اسمين … أو فعل واسم». -/
def qatrMin : List (List Kind) := [[.ism, .ism], [.fil, .ism]]

def norm : List Kind → List Kind
  | [.ism, .fil] => [.fil, .ism]
  | l => l

/-- **الأزواجُ المفيدة المشتقّة من جدول الدور، بلا ترتيب، هي ما في القطر بعينه.** -/
theorem kalam_min_matches :
    (((kinds.flatMap fun a => kinds.map fun b => [a, b]).filter ifada).map norm).eraseDups = qatrMin := by
  decide

/-! ## المعارفُ والإشارةُ والموصول والفعل -/

/-- المعرفةُ ستّة (L123–150)، مرتّبةً بـ«ثمّ». -/
def maarif : List String := ["الضمير", "العلم", "الإشارة", "الموصول", "ذو الأداة", "المضاف"]

/-- أسماءُ الإشارة (L132–134). -/
def ishara : List String := ["ذا", "ذي", "ذه", "تي", "ته", "تا", "ذان", "تان", "أولاء"]

/-- الموصولات (L137–140). -/
def mawsul : List String :=
  ["الذي", "التي", "اللذان", "اللتان", "الذين", "الألى", "اللائي", "اللاتي", "من", "ما", "أي", "أل", "ذو", "ذا"]

/-- المفاعيلُ خمسة (L267–301)، والتوابعُ خمسة (L375–409)، وموانعُ الصرف تسعة (L419–421). -/
def mafail5 : List String := ["المفعول به", "المفعول المطلق", "المفعول له", "المفعول فيه", "المفعول معه"]
def tawabi5 : List String := ["النعت", "التوكيد", "عطف البيان", "عطف النسق", "البدل"]
def mawani9 : List String := ["الوزن", "التركيب", "العجمة", "التعريف", "العدل", "الوصف", "الجمع", "الزيادة", "التأنيث"]

/-- الفعلُ ثلاثة (L53–69)، وحروفُ المضارعة ‎نأيت‎ (L65). -/
def afal : List String := ["ماض", "أمر", "مضارع"]
def nayta : List Nat := [14, 0, 11, 18]

theorem wad_counts :
    maarif.length = 6 ∧ ishara.length = 9 ∧ mawsul.length = 14 ∧ mafail5.length = 5 ∧
    tawabi5.length = 5 ∧ mawani9.length = 9 ∧ afal.length = 3 := by decide

/-- **حروفُ المضارعة وحدةٌ مرخَّصة سابقًا:** ‎نأيت‎ كلُّها من حروف الزيادة ‎سألتمونيها‎ ومن الأحاديّ عند المرادي. -/
theorem nayta_augs : nayta.all (fun c => Law.augs.contains c) = true ∧
    nayta.all (fun c => Law.harf1.contains [c]) = true := by decide

/-- **ذا** إشارةٌ وموصول (بعد ما ومَن الاستفهاميّتين): الدالُّ الواحد في قسمين — فالقسمُ دالٌّ مع وضعه. -/
theorem dha_two : ishara.contains "ذا" = true ∧ mawsul.contains "ذا" = true ∧
    mawsul.contains "من" = true ∧ jazm2F.any (·.name == "من") = true := by decide

end Wad
end SLGE
