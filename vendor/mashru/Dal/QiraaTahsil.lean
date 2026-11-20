import Dal.Tahsil
import Dal.Jumla

/-!
# القارئ على التحصيل: كلُّ خليّةٍ من مقطعٍ مشهود

**الطلب.** الأولويّة ١ من رسالة المالك 2026-10-27 (ما حُفظ منها في رأس `Nizam/Shahada.lean`)، وبندُها الأوّل بعد التحصيل في
`hawkama/عقد_الشهادة.md` §٣ مقترحُ البنّاء. واختاره المالك بعد دمج #92 من سؤالٍ متعدّد الخيارات نصُّ خياراته من البنّاء: «وصلُ القارئ
بالتحصيل (موصى به)» (لفظُه من ملخّص الجلسة بعد ضغطها). والتصميمُ قرارُ البنّاء.

**ما كان.** `tahlil` في `Qari/Main.lean` حلقةٌ أمريّة على الحروف بعد حذف التطويل: لا موضعَ لخليّة ولا شهادة، ووسائطُ ما لم تُبنَ قاعدتُه
مخلوطةٌ بقراءة الحرف المحرّك. والتحصيلُ (`Dal/Tahsil.lean`، #92) كان خارج المحرّك.

**ما صار.** القارئُ يقرأ الكلمةَ على تحصيلها (`qiraa`)، مقطعًا مقطعًا بترتيبها (`juzOf`، `ajza`):
- المقطعُ المرخَّص خلاياه بعينها (`khalayaTahsil`).
- المقطعُ الفاسد رفضٌ للكلمة باسم سببه وبنصّ المقطع.
- المقطعُ المعلَّقُ باسم قاعدته وسيطُ القارئ لها (`wasitOf`): قراءةُ البنّاء لما كان `tahlil` يفعله بذلك المقطع، على سياقه في التحصيل؛ وما
  لا وسيطَ له في موضعه رفضٌ باسم قاعدته (`bilaWasit`).
- وحيث يقرأ التحصيلُ غيرَ ما كان القارئ يقرؤه يتبعه القارئ (`qiraa_tahsil`)، فتتغيّر القراءة: التطويلُ المجرّد مقطعٌ يفصل ما قبله عمّا بعده
  (وكان القارئ يحذفه قبل القراءة)، فالحرفُ بلا علامةٍ قبله فاسدٌ في التحصيل لا آخرُ الكلمة، واللامُ قبله ليست لامَ تعريفٍ مدغمة، والألفُ
  بعده حرفُ مدّ. وألفُ الجماعة لا تكون إلّا بعد واوٍ مجرّدةٍ أو ساكنةٍ تليها (وكان القارئ يعدّها بعد كلّ حرفٍ خليّتُه الأخيرة واوٌ ساكنة)، ولا
  يليها شيء: فالألفُ والمقصورةُ بعد الواو يليهما تطويلٌ مجرّد («قَالُواـ»، «قَالُوىـ») منطوقتان، وكان القارئ يحذف التطويلَ فيقرؤهما ألفَ جماعة
  (`shahid_jamaa`). وما سوى ذلك من المعلَّق يعدّ وسيطُه التطويلَ المجرّد بعده كأنّه غيرُ موجود (`akhirFi` أدناه).
- كلُّ خليّةٍ بموضع مقطعها بنقاط الرمز وأصلِها (`KhaliyaQ`، `Asl`). وبعد المقاطع: الكلمةُ بلا خليّةٍ مرفوضة، وهمزةُ الوصل قبل متحرّكٍ
  مرفوضة، وهمزةُ «أل» من لام التعريف المدغمة أو من لامٍ ساكنةٍ أوّلَ الخلايا (`tamm`)، كما كان.

**المبرهن** (على كلّ كلمة):
- `qiraa_tahsil`: ما أصلُه التحصيلُ من خلايا القراءة هو خلايا المقاطع المرخَّصة بعينها وبترتيبها، في الوقف والوصل: لا يُسقَط منها شيءٌ
  ولا يُبدَّل ولا يُزاد.
- `qiraa_asl` و`qiraa_shahada`: لكلّ خليّةٍ مقطعٌ في التحصيل موضعُه موضعُها، صالحٌ في مصدر NABT وذرّاتُه المقطع، وحكمُ الفاحص
  (`Nizam.Shahada.hukm`) على شهادته ترخيصٌ إن كان أصلُها التحصيل، وتعليقٌ باسم القاعدة إن كان أصلُها وسيطَها.
- `qiraa_la_fasid`: لا تُقرأ كلمةٌ في تحصيلها مقطعٌ فاسد.
- `qiraa_murakhkhasa`: الكلمةُ المرخَّصةُ مقاطعُها كلُّها، ولها خليّة، قراءتُها خلايا التحصيل بلا همزة وصلٍ ولا ملاحظة.
- وخليّةُ همزة الوصل التي يضيفها القارئ بعد القراءة (`ibtida` في `Qari/Main.lean`) ليست من خلايا `qiraa`، فلا تتناولها هذه المبرهنات.

**الوسائط** (`wasitOf`؛ قراءةُ البنّاء لـ`tahlil` كما كان في main ‏09f7b27، وسندُ ما فيها من القطر والألفية في رأس `Qari/Main.lean`):
- همزةُ الوصل: ألفٌ أو ألفُ وصلٍ مجرّدةٌ أوّلَ الكلمة لا خليّةَ لها، والكلمةُ بهمزة وصل. وفي غير الأوّل، أو بعلامة: لا وسيط.
- الممدودة: مجرّدةً همزةٌ مفتوحةٌ ثمّ ألفٌ ساكنة؛ وبعلامة: لا وسيط.
- التاءُ المربوطة: في غير آخر الكلمة رفض؛ وفي الوقف هاءٌ ساكنة؛ وفي الوصل تاءٌ بعلاماتها (`harfAam`).
- المقصورة: بعد تنوين الفتح مجرّدةً ألفُ التنوين بلا خليّة، وبعلامة لا وسيط؛ وأوّلَ الكلمة لا وسيط؛ وبعد واوٍ مجرّدةٍ أو ساكنةٍ، مجرّدةً لا
  يليها شيء (`lahiq`، لا `akhirFi`، كألف الجماعة في التحصيل)، ألفُ الجماعة بلا خليّة؛ وإلّا ألفٌ (`harfAam` بحامل الألف).
- التنوين، والشدّةُ بلا حركة، والحرفُ الأخير بلا حركة: `harfAam` بحامل الرأس.
- ألفُ التنوين وألفُ الجماعة: لا خليّة. ولامُ التعريف المدغمة: لا خليّة، وهمزتُها همزةُ «أل».
- التطويلُ بعلامة: لا وسيط.
- آخرُ الكلمة في الوسائط (`akhirFi`): ما بعد المقطع تطويلٌ مجرّدٌ كلُّه، أو عليه فتحتان ويليه ألفٌ أو ألفٌ مقصورةٌ مجرّدة ثمّ تطويلٌ مجرّدٌ
  كلُّه. فالتطويلُ المجرّد آخرَ الكلمة بعد التنوين أو التاء المربوطة أو الشدّة بلا حركة أو المقصورة لا يُعدّ في وسائطها، كما كان القارئ
  يحذفه («رَدّـ» في الوقف آخرُها الدال: `shahid_tatwil_maqta`)؛ ولا يُتخطّى بين الفتحتين والألف، لأنّ الألفَ بعده حرفُ مدٍّ في التحصيل لا
  ألفُ تنوين. وشرطُ ألف الجماعة في وسيط المقصورة `lahiq` لا هذا.

**ما تغيّر في القارئ:** في `tahaqquq/qari_tahsil/` (الفروقُ مقابل القارئ قبل هذا الطلب بأسبابها، وسكربتُها).

**حدُّه.** الوسائطُ قراءةٌ للقارئ كما كان على سياق التحصيل، لا قواعدُ من مصدر، وكلٌّ منها ينتظر قاعدتَه على ضابطٍ مجمَّد
(`hawkama/عقد_الشهادة.md` §٣). ورسائلُ الرفض صارت بأسماء التحصيل أو الوسائط وبنصّ المقطع، إلّا رسالتَي `tamm` («كلمة فارغة»، و«ألف مجرّدة
قبل متحرّك») كما كانتا؛ فتغيّر لفظُ بعضها. ولا وصلَ ولا وقفَ بين الكلمات هنا: ذلك في `Dal/Jumla.lean` كما كان.

**التعديل الثالث للتحصيل** (2026-10-29): أصنافُه التي لها وسيطٌ قديم (`wasitQaida`) يقرؤها القارئ بوسيطه باسم القاعدة القديمة، في الوقف
والوصل كما كان؛ فما أصلُه التحصيلُ هو خلايا ما لا وسيطَ له (`khalayaTahsil`)، وشهادةُ مقطعٍ أصلُ خليّته وسيطٌ تعليقٌ أو ترخيص (`qiraa_shahada`).

**المبرهنات** (21، بالمعيار الموحَّد في `Nizam/Asas.lean`):
- لكلّ (13): `qaidaWasit_hukm`، `mem_khalayaTahsil`، `juzOf_khalaya`، `ajza_tahsil`، `ajza_asl`، `ajza_la_fasid`، `qiraa_ajza`، `qiraa_tahsil`، `qiraa_la_fasid`،
  `qiraa_asl`، `qiraa_shahada`، `ajza_L`، `qiraa_murakhkhasa`.
- تعريفيّة (3): `juzOf_fasid`، `ajza_cons`، `tamm_khalaya`.
- على الشاهد (5): `shahid_fata`، `shahid_shams`، `shahid_rafd_tatwil`، `shahid_tatwil_maqta`، `shahid_jamaa`.
-/

namespace Dal.QiraaTahsil

open Nabt.UnitDiscovery
open Dal.Tahsil

/-! ## ١. أصلُ الخليّة -/

/-- أصلُ الخليّة في القارئ: مقطعٌ مرخَّصٌ في التحصيل (خلاياه بعينها)، أو مقطعٌ معلَّقٌ باسم قاعدته (وسيطُ القارئ المعلَن لها). -/
inductive Asl
  | tahsil
  | wasit (qaida : String)
  deriving DecidableEq, Repr

/-- خليّةُ القارئ: رقمُها (4·حامل + حالة)، وموضعُ مقطعها بنقاط الرمز، وأصلُها. -/
structure KhaliyaQ where
  raqm : Nat
  a : Nat
  b : Nat
  asl : Asl
  deriving DecidableEq, Repr

/-- ما يُخرجه الوسيطُ لمقطعٍ معلَّق: خلاياه، وملاحظاتُه، وهل هو همزةُ وصلٍ أو لامُ تعريفٍ مدغمة. -/
structure Wasit where
  khalaya : List Nat
  mulahazat : List String
  wasl : Bool
  al : Bool
  deriving DecidableEq, Repr

def kh (c s : Nat) : Nat := 4 * c + s

def fathatan : Char := 'ً'

/-- حالةُ التنوين: فتحتان 0، ضمّتان 1، كسرتان 2. -/
def tanwinHala (c : Char) : Option Nat :=
  if c == 'ً' then some 0 else if c == 'ٌ' then some 1 else if c == 'ٍ' then some 2 else none

/-! ## ٢. وسائطُ القارئ للمعلَّق -/

def mulahazaNun : String := "التنوين في الوصل نون ساكنة (وسيط معلَن)"
def mulahazaWaqfAlif : String := "الوقف على التنوين بعد الفتح بالألف (قطر الندى L442–443، الألفية L1131)"
def mulahazaWaqfHadhf : String := "الوقف على التنوين بحذفه وتسكين الحرف (الألفية L1131، L1136)"
def mulahazaAkhir : String := "الحرف الأخير بلا حركة: عُدّ ساكنًا للوقف"
def mulahazaTa : String := "الوقف على التاء المربوطة بالهاء (قطر الندى L441، الألفية L1142) ساكنةً (الألفية L1136)"
def mulahazaMaqsura : String := "الألف المقصورة ألفٌ رُسمت ياءً (قطر الندى L444–445)"
def mulahazaJamaa : String := "الألف بعد واو الجماعة تُكتب (قطر الندى L443–444) ولا تُنطق (وسيط معلَن)"
def mulahazaLam : String := "لام التعريف مدغمة في المشدّد بعدها، لا خلية لها (وسيط معلَن)"

/-- **الحرفُ في القارئ** بعد معرفة حامله `h` (فرعُه العامّ في `Qari/Main.lean` قبل هذا الطلب): الحركةُ خليّتُها، والشدّةُ ساكنٌ قبلها؛
    والتنوينُ في الوقف آخرَ الكلمة ألفٌ بعد الفتح وحذفٌ في غيره، وفي غير ذلك نونٌ ساكنة؛ وبلا علامة حركة: حرفُ المدّ ساكن، والأخيرُ
    في الوقف ساكن، وما سواه مرفوض. `akhir`: الحرفُ آخرُ الكلمة؛ `aj`: الكلمةُ آخرُ الجملة (الوقف). -/
def harfAam (h : Nat) (r : Char) (ms : List Char) (akhir aj : Bool) : Except String Wasit :=
  let sh := ms.contains shadda
  match (ms.filterMap halaAlama).head?, (ms.filterMap tanwinHala).head? with
  | some s, _ => .ok ⟨if sh then [kh h 3, kh h s.ila.val] else [kh h s.ila.val], [], false, false⟩
  | none, some s =>
    if akhir && aj then
      .ok ⟨(if sh then [kh h 3] else []) ++ (if s == 0 then [kh h 0, kh 2 3] else [kh h 3]),
        [if s == 0 then mulahazaWaqfAlif else mulahazaWaqfHadhf], false, false⟩
    else .ok ⟨(if sh then [kh h 3] else []) ++ [kh h s, kh 14 3], [mulahazaNun], false, false⟩
  | none, none =>
    if h == 2 || h == 28 || h == 11 then .ok ⟨[kh h 3], [], false, false⟩
    else if akhir then
      (if aj then .ok ⟨if sh then [kh h 3, kh h 3] else [kh h 3], [mulahazaAkhir], false, false⟩
       else .error s!"الحرف الأخير بلا حركة في غير آخر الجملة: «{String.ofList (r :: ms)}» — الوصل يحتاج حركته")
    else .error s!"حرف بلا حركة في غير آخر الكلمة: «{String.ofList (r :: ms)}»"

/-- رفضُ المعلَّق الذي لا وسيطَ له في القارئ في موضعه، باسم قاعدته. -/
def bilaWasit (q : String) (s : List Char) : Except String Wasit :=
  .error s!"معلَّقٌ بلا وسيطٍ في القارئ: {q} «{String.ofList s}»"

/-- **وسيطُ القارئ لمقطعٍ معلَّقٍ باسم قاعدته `q`**: قراءةُ البنّاء لما كان القارئ يفعله به قبل هذا الطلب، على سياقه في التحصيل
    (`akhir` من `akhirFi`، وما قبله وما بعده من `siyaq`). -/
def wasitOf (aj akhir : Bool) (m : Maqta) (q : String) : Except String Wasit :=
  match m.nass with
  | [] => bilaWasit q []
  | r :: ms =>
    if q == "قاعدة همزة الوصل" then
      (if m.siyaq.sabiq.isNone && ms.isEmpty then .ok ⟨[], [], true, false⟩ else bilaWasit q m.nass)
    else if q == "قاعدة الألف الممدودة" then
      (if ms.isEmpty then .ok ⟨[kh 0 0, kh 2 3], [], false, false⟩ else bilaWasit q m.nass)
    else if q == "قاعدة التاء المربوطة" then
      (if !akhir then .error s!"تاء مربوطة في غير آخر الكلمة: «{String.ofList m.nass}»"
       else if aj then .ok ⟨[kh 1 3], [mulahazaTa], false, false⟩
       else harfAam 18 r ms akhir aj)
    else if q == "قاعدة الألف المقصورة" then
      (if m.siyaq.sabiq.any (fun p => p.tail.contains fathatan) then
        (if ms.isEmpty then .ok ⟨[], [], false, false⟩ else bilaWasit q m.nass)
      else if m.siyaq.sabiq.isNone then bilaWasit q m.nass
      else if ms.isEmpty && m.siyaq.lahiq.isNone && (m.siyaq.sabiq == some ['و'] || m.siyaq.sabiq == some ['و', 'ْ']) then
        .ok ⟨[], [mulahazaMaqsura, mulahazaJamaa], false, false⟩
      else match harfAam 2 r ms akhir aj with
        | .ok w => .ok { w with mulahazat := mulahazaMaqsura :: w.mulahazat }
        | .error e => .error e)
    else if q == "قاعدة التنوين" && r == 'ا' && ms == [fathatan] then
      (if akhir && aj then .ok ⟨[kh 2 3], [mulahazaWaqfAlif], false, false⟩ else .ok ⟨[kh 14 3], [mulahazaNun], false, false⟩)
    else if q == "قاعدة التنوين" || q == "قاعدة الشدّة بلا حركة" || q == "قاعدة الحرف الأخير بلا حركة" ||
        q == "قاعدة الشدّة في أوّل الكلمة" then
      (match hamilOf r with
       | some h => harfAam h.val r ms akhir aj
       | none => bilaWasit q m.nass)
    else if q == "قاعدة ألف التنوين" then .ok ⟨[], [], false, false⟩
    else if q == "قاعدة ألف الجماعة" then .ok ⟨[], [mulahazaJamaa], false, false⟩
    else if q == "قاعدة لام التعريف المدغمة" then .ok ⟨[], [mulahazaLam], false, true⟩
    else bilaWasit q m.nass

/-! ## ٣. الكلمة على مقاطعها -/

/-- مقطعُ تطويلٍ مجرّد: لا خليّةَ له، وكان القارئ يحذفه قبل القراءة. -/
def tatwilB (n : Maqta) : Bool := n.nass == ['ـ']

/-- آخرُ الكلمة للمقطع في الوسائط: ما بعده تطويلٌ مجرّدٌ كلُّه (وكان القارئ يحذفه)، أو عليه فتحتان ويليه ألفٌ أو ألفٌ مقصورةٌ مجرّدة
    ثمّ تطويلٌ مجرّدٌ كلُّه (وهي التي يعدّها التحصيلُ ألفَ التنوين `alifTanwin`، أو يقرؤها وسيطُ المقصورة بعد الفتحتين بلا خليّة). -/
def akhirFi (m : Maqta) : List Maqta → Bool
  | [] => true
  | n :: rest => rest.all tatwilB && (tatwilB n || (m.nass.tail.contains fathatan && (n.nass == ['ا'] || n.nass == ['ى'])))

/-- جزءُ الكلمة من مقطعٍ واحد. -/
structure Juz where
  khalaya : List KhaliyaQ
  mulahazat : List String
  wasl : Bool
  al : Bool
  deriving DecidableEq, Repr

/-- **أصنافُ التعديل الثالث التي يقرؤها القارئ بوسيطه القديم** (`tahaqquq/tahsil/wasf.md`، 2026-10-29): التحصيلُ يرخّصها على الكلمة وحدها
    (مبتدأً بها موصولًا آخرُها)، والقارئُ يقرؤها في الوقف والوصل وبهمزة الوصل في الجملة كما كان يقرأ المقطعَ المعلَّقَ بالاسم نفسِه؛ ومنها الحرفُ بلا
    علامةٍ آخرَ الكلمة (ساكنٌ في الوقف، ومرفوضٌ في الوصل كما كان). والحرفُ بلا علامةٍ في غير الآخر ساكنًا، وحركةُ ما قبل «اً»، يقرؤهما
    القارئ من خلايا التحصيل. -/
def wasitQaida (m : Maqta) : Option String :=
  match m.hukm with
  | .L .hamzaWaslAl _ => some "قاعدة همزة الوصل"
  | .L .madda _ => some "قاعدة الألف الممدودة"
  | .L .taMarbuta _ => some "قاعدة التاء المربوطة"
  | .L .alifMaqsura _ => some "قاعدة الألف المقصورة"
  | .L .alifKhatt _ =>
    some (if m.nass == ['ى'] then "قاعدة الألف المقصورة"
      else if alifJamaa m.siyaq 'ا' [] then "قاعدة ألف الجماعة" else "قاعدة ألف التنوين")
  | .L .tanwin _ => some "قاعدة التنوين"
  | .L .tanwinAlif _ => some "قاعدة التنوين"
  | .L .shaddaIbtida _ => some "قاعدة الشدّة في أوّل الكلمة"
  | .L .lamMudgham _ => some "قاعدة لام التعريف المدغمة"
  | .L .sukunMuqaddar _ => if m.siyaq.lahiq.isNone then some "قاعدة الحرف الأخير بلا حركة" else none
  | _ => none

/-- قاعدةُ الوسيط للمقطع: اسمُ المعلَّق، أو الاسمُ القديم لصنفٍ من التعديل الثالث. -/
def qaidaWasit (m : Maqta) : Option String :=
  match m.hukm with
  | .P q => some q
  | .L _ _ => wasitQaida m
  | .F _ => none

theorem qaidaWasit_hukm {m : Maqta} {q : String} (h : qaidaWasit m = some q) :
    m.hukm = .P q ∨ ∃ s ks, m.hukm = .L s ks := by
  unfold qaidaWasit at h
  cases hh : m.hukm with
  | P q' => rw [hh] at h; cases h; exact Or.inl rfl
  | L s ks => exact Or.inr ⟨s, ks, rfl⟩
  | F _ => rw [hh] at h; cases h

/-- خلايا المقطع التي يحملها القارئ من التحصيل بعينها: المرخَّصُ الذي لا وسيطَ له. -/
def khalayaTahsil (m : Maqta) : List KhaliyaQ :=
  if (qaidaWasit m).isNone then (khalayaOf m.hukm).map (fun k => ⟨(Dal.n k).val, m.a, m.b, .tahsil⟩) else []

/-- **المقطعُ في القارئ:** الفاسدُ رفضٌ باسم سببه؛ وما له قاعدةُ وسيطٍ وسيطُها؛ والمرخَّصُ سواهما خلاياه بعينها؛ وكلُّ خليّةٍ بموضع مقطعها. -/
def juzOf (aj : Bool) (m : Maqta) (baad : List Maqta) : Except String Juz :=
  match m.hukm with
  | .F e => .error s!"{e}: «{String.ofList m.nass}»"
  | _ =>
    match qaidaWasit m with
    | none => .ok ⟨khalayaTahsil m, [], false, false⟩
    | some q =>
      match wasitOf aj (akhirFi m baad) m q with
      | .ok w => .ok ⟨w.khalaya.map (fun c => ⟨c, m.a, m.b, .wasit q⟩), w.mulahazat, w.wasl, w.al⟩
      | .error e => .error e

/-- أجزاءُ الكلمة بترتيب مقاطعها، أو أوّلُ رفض. -/
def ajza (aj : Bool) : List Maqta → Except String (List Juz)
  | [] => .ok []
  | m :: rest =>
    match juzOf aj m rest, ajza aj rest with
    | .ok j, .ok js => .ok (j :: js)
    | .error e, _ => .error e
    | .ok _, .error e => .error e

/-- قراءةُ الكلمة: خلاياها بأصولها ومواضعها، وهمزةُ الوصل وهمزةُ «أل»، والملاحظات. -/
structure Qiraa where
  khalaya : List KhaliyaQ
  wasl : Bool
  al : Bool
  mulahazat : List String
  deriving DecidableEq, Repr

def tamm (js : List Juz) : Except String Qiraa :=
  let ks := js.flatMap (·.khalaya)
  let wasl := js.any (·.wasl)
  if ks.isEmpty then .error "كلمة فارغة"
  else if wasl && !sakinAwwal (ks.map (·.raqm)) then
    .error "ألف مجرّدة قبل متحرّك: ليست همزة وصل (همزة الوصل لا تكون إلّا قبل ساكن — Hamza.lean)؛ اكتب همزة القطع بمقعدها (أ/إ)"
  else .ok ⟨ks, wasl, js.any (·.al) || (wasl && isAl (ks.map (·.raqm))), js.flatMap (·.mulahazat)⟩

/-- **قراءةُ الكلمة على تحصيلها.** `aj`: الكلمةُ آخرُ الجملة. -/
def qiraa (w : List Char) (aj : Bool) : Except String Qiraa :=
  match ajza aj (tahsil w) with
  | .ok js => tamm js
  | .error e => .error e


/-! ## ٤. البراهين: كلُّ خليّةٍ من مقطعٍ مشهود -/

theorem mem_khalayaTahsil {m : Maqta} {x : KhaliyaQ} (hx : x ∈ khalayaTahsil m) :
    x.asl = .tahsil ∧ x.a = m.a ∧ x.b = m.b ∧ ∃ s ks, m.hukm = .L s ks := by
  unfold khalayaTahsil at hx
  split at hx
  rotate_left
  · cases hx
  rw [List.mem_map] at hx
  obtain ⟨k, hk, rfl⟩ := hx
  refine ⟨rfl, rfl, rfl, ?_⟩
  cases hh : m.hukm with
  | L s ks => exact ⟨s, ks, rfl⟩
  | P _ => rw [hh] at hk; cases hk
  | F _ => rw [hh] at hk; cases hk

/-- المقطعُ في القارئ: المرخَّصُ خلاياه هي خلايا التحصيل بعينها، والمعلَّقُ كلُّ خليّةٍ منه بموضعه وأصلُها وسيطُ قاعدته. -/
theorem juzOf_khalaya (aj : Bool) (m : Maqta) (baad : List Maqta) (j : Juz) (h : juzOf aj m baad = .ok j) :
    (qaidaWasit m = none ∧ j.khalaya = khalayaTahsil m) ∨
    (∃ q, qaidaWasit m = some q ∧ ∀ x ∈ j.khalaya, x.a = m.a ∧ x.b = m.b ∧ x.asl = .wasit q) := by
  unfold juzOf at h
  split at h
  · cases h
  · cases hq : qaidaWasit m with
    | none => rw [hq] at h; cases h; exact Or.inl ⟨rfl, rfl⟩
    | some q =>
      refine Or.inr ⟨q, rfl, ?_⟩
      rw [hq] at h
      simp only at h
      cases hw : wasitOf aj (akhirFi m baad) m q with
      | error e => rw [hw] at h; cases h
      | ok w =>
        rw [hw] at h
        cases h
        intro x hx
        rw [List.mem_map] at hx
        obtain ⟨c, _, rfl⟩ := hx
        exact ⟨rfl, rfl, rfl⟩

theorem juzOf_fasid (aj : Bool) (m : Maqta) (baad : List Maqta) (j : Juz) (h : juzOf aj m baad = .ok j) :
    ∀ e, m.hukm ≠ .F e := by
  intro e he
  unfold juzOf at h
  split at h
  · cases h
  · rename_i hn; exact hn e he

theorem ajza_cons {aj : Bool} {m : Maqta} {rest : List Maqta} {js : List Juz} (h : ajza aj (m :: rest) = .ok js) :
    ∃ j js', juzOf aj m rest = .ok j ∧ ajza aj rest = .ok js' ∧ js = j :: js' := by
  simp only [ajza] at h
  split at h
  · rename_i j js' h1 h2
    cases h
    exact ⟨j, js', h1, h2, rfl⟩
  · cases h
  · cases h

/-- **لا تُسقَط خليّةٌ مرخَّصة ولا تُبدَّل ولا يُغيَّر ترتيبُها ولا تُزاد:** خلايا الأجزاء التي أصلُها التحصيل هي خلايا المقاطع المرخَّصة
    بعينها وبترتيبها. -/
theorem ajza_tahsil (aj : Bool) : ∀ (ms : List Maqta) (js : List Juz), ajza aj ms = .ok js →
    (js.flatMap (·.khalaya)).filter (·.asl == .tahsil) = ms.flatMap khalayaTahsil
  | [], js, h => by simp only [ajza] at h; cases h; rfl
  | m :: rest, js, h => by
    obtain ⟨j, js', h1, h2, rfl⟩ := ajza_cons h
    rw [List.flatMap_cons, List.flatMap_cons, List.filter_append, ajza_tahsil aj rest js' h2]
    congr 1
    rcases juzOf_khalaya aj m rest j h1 with ⟨_, hk⟩ | ⟨q, hq, hx⟩
    · rw [hk, List.filter_eq_self]
      intro x hx
      rw [(mem_khalayaTahsil hx).1]
      rfl
    · have : khalayaTahsil m = [] := by simp [khalayaTahsil, hq]
      rw [this, List.filter_eq_nil_iff]
      intro x hm
      rw [(hx x hm).2.2]
      simp

/-- **أصلُ كلّ خليّة:** لكلّ خليّةٍ في الأجزاء مقطعٌ في الكلمة بموضعها، وهي من خلاياه المرخَّصة أو من وسيطِ قاعدته المعلَّقة. -/
theorem ajza_asl (aj : Bool) : ∀ (ms : List Maqta) (js : List Juz), ajza aj ms = .ok js →
    ∀ x ∈ js.flatMap (·.khalaya), ∃ m ∈ ms, x.a = m.a ∧ x.b = m.b ∧
      (x ∈ khalayaTahsil m ∨ ∃ q, qaidaWasit m = some q ∧ x.asl = .wasit q)
  | [], js, h => by simp only [ajza] at h; cases h; simp
  | m :: rest, js, h => by
    obtain ⟨j, js', h1, h2, rfl⟩ := ajza_cons h
    intro x hx
    rw [List.flatMap_cons, List.mem_append] at hx
    rcases hx with hx | hx
    · refine ⟨m, List.mem_cons_self, ?_⟩
      rcases juzOf_khalaya aj m rest j h1 with ⟨_, hk⟩ | ⟨q, hq, hall⟩
      · rw [hk] at hx
        have := mem_khalayaTahsil hx
        exact ⟨this.2.1, this.2.2.1, Or.inl hx⟩
      · have := hall x hx
        exact ⟨this.1, this.2.1, Or.inr ⟨q, hq, this.2.2⟩⟩
    · obtain ⟨m', hm', hrest⟩ := ajza_asl aj rest js' h2 x hx
      exact ⟨m', List.mem_cons_of_mem _ hm', hrest⟩

/-- **لا يُقرأ ما فيه مقطعٌ فاسد.** -/
theorem ajza_la_fasid (aj : Bool) : ∀ (ms : List Maqta) (js : List Juz), ajza aj ms = .ok js →
    ∀ m ∈ ms, ∀ e, m.hukm ≠ .F e
  | [], _, _ => by simp
  | m :: rest, js, h => by
    obtain ⟨j, js', h1, h2, rfl⟩ := ajza_cons h
    intro m' hm'
    rcases List.mem_cons.1 hm' with rfl | hm'
    · exact juzOf_fasid aj m' rest j h1
    · exact ajza_la_fasid aj rest js' h2 m' hm'

theorem tamm_khalaya {js : List Juz} {q : Qiraa} (h : tamm js = .ok q) : q.khalaya = js.flatMap (·.khalaya) := by
  dsimp only [tamm] at h
  split at h
  · cases h
  · split at h
    · cases h
    · cases h; rfl

theorem qiraa_ajza {w : List Char} {aj : Bool} {q : Qiraa} (h : qiraa w aj = .ok q) :
    ∃ js, ajza aj (tahsil w) = .ok js ∧ q.khalaya = js.flatMap (·.khalaya) := by
  unfold qiraa at h
  split at h
  · rename_i js hj
    exact ⟨js, hj, tamm_khalaya h⟩
  · cases h

/-- **خلايا التحصيل في القارئ هي هي:** ما أصلُه التحصيلُ من خلايا القراءة هو خلايا المقاطع المرخَّصة في التحصيل بعينها وبترتيبها،
    في الوقف والوصل سواءً. -/
theorem qiraa_tahsil (w : List Char) (aj : Bool) (q : Qiraa) (h : qiraa w aj = .ok q) :
    q.khalaya.filter (·.asl == .tahsil) = (tahsil w).flatMap khalayaTahsil := by
  obtain ⟨js, hj, hk⟩ := qiraa_ajza h
  rw [hk]
  exact ajza_tahsil aj _ js hj

/-- **لا يُقرأ ما في تحصيله مقطعٌ فاسد.** -/
theorem qiraa_la_fasid (w : List Char) (aj : Bool) (q : Qiraa) (h : qiraa w aj = .ok q) :
    ∀ m ∈ tahsil w, ∀ e, m.hukm ≠ .F e := by
  obtain ⟨js, hj, _⟩ := qiraa_ajza h
  exact ajza_la_fasid aj _ js hj

/-- **كلُّ خليّةٍ من مقطعٍ في النصّ:** موضعُها موضعُ مقطعٍ في التحصيل ذرّاتُه المقطع، وهي من خلاياه المرخَّصة أو من وسيطِ قاعدته المعلَّقة
    باسمها. -/
theorem qiraa_asl (w : List Char) (aj : Bool) (q : Qiraa) (h : qiraa w aj = .ok q) :
    ∀ x ∈ q.khalaya, ∃ m ∈ tahsil w, x.a = m.a ∧ x.b = m.b ∧ (w.drop m.a).take (m.b - m.a) = m.nass ∧
      (x ∈ khalayaTahsil m ∨ ∃ qd, qaidaWasit m = some qd ∧ x.asl = .wasit qd) := by
  obtain ⟨js, hj, hk⟩ := qiraa_ajza h
  intro x hx
  rw [hk] at hx
  obtain ⟨m, hm, ha, hb, hr⟩ := ajza_asl aj _ js hj x hx
  exact ⟨m, hm, ha, hb, (tahsil_muhadha w m hm).1, hr⟩

/-- **كلُّ خليّةٍ من مقطعٍ مشهود:** لكلّ خليّةٍ في القراءة مقطعٌ موضعُه في مصدر NABT صالحٌ وذرّاتُه المقطع، وحكمُ الفاحص على شهادته
    ترخيصٌ إن كان أصلُها التحصيل؛ وإن كان أصلُها وسيطًا فتعليقٌ باسم قاعدته، أو ترخيصٌ لصنفٍ من التعديل الثالث يقرؤه القارئ بوسيطه. -/
theorem qiraa_shahada (src : Source Char) (aj : Bool) (q : Qiraa) (h : qiraa src.atoms aj = .ok q) :
    ∀ x ∈ q.khalaya, ∃ m ∈ tahsil src.atoms, (mawdi src m).start = x.a ∧ (mawdi src m).stop = x.b ∧
      validSpan src (mawdi src m) = true ∧ spanAtoms src (mawdi src m) = m.nass ∧
      (match x.asl with
       | .tahsil => Nizam.Shahada.hukm (shahada src m) = .murakhkhas
       | .wasit n => Nizam.Shahada.hukm (shahada src m) = .muallaq [n] ∨
           Nizam.Shahada.hukm (shahada src m) = .murakhkhas) := by
  intro x hx
  obtain ⟨m, hm, ha, hb, _, hr⟩ := qiraa_asl src.atoms aj q h x hx
  refine ⟨m, hm, ha.symm, hb.symm, (mawdi_sahih src m hm).1, (mawdi_sahih src m hm).2, ?_⟩
  rw [shahada_hukm src m hm]
  rcases hr with hr | ⟨qd, hq, hx'⟩
  · obtain ⟨hasl, _, _, s, ks, hh⟩ := mem_khalayaTahsil hr
    rw [hasl, hh]
    rfl
  · rw [hx']
    rcases qaidaWasit_hukm hq with hp | ⟨s, ks, hl⟩
    · rw [hp]; exact Or.inl rfl
    · rw [hl]; exact Or.inr rfl

theorem ajza_L (aj : Bool) : ∀ ms : List Maqta, (∀ m ∈ ms, mL m.hukm = true ∧ wasitQaida m = none) →
    ajza aj ms = .ok (ms.map fun m => ⟨khalayaTahsil m, [], false, false⟩)
  | [], _ => rfl
  | m :: rest, hL => by
    have hm := hL m List.mem_cons_self
    have hr := ajza_L aj rest (fun x hx => hL x (List.mem_cons_of_mem _ hx))
    have hj : juzOf aj m rest = .ok ⟨khalayaTahsil m, [], false, false⟩ := by
      have hq : qaidaWasit m = none := by
        unfold qaidaWasit
        cases hh : m.hukm with
        | L s ks => exact hm.2
        | P _ => have := hm.1; rw [hh] at this; cases this
        | F _ => rfl
      unfold juzOf
      split
      · rename_i e he; have := hm.1; rw [he] at this; cases this
      · rw [hq]
    simp only [ajza, hj, hr, List.map_cons]

/-- **الكلمةُ المرخَّصةُ مقاطعُها كلُّها، ولها خليّة:** قراءتُها خلايا التحصيل بعينها وبترتيبها، بلا همزة وصلٍ ولا ملاحظة، في الوقف والوصل
    سواءً. (والتي لا خليّةَ لها، كـ«ـ»، مرفوضةٌ «كلمة فارغة».) -/
theorem qiraa_murakhkhasa (w : List Char) (aj : Bool) (hL : ∀ m ∈ tahsil w, mL m.hukm = true ∧ wasitQaida m = none)
    (hne : (tahsil w).flatMap khalayaTahsil ≠ []) :
    qiraa w aj = .ok ⟨(tahsil w).flatMap khalayaTahsil, false, false, []⟩ := by
  unfold qiraa
  rw [ajza_L aj _ hL]
  unfold tamm
  have h1 : ((tahsil w).map fun m => (⟨khalayaTahsil m, [], false, false⟩ : Juz)).flatMap (·.khalaya) =
      (tahsil w).flatMap khalayaTahsil := by
    simp [List.flatMap_map]
  have h2 : ((tahsil w).map fun m => (⟨khalayaTahsil m, [], false, false⟩ : Juz)).any (·.wasl) = false := by simp
  have h3 : ((tahsil w).map fun m => (⟨khalayaTahsil m, [], false, false⟩ : Juz)).any (·.al) = false := by simp
  have h4 : ((tahsil w).map fun m => (⟨khalayaTahsil m, [], false, false⟩ : Juz)).flatMap (·.mulahazat) = [] := by simp
  simp only [h1, h2, h3, h4, List.isEmpty_iff, hne, ite_false, Bool.false_and, Bool.false_or, Bool.false_eq_true]

/-! ## ٥. شواهد -/

/-- «فَتًى»: الفاءُ مرخَّصة، وخليّتا التنوين من وسيط قاعدته بموضع مقطعه: ألفٌ في الوقف ونونٌ ساكنةٌ في الوصل؛ والألفُ المقصورة بعده بلا خليّة. -/
theorem shahid_fata :
    (qiraa "فَتًى".toList true).toOption.map (·.khalaya) =
      some [⟨100, 0, 2, .tahsil⟩, ⟨72, 2, 4, .wasit "قاعدة التنوين"⟩, ⟨11, 2, 4, .wasit "قاعدة التنوين"⟩] ∧
    (qiraa "فَتًى".toList false).toOption.map (·.khalaya) =
      some [⟨100, 0, 2, .tahsil⟩, ⟨72, 2, 4, .wasit "قاعدة التنوين"⟩, ⟨59, 2, 4, .wasit "قاعدة التنوين"⟩] := by
  decide

/-- «ٱلشَّمْسُ»: همزةُ الوصل ولامُ التعريف المدغمة بلا خليّة، وخلاياها كلُّها من مقاطع مرخَّصة بمواضعها. -/
theorem shahid_shams :
    (qiraa "ٱلشَّمْسُ".toList true).toOption.map (fun q => (q.khalaya, q.wasl, q.al)) =
      some ([⟨43, 2, 5, .tahsil⟩, ⟨40, 2, 5, .tahsil⟩, ⟨111, 5, 7, .tahsil⟩, ⟨81, 7, 9, .tahsil⟩], true, true) := by
  decide

/-- علامتان على حرفٍ واحد: كان القارئ يأخذ الأخيرة، وصارت الكلمةُ ترفض باسم المقطع الفاسد. والتطويلُ المجرّدُ بعد التنوين آخرَ الكلمة لا
    يمنع الوقف عليه. -/
theorem shahid_rafd_tatwil :
    (match qiraa "كَُتَبَ".toList true with | .error e => e | .ok _ => "") = "علامتان متعارضتان: «كَُ»" ∧
    (qiraa "حٍـ".toList true).toOption.map (fun q => q.khalaya.map (·.raqm)) = some [19] := by
  decide

/-- التطويلُ المجرّد مقطعٌ في التحصيل. بعد حرفٍ بلا حركة يجعله في غير آخر الكلمة، فكان التحصيلُ يردّ المقطع؛ وصار بالتعديل الثالث
    (2026-10-29) ساكنًا مقدَّرًا (القاعدة 15)، فـ«كَتَبـ» تُقرأ ساكنةَ الباء كما كان القارئ يقرؤها قبل التحصيل. وبين الفتحتين والألف يجعل الألفَ حرفَ مدٍّ مرخَّصًا لا ألفَ تنوين، فالتنوينُ في غير آخر الكلمة نونٌ ساكنة
    («كِتَابًـا»؛ وكان القارئ يقرؤها «كِتَابًا»). والشدّةُ بلا حركةٍ قبله معلَّقةٌ في التحصيل، فيعدّها وسيطُها آخرَ الكلمة (`akhirFi`): «رَدّـ» في
    الوقف آخرُها الدالُ ساكنةً، كما كان. -/
theorem shahid_tatwil_maqta :
    (qiraa "كَتَبـ".toList true).toOption.map (fun q => q.khalaya.map (·.raqm)) = some [32, 72, 107] ∧
    (qiraa "رَدّـ".toList true).toOption.map (fun q => (q.khalaya.map (·.raqm), q.mulahazat)) = some ([60, 71, 71], [mulahazaAkhir]) ∧
    (qiraa "كِتَابًـا".toList true).toOption.map (fun q => q.khalaya.map (fun x => (x.raqm, x.asl))) =
      some [(34, .tahsil), (72, .tahsil), (11, .tahsil), (104, .wasit "قاعدة التنوين"), (59, .wasit "قاعدة التنوين"), (11, .tahsil)] := by
  decide

/-- ألفُ الجماعة (ألفًا أو ألفًا مقصورة) بعد واوٍ ساكنةٍ تليها: لا خليّةَ لها. وبعد واوٍ مشدَّدةٍ بلا حركة ليست ألفَ جماعةٍ في التحصيل،
    فالألفُ حرفُ مدٍّ مرخَّص (وكان القارئ يعدّها ألفَ جماعةٍ لأنّ خليّةَ الواو الأخيرة ساكنة). وإن تلا الألفَ أو المقصورةَ تطويلٌ مجرّد
    («قَالُواـ»، «قَالُوىـ») فليست ألفَ جماعة: ألفٌ منطوقة (وكان القارئ يحذف التطويلَ فيقرؤهما ألفَ جماعة). -/
theorem shahid_jamaa :
    (qiraa "رَمَوْا".toList true).toOption.map (fun q => (q.khalaya.map (·.raqm), q.mulahazat)) =
      some ([60, 108, 115], [mulahazaJamaa]) ∧
    (qiraa "رَمَوْى".toList true).toOption.map (fun q => (q.khalaya.map (·.raqm), q.mulahazat)) =
      some ([60, 108, 115], [mulahazaMaqsura, mulahazaJamaa]) ∧
    (qiraa "رَمَوّا".toList true).toOption.map (fun q => (q.khalaya.map (·.raqm), q.mulahazat)) =
      some ([60, 108, 115, 11], []) ∧
    (qiraa "قَالُواـ".toList true).toOption.map (fun q => (q.khalaya.map (·.raqm), q.mulahazat)) = some ([28, 11, 53, 115, 11], []) ∧
    (qiraa "قَالُوىـ".toList true).toOption.map (fun q => (q.khalaya.map (·.raqm), q.mulahazat)) =
      some ([28, 11, 53, 115, 11], [mulahazaMaqsura]) := by
  decide

end Dal.QiraaTahsil
