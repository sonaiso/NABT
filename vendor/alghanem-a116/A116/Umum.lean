import A116.Khawass
import A116.Ihala
import A116.Mudari

/-!
# حروفُ «أنيت» بالمتكلّم والمخاطب، وعمومُ النكرة في سياق النفي (ADR ٩٧، أمرُ المالك 2026-10-17)

من نقد المرفق السابق (ADR ٩٦، الجواب): بقي فيه أمران صالحان — حروفُ المضارعة حين يُربط الاشتقاقُ بالمتكلّم والمخاطب،
وعمومُ النكرة في سياق النفي بشرطه «إلّا إذا خُصّصت» لا «قطعيًّا». وأمر المالك: «اعمل Lean».

## السند (الأسطرُ 1-based)

شرحُ السيرافيّ (Sham19Y0017726):
* س48515–48516: «نحو الألف للمتكلّم والنون للجماعة والتاء للمخاطب والياء للغائب».
* س45472–45473: «والهمزة والياء يدخلان في أوّل الفعل المضارع للمتكلّم والغائب كقولك أذهب ويذهب».
* س69188–69189: «التاء في أوّل الفعل المستقبل علامةٌ للمخاطب أو للمؤنّثة الغائبة».
* س28920: «لأنّ "أحدًا" وُضع لما يعقل».

الشخصيّة ج3:
* س650: «العمومُ الثابتُ باللفظ، إمّا أن يثبت لغةً وهو المستفادُ من وضع اللغة…».
* س652: «فإنّ النكرةَ في سياق النفي تعمّ سواءٌ باشرها النفيُ نحو ما أحدٌ قائم أم باشر عاملَها نحو ما قام أحد، وسواءٌ كان
  النافي ما أم لم أم لن أم ليس أم غيرها. وكذلك الفعلُ المتعدّي المنفيّ فهو يعمّ جميعَ مفعولاته كقولك والله لا آكل… إلّا إذا
  خصَّصت»؛ و«والداخلُ على اسم الجنس من أل والإضافة يعمّ المفردات، وعلى الجمع يعمّ الجموع».
* س462: «لأنّ الباقي بعد التخصيص يتعيّن فيُعرف».
* س675: «التخصيصُ بالاستثناء هو إخراجُ ما بعد إلّا أو إحدى أخواتها ممّا قبلها».

## ما يُبنى

* الحرفُ يعيّن الشخصَ إلّا التاء فمشتركةٌ بين المخاطب والغائبة؛ فالاشتقاقُ من الشخص دالّةٌ والاسترجاعُ علاقة، والحضورُ
  (`Ihala.Hudur`) مع التاء يحتاج قرينة، والغائبُ وحدَه يحتاج مفسِّرًا في النصّ.
* العمومُ ثابتٌ بقرينته (أل، الإضافة، النفي)، لا يتغيّر بالنافي ولا بموضع مباشرته، ويرتفع بالتخصيص إلى «الباقي»، والباقي
  متعيّنٌ جامعًا مانعًا؛ والنكرةُ في الإثبات بلا أل ولا إضافة «لا حكم» في العموم من هذا السطر.
-/

namespace A116.Umum

/-! ## ١. حروفُ «أنيت» والشخص -/

inductive Harf | hamza | nun | ya | ta
  deriving DecidableEq, Repr

def harfChar : Harf → Char
  | .hamza => 'ء' | .nun => 'ن' | .ya => 'ي' | .ta => 'ت'

/-- الحروفُ الأربعة هي «أنيت» في `Mudari` بعينها. -/
theorem anayt_harf : [Harf.hamza, .nun, .ya, .ta].map harfChar = Mudari.anayt := by decide

/-- الشخص بألفاظ السيرافيّ: المتكلّم، والجماعة، والمخاطب، والغائب، والمؤنّثة الغائبة. -/
inductive Shakhs | mutakallim | jamaa | mukhatab | ghaib | ghaiba
  deriving DecidableEq, Repr

