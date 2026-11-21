import Nizam.Shahada
import Dal.Makharij

/-!
# تحصيلُ النصّ ومحاذاتُه، بشهادةٍ على كلّ مقطع (الطبقة ١)

**الطلب.** رسالةُ المالك 2026-10-27 (ما حُفظ منها بنصّه وما بقي بمعناه في رأس `Nizam/Shahada.lean`)، وأوّلُ أولويّاتها إغلاقُ تحصيل
النصّ ومحاذاته قبل أيّ ترقيةٍ دلاليّة. والتصميمُ وقواعدُ التصنيف قرارُ البنّاء، ومواصفتُها التي كتب منها مؤلّفٌ مستقلٌّ العرّافَ في
`tahaqquq/tahsil/wasf.md`.

**ما كان.** القارئ (`Qari/Main.lean`، `tahlil`) يحوّل الكلمة خلايا بحلقةٍ أمريّة لا تحفظ موضعًا. فيُسقط ما لا خليّةَ له: التطويلَ، وألفَ
التنوين، واللامَ المدغمة، وألفَ الجماعة، وألفَ الوصل أوّلَ الكلمة. ويبدّل: ى ألفًا، وة تاءً في الوصل وهاءً في الوقف. والجسرُ إلى NABT
(`Jisr/Nabt.lean`) يقول: «مواضع المصدر مواضع خلايا معلنة؛ ليست إحداثيات بايت أو محارف Unicode مستنتجة».

**ما صار هنا.**
- **القطعُ بلا فقد:** النصُّ قائمةُ نقاط رمز، ويُقطع مقاطعَ (رأسٌ ثمّ أطولُ متتاليةٍ من العلامات بعده)؛ وضمُّ المقاطع هو النصُّ نفسُه
  (`qatta_flatten`)، ولا مقطعَ فارغ (`qatta_ghayr_farigh`)، وما بعد الرأس علاماتٌ كلُّه (`qatta_alamat`)، ورأسُ كلّ مقطعٍ بعد الأوّل
  ليس علامة (`qatta_ras`).
- **المحاذاة:** لكلّ مقطعٍ موضعُه `[a, b)` بنقاط الرمز؛ والمواضعُ متّصلةٌ تغطّي النصّ (`tahsil_tughatti`)، وكلُّ موضعٍ صالحٌ في مصدر NABT
  (`Nabt.UnitDiscovery.validSpan`) وذرّاتُه هي المقطعُ بعينه (`mawdi_sahih`).
- **التصنيف:** لكلّ مقطعٍ حكمٌ من ثلاثة: مرخَّصٌ بصنفه وخلاياه، أو معلَّقٌ باسم القاعدة الناقصة، أو مدخلٌ فاسدٌ باسم سببه (`tasnif`). فما لم
  تُبنَ قاعدتُه (همزةُ الوصل، والتنوين، والتاءُ المربوطة، والألفُ المقصورة والممدودة، وألفا التنوين والجماعة، ولامُ التعريف المدغمة،
  والحرفُ الأخيرُ بلا حركة، والشدّةُ بلا حركة، والتطويلُ بعلامة) يبقى ظاهرًا باسمه، ولا يُسقط ولا يُبدَّل.
- **سلامةُ المرخَّص:** خلايا المقطع المرخَّص تُفكّ بجدول المخارج المعلَن (`Dal.harf`) إلى رأسه (والمقعدُ همزة) وحالةِ علامته، وفي المشدَّد
  خليّةٌ ساكنةٌ من الحامل نفسِه قبلها، والمقطعُ كلُّه رأسٌ وحركةٌ وشدّةٌ على الأكثر (`tasnif_salim`). وهذا المعنى (`SahihL`) تعريفُ البنّاء.
- **الشهادة:** لكلّ مقطعٍ انتقالٌ مشهود بعقد `Nizam/Shahada.lean` (`shahada`)، وحكمُ الفاحص عليه هو حكمُ التصنيف: مرخَّص، أو تعليقٌ
  باسم القاعدة، أو مدخلٌ فاسدٌ باسم سببه (`shahada_hukm`). والعقدُ مطبَّقٌ على قواعد الترخيص الأربع (`qaida`، `shahada_tahsil_salima`).
  وصدقُ الشواهد وصحّةُ المدخل في `qaida` معرَّفان من `tasnif` و`tahsil` أنفسهما؛ فـ`shahada_tahsil_salima` تُلبس `tasnif_salim`
  و`mawdi_sahih` صورةَ العقد، ولا تزيد عليهما شاهدًا مستقلًّا. والشاهدُ المستقلُّ العرّافُ في `tahaqquq/test_tahsil.py`.
- **محاذاةُ الخلايا:** كلُّ خليّةٍ في مقطعٍ مرخَّص مقرونةٌ بموضع مقطعها بنقاط الرمز، وحاملُها رأسُه (`khalaya_muhadhat`).

**حدُّه.**
- لا وصلَ ولا وقف ولا إعرابَ ولا معجم: الطبقةُ تقطع وتحاذي وترمّز الحرفَ المحرّك وحرفَ المدّ وحدهما.
- الفاصلُ بين الكلمات U+0020 وحده، ولا تطبيعَ لـ Unicode: الصورُ المركّبة والعلاماتُ القرآنيّة خارج الثماني حروفٌ ليست في الجدول.
- المقعدُ يُرمَّز همزةً، فتسقط صورتُه من الخلايا وتبقى في الموضع. وترتيبُ الشدّة والحركة في المقطع لا تحمله الخلايا.
- مواضعُ غموض المواصفة كتب فيها مؤلّفُ العرّاف قراءتَه في `tahaqquq/tahsil/NOTES.md`، وقرأها البنّاءُ قبل كتابة هذا الملفّ. وهذا الملفّ يوافقها
  فيها اختيارًا، فاتّفاقُهما هناك ليس شاهدًا مستقلًّا. ومنها: علامتان من جنسٍ واحد متعارضتان، والشدّةُ مع السكون خليّتان ساكنتان، وحدُّ
  الكلمة غيرُ شامل، وخلايا الكلمة غيرِ المرخَّصة مضمومة.
- البدائلُ فارغةٌ في هذه الطبقة.

**التعديل الثالث** (2026-10-29، `tahaqquq/tahsil/wasf.md`؛ قولُ المالك في الجلسة 02:05 بتوقيت عمّان «قواعد التحصيل المعلّقة، كلٌّ على ضابطٍ
مجمَّد، لرفع التغطية فوق النصف» من بندٍ ألصقه من جواب البنّاء، وفيها «انت مفوض بشكل مطلق … نفذ واكمل البرهان»؛ والقواعدُ وسندُها قرارُ البنّاء): أحدَ
عشرَ صنفًا مرخَّصًا مكانَ المعلَّق حيث تُستوفى شروطُها — همزةُ أل مفتوحةً (`hamzaWaslAl`)، والممدودة (`madda`)، والتاءُ المربوطة تاءً موصولةً
(`taMarbuta`)، والمقصورةُ ألفًا (`alifMaqsura`)، وألفُ الخطّ بلا خليّة (`alifKhatt`)، والتنوينُ نونًا ساكنة (`tanwin`، `tanwinAlif`)، وحركةُ ما قبل «اً»
(`harakaMinTanwin`)، والشدّةُ أوّلَ الكلمة بلا نصفها الساكن (`shaddaIbtida`)، واللامُ المدغمة (`lamMudgham`)، والحرفُ بلا علامةٍ ساكنًا (`sukunMuqaddar`).
وسلامتُها في `SahihL` (`tasnif_salim` عليها كلِّها). ومحاذاةُ الخلايا صارت بالرأس أو ببدله المسمّى (`ibdal`: نونُ التنوين، وهمزةُ أل، وما تُبدَل به
الممدودةُ والمربوطةُ والمقصورة). والكلمةُ بهذا التعديل تُقرأ مبتدأً بها وموصولًا آخرُها.

**المبرهنات** (40، بالمعيار الموحَّد في `Nizam/Asas.lean`):
- لكلّ (33): `taOf_salim`، `maqsuraOf_salim`، `tanwinOf_salim`، `harakaTanwinOf_salim`، `shaddaIbtidaOf_salim`، `sukunOf_salim`، `shadda_wahda`، `hamilOf_harf`، `qatta_flatten`، `qatta_ghayr_farigh`، `qatta_alamat`، `qatta_ras`، `filterMap_hala_le`، `harfMaddOf_salim`،
  `harfHarakaOf_salim`، `tasnif_salim`، `binaMin_nass`، `tahsil_nass`، `tahsil_flatten`، `mem_tahsil_qatta`، `binaMin_hukm`، `tahsil_hukm`،
  `binaMin_tughatti`، `tahsil_tughatti`، `binaMin_muhadha`، `tahsil_muhadha`، `tughatti_mem`، `mawdi_sahih`، `tahsil_salim`، `ismSinf_ne`،
  `shahada_hukm`، `shahada_tahsil_salima`، `khalaya_muhadhat`.
- تعريفيّة (1): `fakk_khaliyaMin`.
- على الشاهد (6): `harf_sifr`، `harf_thabit`، `shahid_kataba`، `shahid_shams`، `shahid_muallaq`، `shahid_wasl`.
-/

namespace Dal.Tahsil

open Nabt.UnitDiscovery
open Nizam.Shahada (Naqla Muqaddima Hawiyya Natija Naw Hal)

/-! ## ١. الثوابت -/

def shadda : Char := '\u0651'

/-- حالةُ العلامة: فتحة، ضمّة، كسرة، سكون. -/
def halaAlama (c : Char) : Option HalaIsm :=
  if c == '\u064E' then some .fatha
  else if c == '\u064F' then some .damma
  else if c == '\u0650' then some .kasra
  else if c == '\u0652' then some .sukun
  else none

def tanwin (c : Char) : Bool := c == '\u064B' || c == '\u064C' || c == '\u064D'

/-- علامةُ حركة: إحدى الأربع أو التنوينات الثلاثة. -/
def harakaB (c : Char) : Bool := (halaAlama c).isSome || tanwin c

/-- العلامات الثماني. -/
def alama (c : Char) : Bool := harakaB c || c == shadda

/-- مقاعدُ الهمزة. -/
def maqaid : List Char := ['أ', 'إ', 'ؤ', 'ئ']

/-- الخاصّة: التاء المربوطة، والألف المقصورة، والممدودة، وألف الوصل، والتطويل، والفراغ. -/
def khassa : List Char := ['ة', 'ى', 'آ', 'ٱ', 'ـ', ' ']

