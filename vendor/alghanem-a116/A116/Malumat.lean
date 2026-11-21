/-!
# المعلوماتُ السابقة (ADR ٨٧، أمرُ المالك 2026-10-17)

السندُ نصوصُ النبهانيّ المختومة في `corpora/nabhani/` (السطرُ 1-based)، ومراسيها في `MalumatData.tarifat`:

* «التفكير» س24: «العقلُ… نقلُ الحسّ بالواقع… ووجودُ معلوماتٍ سابقة يفسَّر بواسطتها هذا الواقع».
* «التفكير» س28: الحكمُ على **وجود** الواقع قطعيّ، وعلى **حقيقة الشيء أو صفته** ظنّيّ،
  «ولكن تبقى فكرًا صائبًا حتى يتبيّن خطؤها».
* «التفكير» س18: تمييزُ «التفاحةُ تؤكل والحجرُ لا يؤكل» غريزيّ، «ليس فكرًا ولا إدراكًا».
* «التفكير» س76: الضوءُ «خاصّةٌ من خواصّها وليس شيئًا ثانيًا».
* ج3 س363: الوضعُ «للمعاني الذهنيّة دون الخارجيّة». وج3 س365: «حقائقُ الأشياء وخواصُّها» هي المعلومات.
* ج3 س373، والشرح س1314، س1019: «الآن» و«هنا» إشارتان من المقام.
* ج3 س364، س388: اللغةُ اصطلاح، والمنقولُ عرفيٌّ أو اصطلاحيٌّ خاصّ بجماعته.

## ما يُبنى

1. **النوعُ يعيّن المرتبة** (`martaba`): الوجودُ قطعيّ، والحقيقةُ والصفةُ والخاصّةُ والقابليّةُ ظنّيّة،
   وما سواها ليس حكمًا على شيء: لا التمييزُ الغريزيّ، ولا المرساة، ولا الاصطلاح، ولا الكلّيُّ والجزئيّ.
2. **الحكمُ** (`hukm`): القطعيُّ صائبٌ مع المعارض، والظنّيُّ صائبٌ حتى يُعارَض.
3. **المرساةُ والإطار** (`Itar`، `nisba`): القبلُ والمعُ والبعدُ نسبةٌ في إطارٍ واحد. والنسبةُ لا تتغيّر
   بنقل المرساة، فلا إحداثيَّ مطلقًا. وبين إطارين مختلفين لا نسبة.
4. **على المودَع**: الخاصّةُ ليست موضوعًا لصفّ؛ وخاصّيّةُ الربط تفصل الإنسانَ من الحيوان؛ والتمييزُ لا مرتبةَ له؛
   والإطاران الهجريّ والميلاديّ مستعملان في الجزء الأوّل.

هذا نقلٌ مودَع: Lean يبرهن اتّساقَ المرويّ بنصّه، لا حقائقَ الأشياء (المادّة ١٧).
-/

namespace A116.Malumat

/-- نوعُ الصفّ. -/
inductive Naw
  | wujud | haqiqa | sifa | khassa | qabiliyya
  | tamyiz
  | marsaZaman | marsaMakan
  | istilah
  | mutawati | mushakkik | juzi
  deriving DecidableEq, Repr

/-- مرتبةُ الحكم («التفكير» س28). -/
inductive Martaba | qati | zanni
  deriving DecidableEq, Repr

/-- صفٌّ من المودَع: النصّ، والسطر (1-based)، والاقتباسُ بعينه، والموضوع، والنوع، والمحمول، والإيجاب، والمرتبة
    كما ملأها الوكيل. -/
structure Saff where
  nass : String
  satr : Nat
  iqtibas : String
  mawdu : String
  naw : Naw
  mahmul : String
  ijab : Bool
  martaba : Option Martaba
  deriving DecidableEq, Repr

/-- المرتبةُ دالّةٌ في النوع وحدَه. -/
def martaba : Naw → Option Martaba
  | .wujud => some .qati
  | .haqiqa | .sifa | .khassa | .qabiliyya => some .zanni
  | _ => none

/-- القطعيُّ هو الوجودُ وحدَه. -/
theorem qati_iff (n : Naw) : martaba n = some .qati ↔ n = .wujud := by
  cases n <;> simp [martaba]

/-- الظنّيُّ: الحقيقةُ والصفةُ والخاصّةُ والقابليّة. -/
theorem zanni_iff (n : Naw) :
    martaba n = some .zanni ↔ n = .haqiqa ∨ n = .sifa ∨ n = .khassa ∨ n = .qabiliyya := by
  cases n <;> simp [martaba]