/-- ما يدلّ عليه الحرف (س48515–48516، س69188–69189). -/
def dalala : Harf → List Shakhs
  | .hamza => [.mutakallim]
  | .nun => [.jamaa]
  | .ya => [.ghaib]
  | .ta => [.mukhatab, .ghaiba]

/-- الاشتقاقُ من الشخص إلى الحرف: دالّة. -/
def harfOf : Shakhs → Harf
  | .mutakallim => .hamza
  | .jamaa => .nun
  | .mukhatab | .ghaiba => .ta
  | .ghaib => .ya

/-- **الاشتقاقُ سليم**: حرفُ كلّ شخصٍ يدلّ عليه. -/
theorem harfOf_salim (s : Shakhs) : s ∈ dalala (harfOf s) := by cases s <;> decide

/-- **والاسترجاعُ تامّ**: كلُّ ما يدلّ عليه الحرفُ حرفُه هو. -/
theorem dalala_tamm (h : Harf) (s : Shakhs) (hs : s ∈ dalala h) : harfOf s = h := by
  cases h <;> simp [dalala] at hs <;> rcases hs with rfl | rfl <;> rfl

/-- **الحرفُ يعيّن الشخصَ إلّا التاء.** -/
theorem yuayyin_illa_ta (h : Harf) : (dalala h).length = 1 ↔ h ≠ .ta := by cases h <;> decide

/-- فالاسترجاعُ من الحرف ليس دالّة: للتاء شخصان والاشتقاقُ يرسلهما إليها. -/
theorem ta_mushtarak : harfOf .mukhatab = harfOf .ghaiba ∧ Shakhs.mukhatab ≠ .ghaiba := by decide

/-- الحضور: المتكلّمُ والجماعةُ متكلّم (`NUN_JAMAA_IS_MUTAKALLIM_DECLARED`)، والمخاطبُ مخاطب، والغائبُ والغائبةُ غائب. -/
def hudurOf : Shakhs → Ihala.Hudur
  | .mutakallim | .jamaa => .mutakallim
  | .mukhatab => .mukhatab
  | .ghaib | .ghaiba => .ghaib

/-- الحضورُ من الحرف وقرينة: يتعيّن بالحرف إن دلّ على شخصٍ واحد، وإلّا بقرينةٍ من دلالته، وإلّا `none`. -/
def hudurQ (h : Harf) (qarina : Option Shakhs) : Option Ihala.Hudur :=
  match dalala h with
  | [s] => some (hudurOf s)
  | ss => match qarina with
    | some q => if ss.contains q then some (hudurOf q) else none
    | none => none

/-- «أذهب» متكلّم، و«يذهب» غائب، و«تذهب» وحدَها «لا حكم»، وبقرينة المؤنّثة الغائبة غائب. -/
theorem shawahid_hudur :
    hudurQ .hamza none = some .mutakallim ∧ hudurQ .ya none = some .ghaib ∧
    hudurQ .ta none = none ∧ hudurQ .ta (some .ghaiba) = some .ghaib ∧
    hudurQ .ta (some .mukhatab) = some .mukhatab ∧ hudurQ .ta (some .mutakallim) = none := by decide

/-- **قراءتا التاء تفترقان في الحاجة إلى المفسِّر**: الغائبةُ تحتاجه في النصّ والمخاطبُ لا (`Ihala.mufassirFiNass`). -/
theorem ta_mufassir :
    Ihala.mufassirFiNass (hudurOf .ghaiba) = true ∧ Ihala.mufassirFiNass (hudurOf .mukhatab) = false := by decide

/-- والياءُ وحدَها تحتاج مفسِّرًا، والهمزةُ والنونُ لا. -/
theorem ya_wahdaha : ∀ h ∈ [Harf.hamza, .nun, .ya],
    (dalala h).all (fun s => Ihala.mufassirFiNass (hudurOf s)) = (h == .ya) := by decide

/-! ## ٢. العموم -/

/-- النافي: «ما، لم، لن، ليس، أم غيرها»؛ و«لا» من مثاله «والله لا آكل». -/
inductive Nafi | ma | lam | lan | laysa | la | ghayruha
  deriving DecidableEq, Repr