/-- الحاملُ من جدول المخارج المعلَن (`Dal.hawamil`)؛ والمقعدُ همزة. -/
def hamilOf (r : Char) : Option Hamil :=
  if r ∈ maqaid then some 0 else (List.finRange 29).find? (fun h => harf h == r)

/-- ما يُفكّ إليه الرأس: المقعدُ همزة، وغيرُه هو. -/
def raddHarf (r : Char) : Char := if r ∈ maqaid then 'ء' else r

theorem harf_sifr : harf 0 = 'ء' := by decide

/-- **الحاملُ يُفكّ إلى رأسه:** حرفُ الحامل في الجدول هو الرأس، والمقعدُ همزة. -/
theorem hamilOf_harf {r : Char} {h : Hamil} (e : hamilOf r = some h) : harf h = raddHarf r := by
  unfold hamilOf at e
  unfold raddHarf
  by_cases hm : r ∈ maqaid
  · rw [ite_eq_left hm, Option.some.injEq] at e
    subst e
    rw [ite_eq_left hm, harf_sifr]
  · rw [ite_eq_right hm] at e
    have := List.find?_some e
    simp only [beq_iff_eq] at this
    rw [ite_eq_right hm, this]

/-! ## ٢. القطع بلا فقد -/

/-- رأسٌ ثمّ أطولُ متتاليةٍ من العلامات بعده: يُبنى من الآخر، فالحرفُ يُضمّ إلى المقطع بعده إن بدأ ذلك بعلامة. -/
def qatta : List Char → List (List Char)
  | [] => []
  | c :: cs =>
    match qatta cs with
    | [] => [[c]]
    | s :: ss => if s.head?.any alama then (c :: s) :: ss else [c] :: s :: ss

/-- **بلا فقد:** ضمُّ المقاطع هو النصّ. -/
theorem qatta_flatten : ∀ t : List Char, (qatta t).flatten = t
  | [] => rfl
  | c :: cs => by
    have ih := qatta_flatten cs
    simp only [qatta]
    split
    · rename_i h; rw [h] at ih; simp at ih; simp [ih]
    · rename_i s ss h
      rw [h] at ih
      split <;> simp [← ih]

theorem qatta_ghayr_farigh : ∀ t : List Char, ∀ s ∈ qatta t, s ≠ []
  | [] => by simp [qatta]
  | c :: cs => by
    have ih := qatta_ghayr_farigh cs
    simp only [qatta]
    split
    · simp
    · rename_i s ss h
      rw [h] at ih
      split
      · intro x hx
        rcases List.mem_cons.1 hx with rfl | hx
        · simp
        · exact ih x (List.mem_cons_of_mem _ hx)
      · intro x hx
        rcases List.mem_cons.1 hx with rfl | hx
        · simp
        · exact ih x hx

/-- ما بعد الرأس علاماتٌ كلُّه. -/
theorem qatta_alamat : ∀ t : List Char, ∀ s ∈ qatta t, ∀ x ∈ s.tail, alama x = true
  | [] => by simp [qatta]
  | c :: cs => by
    have ih := qatta_alamat cs
    simp only [qatta]
    split
    · simp
    · rename_i s ss h
      rw [h] at ih
      split
      · rename_i hs
        intro x hx
        rcases List.mem_cons.1 hx with rfl | hx
        · intro y hy
          simp only [List.tail_cons] at hy
          cases s with
          | nil => simp at hy
          | cons z zs =>
            rcases List.mem_cons.1 hy with rfl | hy
            · simpa using hs
            · exact ih _ List.mem_cons_self y hy
        · exact ih x (List.mem_cons_of_mem _ hx)
      · intro x hx
        rcases List.mem_cons.1 hx with rfl | hx
        · simp
        · exact ih x hx

/-- **المقطعُ أطولُ ما يمكن:** رأسُ كلّ مقطعٍ بعد الأوّل ليس علامة. -/
theorem qatta_ras : ∀ t : List Char, ∀ s ∈ (qatta t).tail, (s.head?.any alama) = false
  | [] => by simp [qatta]
  | c :: cs => by
    have ih := qatta_ras cs
    simp only [qatta]
    split
    · simp
    · rename_i s ss h
      rw [h] at ih
      split
      · exact ih
      · rename_i hs
        intro x hx
        rcases List.mem_cons.1 hx with rfl | hx
        · simpa using hs
        · exact ih x hx

/-! ## ٣. السياق والتصنيف -/

def fasil (s : List Char) : Bool := s.head? == some ' '

/-- سياقُ المقطع في كلمته: ما قبله فيها، وهل ذلك أوّلُها، وهل حكمُه ألفُ الوصل (14ب)، وهل ما قبله فيها كلُّه سوابق، وما بعده فيها،
    وما بعد ذلك فيها. -/
structure Siyaq where
  sabiq : Option (List Char)
  sabiqAwwal : Bool
  sabiqWasl : Bool
  sawabiq : Bool
  lahiq : Option (List Char)
  lahiq2 : Option (List Char)
  /-- المقاطعُ بعده في كلمته كلُّها (التعديل الثالث، القاعدة 11). -/
  lawahiq : List (List Char)
  deriving DecidableEq, Repr

inductive Sinf
  | fasil
  | tatwil
  | harfMadd
  | harfHaraka
  | hamzaWasl
  /-- التعديل الثالث (2026-10-29). -/
  | hamzaWaslAl
  | madda
  | taMarbuta
  | alifMaqsura
  | alifKhatt
  | tanwin
  | tanwinAlif
  | harakaMinTanwin
  | shaddaIbtida
  | lamMudgham
  | sukunMuqaddar
  deriving DecidableEq, Repr

inductive Hukm
  /-- مرخَّص: صنفُه وخلاياه. -/
  | L (sinf : Sinf) (khalaya : List Khaliya)
  /-- معلَّق: اسمُ القاعدة الناقصة. -/
  | P (ism : String)
  /-- مدخلٌ فاسد: اسمُ السبب. -/
  | F (ism : String)
  deriving DecidableEq, Repr

def khaliyaMin (h : Hamil) (s : HalaIsm) : Khaliya := ⟨h, s.ila⟩

/-! شروطُ القواعد بأسمائها (بترتيب المواصفة). -/

/-- ٣: الرأسُ ليس حاملًا ولا مقعدًا ولا خاصًّا. -/
def ghayrMaruf (r : Char) : Bool := (hamilOf r).isNone && !(khassa.contains r)
/-- ٤: أكثرُ من شدّة، أو أكثرُ من علامة حركة. -/
def mutaarida (ms : List Char) : Bool := ms.count shadda > 1 || (ms.filter harakaB).length > 1
/-- ٦: ألفٌ أو ألفُ وصلٍ أوّلَ الكلمة. -/
def alifAwwal (c : Siyaq) (r : Char) : Bool := (r == 'ا' || r == 'ٱ') && c.sabiq.isNone
/-- ١٢: ألفٌ مجرّدة بعد فتحتين. -/
def alifTanwin (c : Siyaq) (r : Char) (ms : List Char) : Bool :=
  r == 'ا' && ms.isEmpty && c.sabiq.any (fun p => p.tail.contains '\u064B')
/-- ١٣: ألفٌ مجرّدة آخرَ الكلمة بعد واوٍ مجرّدةٍ أو ساكنة. -/
def alifJamaa (c : Siyaq) (r : Char) (ms : List Char) : Bool :=
  r == 'ا' && ms.isEmpty && c.lahiq.isNone && (c.sabiq == some ['و'] || c.sabiq == some ['و', '\u0652'])
/-- ١٤: شدّةٌ بلا علامة حركة. -/
def shaddaBilaHaraka (ms : List Char) : Bool := ms.contains shadda && !(ms.any harakaB)
/-- ١٤أ: حاملٌ أو مقعدٌ أوّلَ الكلمة، وفي علاماته شدّة. -/
def shaddaAwwal (c : Siyaq) (r : Char) (ms : List Char) : Bool :=
  (hamilOf r).isSome && c.sabiq.isNone && ms.contains shadda
/-- الفتحةُ والضمّةُ والكسرة. -/
def harakaQasira (x : Char) : Bool := x == '\u064E' || x == '\u064F' || x == '\u0650'
/-- حروفُ السوابق في 14ب (تعيينُ البنّاء، المواصفة: التعديل الثاني). -/
def hurufSabiqa : List Char := ['و', 'ف', 'ب', 'ك', 'ل', 'ت', 'أ']
/-- السابقة: رأسُها من حروف السوابق، وعلاماتُها فتحةٌ أو ضمّةٌ أو كسرةٌ وحدها. -/
def sabiqa (s : List Char) : Bool :=
  s.head?.any (fun h => hurufSabiqa.contains h) && s.tail.length == 1 && s.tail.all harakaQasira
/-- رأسُ المقطع حاملٌ من الجدول أو مقعدُ همزة. -/
def raasHamil (n : List Char) : Bool := n.head?.any (fun h => (hamilOf h).isSome)
/-- ١٤ب: ألفٌ مجرّدةٌ في غير أوّل الكلمة، ما قبلها في الكلمة سوابقُ كلُّه، وقبل حاملٍ ساكن، أو قبل لامٍ مجرّدةٍ يليها مشدَّد. -/
def alifWasl (c : Siyaq) (r : Char) (ms : List Char) : Bool :=
  r == 'ا' && ms.isEmpty && c.sabiq.isSome && c.sawabiq &&
    c.lahiq.any (fun n => raasHamil n &&
      (n.tail == ['\u0652'] || (n == ['ل'] && c.lahiq2.any (fun m => m.tail.contains shadda))))
/-- ١٥أ: ا أو و أو ي مجرّدةٌ في غير أوّل الكلمة. -/
def madd (c : Siyaq) (r : Char) : Bool := (r == 'ا' || r == 'و' || r == 'ي') && c.sabiq.isSome
/-- ١٥ب: لامٌ بعد ألفٍ هي أوّلُ الكلمة أو بعد ألفِ وصلٍ بالقاعدة ١٤ب، وبعدها مشدَّد. -/
def lamTarif (c : Siyaq) (r : Char) : Bool :=
  r == 'ل' && ((c.sabiqAwwal && c.sabiq.any (fun p => p.head? == some 'ا' || p.head? == some 'ٱ')) || c.sabiqWasl) &&
    c.lahiq.any (fun n => n.tail.contains shadda)

