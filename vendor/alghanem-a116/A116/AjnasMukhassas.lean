import A116.HukmMuwahhad
import A116.Naql

/-!
# شجرةُ الأجناس من «المخصَّص»: الجنسُ تحت كتابه بشهادة ابن سيده، والقابليّةُ موروثة (ADR ١٠٤)

أمرُ المالك (2026-10-18): «شجرة الأجناس لم تُربط بالمخصَّص … اعمل lean الجنس واستعمل شواهد من المخصص لا يحتاج تواتر
ايضا».

## السند

* «المخصَّص» المختوم (`corpora/mukhassas/`، `MUKHASSAS_SHA256`): كلُّ بابٍ تحت كتابه، والسطرُ رأسُ الباب بعينه
  (`corpora/mukhassas/nodes.tsv`). مثالُه: «### $ 3 - (الكلاب وإرادتها)» (س26981) في «كتاب السباع».
* «التفكير» المختوم س23: «العقل غير موجود إلا عند الإنسان».

## ما يُبنى

١. **الشجرة** (`abb`): الجنسُ ← كتابُه في المخصَّص، بصفٍّ من `corpora/mukhassas/ajnas.tsv`. الصفُّ شهادةُ نقلٍ من مودَع
   «وضع» برتبتها، فهو مفهومُ وضعٍ ظنّيّ (`wad_mafhum`، ADR ١٠٤: لا يُشترط التواتر).
٢. **القابليّة على الكتاب** (`qKitab`): «كتاب خلق الإنسان» يعقل بنصّ التفكير س23، وسائرُ الكتب المسمّاة هنا لا تعقل بحصره
   («إلا عند الإنسان»). والحصرُ على الكتب الخمسة المسمّاة معلَن (`HASR_ON_BOOKS_DECLARED`).
٣. **الوراثة** (`HukmMuwahhad.maurutha`): الجنسُ يرث كتابَه.
   * «الكلب» تحت «كتاب السباع» لا يعقل بالوراثة، بشهادة ابن سيده. وكان في `Khawass` بإعلان المالك (`KALB_ISA_DECLARED`)،
     فصار بشاهدٍ مودَع.
   * وما لا صفَّ له «لا حكم».
٤. **الموافقة** (`muwafiq_khawass`): على الأجناس المشتركة يوافق الحكمُ `Khawass.aqilOf`.
-/

namespace A116.AjnasMukhassas

open A116.HukmMuwahhad (Shajara maurutha)

/-- صفُّ الجنس: الجنس، ورقمُ العقدة، وسطرُها في المخصَّص المختوم، وكتابُه. -/
structure Saff where
  jins : String
  uqda : Nat
  satr : Nat
  kitab : String
  deriving DecidableEq, Repr

/-- الصفوف (`corpora/mukhassas/ajnas.tsv`). -/
def sufuf : List Saff :=
  [⟨"الإنسان", 3, 383, "كتاب خلق الإنسان"⟩,
   ⟨"الكلب", 994, 26981, "كتاب السباع"⟩,
   ⟨"الحيات", 1043, 27666, "كتاب الحشرات"⟩,
   ⟨"النمل", 1054, 27983, "كتاب الحشرات"⟩,
   ⟨"الإبل", 867, 24783, "كتاب الإبل"⟩,
   ⟨"الحجر", 1268, 35551, "كتاب الدهور والأزمنة والأهوية والرياح"⟩]

/-- الشجرة: الجنسُ ← كتابُه. -/
def abb : Shajara := fun j => (sufuf.find? (·.jins == j)).map (·.kitab)

/-- العقلُ على الكتاب: نصُّ التفكير س23 للإنسان، وحصرُه لما سواه من الكتب المسمّاة. -/
def qKitab : String → Option Bool
  | "كتاب خلق الإنسان" => some true
  | "كتاب السباع" | "كتاب الحشرات" | "كتاب الإبل"
  | "كتاب الدهور والأزمنة والأهوية والرياح" => some false
  | _ => none

/-- العقلُ الموروث: الجنسُ يرث كتابَه. -/
def aqil (j : String) : Option Bool := maurutha abb 1 qKitab j

/-- **الوراثةُ من الكتاب** (`decide`): الإنسانُ يعقل، والكلبُ والحيّاتُ والنملُ والإبلُ والحجرُ لا تعقل، والغولُ لا حكم. -/
theorem wiratha :
    aqil "الإنسان" = some true ∧ aqil "الكلب" = some false ∧ aqil "الحيات" = some false ∧
    aqil "النمل" = some false ∧ aqil "الإبل" = some false ∧ aqil "الحجر" = some false ∧
    aqil "الغول" = none := by decide

/-- **الموافقة**: على الأجناس المشتركة يوافق الحكمُ `Khawass.aqilOf`. -/
theorem muwafiq_khawass :
    ["الإنسان", "الكلب", "الحيات", "النمل", "الحجر"].all (fun j => aqil j == Khawass.aqilOf j) = true := by
  decide

/-- **صفُّ الجنس شهادةُ وضعٍ ظنّيّة** (ADR ١٠٤): «الكلب» تحت «كتاب السباع» بسطر المخصَّص مفهومٌ ظنّيّ بشاهدٍ واحد. -/
theorem wad_mafhum :
    Naql.jisrWad (fun _ => false) [⟨"mukhassas", "ibn-sida", .naql, .wad, 26981⟩] =
      .mafhum .zanni ⟨"mukhassas", "ibn-sida", .naql, .wad, 26981⟩ [] := by decide

/-- **الحكمُ الموحَّد على الشجرة**: «الكلبُ يُخاطَب» على شجرة المخصَّص مجازٌ بالتشبيه، و«الإنسانُ يتكلّم» حقيقة. -/
theorem hukm_ala_shajara :
    HukmMuwahhad.hukm abb 1 qKitab (Khawass.sighaLink .ismMafool .mafool) HukmMuwahhad.tashbih "الكلب"
      = .majaz ∧
    HukmMuwahhad.hukm abb 1 qKitab (Khawass.sighaLink .filMaloom .faail) HukmMuwahhad.tashbih "الإنسان"
      = .haqiqa ∧
    HukmMuwahhad.hukm abb 1 qKitab .haqiqa HukmMuwahhad.tashbih "الغول" = .laHukm := by decide

end A116.AjnasMukhassas