/-- «سواءٌ باشرها النفيُ… أم باشر عاملَها». -/
inductive Mubashara | nafsuha | amiluha
  deriving DecidableEq, Repr

/-- ما يتناوله العموم: المفردات، والجموع، والمفعولات، وأفرادُ النكرة. -/
inductive Tanawul | mufradat | jumu | mafulat | afrad
  deriving DecidableEq, Repr

/-- القرينةُ وسياقُها. -/
inductive Qarina
  | alJins | alJam | idafaJins | idafaJam           -- الإثبات: «أل» والإضافة
  | nakiraNafy (n : Nafi) (m : Mubashara)            -- النفي: النكرة
  | filManfi (n : Nafi)                              -- النفي: الفعلُ المتعدّي
  | nakiraIthbat                                      -- الإثبات بلا أل ولا إضافة
  deriving DecidableEq, Repr

inductive Umum | aamm (t : Tanawul) | baqi (t : Tanawul) | laHukm
  deriving DecidableEq, Repr

/-- ما تتناوله القرينة، أو `none`. -/
def tanawul : Qarina → Option Tanawul
  | .alJins | .idafaJins => some .mufradat   -- «يعمّ المفردات»
  | .alJam | .idafaJam => some .jumu         -- «وعلى الجمع يعمّ الجموع»
  | .nakiraNafy _ _ => some .afrad           -- «النكرةُ في سياق النفي تعمّ»
  | .filManfi _ => some .mafulat             -- «يعمّ جميعَ مفعولاته»
  | .nakiraIthbat => none

/-- العموم: عامٌّ بقرينته، وبالتخصيص «الباقي» (س652 «إلّا إذا خصَّصت»، س675)، وبلا قرينة «لا حكم». -/
def umum (q : Qarina) (takhsis : Bool) : Umum :=
  match tanawul q with
  | some t => if takhsis then .baqi t else .aamm t
  | none => .laHukm

/-- **النكرةُ في سياق النفي تعمّ أيًّا كان النافي وأيًّا كان ما باشره.** -/
theorem nakira_nafy (n : Nafi) (m : Mubashara) : umum (.nakiraNafy n m) false = .aamm .afrad := rfl

/-- فالنافي وموضعُ المباشرة لا يغيّران العموم. -/
theorem nafi_la_yughayyir (n n' : Nafi) (m m' : Mubashara) (b : Bool) :
    umum (.nakiraNafy n m) b = umum (.nakiraNafy n' m') b := rfl

/-- **«إلّا إذا خُصّصت»**: كلُّ عامٍّ يرتفع بالتخصيص إلى الباقي ممّا تناوله. -/
theorem takhsis_baqi (q : Qarina) (t : Tanawul) (h : umum q false = .aamm t) : umum q true = .baqi t := by
  unfold umum at *; cases ht : tanawul q <;> simp_all

/-- **فالعمومُ ليس ثابتًا على كلّ حال**: النكرةُ المنفيّةُ نفسُها عامّةٌ بلا تخصيص وغيرُ عامّةٍ به — فلا «قطعيّ» بإطلاق. -/
theorem laysa_qati (n : Nafi) (m : Mubashara) :
    umum (.nakiraNafy n m) true ≠ umum (.nakiraNafy n m) false := by simp [umum, tanawul]

/-- **السياقُ يفرّق**: النكرةُ في الإثبات بلا أل ولا إضافة «لا حكم» في العموم من هذا السطر، وفي النفي عامّة. -/
theorem siyaq_yufarriq (n : Nafi) (m : Mubashara) :
    umum .nakiraIthbat false = .laHukm ∧ umum (.nakiraNafy n m) false = .aamm .afrad := ⟨rfl, rfl⟩

/-- «أل» والإضافة على اسم الجنس تعمّان المفردات، وعلى الجمع الجموع. -/
theorem al_idafa :
    umum .alJins false = .aamm .mufradat ∧ umum .idafaJins false = .aamm .mufradat ∧
    umum .alJam false = .aamm .jumu ∧ umum .idafaJam false = .aamm .jumu := by decide