/-! ### قواعدُ التعديل الثالث (`tahaqquq/tahsil/wasf.md`، 2026-10-29) -/

/-- الحالةُ من التنوين: فتحتان 0، ضمّتان 1، كسرتان 2. -/
def tanwinHala (c : Char) : Option HalaIsm :=
  if c == '\u064B' then some .fatha
  else if c == '\u064C' then some .damma
  else if c == '\u064D' then some .kasra
  else none

/-- حروفُ اللام المدغمة (الكتاب س21531–21539، واللامُ تعيينُ البنّاء). -/
def hurufIdgham : List Char := ['ن', 'ر', 'د', 'ت', 'ص', 'ط', 'ز', 'س', 'ظ', 'ث', 'ذ', 'ض', 'ش', 'ل']

/-- ٦: «لامُ التعريف» بعد المقطع. -/
def lamBaad (c : Siyaq) : Bool :=
  c.lahiq.any (fun n => n.head? == some 'ل' &&
    (n.tail == ['\u0652'] || (n.tail.contains shadda && c.lahiq2.isSome)
      || (n.tail.isEmpty && c.lahiq2.any (fun m => m.tail.contains shadda))))

/-- ١٤ و١٥: التالي «اً» آخرَ الكلمة. -/
def alifTanwinBaad (c : Siyaq) : Bool := c.lahiq == some ['ا', '\u064B'] && c.lahiq2.isNone

/-- ١١: كلُّ ما بعده في كلمته ا أو ى بلا علامات. -/
def baqiKhatt (c : Siyaq) : Bool := c.lawahiq.all (fun n => n == ['ا'] || n == ['ى'])

/-- ٩: التاءُ المربوطة آخرَ الكلمة بحركةٍ قصيرةٍ أو تنوين. -/
def taOf (c : Siyaq) : List Char → Hukm
  | [m] =>
    if c.lahiq.isNone then
      match halaAlama m, tanwinHala m with
      | some st, _ => if st == .sukun then .P "قاعدة التاء المربوطة" else .L .taMarbuta [khaliyaMin 18 st]
      | none, some st => .L .taMarbuta [khaliyaMin 18 st, khaliyaMin 14 .sukun]
      | none, none => .P "قاعدة التاء المربوطة"
    else .P "قاعدة التاء المربوطة"
  | _ => .P "قاعدة التاء المربوطة"

/-- ١٠: الألفُ المقصورة آخرَ الكلمة بعد فتحةٍ أو فتحتين. -/
def maqsuraOf (c : Siyaq) (ms : List Char) : Hukm :=
  if ms.isEmpty && c.lahiq.isNone then
    match c.sabiq with
    | some p =>
      if p.tail.contains '\u064E' then .L .alifMaqsura [khaliyaMin 2 .sukun]
      else if p.tail.contains '\u064B' then .L .alifKhatt []
      else .P "قاعدة الألف المقصورة"
    | none => .P "قاعدة الألف المقصورة"
  else .P "قاعدة الألف المقصورة"

/-- ١١: التنوين. -/
def tanwinOf (c : Siyaq) (r : Char) (ms : List Char) : Hukm :=
  match hamilOf r, (ms.filterMap tanwinHala).head? with
  | some h, some st =>
    if !(r == 'ا' || r == 'و' || r == 'ي') && baqiKhatt c && !(c.sabiq.isNone && ms.contains shadda) then
      .L .tanwin ((if ms.contains shadda then [khaliyaMin h .sukun] else []) ++ [khaliyaMin h st, khaliyaMin 14 .sukun])
    else if r == 'ا' && ms == ['\u064B'] && c.lahiq.isNone && c.sabiq.isSome then .L .tanwinAlif [khaliyaMin 14 .sukun]
    else .P "قاعدة التنوين"
  | _, _ => .P "قاعدة التنوين"

/-- ١٤ و١٥: حركةُ ما قبل «اً» فتحة (وقبلها ساكنٌ إن كان مشدَّدًا). -/
def harakaTanwinOf (r : Char) (sh : Bool) : Hukm :=
  match hamilOf r with
  | some h => .L .harakaMinTanwin ((if sh then [khaliyaMin h .sukun] else []) ++ [khaliyaMin h .fatha])
  | none => .F "خلل داخلي"

/-- ١٤أ: الشدّةُ أوّلَ الكلمة بحركةٍ قصيرة: يسقط نصفُها الساكن. -/
def shaddaIbtidaOf (r : Char) (ms : List Char) : Hukm :=
  match hamilOf r, (ms.filterMap halaAlama).head? with
  | some h, some st => if st == .sukun then .P "قاعدة الشدّة في أوّل الكلمة" else .L .shaddaIbtida [khaliyaMin h st]
  | _, _ => .P "قاعدة الشدّة في أوّل الكلمة"

/-- ١٥: الحرفُ بلا علامةٍ ساكن. -/
def sukunOf (r : Char) : Hukm :=
  match hamilOf r with
  | some h => .L .sukunMuqaddar [khaliyaMin h .sukun]
  | none => .F "خلل داخلي"

/-- ١٦: الحرفُ المحرَّك. -/
def harfHarakaOf (r : Char) (ms : List Char) : Hukm :=
  match hamilOf r, (ms.filterMap halaAlama).head? with
  | some h, some s =>
    .L .harfHaraka (if ms.contains shadda then [khaliyaMin h .sukun, khaliyaMin h s] else [khaliyaMin h s])
  | _, _ => .F "خلل داخلي"

/-- ١٥أ: حرفُ المدّ. -/
def harfMaddOf (r : Char) : Hukm :=
  match hamilOf r with
  | some h => .L .harfMadd [khaliyaMin h .sukun]
  | none => .F "خلل داخلي"

/-- **التصنيف:** أوّلُ قاعدةٍ تنطبق، بترتيب المواصفة (`tahaqquq/tahsil/wasf.md`، القواعد ١–١٦ و١٤أ و١٤ب). -/
def tasnifRas (c : Siyaq) (r : Char) (ms : List Char) : Hukm :=
  if r == ' ' then (if ms.isEmpty then .L .fasil [] else .F "علامة على فاصل")
  else if alama r then .F "علامة بلا حامل"
  else if ghayrMaruf r then .F "حرف ليس في جدول المخارج"
  else if mutaarida ms then .F "علامتان متعارضتان"
  else if r == 'ـ' then (if ms.isEmpty then .L .tatwil [] else .P "قاعدة التطويل بعلامة")
  else if alifAwwal c r then
    (if ms.any harakaB then .F "ألف محرّكة في أوّل الكلمة"
    else if ms.isEmpty && lamBaad c then .L .hamzaWaslAl [khaliyaMin 0 .fatha]
    else .P "قاعدة همزة الوصل")
  else if r == 'ٱ' then .P "قاعدة همزة الوصل"
  else if r == 'آ' then (if ms.isEmpty then .L .madda [khaliyaMin 0 .fatha, khaliyaMin 2 .sukun] else .P "قاعدة الألف الممدودة")
  else if r == 'ة' then taOf c ms
  else if r == 'ى' then maqsuraOf c ms
  else if ms.any tanwin then tanwinOf c r ms
  else if alifTanwin c r ms then .L .alifKhatt []
  else if alifJamaa c r ms then .L .alifKhatt []
  else if shaddaBilaHaraka ms then
    (if alifTanwinBaad c && (hamilOf r).isSome then harakaTanwinOf r true else .P "قاعدة الشدّة بلا حركة")
  else if shaddaAwwal c r ms then shaddaIbtidaOf r ms
  else if alifWasl c r ms then .L .hamzaWasl []
  else if ms.isEmpty then
    (if madd c r then harfMaddOf r
    else if lamTarif c r then
      (if c.lahiq.any (fun n => n.head?.any (fun x => hurufIdgham.contains x)) then .L .lamMudgham []
      else .P "قاعدة لام التعريف المدغمة")
    else if (hamilOf r).isSome && c.sabiq.isSome && alifTanwinBaad c then harakaTanwinOf r false
    else if (hamilOf r).isSome && c.sabiq.isSome then sukunOf r
    else if c.lahiq.isNone then .P "قاعدة الحرف الأخير بلا حركة"
    else .F "حرف بلا حركة في غير آخر الكلمة")
  else harfHarakaOf r ms

def tasnif (c : Siyaq) : List Char → Hukm
  | [] => .F "مقطع فارغ"
  | r :: ms => tasnifRas c r ms

/-! ## ٤. سلامةُ المرخَّص -/

/-- الخليّةُ مفكوكةً بجدول المخارج: حرفُ حاملها وحالتُها. -/
def fakkKhaliya (k : Khaliya) : Char × Hala := (harf k.hamil, k.hala)

/-- **صحّةُ مخرج القاعدة:** ما يعنيه كلُّ صنفٍ مرخَّص في مقطعه وخلاياه. -/
def SahihL : Sinf → List Char → List Khaliya → Prop
  | .fasil, s, ks => s = [' '] ∧ ks = []
  | .tatwil, s, ks => s = ['ـ'] ∧ ks = []
  | .hamzaWasl, s, ks => s = ['ا'] ∧ ks = []
  | .hamzaWaslAl, s, ks => (s = ['ا'] ∨ s = ['ٱ']) ∧ ks.map fakkKhaliya = [('ء', 0)]
  | .madda, s, ks => s = ['آ'] ∧ ks.map fakkKhaliya = [('ء', 0), ('ا', 3)]
  | .taMarbuta, s, ks => ∃ m st, s = ['ة', m] ∧
      ((halaAlama m = some st ∧ st ≠ .sukun ∧ ks.map fakkKhaliya = [('ت', st.ila)]) ∨
       (tanwinHala m = some st ∧ ks.map fakkKhaliya = [('ت', st.ila), ('ن', 3)]))
  | .alifMaqsura, s, ks => s = ['ى'] ∧ ks.map fakkKhaliya = [('ا', 3)]
  | .alifKhatt, s, ks => (s = ['ا'] ∨ s = ['ى']) ∧ ks = []
  | .tanwin, s, ks => ∃ r ms st, s = r :: ms ∧ (ms.filterMap tanwinHala).head? = some st ∧
      ks.map fakkKhaliya = (if ms.contains shadda then [(raddHarf r, 3)] else []) ++ [(raddHarf r, st.ila), ('ن', 3)]
  | .tanwinAlif, s, ks => s = ['ا', '\u064B'] ∧ ks.map fakkKhaliya = [('ن', 3)]
  | .harakaMinTanwin, s, ks => ∃ (r : Char) (sh : Bool), (s = [r] ∨ s = [r, shadda]) ∧
      ks.map fakkKhaliya = (if sh = true then [(raddHarf r, 3)] else []) ++ [(raddHarf r, 0)]
  | .shaddaIbtida, s, ks => ∃ r ms st, s = r :: ms ∧ ms.contains shadda ∧ (ms.filterMap halaAlama).head? = some st ∧
      st ≠ .sukun ∧ ks.map fakkKhaliya = [(raddHarf r, st.ila)]
  | .lamMudgham, s, ks => s = ['ل'] ∧ ks = []
  | .sukunMuqaddar, s, ks => ∃ r, s = [r] ∧ ks.map fakkKhaliya = [(raddHarf r, 3)]
  | .harfMadd, s, ks => ∃ r, s = [r] ∧ (r = 'ا' ∨ r = 'و' ∨ r = 'ي') ∧ ks.map fakkKhaliya = [(r, 3)]
  | .harfHaraka, s, ks => ∃ r ms st, s = r :: ms ∧ ms.filterMap halaAlama = [st] ∧
      (∀ x ∈ ms, x = shadda ∨ (halaAlama x).isSome) ∧ ms.count shadda ≤ 1 ∧
      ks.map fakkKhaliya = (if ms.contains shadda then [(raddHarf r, 3)] else []) ++ [(raddHarf r, st.ila)]