/-- التمييزُ الغريزيُّ ليس حكمًا («ليس فكرًا ولا إدراكًا»)، وكذلك المرساةُ والاصطلاحُ والكلّيُّ والجزئيّ. -/
theorem laysa_hukm :
    martaba .tamyiz = none ∧ martaba .marsaZaman = none ∧ martaba .marsaMakan = none ∧
    martaba .istilah = none ∧ martaba .mutawati = none ∧ martaba .mushakkik = none ∧
    martaba .juzi = none := by
  decide

/-- الحكمُ بالمعارض: القطعيُّ صائب، والظنّيُّ صائبٌ ما لم يُعارَض، وما ليس حكمًا لا حكمَ عليه. -/
def hukm (n : Naw) (muarid : Bool) : Option Bool :=
  match martaba n with
  | some .qati => some true
  | some .zanni => some (!muarid)
  | none => none

/-- «إحساسُ الحواسّ بوجود الواقع قطعيّ»: لا يرفعه معارض. -/
theorem qati_la_yanqud (m : Bool) : hukm .wujud m = some true := rfl

/-- «تبقى فكرًا صائبًا حتى يتبيّن خطؤها». -/
theorem zanni_hatta_yatabayyan (n : Naw) (h : martaba n = some .zanni) :
    hukm n false = some true ∧ hukm n true = some false := by
  simp [hukm, h]

/-- المعارضُ لا يغيّر شيئًا إلّا في الظنّيّ. -/
theorem muarid_fi_zanni (n : Naw) :
    hukm n true ≠ hukm n false ↔ martaba n = some .zanni := by
  cases n <;> simp [hukm, martaba]

/-! ## المرساةُ والإطار -/

/-- الإطار: مرساةُ المقام (الآن، هنا) أو اصطلاحُ جماعةٍ مسمّاة. -/
inductive Itar
  | alAn | huna
  | istilah (jamaa : String)
  deriving DecidableEq, Repr

/-- موضعٌ في إطار: مقدارٌ من مرساته. -/
structure Mawqi where
  itar : Itar
  qadr : Int
  deriving DecidableEq, Repr

/-- النسبةُ بين موضعين: قبلُ، ومعُ، وبعدُ (أو قربٌ وبُعدٌ في المكان). -/
inductive Nisba | qabl | maa | bad
  deriving DecidableEq, Repr

def cmpInt (a b : Int) : Nisba :=
  if a < b then .qabl else if a = b then .maa else .bad

/-- النسبةُ في إطارٍ واحد، ولا نسبةَ بين إطارين. -/
def nisba (a b : Mawqi) : Option Nisba :=
  if a.itar = b.itar then some (cmpInt a.qadr b.qadr) else none

/-- نقلُ المرساة لا يغيّر النسبة: فالنسبةُ لا تحتاج إحداثيًّا مطلقًا من العالم. -/
theorem nisba_shift (i : Itar) (a b k : Int) :
    nisba ⟨i, a + k⟩ ⟨i, b + k⟩ = nisba ⟨i, a⟩ ⟨i, b⟩ := by
  have e1 : (a + k < b + k) = (a < b) := propext ⟨fun h => by omega, fun h => by omega⟩
  have e2 : (a + k = b + k) = (a = b) := propext ⟨fun h => by omega, fun h => by omega⟩
  simp only [nisba, cmpInt, e1, e2]

/-- بين إطارين مختلفين لا نسبة. -/
theorem la_nisba_bayna_itarayn (a b : Mawqi) (h : a.itar ≠ b.itar) : nisba a b = none := by
  simp [nisba, h]

/-- الهجريُّ والميلاديُّ إطاران: لا نسبةَ بينهما بلا مقابلةٍ مسمّاة. -/
theorem hijri_miladi (a b : Int) :
    nisba ⟨.istilah "الهجري", a⟩ ⟨.istilah "الميلادي", b⟩ = none := by
  exact la_nisba_bayna_itarayn _ _ (by simp)

/-- و«الآن» غيرُ «هنا»: الزمانُ والمكانُ لا يتقابلان. -/
theorem alAn_huna (a b : Int) : nisba ⟨.alAn, a⟩ ⟨.huna, b⟩ = none := by
  exact la_nisba_bayna_itarayn _ _ (by simp)

/-- النسبةُ عكسيّة: قبلُ في اتّجاهٍ بعدُ في الآخر. -/
theorem qabl_bad (i : Itar) (a b : Int) (h : a < b) :
    nisba ⟨i, a⟩ ⟨i, b⟩ = some .qabl ∧ nisba ⟨i, b⟩ ⟨i, a⟩ = some .bad := by
  have h' : ¬ b < a := Int.not_lt.mpr (Int.le_of_lt h)
  have h'' : b ≠ a := fun e => by subst e; exact Int.lt_irrefl _ h
  simp [nisba, cmpInt, h, h', h'']

end A116.Malumat