/-- «والله لا آكل»: يعمّ كلَّ مأكول، و«إلّا أن تخصّص بنوعٍ من الأكل». -/
theorem la_akul : umum (.filManfi .la) false = .aamm .mafulat ∧ umum (.filManfi .la) true = .baqi .mafulat := by
  decide

/-! ## ٣. الباقي بعد التخصيص يتعيّن (س462، س675) -/

/-- الباقي: ما تناوله العامُّ إلّا المُخرَج. -/
def baqi {α : Type} [DecidableEq α] (afrad mukhraj : List α) : List α :=
  afrad.filter (fun a => !mukhraj.contains a)

/-- **الباقي جامعٌ مانع**: فردٌ في الباقي ⟺ متناوَلٌ وغيرُ مُخرَج — «يتعيّن فيُعرف». -/
theorem baqi_iff {α : Type} [DecidableEq α] (afrad mukhraj : List α) (a : α) :
    a ∈ baqi afrad mukhraj ↔ a ∈ afrad ∧ a ∉ mukhraj := by
  simp [baqi]

/-- والإخراجُ لا يزيد. -/
theorem baqi_la_yazid {α : Type} [DecidableEq α] (afrad mukhraj : List α) :
    (baqi afrad mukhraj).length ≤ afrad.length := List.length_filter_le _ _

/-! ## ٤. «أحدٌ وُضع لما يعقل» على خواصّ الجنس (ADR ٩٦) -/

/-- ما يتناوله «أحد» من أجناس المودَع: ما يعقل وحدَه (السيرافيّ س28920، و`Khawass.aqilOf`). -/
def nitaqAhad : List String :=
  (Khawass.sufuf.map (·.jins)).filter (fun j => Khawass.aqilOf j == some true)

/-- **«ما قام أحد»** يعمّ الإنسانَ والثقلين والملائكة، ولا يتناول الحجرَ ولا الكلبَ ولا القمر. -/
theorem nitaq_ahad :
    nitaqAhad = ["الإنسان", "الثقلان", "الملائكة"] ∧
    ∀ j ∈ ["الحجر", "الكلب", "القمر"], j ∉ nitaqAhad := by decide

/-- و«ما قام أحدٌ إلّا الملائكة»: الباقي الإنسانُ والثقلان. -/
theorem ma_qama_ahad_illa : baqi nitaqAhad ["الملائكة"] = ["الإنسان", "الثقلان"] := by decide

/-! ## المراسي -/

/-- (النصّ، السطر 1-based، النصّ بعينه). -/
def marasi : List (String × Nat × String) :=
  [("sirafi", 48515, "نحو الألف للمتكلم والنون للجماعة"),
   ("sirafi", 48516, "والتاء للمخاطب والياء للغائب"),
   ("sirafi", 45472, "والهمزة والياء يدخلان في أول الفعل المضارع للمتكلم"),
   ("sirafi", 69188, "إدغام التاء في أول الفعل المستقبل علامة للمخاطب أو للمؤنثة"),
   ("sirafi", 28920, "وضع لما يعقل"),
   ("j3", 650, "العموم الثابت باللفظ، إما أن يثبت لغة وهو المستفاد من وضع اللغة"),
   ("j3", 652, "فإن النكرة في سياق النفي تعم سواء باشرها النفي نحو ما أحد قائم أم باشر عاملها نحو ما قام أحد"),
   ("j3", 652, "وسواء كان النافي «ما»، أم «لم»، أم «لن»، أم «ليس»، أم غيرها"),
   ("j3", 652, "وكذلك الفعل المتعدي المنفي فهو يعم جميع مفعولاته كقولك «والله لا آكل»"),
   ("j3", 652, "إلا إذا خصَّصت "),
   ("j3", 652, "والداخل على اسم الجنس من «أل» والإضافة يعم المفردات، وعلى الجمع يعم الجموع"),
   ("j3", 462, "لأن الباقي بعد التخصيص يتعين فيعرف"),
   ("j3", 675, "التخصيص بالاستثناء هو إخراج ما بعد «إلا» أو إحدى أخواتها مما قبلها")]

end A116.Umum