theorem filterMap_hala_le : ∀ l : List Char, (l.filterMap halaAlama).length ≤ (l.filter harakaB).length
  | [] => by simp
  | x :: xs => by
    have ih := filterMap_hala_le xs
    cases hx : halaAlama x with
    | none =>
      rw [List.filterMap_cons, hx]
      by_cases hb : harakaB x
      · rw [List.filter_cons_of_pos hb]; simp only [List.length_cons]; omega
      · rw [List.filter_cons_of_neg hb]; exact ih
    | some s =>
      have hb : harakaB x = true := by simp [harakaB, hx]
      rw [List.filterMap_cons, hx, List.filter_cons_of_pos hb]
      simp only [List.length_cons]
      omega

theorem fakk_khaliyaMin (h : Hamil) (s : HalaIsm) : fakkKhaliya (khaliyaMin h s) = (harf h, s.ila) := rfl

theorem harfMaddOf_salim (r : Char) (ks : List Khaliya) (hr : r = 'ا' ∨ r = 'و' ∨ r = 'ي')
    (h : harfMaddOf r = .L .harfMadd ks) : SahihL .harfMadd [r] ks := by
  unfold harfMaddOf at h
  cases hh : hamilOf r with
  | none => rw [hh] at h; cases h
  | some hr' =>
    rw [hh] at h
    cases h
    have hharf := hamilOf_harf hh
    have hrad : raddHarf r = r := by
      unfold raddHarf
      rcases hr with h1 | h1 | h1 <;> subst h1 <;> decide
    refine ⟨r, rfl, hr, ?_⟩
    simp only [List.map_cons, List.map_nil, fakk_khaliyaMin, hharf, hrad]
    rfl

theorem harfHarakaOf_salim (r : Char) (ms : List Char) (sinf : Sinf) (ks : List Khaliya)
    (hm : ∀ x ∈ ms, alama x = true) (n4 : mutaarida ms = false) (n11 : ms.any tanwin = false)
    (h : harfHarakaOf r ms = .L sinf ks) : SahihL sinf (r :: ms) ks := by
  unfold harfHarakaOf at h
  cases hh : hamilOf r with
  | none => rw [hh] at h; cases h
  | some hr =>
    cases hst : (ms.filterMap halaAlama).head? with
    | none => rw [hh, hst] at h; cases h
    | some st =>
      rw [hh, hst] at h
      cases h
      simp only [mutaarida, Bool.or_eq_false_iff, decide_eq_false_iff_not, gt_iff_lt, Nat.not_lt] at n4
      have hlen : (ms.filterMap halaAlama).length ≤ 1 := by
        have := filterMap_hala_le ms
        omega
      have hfm : ms.filterMap halaAlama = [st] := by
        cases hl : ms.filterMap halaAlama with
        | nil => rw [hl] at hst; cases hst
        | cons y ys =>
          rw [hl] at hst hlen
          simp only [List.head?_cons, Option.some.injEq] at hst
          subst hst
          cases ys with
          | nil => rfl
          | cons _ _ => simp at hlen
      have hall : ∀ x ∈ ms, x = shadda ∨ (halaAlama x).isSome := by
        intro x hx
        have hax := hm x hx
        simp only [alama, harakaB, Bool.or_eq_true, beq_iff_eq] at hax
        rcases hax with (hax | hax) | hax
        · exact Or.inr hax
        · have : ms.any tanwin = true := List.any_eq_true.2 ⟨x, hx, hax⟩
          rw [n11] at this; cases this
        · exact Or.inl hax
      refine ⟨r, ms, st, rfl, hfm, hall, n4.1, ?_⟩
      have hharf := hamilOf_harf hh
      split <;> simp [fakk_khaliyaMin, hharf, HalaIsm.ila]

theorem harf_thabit : harf 0 = 'ء' ∧ harf 2 = 'ا' ∧ harf 14 = 'ن' ∧ harf 18 = 'ت' := by decide

theorem taOf_salim (c : Siyaq) (ms : List Char) (sinf : Sinf) (ks : List Khaliya)
    (h : taOf c ms = .L sinf ks) : SahihL sinf ('ة' :: ms) ks := by
  rcases ms with _ | ⟨m, _ | ⟨_, _⟩⟩
  · simp [taOf] at h
  · simp only [taOf] at h
    by_cases hl : c.lahiq.isNone = true
    · rw [ite_eq_left hl] at h
      cases hh : halaAlama m with
      | some st =>
        rw [hh] at h
        simp only at h
        by_cases hs : (st == HalaIsm.sukun) = true
        · rw [ite_eq_left hs] at h; cases h
        · rw [ite_eq_right hs] at h; cases h
          exact ⟨m, st, rfl, Or.inl ⟨hh, by simpa using hs, by simp [fakk_khaliyaMin, harf_thabit, HalaIsm.ila]⟩⟩
      | none =>
        cases ht : tanwinHala m with
        | some st =>
          rw [hh, ht] at h; cases h
          exact ⟨m, st, rfl, Or.inr ⟨ht, by simp [fakk_khaliyaMin, harf_thabit, HalaIsm.ila]⟩⟩
        | none => rw [hh, ht] at h; cases h
    · rw [ite_eq_right hl] at h; cases h
  · simp [taOf] at h

theorem maqsuraOf_salim (c : Siyaq) (ms : List Char) (sinf : Sinf) (ks : List Khaliya)
    (h : maqsuraOf c ms = .L sinf ks) : SahihL sinf ('ى' :: ms) ks := by
  unfold maqsuraOf at h
  by_cases he : (ms.isEmpty && c.lahiq.isNone) = true
  · rw [ite_eq_left he] at h
    have hms : ms = [] := by simp only [Bool.and_eq_true, List.isEmpty_iff] at he; exact he.1
    subst hms
    cases hp : c.sabiq with
    | none => rw [hp] at h; cases h
    | some p =>
      rw [hp] at h
      simp only at h
      split at h
      · cases h; exact ⟨rfl, by simp [fakk_khaliyaMin, harf_thabit, HalaIsm.ila]⟩
      · split at h
        · cases h; exact ⟨Or.inr rfl, rfl⟩
        · cases h
  · rw [ite_eq_right he] at h; cases h

theorem tanwinOf_salim (c : Siyaq) (r : Char) (ms : List Char) (sinf : Sinf) (ks : List Khaliya)
    (h : tanwinOf c r ms = .L sinf ks) : SahihL sinf (r :: ms) ks := by
  unfold tanwinOf at h
  cases hh : hamilOf r with
  | none => rw [hh] at h; cases h
  | some hr =>
    cases hst : (ms.filterMap tanwinHala).head? with
    | none => rw [hh, hst] at h; cases h
    | some st =>
      rw [hh, hst] at h
      simp only at h
      have hharf := hamilOf_harf hh
      split at h
      · cases h
        refine ⟨r, ms, st, rfl, hst, ?_⟩
        split <;> simp [fakk_khaliyaMin, hharf, harf_thabit, HalaIsm.ila]
      · split at h
        · cases h
          rename_i hc
          simp only [Bool.and_eq_true, beq_iff_eq] at hc
          obtain ⟨⟨⟨hr1, hm1⟩, _⟩, _⟩ := hc
          subst hr1; subst hm1
          exact ⟨rfl, by simp [fakk_khaliyaMin, harf_thabit, HalaIsm.ila]⟩
        · cases h

theorem harakaTanwinOf_salim (r : Char) (sh : Bool) (s : List Char) (hs : s = [r] ∨ s = [r, shadda])
    (sinf : Sinf) (ks : List Khaliya) (h : harakaTanwinOf r sh = .L sinf ks) : SahihL sinf s ks := by
  unfold harakaTanwinOf at h
  cases hh : hamilOf r with
  | none => rw [hh] at h; cases h
  | some hr =>
    rw [hh] at h; cases h
    have hharf := hamilOf_harf hh
    refine ⟨r, sh, hs, ?_⟩
    cases sh <;> simp [fakk_khaliyaMin, hharf, HalaIsm.ila]

theorem shaddaIbtidaOf_salim (r : Char) (ms : List Char) (hsh : ms.contains shadda = true) (sinf : Sinf) (ks : List Khaliya)
    (h : shaddaIbtidaOf r ms = .L sinf ks) : SahihL sinf (r :: ms) ks := by
  unfold shaddaIbtidaOf at h
  cases hh : hamilOf r with
  | none => rw [hh] at h; cases h
  | some hr =>
    cases hst : (ms.filterMap halaAlama).head? with
    | none => rw [hh, hst] at h; cases h
    | some st =>
      rw [hh, hst] at h
      simp only at h
      by_cases hs : (st == HalaIsm.sukun) = true
      · rw [ite_eq_left hs] at h; cases h
      · rw [ite_eq_right hs] at h; cases h
        have hharf := hamilOf_harf hh
        exact ⟨r, ms, st, rfl, hsh, hst, by simpa using hs, by simp [fakk_khaliyaMin, hharf, HalaIsm.ila]⟩

