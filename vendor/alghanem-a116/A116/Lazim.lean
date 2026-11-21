import A116.Dalalat
import A116.Naql
import A116.LazimData

/-!
# جدولُ اللزوم من شبكة المعاجم: وجهُ التسمية والحملُ بشهادة ابن فارس (ADR ١٠١)

أمرُ المالك (2026-10-17): «جدول اللزوم من شبكة المعاجم: لم يُبدأ (خارطة الطريق). Lean اعمل».

## السند

* الدلالاتُ الثلاث `Dalalat` (ADR ٩٣)، ج3 س371: الالتزامُ «على لازمه… والمعتبر باللزوم هو اللزوم الذهني».
  ومسمّى اللفظ هناك مُدخَلٌ بلا مودَع (`MUSAMMA_IS_INPUT`).
* ابنُ فارس في «مقاييس اللغة» المختومة: لكلّ جذرٍ أصلٌ يحكم به (ADR ١٠٠، `Naql.Asl`). ثمّ يربط ألفاظَ الجذر بأصله بجملٍ
  صريحة صنفين:
  * **التعليل**: «والمِداد: ما يكتب به، لأنّه يُمَدُّ بالماء»، «ومنه تِلاوةُ القُرآن، لأنّه يُتْبِع آيةً بعد آية».
  * **الحمل**: «والمجاز قولهم خَشِيت بمعنى عَلِمت»، «ثمّ يُحمل عليه ما يقاربُه مجازاً وتشبيها»، «ثم يسمُّون العينَ
    الطَّرْف مجازاً».

## ما يُبنى

١. **وجهُ التسمية لازمٌ ذهنيٌّ مشهود** (`musamma`، `taalil_iltizam`):
   * جملةُ التعليل شهادةُ ابن فارس أنّ أصلَ الجذر لازمٌ ذهنيٌّ لمسمّى اللفظ.
   * فـ`Dalalat.dalala` على الأصل التزام.
   * وهذا الربطُ تعيينٌ معلَن (`TAALIL_AS_ILTIZAM_DECLARED`)، لا نصٌّ من ابن فارس بلفظ «اللزوم».
٢. **الحملُ ليس لزومًا** (`haml_la_iltizam`): ما سمّاه ابنُ فارس مجازًا أو شبّهه بكأنّ لا يُعدّ لازمًا للمسمّى. هو مادّةُ
   المجاز، وشهادتُه نقلٌ: مفهومُ وضعٍ ظنّيّ (`haml_mafhum_zanni`، ADR ١٠٤).
٣. **لا لزومَ بلا شهادة** (`la_lazim_bila_shahada`): لفظٌ لا جملةَ تعليلٍ فيه لا لازمَ له في الجدول — لا يُستنتج اللزومُ من
   انتسابه إلى الجذر.
٤. **اللازمُ المعيَّن له سندُه** (`lazim_muayyan`): إن تعيّن لازمُ لفظٍ ففي الجدول صفُّ تعليلٍ فيه اللفظ، وحكمُ القاعدة على
   جذره أصلٌ واحد أو كلمة أو أصولٌ عددُها واحد. والأصولُ اثنان فأكثر تُحتمل (`Naql.usul_muhtamal`).
٥. **المودَع** (`LazimData`، `corpora/naql/lawazim.tsv`): 1,210 جملةَ تعليلٍ و1,044 جملةَ حمل، والشواهدُ بأعيانها.
-/

namespace A116.Lazim

/-- صنفُ الجملة عند ابن فارس (`RULE_ILAQA` في `tools/gen_naql.py`؛ القاعدةُ معلنةٌ لم تُقَس على مرجعٍ محجوب). -/
inductive Ilaqa | taalil | haml
  deriving DecidableEq, Repr

def Ilaqa.ofString : String → Option Ilaqa
  | "taalil" => some .taalil
  | "haml" => some .haml
  | _ => none

/-- مسمّى اللفظ بشهادة ابن فارس: بالتعليل أصلُ الجذر لازمٌ ذهنيّ، وبالحمل لا لازم. -/
def musamma (w asl : String) : Ilaqa → Dalalat.Musamma
  | .taalil => ⟨[w], [asl], []⟩
  | .haml => ⟨[w], [], []⟩