theorem sukunOf_salim (r : Char) (sinf : Sinf) (ks : List Khaliya)
    (h : sukunOf r = .L sinf ks) : SahihL sinf [r] ks := by
  unfold sukunOf at h
  cases hh : hamilOf r with
  | none => rw [hh] at h; cases h
  | some hr =>
    rw [hh] at h; cases h
    exact ⟨r, rfl, by simp [fakk_khaliyaMin, hamilOf_harf hh, HalaIsm.ila]⟩

/-- الشدّةُ وحدها: علاماتٌ بلا علامة حركة، فيها شدّةٌ واحدة على الأكثر وفيها شدّة ⇒ هي الشدّةُ وحدها. -/
theorem shadda_wahda (ms : List Char) (hm : ∀ x ∈ ms, alama x = true) (n4 : mutaarida ms = false)
    (h14 : shaddaBilaHaraka ms = true) : ms = [shadda] := by
  simp only [shaddaBilaHaraka, Bool.and_eq_true, Bool.not_eq_true', List.any_eq_false] at h14
  simp only [mutaarida, Bool.or_eq_false_iff, decide_eq_false_iff_not, gt_iff_lt, Nat.not_lt] at n4
  have hall : ∀ x ∈ ms, x = shadda := by
    intro x hx
    have := hm x hx
    simp only [alama, Bool.or_eq_true, beq_iff_eq] at this
    rcases this with hb | hb
    · have := h14.2 x hx; simp [hb] at this
    · exact hb
  have hc : ms.count shadda = ms.length := List.count_eq_length.2 (fun x hx => by simp [hall x hx])
  have hpos : 0 < ms.length := List.length_pos_of_mem (List.contains_iff_mem.1 h14.1)
  match ms, hall, hc, hpos with
  | [a], hall, _, _ => rw [hall a (by simp)]
  | _ :: _ :: _, _, hc, _ => simp only [List.length_cons] at hc; omega

/-- **سلامةُ المرخَّص:** مقطعٌ ما بعد رأسه علامات، يرخّصه التصنيف بصنفٍ وخلايا ⇒ صحيحٌ بمعنى صنفه. -/
theorem tasnif_salim (c : Siyaq) (s : List Char) (sinf : Sinf) (ks : List Khaliya)
    (hm : ∀ x ∈ s.tail, alama x = true) (h : tasnif c s = .L sinf ks) : SahihL sinf s ks := by
  match s, hm, h with
  | [], _, h => cases h
  | r :: ms, hm, h =>
    simp only [List.tail_cons] at hm
    change tasnifRas c r ms = _ at h
    unfold tasnifRas at h
    by_cases h1 : (r == ' ') = true
    · rw [ite_eq_left h1] at h
      by_cases h1a : ms.isEmpty = true
      · rw [ite_eq_left h1a] at h
        cases h
        simp only [beq_iff_eq] at h1
        simp only [List.isEmpty_iff] at h1a
        subst h1; subst h1a; exact ⟨rfl, rfl⟩
      · rw [ite_eq_right h1a] at h; cases h
    rw [ite_eq_right h1] at h
    by_cases h2 : alama r = true
    · rw [ite_eq_left h2] at h; cases h
    rw [ite_eq_right h2] at h
    by_cases h3 : ghayrMaruf r = true
    · rw [ite_eq_left h3] at h; cases h
    rw [ite_eq_right h3] at h
    by_cases h4 : mutaarida ms = true
    · rw [ite_eq_left h4] at h; cases h
    rw [ite_eq_right h4] at h
    by_cases h5 : (r == 'ـ') = true
    · rw [ite_eq_left h5] at h
      by_cases h5a : ms.isEmpty = true
      · rw [ite_eq_left h5a] at h
        cases h
        simp only [beq_iff_eq] at h5
        simp only [List.isEmpty_iff] at h5a
        subst h5; subst h5a; exact ⟨rfl, rfl⟩
      · rw [ite_eq_right h5a] at h; cases h
    rw [ite_eq_right h5] at h
    by_cases h6 : alifAwwal c r = true
    · rw [ite_eq_left h6] at h
      by_cases h6a : ms.any harakaB = true
      · rw [ite_eq_left h6a] at h; cases h
      · rw [ite_eq_right h6a] at h
        by_cases h6b : (ms.isEmpty && lamBaad c) = true
        · rw [ite_eq_left h6b] at h
          cases h
          simp only [Bool.and_eq_true, List.isEmpty_iff] at h6b
          simp only [alifAwwal, Bool.and_eq_true, Bool.or_eq_true, beq_iff_eq] at h6
          rw [h6b.1]
          refine ⟨?_, by simp [fakk_khaliyaMin, harf_thabit, HalaIsm.ila]⟩
          rcases h6.1 with h' | h' <;> subst h' <;> simp
        · rw [ite_eq_right h6b] at h; cases h
    rw [ite_eq_right h6] at h
    by_cases h7 : (r == 'ٱ') = true
    · rw [ite_eq_left h7] at h; cases h
    rw [ite_eq_right h7] at h
    by_cases h8 : (r == 'آ') = true
    · rw [ite_eq_left h8] at h
      simp only [beq_iff_eq] at h8; subst h8
      by_cases h8a : ms.isEmpty = true
      · rw [ite_eq_left h8a] at h; cases h
        rw [show ms = [] by simpa using h8a]
        exact ⟨rfl, by simp [fakk_khaliyaMin, harf_thabit, HalaIsm.ila]⟩
      · rw [ite_eq_right h8a] at h; cases h
    rw [ite_eq_right h8] at h
    by_cases h9 : (r == 'ة') = true
    · rw [ite_eq_left h9] at h
      simp only [beq_iff_eq] at h9; subst h9
      exact taOf_salim c ms sinf ks h
    rw [ite_eq_right h9] at h
    by_cases h10 : (r == 'ى') = true
    · rw [ite_eq_left h10] at h
      simp only [beq_iff_eq] at h10; subst h10
      exact maqsuraOf_salim c ms sinf ks h
    rw [ite_eq_right h10] at h
    by_cases h11 : ms.any tanwin = true
    · rw [ite_eq_left h11] at h
      exact tanwinOf_salim c r ms sinf ks h
    rw [ite_eq_right h11] at h
    by_cases h12 : alifTanwin c r ms = true
    · rw [ite_eq_left h12] at h
      cases h
      simp only [alifTanwin, Bool.and_eq_true, beq_iff_eq, List.isEmpty_iff] at h12
      obtain ⟨⟨hra, hms⟩, _⟩ := h12
      subst hra; subst hms; exact ⟨Or.inl rfl, rfl⟩
    rw [ite_eq_right h12] at h
    by_cases h13 : alifJamaa c r ms = true
    · rw [ite_eq_left h13] at h
      cases h
      simp only [alifJamaa, Bool.and_eq_true, beq_iff_eq, List.isEmpty_iff] at h13
      obtain ⟨⟨⟨hra, hms⟩, _⟩, _⟩ := h13
      subst hra; subst hms; exact ⟨Or.inl rfl, rfl⟩
    rw [ite_eq_right h13] at h
    by_cases h14 : shaddaBilaHaraka ms = true
    · rw [ite_eq_left h14] at h
      by_cases h14' : (alifTanwinBaad c && (hamilOf r).isSome) = true
      · rw [ite_eq_left h14'] at h
        have hms := shadda_wahda ms hm (by simpa using h4) h14
        subst hms
        exact harakaTanwinOf_salim r true _ (Or.inr rfl) sinf ks h
      · rw [ite_eq_right h14'] at h; cases h
    rw [ite_eq_right h14] at h
    by_cases h14a : shaddaAwwal c r ms = true
    · rw [ite_eq_left h14a] at h
      simp only [shaddaAwwal, Bool.and_eq_true] at h14a
      exact shaddaIbtidaOf_salim r ms h14a.2 sinf ks h
    rw [ite_eq_right h14a] at h
    by_cases h14b : alifWasl c r ms = true
    · rw [ite_eq_left h14b] at h
      cases h
      simp only [alifWasl, Bool.and_eq_true, beq_iff_eq, List.isEmpty_iff] at h14b
      obtain ⟨⟨⟨⟨hra, hms⟩, _⟩, _⟩, _⟩ := h14b
      subst hra; subst hms; exact ⟨rfl, rfl⟩
    rw [ite_eq_right h14b] at h
    by_cases h15 : ms.isEmpty = true
    · rw [ite_eq_left h15] at h
      by_cases h15a : madd c r = true
      · rw [ite_eq_left h15a] at h
        have hms : ms = [] := by simpa using h15
        subst hms
        have hr : r = 'ا' ∨ r = 'و' ∨ r = 'ي' := by
          simp only [madd, Bool.and_eq_true, Bool.or_eq_true, beq_iff_eq] at h15a
          rcases h15a.1 with (h1 | h1) | h1
          · exact Or.inl h1
          · exact Or.inr (Or.inl h1)
          · exact Or.inr (Or.inr h1)
        cases sinf with
        | harfMadd => exact harfMaddOf_salim r ks hr h
        | _ => unfold harfMaddOf at h; split at h <;> cases h
      rw [ite_eq_right h15a] at h
      have hms : ms = [] := by simpa using h15
      subst hms
      by_cases h15b : lamTarif c r = true
      · rw [ite_eq_left h15b] at h
        split at h
        · cases h
          simp only [lamTarif, Bool.and_eq_true, beq_iff_eq] at h15b
          rw [h15b.1.1]; exact ⟨rfl, rfl⟩
        · cases h
      rw [ite_eq_right h15b] at h
      by_cases h15d : ((hamilOf r).isSome && c.sabiq.isSome && alifTanwinBaad c) = true
      · rw [ite_eq_left h15d] at h
        exact harakaTanwinOf_salim r false _ (Or.inl rfl) sinf ks h
      rw [ite_eq_right h15d] at h
      by_cases h15e : ((hamilOf r).isSome && c.sabiq.isSome) = true
      · rw [ite_eq_left h15e] at h
        exact sukunOf_salim r sinf ks h
      rw [ite_eq_right h15e] at h
      by_cases h15c : c.lahiq.isNone = true
      · rw [ite_eq_left h15c] at h; cases h
      · rw [ite_eq_right h15c] at h; cases h
    rw [ite_eq_right h15] at h
    exact harfHarakaOf_salim r ms sinf ks hm (by simpa using h4) (by simpa using h11) h

/-! ## ٥. البناء: المقاطعُ بمواضعها وسياقاتها وأحكامها -/

structure Maqta where
  i : Nat
  a : Nat
  b : Nat
  nass : List Char
  siyaq : Siyaq
  hukm : Hukm
  deriving Repr

def lahiqMin : List (List Char) → Option (List Char)
  | n :: _ => if fasil n then none else some n
  | [] => none

/-- المقطعُ بعد التالي في الكلمة. -/
def lahiq2Min : List (List Char) → Option (List Char)
  | n :: rest => if fasil n then none else lahiqMin rest
  | [] => none

def binaMin : Nat → Nat → Option (List Char) → Bool → Bool → Bool → List (List Char) → List Maqta
  | _, _, _, _, _, _, [] => []
  | i, k, p, pa, pw, ps, s :: rest =>
    let c : Siyaq := ⟨p, pa, pw, ps, lahiqMin rest, lahiq2Min rest, rest.takeWhile (fun n => !fasil n)⟩
    ⟨i, k, k + s.length, s, c, tasnif c s⟩ ::
      binaMin (i + 1) (k + s.length) (if fasil s then none else some s) (if fasil s then false else p.isNone)
        (tasnif c s == .L .hamzaWasl []) (fasil s || (ps && sabiqa s)) rest

/-- **التحصيل:** مقاطعُ النصّ بمواضعها وسياقاتها وأحكامها. -/
def tahsil (t : List Char) : List Maqta := binaMin 0 0 none false false true (qatta t)

theorem binaMin_nass (i k : Nat) (p : Option (List Char)) (pa pw ps : Bool) (ss : List (List Char)) :
    (binaMin i k p pa pw ps ss).map (·.nass) = ss := by
  induction ss generalizing i k p pa pw ps with
  | nil => rfl
  | cons s rest ih => simp [binaMin, ih]

theorem tahsil_nass (t : List Char) : (tahsil t).map (·.nass) = qatta t := binaMin_nass _ _ _ _ _ _ _

/-- **التحصيلُ بلا فقد:** ضمُّ نصوص المقاطع هو النصّ. -/
theorem tahsil_flatten (t : List Char) : ((tahsil t).map (·.nass)).flatten = t := by
  rw [tahsil_nass, qatta_flatten]

theorem mem_tahsil_qatta {t : List Char} {m : Maqta} (h : m ∈ tahsil t) : m.nass ∈ qatta t := by
  rw [← tahsil_nass]; exact List.mem_map_of_mem h

theorem binaMin_hukm (i k : Nat) (p : Option (List Char)) (pa pw ps : Bool) (ss : List (List Char)) :
    ∀ m ∈ binaMin i k p pa pw ps ss, m.hukm = tasnif m.siyaq m.nass := by
  induction ss generalizing i k p pa pw ps with
  | nil => simp [binaMin]
  | cons s rest ih =>
    intro m hm
    simp only [binaMin, List.mem_cons] at hm
    rcases hm with rfl | hm
    · rfl
    · exact ih _ _ _ _ _ _ m hm

theorem tahsil_hukm (t : List Char) : ∀ m ∈ tahsil t, m.hukm = tasnif m.siyaq m.nass :=
  binaMin_hukm _ _ _ _ _ _ _

/-- المواضعُ متّصلةٌ من k إلى n، وكلُّ موضعٍ غيرُ فارغ. -/
def tughatti : Nat → List Maqta → Nat → Prop
  | k, [], n => k = n
  | k, m :: ms, n => m.a = k ∧ m.a < m.b ∧ tughatti m.b ms n

theorem binaMin_tughatti (i k : Nat) (p : Option (List Char)) (pa pw ps : Bool) (ss : List (List Char))
    (hne : ∀ s ∈ ss, s ≠ []) : tughatti k (binaMin i k p pa pw ps ss) (k + (ss.map List.length).sum) := by
  induction ss generalizing i k p pa pw ps with
  | nil => simp [binaMin, tughatti]
  | cons s rest ih =>
    simp only [binaMin]
    have hs : s.length > 0 := List.length_pos_iff.2 (hne s (List.mem_cons_self))
    refine ⟨rfl, ?_, ?_⟩
    · show k < k + s.length
      omega
    · rw [List.map_cons, List.sum_cons, ← Nat.add_assoc]
      exact ih _ _ _ _ _ _ (fun x hx => hne x (List.mem_cons_of_mem _ hx))

/-- **التغطية:** مواضعُ المقاطع متّصلةٌ تبدأ من 0 وتنتهي بطول النصّ، ولا موضعَ فارغ. -/
theorem tahsil_tughatti (t : List Char) : tughatti 0 (tahsil t) t.length := by
  have := binaMin_tughatti 0 0 none false false true (qatta t) (qatta_ghayr_farigh t)
  rwa [← List.length_flatten, qatta_flatten, Nat.zero_add] at this

theorem binaMin_muhadha (i k : Nat) (p : Option (List Char)) (pa pw ps : Bool) (ss : List (List Char))
    (pre : List Char) (hpre : pre.length = k) :
    ∀ m ∈ binaMin i k p pa pw ps ss, ((pre ++ ss.flatten).drop m.a).take (m.b - m.a) = m.nass ∧
      m.b ≤ (pre ++ ss.flatten).length := by
  induction ss generalizing i k p pa pw ps pre with
  | nil => simp [binaMin]
  | cons s rest ih =>
    intro m hm
    simp only [binaMin, List.mem_cons] at hm
    rcases hm with rfl | hm
    · subst hpre
      simp only [List.flatten_cons, List.length_append]
      refine ⟨?_, by omega⟩
      show List.take (pre.length + s.length - pre.length) (List.drop pre.length (pre ++ (s ++ rest.flatten))) = s
      rw [List.drop_left, Nat.add_sub_cancel_left, List.take_left]
    · have := ih (i + 1) (k + s.length) _ _ _ _ (pre ++ s) (by simp [hpre]) m hm
      simpa [List.append_assoc] using this

/-- **المحاذاة بنقاط الرمز:** ذرّاتُ النصّ في موضع المقطع هي المقطعُ بعينه، والموضعُ داخل النصّ. -/
theorem tahsil_muhadha (t : List Char) :
    ∀ m ∈ tahsil t, (t.drop m.a).take (m.b - m.a) = m.nass ∧ m.b ≤ t.length := by
  intro m hm
  have := binaMin_muhadha 0 0 none false false true (qatta t) [] rfl m hm
  simpa [qatta_flatten] using this

theorem tughatti_mem {k n : Nat} : ∀ {ms : List Maqta}, tughatti k ms n → ∀ m ∈ ms, m.a < m.b
  | [], _, _, hm => by simp at hm
  | m' :: ms, h, m, hm => by
    simp only [tughatti] at h
    rcases List.mem_cons.1 hm with rfl | hm
    · exact h.2.1
    · exact tughatti_mem h.2.2 m hm

/-- موضعُ المقطع في مصدر NABT. -/
def mawdi (src : Source Char) (m : Maqta) : Span :=
  ⟨src.sourceId, src.revision, src.scopeId, src.atomizationId, m.a, m.b⟩

/-- **الموضعُ في مصدر NABT:** صالحٌ، وذرّاتُه المقطع. -/
theorem mawdi_sahih (src : Source Char) :
    ∀ m ∈ tahsil src.atoms, validSpan src (mawdi src m) = true ∧ spanAtoms src (mawdi src m) = m.nass := by
  intro m hm
  have ⟨hat, hle⟩ := tahsil_muhadha src.atoms m hm
  have hlt := tughatti_mem (tahsil_tughatti src.atoms) m hm
  refine ⟨?_, hat⟩
  unfold validSpan
  exact decide_eq_true ⟨rfl, rfl, rfl, rfl, hlt, hle⟩

/-- **التصنيفُ سليمٌ على المقاطع:** كلُّ مقطعٍ مرخَّصٍ في التحصيل صحيحٌ بمعنى صنفه. -/
theorem tahsil_salim (t : List Char) :
    ∀ m ∈ tahsil t, ∀ sinf ks, m.hukm = .L sinf ks → SahihL sinf m.nass ks := by
  intro m hm sinf ks h
  rw [tahsil_hukm t m hm] at h
  exact tasnif_salim _ _ _ _ (qatta_alamat t _ (mem_tahsil_qatta hm)) h

/-! ## ٦. الشهادة لكلّ مقطع -/

def ismSinf : Sinf → String
  | .fasil => "Dal.Tahsil.fasil"
  | .tatwil => "Dal.Tahsil.tatwil"
  | .harfMadd => "Dal.Tahsil.harfMadd"
  | .harfHaraka => "Dal.Tahsil.harfHaraka"
  | .hamzaWasl => "Dal.Tahsil.hamzaWasl"
  | .hamzaWaslAl => "Dal.Tahsil.hamzaWaslAl"
  | .madda => "Dal.Tahsil.madda"
  | .taMarbuta => "Dal.Tahsil.taMarbuta"
  | .alifMaqsura => "Dal.Tahsil.alifMaqsura"
  | .alifKhatt => "Dal.Tahsil.alifKhatt"
  | .tanwin => "Dal.Tahsil.tanwin"
  | .tanwinAlif => "Dal.Tahsil.tanwinAlif"
  | .harakaMinTanwin => "Dal.Tahsil.harakaMinTanwin"
  | .shaddaIbtida => "Dal.Tahsil.shaddaIbtida"
  | .lamMudgham => "Dal.Tahsil.lamMudgham"
  | .sukunMuqaddar => "Dal.Tahsil.sukunMuqaddar"

def madkhalSalim : String := "مدخل سليم"

theorem ismSinf_ne (s : Sinf) : ismSinf s ≠ madkhalSalim ∧ ismSinf s ≠ "" := by cases s <;> decide

def khalayaOf : Hukm → List Khaliya
  | .L _ ks => ks
  | _ => []

/-- هويّةُ القاعدة: صنفُ المرخَّص؛ وفي المعلَّق والفاسد التصنيفُ نفسُه، واسمُ القاعدة الناقصة أو السببِ في المقدّمة. -/
def qaidaOf : Hukm → Hawiyya
  | .L s _ => ⟨ismSinf s, 1⟩
  | .P _ => ⟨"Dal.Tahsil.tasnif", 1⟩
  | .F _ => ⟨"Dal.Tahsil.tasnif", 1⟩

/-- المقدّماتُ بشواهدها: صحّةُ المدخل وقاعدةُ الصنف في المرخَّص، والقاعدةُ الناقصةُ بلا سندٍ في المعلَّق، وسببُ الفساد في الفاسد. -/
def muqaddimatOf : Hukm → List Muqaddima
  | .L s _ => [⟨madkhalSalim, .madkhal, .mashhud, "Dal.Tahsil.tasnif"⟩, ⟨ismSinf s, .shart, .mashhud, "Dal.Tahsil.tasnif"⟩]
  | .P ism => [⟨madkhalSalim, .madkhal, .mashhud, "Dal.Tahsil.tasnif"⟩, ⟨ism, .shart, .ghayrMafhus, ""⟩]
  | .F ism => [⟨ism, .madkhal, .manfi, "Dal.Tahsil.tasnif"⟩]

def haddTabaqa : String :=
  "الطبقة ١: قطع ومحاذاة بنقاط الرمز وخلايا الحرف المحرّك وحرف المدّ؛ لا وصل ولا وقف ولا إعراب"

/-- **الانتقالُ المشهود للمقطع:** مصدرُه وموضعُه، والمدخلُ (السياقُ والمقطع) والمخرجُ (الخلايا)، وهويّةُ القاعدة، ومقدّماتُها،
    وحدُّ الدعوى. -/
def shahada (src : Source Char) (m : Maqta) : Naqla (Siyaq × List Char) (List Khaliya) :=
  ⟨src, mawdi src m, (m.siyaq, m.nass), khalayaOf m.hukm, qaidaOf m.hukm, muqaddimatOf m.hukm, [], haddTabaqa⟩

def natijaOf : Hukm → Natija
  | .L _ _ => .murakhkhas
  | .P ism => .muallaq [ism]
  | .F ism => .madkhalFasid ism

/-- **حكمُ الفاحص هو حكمُ التصنيف** على كلّ مقطعٍ في التحصيل. -/
theorem shahada_hukm (src : Source Char) (m : Maqta) (hm : m ∈ tahsil src.atoms) :
    Nizam.Shahada.hukm (shahada src m) = natijaOf m.hukm := by
  have hv := (mawdi_sahih src m hm).1
  cases hh : m.hukm with
  | L s ks =>
    show Nizam.Shahada.hukm (shahada src m) = .murakhkhas
    rw [Nizam.Shahada.murakhkhas_iff]
    refine ⟨?_, ⟨⟨madkhalSalim, .madkhal, .mashhud, "Dal.Tahsil.tasnif"⟩, by simp [shahada, hh, muqaddimatOf], rfl⟩, ?_⟩
    · simp only [Nizam.Shahada.Naqla.marbut, shahada, hv, hh, qaidaOf, Bool.true_and, Bool.not_eq_true']
      simpa using (ismSinf_ne s).2
    · intro q hq
      simp only [shahada, hh, muqaddimatOf, List.mem_cons, List.not_mem_nil, or_false] at hq
      rcases hq with rfl | rfl <;> rfl
  | P ism =>
    have hb : (shahada src m).marbut = true := by
      simp only [Nizam.Shahada.Naqla.marbut, shahada, hv, hh, qaidaOf, Bool.true_and, Bool.not_eq_true']
      decide
    simp only [Nizam.Shahada.hukm, hb, ite_true, natijaOf]
    simp [Nizam.Shahada.hukmMarbut, Nizam.Shahada.awwalNaqid, Nizam.Shahada.naqisa, Nizam.Shahada.naqisaMadkhal,
      Nizam.Shahada.fihiMadkhal, shahada, hh, muqaddimatOf, Muqaddima.halFiil, Nizam.Shahada.naqid, madkhalSalim]
  | F ism =>
    have hb : (shahada src m).marbut = true := by
      simp only [Nizam.Shahada.Naqla.marbut, shahada, hv, hh, qaidaOf, Bool.true_and, Bool.not_eq_true']
      decide
    simp only [Nizam.Shahada.hukm, hb, ite_true, natijaOf]
    simp [Nizam.Shahada.hukmMarbut, Nizam.Shahada.awwalNaqid, shahada, hh, muqaddimatOf, Muqaddima.halFiil,
      Nizam.Shahada.naqid]

/-! ## ٧. العقدُ مطبَّقًا على قواعد الترخيص الأربع -/

/-- **القاعدة بمعناها:** المدخلُ صحيحٌ إذا كان موضعُه صالحًا وذرّاتُه المقطعَ، وكان المقطعُ بسياقه مقطعَ ذلك الموضع في تحصيل المصدر
    (مطابقةُ المصدر والمقام)؛ والمقدّمتان صحّةُ المدخل (لا سببَ فساد) وانطباقُ الصنف؛ والمخرجُ صحيحٌ بمعنى الصنف (`SahihL`). -/
def qaida (s : Sinf) : Nizam.Shahada.Qaida (Siyaq × List Char) (List Khaliya) where
  hawiyya := ⟨ismSinf s, 1⟩
  asma := [(madkhalSalim, .madkhal), (ismSinf s, .shart)]
  tatbiq x := khalayaOf (tasnif x.1 x.2)
  sahihMadkhal src sp x := validSpan src sp = true ∧ spanAtoms src sp = x.2 ∧
    ∃ m ∈ tahsil src.atoms, m.a = sp.start ∧ m.b = sp.stop ∧ m.nass = x.2 ∧ m.siyaq = x.1
  sadiq ism x := (ism = madkhalSalim → ∀ e, tasnif x.1 x.2 ≠ .F e) ∧
    (ism = ismSinf s → ∃ ks, tasnif x.1 x.2 = .L s ks)
  sahihMakhraj src sp x y := spanAtoms src sp = x.2 ∧ SahihL s x.2 y
  aqd := by
    intro src sp x hin hs _
    obtain ⟨_, hat, m, hm, _, _, hn, _⟩ := hin
    obtain ⟨ks, hks⟩ := (hs (ismSinf s, .shart) (by simp) (by simp)).2 rfl
    refine ⟨hat, ?_⟩
    simp only [hks, khalayaOf]
    have hal := qatta_alamat src.atoms _ (mem_tahsil_qatta hm)
    rw [hn] at hal
    exact tasnif_salim _ _ _ _ hal hks

/-- **الشواهدُ التنفيذيّة للعقد:** كلُّ مقطعٍ مرخَّصٍ في تحصيل المصدر شهادتُه أمينةٌ لقاعدة صنفه، صادقةُ الشواهد، صحيحةُ المدخل؛
    فمخرجُها صحيحٌ بعقد القاعدة — من `Nizam.Shahada.shahada_salima` نفسِها. -/
theorem shahada_tahsil_salima (src : Source Char) (m : Maqta) (hm : m ∈ tahsil src.atoms) (s : Sinf)
    (ks : List Khaliya) (hh : m.hukm = .L s ks) :
    (qaida s).sahihMakhraj src (mawdi src m) (m.siyaq, m.nass) (shahada src m).makhraj := by
  have hk := tahsil_hukm src.atoms m hm
  have ⟨hv, hat⟩ := mawdi_sahih src m hm
  have hmur : Nizam.Shahada.hukm (shahada src m) = .murakhkhas := by
    rw [shahada_hukm src m hm, hh]
    rfl
  have hne := ismSinf_ne s
  refine Nizam.Shahada.shahada_salima (qaida s) (shahada src m) ?_ ?_ ?_ hmur
  · refine ⟨by simp [shahada, hh, qaidaOf, qaida], ?_, ?_⟩
    · show khalayaOf m.hukm = khalayaOf (tasnif m.siyaq m.nass)
      rw [← hk]
    · simp [shahada, qaida, hh, muqaddimatOf]
  · intro q hq
    simp only [shahada, hh, muqaddimatOf, List.mem_cons, List.not_mem_nil, or_false] at hq
    rcases hq with rfl | rfl
    · refine ⟨fun _ => ⟨fun _ e h2 => ?_, fun e => absurd e.symm hne.1⟩, fun e => by cases e⟩
      show False
      change tasnif m.siyaq m.nass = _ at h2
      rw [← hk, hh] at h2; cases h2
    · refine ⟨fun _ => ⟨fun e => absurd e hne.1, fun _ => ⟨ks, ?_⟩⟩, fun e => by cases e⟩
      show tasnif m.siyaq m.nass = _
      rw [← hk, hh]
  · exact ⟨hv, hat, m, hm, rfl, rfl, rfl, rfl⟩

/-! ## ٨. محاذاةُ الخلايا، والكلمات -/

/-- كلُّ خليّةٍ مرخَّصةٍ مقرونةً بموضع مقطعها بنقاط الرمز. -/
def khalayaMuhadhat (t : List Char) : List (Khaliya × Nat × Nat) :=
  (tahsil t).flatMap fun m => (khalayaOf m.hukm).map fun k => (k, m.a, m.b)

/-- ما يُبدَل به الرأسُ في التعديل الثالث: نونُ التنوين لكلّ رأس، وهمزةُ أل للألف، والهمزةُ والألفُ للممدودة، والتاءُ للمربوطة، والألفُ
    للمقصورة. -/
def ibdal (r : Char) : List Char :=
  'ن' :: (if r == 'ا' || r == 'ٱ' then ['ء'] else if r == 'آ' then ['ء', 'ا'] else if r == 'ة' then ['ت']
    else if r == 'ى' then ['ا'] else [])

/-- **محاذاةُ الخلايا:** كلُّ خليّةٍ في تيّار الخلايا لها موضعُ مقطعٍ في النصّ، ذرّاتُه المقطع، وحرفُ حاملها رأسُه (والمقعدُ همزة) أو بدلُه
    المسمّى (`ibdal`). -/
theorem khalaya_muhadhat (t : List Char) :
    ∀ x ∈ khalayaMuhadhat t, ∃ m ∈ tahsil t, m.a = x.2.1 ∧ m.b = x.2.2 ∧
      (t.drop m.a).take (m.b - m.a) = m.nass ∧ ∃ r ∈ m.nass.head?,
        harf x.1.hamil = raddHarf r ∨ harf x.1.hamil ∈ ibdal r := by
  intro x hx
  simp only [khalayaMuhadhat, List.mem_flatMap, List.mem_map] at hx
  obtain ⟨m, hm, k, hk, rfl⟩ := hx
  refine ⟨m, hm, rfl, rfl, (tahsil_muhadha t m hm).1, ?_⟩
  cases hh : m.hukm with
  | P _ => rw [hh] at hk; cases hk
  | F _ => rw [hh] at hk; cases hk
  | L s ks =>
    rw [hh] at hk
    have hs := tahsil_salim t m hm s ks hh
    have hkm : fakkKhaliya k ∈ ks.map fakkKhaliya := List.mem_map_of_mem hk
    cases s with
    | fasil => rw [hs.2] at hk; cases hk
    | tatwil => rw [hs.2] at hk; cases hk
    | hamzaWasl => rw [hs.2] at hk; cases hk
    | harfMadd =>
      obtain ⟨r, hr, hmem, hmap⟩ := hs
      refine ⟨r, by simp [hr], ?_⟩
      rw [hmap, List.mem_singleton] at hkm
      have hk1 : harf k.hamil = r := congrArg Prod.fst hkm
      have hrad : raddHarf r = r := by
        unfold raddHarf
        rcases hmem with h | h | h <;> subst h <;> decide
      exact Or.inl (by rw [hk1, hrad])
    | alifKhatt => rw [hs.2] at hk; cases hk
    | lamMudgham => rw [hs.2] at hk; cases hk
    | hamzaWaslAl =>
      obtain ⟨hr, hmap⟩ := hs
      rw [hmap, List.mem_singleton] at hkm
      have hk1 : harf k.hamil = 'ء' := congrArg Prod.fst hkm
      rcases hr with hr | hr
      · exact ⟨'ا', by simp [hr], Or.inr (by rw [hk1]; decide)⟩
      · exact ⟨'ٱ', by simp [hr], Or.inr (by rw [hk1]; decide)⟩
    | madda =>
      obtain ⟨hr, hmap⟩ := hs
      rw [hmap] at hkm
      refine ⟨'آ', by simp [hr], Or.inr ?_⟩
      simp only [List.mem_cons, List.not_mem_nil, or_false] at hkm
      rcases hkm with hkm | hkm <;> (have e : harf k.hamil = (fakkKhaliya k).1 := rfl; rw [e, hkm]; dsimp only; first | exact List.mem_cons_self | decide)
    | taMarbuta =>
      obtain ⟨mm, st, hr, hc⟩ := hs
      refine ⟨'ة', by simp [hr], Or.inr ?_⟩
      rcases hc with ⟨_, _, hmap⟩ | ⟨_, hmap⟩ <;> rw [hmap] at hkm <;>
        simp only [List.mem_cons, List.not_mem_nil, or_false] at hkm
      · (have e : harf k.hamil = (fakkKhaliya k).1 := rfl; rw [e, hkm]; dsimp only; first | exact List.mem_cons_self | decide)
      · rcases hkm with hkm | hkm <;> (have e : harf k.hamil = (fakkKhaliya k).1 := rfl; rw [e, hkm]; dsimp only; first | exact List.mem_cons_self | decide)
    | alifMaqsura =>
      obtain ⟨hr, hmap⟩ := hs
      rw [hmap, List.mem_singleton] at hkm
      refine ⟨'ى', by simp [hr], Or.inr ?_⟩
      (have e : harf k.hamil = (fakkKhaliya k).1 := rfl; rw [e, hkm]; dsimp only; first | exact List.mem_cons_self | decide)
    | tanwinAlif =>
      obtain ⟨hr, hmap⟩ := hs
      rw [hmap, List.mem_singleton] at hkm
      refine ⟨'ا', by simp [hr], Or.inr ?_⟩
      (have e : harf k.hamil = (fakkKhaliya k).1 := rfl; rw [e, hkm]; dsimp only; first | exact List.mem_cons_self | decide)
    | tanwin =>
      obtain ⟨r, ms, st, hr, _, hmap⟩ := hs
      refine ⟨r, by simp [hr], ?_⟩
      rw [hmap] at hkm
      simp only [List.mem_append, List.mem_cons, List.not_mem_nil, or_false] at hkm
      rcases hkm with hkm | hkm | hkm
      · split at hkm
        · simp only [List.mem_singleton] at hkm; exact Or.inl (congrArg Prod.fst hkm)
        · cases hkm
      · exact Or.inl (congrArg Prod.fst hkm)
      · exact Or.inr (by (have e : harf k.hamil = (fakkKhaliya k).1 := rfl; rw [e, hkm]; dsimp only; first | exact List.mem_cons_self | decide))
    | harakaMinTanwin =>
      obtain ⟨r, sh, hr, hmap⟩ := hs
      refine ⟨r, by rcases hr with hr | hr <;> simp [hr], Or.inl ?_⟩
      rw [hmap] at hkm
      simp only [List.mem_append, List.mem_singleton] at hkm
      rcases hkm with hkm | hkm
      · split at hkm
        · simp only [List.mem_singleton] at hkm; exact congrArg Prod.fst hkm
        · cases hkm
      · exact congrArg Prod.fst hkm
    | shaddaIbtida =>
      obtain ⟨r, ms, st, hr, _, _, _, hmap⟩ := hs
      refine ⟨r, by simp [hr], Or.inl ?_⟩
      rw [hmap, List.mem_singleton] at hkm
      exact congrArg Prod.fst hkm
    | sukunMuqaddar =>
      obtain ⟨r, hr, hmap⟩ := hs
      refine ⟨r, by simp [hr], Or.inl ?_⟩
      rw [hmap, List.mem_singleton] at hkm
      exact congrArg Prod.fst hkm
    | harfHaraka =>
      obtain ⟨r, ms, st, hr, _, _, _, hmap⟩ := hs
      refine ⟨r, by simp [hr], ?_⟩
      rw [hmap] at hkm
      have : (fakkKhaliya k).1 = raddHarf r := by
        simp only [List.mem_append, List.mem_singleton] at hkm
        rcases hkm with hkm | hkm
        · split at hkm
          · simp only [List.mem_singleton] at hkm
            rw [hkm]
          · cases hkm
        · rw [hkm]
      exact Or.inl this

structure Kalima where
  a : Nat
  b : Nat
  murakhkhasa : Bool
  khalaya : List Khaliya
  deriving Repr

def mL : Hukm → Bool
  | .L _ _ => true
  | _ => false

def kalimaMin (ms : List Maqta) : Option Kalima :=
  match ms.head?, ms.getLast? with
  | some f, some l =>
    let ks := ms.flatMap (fun m => khalayaOf m.hukm)
    some ⟨f.a, l.b, ms.all (fun m => mL m.hukm) && !ks.isEmpty, ks⟩
  | _, _ => none

/-- الكلماتُ: أطولُ المتتاليات من المقاطع التي ليس رأسُها الفراغ. -/
def kalimat (t : List Char) : List Kalima :=
  let gs := (tahsil t).foldl (fun (acc : List (List Maqta)) m =>
    if fasil m.nass then [] :: acc
    else match acc with
      | g :: gs => (g ++ [m]) :: gs
      | [] => [[m]]) [[]]
  gs.reverse.filterMap kalimaMin

/-! ## ٩. شواهد -/

/-- «كَتَبَ»: ثلاثةُ مقاطع مرخَّصة متّصلة، وخلاياها 32 و72 و104 بترميز المالك. -/
theorem shahid_kataba :
    (tahsil "كَتَبَ".toList).map (fun m => (m.a, m.b, m.hukm)) =
      [(0, 2, .L .harfHaraka [⟨8, 0⟩]), (2, 4, .L .harfHaraka [⟨18, 0⟩]), (4, 6, .L .harfHaraka [⟨26, 0⟩])] ∧
    ((tahsil "كَتَبَ".toList).flatMap (fun m => khalayaOf m.hukm)).map Dal.n = [32, 72, 104] := by
  decide

/-- «ٱلشَّمْسُ»: همزةُ أل مفتوحةً (التعديل الثالث، 6) ولامُ التعريف مدغمةٌ في الشين بلا خليّة (15)، والباقي مرخَّص. -/
theorem shahid_shams :
    (tahsil "ٱلشَّمْسُ".toList).map (fun m => m.hukm) =
      [.L .hamzaWaslAl [⟨0, 0⟩], .L .lamMudgham [], .L .harfHaraka [⟨10, 3⟩, ⟨10, 0⟩],
       .L .harfHaraka [⟨27, 3⟩], .L .harfHaraka [⟨20, 1⟩]] := by
  decide

/-- «كِتَابًا» و«ذَهَبُوا»: التنوينُ نونٌ ساكنةٌ بعد حركته، وألفُه وألفُ الجماعة خطٌّ بلا خليّة (التعديل الثالث، 11–13)؛ وحرفٌ بلا حركةٍ
    أوّلَ الكلمة مدخلٌ فاسدٌ كما كان. -/
theorem shahid_muallaq :
    ((tahsil "كِتَابًا".toList).map (fun m => m.hukm)).drop 3 = [.L .tanwin [⟨26, 0⟩, ⟨14, 3⟩], .L .alifKhatt []] ∧
    ((tahsil "ذَهَبُوا".toList).map (fun m => m.hukm)).drop 3 = [.L .harfMadd [⟨28, 3⟩], .L .alifKhatt []] ∧
    ((tahsil "كتَبَ".toList).map (fun m => m.hukm)).head? = some (.F "حرف بلا حركة في غير آخر الكلمة") := by
  decide

/-- القاعدتان 14أ و14ب: «وَالْأَرْضِ» ألفُها بعد السابقة ألفُ وصلٍ بلا خليّة والكلمةُ مرخَّصة؛ و«بِاللَّهِ» لامُها بعد ألف الوصل لامُ التعريف المدغمة؛
    و«قَالْتُ» ألفُها في وسط الكلمة حرفُ مدٍّ لا ألفُ وصل؛ و«مِّنَ» شدّتُها أوّلَ الكلمة يسقط نصفُها الساكن (التعديل الثالث، 14أ). -/
theorem shahid_wasl :
    (kalimat "وَالْأَرْضِ".toList).map (fun k => (k.murakhkhasa, k.khalaya.map Dal.n)) = [(true, [112, 55, 0, 63, 50])] ∧
    (((tahsil "وَالْأَرْضِ".toList).map (fun m => m.hukm)).drop 1).head? = some (.L .hamzaWasl []) ∧
    ((((tahsil "بِاللَّهِ".toList).map (fun m => m.hukm)).drop 1).take 2) = [.L .hamzaWasl [], .L .lamMudgham []] ∧
    (((tahsil "قَالْتُ".toList).map (fun m => m.hukm)).drop 1).head? = some (.L .harfMadd [⟨2, 3⟩]) ∧
    ((tahsil "مِّنَ".toList).map (fun m => m.hukm)).head? = some (.L .shaddaIbtida [⟨27, 2⟩]) := by
  decide

end Dal.Tahsil