/-- **وجهُ التسمية التزام**: لفظٌ غيرُ أصله، بجملة تعليل، يدلّ على الأصل التزامًا. -/
theorem taalil_iltizam (w asl : String) (h : w ≠ asl) :
    Dalalat.dalala true (musamma w asl .taalil) [asl] = some .iltizam := by
  have h' : asl ≠ w := fun e => h e.symm
  simp [Dalalat.dalala, musamma, h']

/-- **الحملُ ليس لزومًا**: ما حُمل على الأصل مجازًا لا يدلّ عليه التزامًا. -/
theorem haml_la_iltizam (w asl : String) (h : w ≠ asl) :
    Dalalat.dalala true (musamma w asl .haml) [asl] = none := by
  have h' : asl ≠ w := fun e => h e.symm
  simp [Dalalat.dalala, musamma, h']

/-- صفٌّ من الجدول: الجذر، وحكمُ ابن فارس، والصنف، والألفاظ. -/
structure Saff where
  jidhr : String
  hukm : Naql.Asl
  ilaqa : Ilaqa
  alfaz : List String
  deriving DecidableEq, Repr

/-- اللازمُ في الجدول: أوّلُ صفّ تعليلٍ فيه اللفظُ من جذره، ثمّ معناه بحكم ابن فارس (`Naql.nisba`). -/
def lazim (jadwal : List Saff) (jumla : String → String) (j w : String) :
    Iqtiran.Mantuq (String × Nat) :=
  match jadwal.find? (fun r => r.jidhr == j && r.ilaqa == .taalil && r.alfaz.contains w) with
  | some r => Naql.nisba r.hukm (jumla j)
  | none => .laHukm

/-- **لا لزومَ بلا شهادة**: لفظٌ لا صفَّ تعليلٍ له لا حكمَ للازمه. -/
theorem la_lazim_bila_shahada (jadwal : List Saff) (jumla : String → String) (j w : String)
    (h : ∀ r ∈ jadwal, r.jidhr = j → r.ilaqa = .taalil → w ∉ r.alfaz) :
    lazim jadwal jumla j w = .laHukm := by
  unfold lazim
  have : jadwal.find? (fun r => r.jidhr == j && r.ilaqa == .taalil && r.alfaz.contains w) = none := by
    rw [List.find?_eq_none]
    intro r hr
    cases hj : (r.jidhr == j) <;> cases hi : (r.ilaqa == Ilaqa.taalil) <;> simp_all
  rw [this]

/-- **اللازمُ المعيَّن من صفّ تعليلٍ بأصلٍ واحد**: إن تعيّن اللازمُ فله صفُّ تعليلٍ في الجدول، وحكمُه أصلٌ واحد أو كلمة أو
أصولٌ عددُها واحد. -/
theorem lazim_muayyan (jadwal : List Saff) (jumla : String → String) (j w : String) (m : String × Nat)
    (h : lazim jadwal jumla j w = .muayyan m) :
    ∃ r ∈ jadwal, r.jidhr = j ∧ r.ilaqa = .taalil ∧ w ∈ r.alfaz ∧
      (r.hukm = .wahid ∨ r.hukm = .kalima ∨ r.hukm = .usul 1) := by
  unfold lazim at h
  split at h
  · rename_i r hr
    have hm := List.find?_some hr
    have hmem := List.mem_of_find?_eq_some hr
    simp only [Bool.and_eq_true, beq_iff_eq, List.contains_iff_mem] at hm
    exact ⟨r, hmem, hm.1.1, hm.1.2, hm.2, Naql.la_takhmin_asl _ _ _ h⟩
  · cases h

/-- **الحملُ نقلٌ** (ADR ١٠٤): شهادةُ ابن فارس بالحمل («والمجاز قولهم خَشِيت بمعنى عَلِمت»، المدخل 987) خبرُ آحادٍ من
مودَع «وضع»، فهي مفهومُ وضعٍ ظنّيّ برتبة شهادتها؛ ووجودُ المسمّى بها «معلومة» بلا شاهد. -/
theorem haml_mafhum_zanni :
    Naql.jisrWad (fun _ => false) [⟨"f", "ibn-faris", .naql, .wad, 987⟩] =
      .mafhum .zanni ⟨"f", "ibn-faris", .naql, .wad, 987⟩ [] ∧
    Naql.jisrWaqi [⟨"f", "ibn-faris", .naql, .wad, 987⟩] = .maluma [] := by decide

/-! ## المودَع -/

/-- عددُ الأصول من حكم ابن فارس على الجذر في المودَع. -/
def adad (j : String) : Nat := ((LazimData.usul.find? (·.1 == j)).map (·.2.2.1)).getD 0

def saffOf (r : String × String × String × Nat × List String × String) : Option Saff :=
  (Ilaqa.ofString r.2.2.1).map fun k => ⟨r.1, Naql.Asl.ofString r.2.1 (adad r.1), k, r.2.2.2.2.1⟩

def jadwal : List Saff := LazimData.shawahid.filterMap saffOf

def jumla (j : String) : String := ((LazimData.usul.find? (·.1 == j)).map (·.2.2.2)).getD ""

/-- عددُ الجمل في المودَع. -/
theorem jumal_count : LazimData.bisinf = [1210, 1044] ∧ LazimData.biAslWahid = [910, 804] := by decide

/-- **الشواهد** على جدولٍ من صفوف الشواهد الستّة وحدَها (لا الجدول كلّه): المِداد والتِّلاوة والكِنْف لازمُها أصلُ
جذرها بعينه؛ و«خشيت» و«الشرب» حملٌ لا لازمَ لهما؛ و«الطرف» من أصلين حملٌ أيضًا. -/
theorem shawahid :
    lazim jadwal jumla "مدد" "المداد" = .muayyan (jumla "مدد", 1) ∧
    lazim jadwal jumla "تلو" "تلاوة" = .muayyan (jumla "تلو", 1) ∧
    lazim jadwal jumla "كنف" "الكنف" = .muayyan (jumla "كنف", 1) ∧
    lazim jadwal jumla "خشي" "خشيت" = .laHukm ∧
    lazim jadwal jumla "شرب" "الشرب" = .laHukm ∧
    (jadwal.filter (·.ilaqa == .haml)).map (·.jidhr) = ["خشي", "شرب", "طرف"] := by decide +kernel

/-- **والتزامُ المِداد على أصله**: «المداد» يدلّ على جملة ابن فارس في «مدد» التزامًا، لا تضمّنًا ولا مطابقة. -/
theorem midad_iltizam :
    Dalalat.dalala true (musamma "المداد" (jumla "مدد") .taalil) [jumla "مدد"] = some .iltizam :=
  taalil_iltizam _ _ (by decide +kernel)

end A116.Lazim
