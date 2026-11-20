import A116.Makharij
import A116.Hadd

/-!
# قانونُ الإدغام من «الكتاب»: R المكتوبةُ من أبواب الإدغام، وقوانينُ الابتداء والوصل والوقف عليها (ADR ٦٨)

**المصدر.** «الكتاب» نسخة JK006989 المختومة في `corpora/kitab/` (`tools/gen_kitab.py`)، الأبوابُ الثلاثة من «هذا باب
الإدغام في الحرفين اللذين تضع لسانك لهما موضعا واحدا» إلى ما قبل «هذا باب الحرف الذي يضارع به حرف من موضعه».
كلُّ صفٍّ أدناه مرساةٌ منقولةٌ بحروفها (تقع في الأبواب مرّةً واحدة — `tests/test_makharij.py`)، ومعها الحروفُ المدغَمة
والمدغَمُ فيها كما تسمّيها المرساةُ أو مثالُها، وحكمُها: **يُدغم** (حسنٌ أو جائزٌ أو عربيّ) أو **لا يُدغم**.
ما خرج عن الإدغام إلى غيره لم يُنقل صفًّا: قلبُ النون مع الباء ميمًا (قلبٌ لا إدغام)، والعينُ مع الهاء وأخواتُها مما
لا يُدغم إلّا بتحويل الحرفين حاءً (إبدالٌ ثمّ إدغام).

## R داخل البرهان (ADR ٧٢)

الصفوفُ شواهد؛ وR تُعرَّف من **أسباب الإدغام وموانعه كما نصّ عليها الباب** (`Rd`): المثلُ في مثله إلّا الهمزةَ والألف، أو
سببٌ (قربُ المخرج، لامُ المعرفة، الغنّة، الاستطالة، الحيّز) بلا مانع (الهمزةُ والألف، المفرّ، الصفير، اللين، اتّجاهُ الحلق).
كلُّ إدغامٍ مشهودٍ تحت سببٍ بلا مانع، وكلُّ امتناعٍ مشهودٍ بلا سببٍ أو بمانع (`shawahid_idgham`، `shawahid_mumtani`)؛ ولكلّ
سببٍ ولكلّ مانعٍ شاهدٌ لا يغطّيه غيرُه — حدٌّ أدنى مكتمل (`sabab_needed`، `mani_needed`)؛ و**الاستنفاد**: الأزواجُ الـ841
أقسامٌ سبعة بأعدادها (`istinfad`)، والمسكوتُ عنه اثنان وعشرون بأعيانه وهو Rd بلا R (`maskut_list`)؛ والنوافذُ الـ13,456 محكومٌ
على كلٍّ منها بحكمٍ واحدٍ من أحد عشر (`istinfad_ibtida`، `istinfad_mutaharrik`، `istinfad_madd`، `istinfad_sakin`، `labels_closed`). وعلى النافذة قوانينُ الابتداء والوصل والوقف: `ibtida_then_wasl`،
`mukhtamal`، `waqf_after_idgham`، `window_minimal`.

## ما يُبرهَن (ADR ٦٨)

* **الاتّساق**: لا زوجَ في الصفوف مُدغَمٌ وغيرُ مُدغَمٍ معًا (`consistent`).
* **الهمزةُ والألف لا تدخلان** في زوجٍ مُدغَم (`hamza_alif_inert`) — «ما لا يدغم في مقاربه ولا يدغم فيه مقاربه … الهمزة»،
  «وكذلك الألف».
* **الأربعةُ في اتّجاهٍ واحد** (`arbaa_one_way`): الميمُ والراءُ والفاءُ والشينُ لا تُدغم في مقاربها، ويُدغم فيها مقاربُها —
  «وتلك الحروف الميم والراء والفاء والشين».
* **R الترتيبيّة لا تطابق الإدغام** في الاتّجاهين: أربعةٌ وأربعون زوجًا مُدغَمًا أبعدُ من مخرجٍ واحدٍ في الترتيب، وكلُّها
  تحت أربعة أسبابٍ نصّ عليها الباب لا غير (`far_pairs_named`، وكلُّ سببٍ لازمٌ بشاهد: `far_clauses_needed`): اللامُ والنونُ
  مصدرًا («لام المعرفة تدغم في ثلاثة عشر حرفا»، «صوتهما واحد … في الخياشيم»)، والضادُ والشينُ مُدغَمًا فيهما («استطالت»)،
  وحروفُ الثنايا بعضُها في بعض («لا يمتنع بعضهن من بعض»)؛ وسبعةُ أضلاعٍ من R الترتيبيّة لا إدغامَ عليها في أيّ اتّجاه
  (`order_edges_unattested`).
* **قانونُ الموضع** على الخانات (`idghamAt`): الإدغامُ يُسكِّن الأوّلَ حرفًا من جنس الثاني فيصير الزوجُ `Hadd.idghamPair`
  (`result_geminate`)؛ و**الوقفُ** يمنعه (الثاني ساكن: «أردد … بين ساكنين»، `waqf_law`)؛ و**الابتداءُ** يحتاج همزةَ الوصل
  («وألحقوا الألف الخفيفة لأنهم لا يستطيعون أن يبتدئوا بساكن»، `ibtida_law`)؛ و**الوصلُ** شرطُه ما قبل الأوّل: متحرّكٌ أو حرفُ
  مدٍّ لا ساكنٌ («اسم موسى» لا يُدغم) — وهذا الشرطُ هو بعينه قانونُ الجوار الثلاثيّ `Nizam.ternary` (`wasl_law_is_ternary`).
* **تعارضٌ مسمًّى مع قيد الحدّ**: «إنّ المالَ لك» — مدٌّ قبل المثلين في المنفصل — قال فيه الباب «فإن الإدغام حسن»، و`Hadd.strictJoinB`
  يرفض صورتَه المدغمة لأنّ قافيةَ المدّ يقطعها الحدّ (`mal_laka_refused`). يُسمّى ولا يُغيَّر القانونُ هنا (قرارٌ للمالك).
-/

namespace A116.MakharijIdgham

open A116 A116.Nizam A116.Jisr A116.Makharij A116.Ladder

/-! ## ١. الصفوف -/

/-- صفٌّ: (مرساةٌ منقولة، المدغَمات، المدغَمُ فيها، يُدغم؟). الأزواجُ حاصلُ الضرب بلا الحرف مع نفسه. -/
structure Saff where
  anchor : String
  src : List Char
  dst : List Char
  idgham : Bool

def rows : List Saff := [
  ⟨"الهاء مع الحاء كقولك اجبه حملا", ['ه'], ['ح'], true⟩,
  ⟨"ولا تدغم الحاء في الهاء", ['ح'], ['ه'], false⟩,
  ⟨"العين مع الحاء كقولك اقطع حملا الإدغام حسن", ['ع'], ['ح'], true⟩,
  ⟨"ولم تدغم الحاء في العين", ['ح'], ['ع'], false⟩,
  ⟨"الغين مع الخاء البيان أحسن والإدغام حسن", ['غ'], ['خ'], true⟩,
  ⟨"والخاء مع الغين البيان فيهما أحسن", ['خ'], ['غ'], true⟩,
  ⟨"القاف مع الكاف كقولك الحق كلدة الإدغام حسن", ['ق'], ['ك'], true⟩,
  ⟨"والكاف مع القاف انهك قطنا البيان أحسن والإدغام حسن", ['ك'], ['ق'], true⟩,
  ⟨"الجيم مع الشين كقولك ابعج شيئا الإدغام والبيان حسنان", ['ج'], ['ش'], true⟩,
  ⟨"والشين لا تدغم في الجيم", ['ش'], ['ج'], false⟩,
  ⟨"اللام مع الراء نحو اشغل رحبة", ['ل'], ['ر'], true⟩,
  ⟨"والراء لا تدغم في اللام ولا في النون", ['ر'], ['ل', 'ن'], false⟩,
  ⟨"النون تدغم مع الراء لقرب المخرجين", ['ن'], ['ر'], true⟩,
  ⟨"وتدغم في اللام لأنها قريبة منها", ['ن'], ['ل'], true⟩,
  ⟨"وتدغم النون مع الميم لأن صوتهما واحد", ['ن'], ['م'], true⟩,
  ⟨"وتدغم النون مع الواو بغنة وبلا غنة", ['ن'], ['و'], true⟩,
  ⟨"وتدغم النون مع الياء بغنة وبلا غنة", ['ن'], ['ي'], true⟩,
  ⟨"ولا تدغم في حروف الحلق البتة", ['ن'], ['ء', 'ه', 'ع', 'ح', 'غ', 'خ'], false⟩,
  ⟨"وأما اللام فقد تدغم فيها وذلك قولك هنرى", ['ل'], ['ن'], true⟩,
  ⟨"ولم يدغموا الميم في النون", ['م'], ['ن'], false⟩,
  ⟨"فالميم لا تدغم في الباء", ['م'], ['ب'], false⟩,
  ⟨"اصحمطرا تريد اصحب مطرا مدغم", ['ب'], ['م'], true⟩,
  ⟨"والفاء لا تدغم في الباء", ['ف'], ['ب'], false⟩,
  ⟨"والباء قد تدغم في الفاء للتقارب", ['ب'], ['ف'], true⟩,
  ⟨"والأحد عشر حرفا النون والراء والدال والتاء والصاد والطاء والزاي والسين والظاء والثاء والذال", ['ل'], ['ن', 'ر', 'د', 'ت', 'ص', 'ط', 'ز', 'س', 'ظ', 'ث', 'ذ'], true⟩,
  ⟨"واللذان خالطاها الضاد والشين", ['ل'], ['ض', 'ش'], true⟩,
  ⟨"ومن الحروف ما لا يدغم في مقاربه ولا يدغم فيه مقاربه", ['ء'], ['ه'], false⟩,
  ⟨"ومن الحروف ما لا يدغم في مقاربه ولا يدغم فيه مقاربه", ['ه'], ['ء'], false⟩,
  ⟨"وكذلك الألف لا تدغم في الهاء", ['ا'], ['ه'], false⟩,
  ⟨"الطاء مع الدال كقولك اضبد لما", ['ط'], ['د'], true⟩,
  ⟨"وكذلك الطاء مع التاء", ['ط'], ['ت'], true⟩,
  ⟨"وتصير الدال مع الطاء طاء", ['د'], ['ط'], true⟩,
  ⟨"وكذلك التاء وهو قولك انعطالبا", ['ت'], ['ط'], true⟩,
  ⟨"والتاء والدال سواء كل واحدة منها تدغم في صاحبتها", ['ت', 'د'], ['ت', 'د'], true⟩,
  ⟨"وذلك قولك افحسالما فتصير سينا", ['ص'], ['س'], true⟩,
  ⟨"وتقول افحزردة", ['ص'], ['ز'], true⟩,
  ⟨"وذلك قولك احبصابرا وأحوصابرا", ['س', 'ز'], ['ص'], true⟩,
  ⟨"والزاي والسين بمنزلة التاء والدال تقول احبزردة ورسلمة فتدغم", ['ز', 'س'], ['ز', 'س'], true⟩,
  ⟨"وذلك قولك احفذلك فتدغم", ['ظ'], ['ذ'], true⟩,
  ⟨"وتقول احفثابتا", ['ظ'], ['ث'], true⟩,
  ⟨"وذلك قولك خظالما", ['ذ'], ['ظ'], true⟩,
  ⟨"والذال والثاء منزلة كل واحدة منهما من صاحبتها منزلة الدال والتاء", ['ذ', 'ث'], ['ذ', 'ث'], true⟩,
  ⟨"والطاء والدال والتاء يدغمن كلهن في الصاد والزاي والسين", ['ط', 'د', 'ت'], ['ص', 'ز', 'س'], true⟩,
  ⟨"وكذلك الظاء والثاء والذال لأنهن من طرف اللسان وأطراف الثنايا", ['ظ', 'ث', 'ذ'], ['ص', 'ز', 'س'], true⟩,
  ⟨"والظاء والثاء والذال أخوات الطاء والدال والتاء لا يمتنع بعضهن من بعض في الإدغام", ['ظ', 'ث', 'ذ', 'ط', 'د', 'ت'], ['ظ', 'ث', 'ذ', 'ط', 'د', 'ت'], true⟩,
  ⟨"وأما الصاد والسين والزاي فلا تدغمهن في هذه الحروف التي أدغمت فيهن", ['ص', 'س', 'ز'], ['ط', 'د', 'ت', 'ظ', 'ث', 'ذ'], false⟩,
  ⟨"وقد تدغم الطاء والتاء والدال في الضاد", ['ط', 'ت', 'د'], ['ض'], true⟩,
  ⟨"وذلك احفضرمة وخضرمة وابعضرمة", ['ظ', 'ذ', 'ث'], ['ض'], true⟩,
  ⟨"ولا تدغم في الصاد والسين والزاي لاستطالتها يعني الضاد", ['ض'], ['ص', 'س', 'ز'], false⟩,
  ⟨"ولا تدغم الصاد وأختاها فيها", ['ص', 'س', 'ز'], ['ض'], false⟩,
  ⟨"وتدغم الطاء والدال والتاء في الشين", ['ط', 'د', 'ت'], ['ش'], true⟩,
  ⟨"وتدغم الظاء والذال والثاء فيها لأنهم قد أنزلوها منزلة الضاد", ['ظ', 'ذ', 'ث'], ['ش'], true⟩,
  ⟨"وذلك قولك رأيت قاضي جابر ورأيت دلو مالك", ['ي'], ['ج'], false⟩,
  ⟨"وذلك قولك رأيت قاضي جابر ورأيت دلو مالك", ['و'], ['م'], false⟩,
  ⟨"ولا تدغم في هذه الياء الجيم", ['ج'], ['ي'], false⟩]

def pairsOf (r : Saff) : List (Char × Char) :=
  r.src.flatMap fun a => (r.dst.filter (· != a)).map fun b => (a, b)

/-- الأزواجُ المُدغَمة. -/
def pos : List (Char × Char) := (rows.filter (·.idgham)).flatMap pairsOf
/-- الأزواجُ التي نصّ الباب على أنّها لا تُدغم. -/
def neg : List (Char × Char) := (rows.filter (! ·.idgham)).flatMap pairsOf

/-- **الاتّساق**: لا زوجَ في الجهتين. -/
theorem consistent : pos.all (fun p => !neg.contains p) = true := by decide

/-- عددُ الأزواج المدغَمة بلا تكرار. -/
theorem pos_count : pos.eraseDups.length = 93 := by decide

/-- عددُ الأزواج المنصوص على امتناعها بلا تكرار. -/
theorem neg_count : neg.eraseDups.length = 44 := by decide

theorem hamza_alif_inert : pos.all (fun (a, b) => a != 'ء' && a != 'ا' && b != 'ء' && b != 'ا') = true := by
  decide

def arbaa : List Char := ['م', 'ر', 'ف', 'ش']

/-- **الأربعةُ في اتّجاهٍ واحد**: لا تُدغم في غيرها، ولكلٍّ منها مُدغَمٌ فيه، ولكلٍّ منها امتناعٌ منصوص. -/
theorem arbaa_one_way :
    pos.all (fun (a, _) => !arbaa.contains a) = true ∧
    arbaa.all (fun x => pos.any (·.2 == x)) = true ∧
    arbaa.all (fun x => neg.any (·.1 == x)) = true := by
  decide

/-! ## ٢. R المكتوبة: علاقةُ الإدغام على الحروف -/

/-- **R**: الحرفُ يُدغم في مثله (إلّا الهمزةَ والألف: «وأما الهمزتان فليس فيهما إدغام»، «الألف لا تدغم في الألف») أو في ما
نصّ الباب على إدغامه فيه. -/
def R (a b : Char) : Bool := (a == b && a != 'ء' && a != 'ا') || pos.contains (a, b)

/-- عددُ أزواج R على الحروف التسعة والعشرين. -/
theorem R_count : (huruf.flatMap fun a => (huruf.filter (R a)).map fun b => (a, b)).length = 120 := by
  decide +kernel

/-! ## ٣. R الترتيبيّة مقابلَ R المكتوبة -/

def dist (a b : Char) : Nat := (makhrajOf a - makhrajOf b) + (makhrajOf b - makhrajOf a)

def thanaya : List Char := ['ط', 'د', 'ت', 'ظ', 'ث', 'ذ']

/-- الأسبابُ الأربعة المنصوصة لإدغامٍ أبعدَ من مخرجٍ واحد. -/
def named (a b : Char) : Bool :=
  ['ل', 'ن'].contains a || ['ض', 'ش'].contains b || (thanaya.contains a && thanaya.contains b)

/-- الأزواجُ المدغَمة الأبعدُ من مخرجٍ واحد. -/
def far : List (Char × Char) := pos.filter fun (a, b) => decide (dist a b > 1)

theorem far_count : far.eraseDups.length = 44 := by decide

/-- **كلُّ إدغامٍ أبعدَ من مخرجٍ واحدٍ تحت سببٍ منصوص**. -/
theorem far_pairs_named : far.all (fun (a, b) => named a b) = true := by decide

/-- **ولا سببَ زائد**: لكلّ سببٍ زوجٌ بعيدٌ لا يغطّيه غيرُه. -/
theorem far_clauses_needed :
    far.any (fun (a, b) => ['ل', 'ن'].contains a && !(['ض', 'ش'].contains b) &&
      !(thanaya.contains a && thanaya.contains b)) = true ∧
    far.any (fun (a, b) => ['ض', 'ش'].contains b && !(['ل', 'ن'].contains a) &&
      !(thanaya.contains a && thanaya.contains b)) = true ∧
    far.any (fun (a, b) => thanaya.contains a && thanaya.contains b &&
      !(['ل', 'ن'].contains a) && !(['ض', 'ش'].contains b)) = true := by
  decide

/-- أضلاعُ R الترتيبيّة (m، m+1) التي لا إدغامَ عليها في أيّ اتّجاه. -/
def unattested : List (Nat × Nat) :=
  ((List.range 15).map fun m => (m, m + 1)).filter fun (m, m') =>
    !pos.any (fun (a, b) => (makhrajOf a == m && makhrajOf b == m') || (makhrajOf a == m' && makhrajOf b == m))

/-- **R الترتيبيّة تزيد على الإدغام**: سبعةُ أضلاعٍ بلا إدغام — الحلقُ الأوسطُ والأدنى، والأدنى والقاف، والكافُ والجيم،
والجيمُ والضاد، والراءُ والطاء، والظاءُ والفاء، والشفتان والخياشيم. -/
theorem order_edges_unattested :
    unattested = [(1, 2), (2, 3), (4, 5), (5, 6), (9, 10), (12, 13), (14, 15)] := by decide

/-- **ولا تحتويه**: «اشغل رحبة» — اللامُ في الراء — بين مخرجيهما في الترتيب مخرجُ النون، وقال الباب «وليس بين مخرجيهما
مخرج»؛ والنونُ في الميم أبعدُ بستّة. -/
theorem order_misses : nM.wasl (makhrajOf 'ل') (makhrajOf 'ر') = false ∧ R 'ل' 'ر' = true ∧
    dist 'ن' 'م' = 6 ∧ R 'ن' 'م' = true := by
  decide

/-! ## ٢ب. R داخل البرهان: السببُ والمانع، والاستنفادُ بالشرط وبالسبب، ومانعُ الاستنفاد

R المنقولةُ صفوفًا شاهدٌ، لا تعريف. التعريفُ هنا من **أسباب الإدغام وموانعه كما نصّ عليها الباب** (كلٌّ بمرساته، يفحصها
`tests/test_makharij.py`)، ثمّ يُبرهَن أنّ الصفوفَ كلَّها تحته:
* **السبب** (لا إدغامَ بلا سبب): قربُ المخرج (المخرجُ نفسُه أو المجاور)، ولامُ المعرفة في الثلاثة عشر، والغنّةُ (النونُ في
  الميم والواو والياء)، والاستطالةُ (حروفُ الثنايا في الضاد والشين)، والحيّزُ الواحد (حروفُ الثنايا بعضُها في بعض).
* **المانع**: الهمزةُ والألف، والمفرُّ (الميمُ والراءُ والفاءُ والشينُ، والحاءُ مع العين «أجريت مجرى الميم مع الباء»)،
  والصفيرُ (الصادُ والسينُ والزايُ في غيرها)، واللينُ (الواوُ والياءُ إلّا مع النون)، واتّجاهُ الحلق (الأقربُ إلى الفم لا
  يُدغم في ما قبله).
* **Rd**: المثلُ في مثله إلّا الهمزةَ والألف، أو سببٌ بلا مانع.

والحكمُ على كلّ زوجٍ من الـ29 × 29 **ثلاثيٌّ لا ثنائيّ** (المادّة ١٣): مشهودٌ له، أو ممنوعٌ باسم، أو **مسكوتٌ عنه** — سببٌ بلا
مانعٍ ولا صفّ؛ لا يُعدّ إدغامًا ولا امتناعًا (لا يُستنتج الامتناعُ من غياب الشاهد). -/

inductive Sabab where
  | qurb | lam | ghunna | istitala | hayyiz
  deriving DecidableEq, Repr

inductive Mani where
  | hamzaAlif | mafarr | safir | lin | halq
  deriving DecidableEq, Repr

def asbabAll : List Sabab := [.qurb, .lam, .ghunna, .istitala, .hayyiz]
def mawaniAll : List Mani := [.hamzaAlif, .mafarr, .safir, .lin, .halq]

/-- مراسي الأسباب. -/
def sababAnchor : Sabab → String
  | .qurb => "والحروف المتقاربة مخارجها إذا أدغمت"
  | .lam => "ولام المعرفة تدغم في ثلاثة عشرة حرفا"
  | .ghunna => "وتدغم النون مع الميم لأن صوتهما واحد"
  | .istitala => "لأن الضاد استطالت لرخاوتها حتى اتصلت بمخرج اللام"
  | .hayyiz => "لا يمتنع بعضهن من بعض في الإدغام لأنهن من حيز واحد"

/-- مراسي الموانع. -/
def maniAnchor : Mani → List String
  | .hamzaAlif => ["ومن الحروف ما لا يدغم في مقاربه ولا يدغم فيه مقاربه"]
  | .mafarr => ["ومن الحروف حروف لا تدغم في المقاربة وتدغم المقاربة فيها", "فأجريت مجرى الميم مع الباء"]
  | .safir => ["لأنهن حروف الصفير وهن أندى في السمع"]
  | .lin => ["لأن فيهما لينا ومدا"]
  | .halq => ["لأن ما كان أقرب إلى حروف الفم كان أقوى على الإدغام"]

def lam13 : List Char := ['ن', 'ر', 'د', 'ت', 'ص', 'ط', 'ز', 'س', 'ظ', 'ث', 'ذ', 'ض', 'ش']

def isSabab : Sabab → Char → Char → Bool
  | .qurb, a, b => decide (dist a b ≤ 1)
  | .lam, a, b => a == 'ل' && lam13.contains b
  | .ghunna, a, b => a == 'ن' && ['م', 'و', 'ي'].contains b
  | .istitala, a, b => thanaya.contains a && ['ض', 'ش'].contains b
  | .hayyiz, a, b => thanaya.contains a && thanaya.contains b

def isMani : Mani → Char → Char → Bool
  | .hamzaAlif, a, b => ['ء', 'ا'].contains a || ['ء', 'ا'].contains b
  | .mafarr, a, b => arbaa.contains a || (a == 'ح' && b == 'ع')
  | .safir, a, b => ['ص', 'س', 'ز'].contains a && !(['ص', 'س', 'ز'].contains b)
  | .lin, a, b => ['و', 'ي'].contains a || (['و', 'ي'].contains b && a != 'ن')
  | .halq, a, b => decide (makhrajOf a ≤ 2 ∧ makhrajOf b ≤ 2 ∧ makhrajOf b < makhrajOf a)

def asbab (a b : Char) : List Sabab := asbabAll.filter (isSabab · a b)
def mawani (a b : Char) : List Mani := mawaniAll.filter (isMani · a b)

/-- **R داخل البرهان**. -/
def Rd (a b : Char) : Bool :=
  (a == b && a != 'ء' && a != 'ا') || (a != b && !(asbab a b).isEmpty && (mawani a b).isEmpty)

/-- **كلُّ إدغامٍ مشهودٍ له سببٌ ولا مانع**. -/
theorem shawahid_idgham : pos.all (fun (a, b) => !(asbab a b).isEmpty && (mawani a b).isEmpty) = true := by
  decide

/-- **كلُّ امتناعٍ مشهودٍ لا سببَ له أو له مانع**. -/
theorem shawahid_mumtani : neg.all (fun (a, b) => (asbab a b).isEmpty || !(mawani a b).isEmpty) = true := by
  decide

/-- **الحدُّ الأدنى المكتمل للأسباب**: لكلّ سببٍ إدغامٌ مشهودٌ لا سببَ له غيرُه — فلا سببَ زائد. -/
theorem sabab_needed : asbabAll.all (fun s => pos.any (fun (a, b) => asbab a b == [s])) = true := by
  decide

/-- **ومانعُ الاستنفاد كذلك**: لكلّ مانعٍ امتناعٌ مشهودٌ له سببٌ ولا مانعَ له غيرُه — فلا مانعَ زائد. -/
theorem mani_needed :
    mawaniAll.all (fun m => neg.any (fun (a, b) => !(asbab a b).isEmpty && mawani a b == [m])) = true := by
  decide

/-- R المشهودةُ داخل Rd. -/
theorem R_sub_Rd : huruf.all (fun a => huruf.all (fun b => !R a b || Rd a b)) = true := by
  decide +kernel

/-- القسمةُ الثلاثيّة للأزواج. -/
inductive Qism where
  | mithl | mithlMumtani | shahidIdgham | shahidMumtani | maskut | mumtani | izhar
  deriving DecidableEq, Repr

def qism (a b : Char) : Qism :=
  if a == b then (if a == 'ء' || a == 'ا' then .mithlMumtani else .mithl)
  else if pos.contains (a, b) then .shahidIdgham
  else if neg.contains (a, b) then .shahidMumtani
  else if (asbab a b).isEmpty then .izhar
  else if (mawani a b).isEmpty then .maskut
  else .mumtani

def qismAll : List Qism := [.mithl, .mithlMumtani, .shahidIdgham, .shahidMumtani, .maskut, .mumtani, .izhar]

def allPairs : List (Char × Char) := huruf.flatMap fun a => huruf.map fun b => (a, b)

/-- **الاستنفادُ بالشرط**: كلُّ زوجٍ من الـ29 × 29 في قسمٍ واحد، والأقسامُ بأعدادها، ومجموعُها 841. -/
theorem istinfad :
    allPairs.length = 841 ∧
    qismAll.map (fun q => (allPairs.filter fun (a, b) => qism a b == q).length) = [27, 2, 93, 44, 22, 37, 616] := by
  decide +kernel

/-- **المسكوتُ عنه بأعيانه**: سببٌ بلا مانعٍ ولا صفّ — وهو بعينه Rd بلا R. -/
theorem maskut_list :
    (allPairs.filter fun (a, b) => qism a b == .maskut) =
      [('ت', 'ر'), ('ث', 'ف'), ('ج', 'ض'), ('ج', 'ك'), ('ح', 'خ'), ('ح', 'غ'), ('خ', 'ق'), ('د', 'ر'), ('ذ', 'ف'),
       ('ض', 'ج'), ('ض', 'ش'), ('ض', 'ل'), ('ط', 'ر'), ('ظ', 'ف'), ('ع', 'خ'), ('ع', 'غ'), ('غ', 'ق'), ('ق', 'خ'),
       ('ق', 'غ'), ('ك', 'ج'), ('ك', 'ش'), ('ه', 'ع')] ∧
    (allPairs.filter fun (a, b) => Rd a b && !R a b) = (allPairs.filter fun (a, b) => qism a b == .maskut) := by
  decide +kernel

/-- **الصفةُ لازمة**: R ليست دالّةً في زوج المخرجين — الباءُ والميمُ مخرجٌ واحد، والباءُ تُدغم في الميم ولا عكس. -/
theorem R_needs_sifa : makhrajOf 'ب' = makhrajOf 'م' ∧ R 'ب' 'م' = true ∧ R 'م' 'ب' = false := by decide

/-- اسمُ الرفض لزوجٍ ليس في R. -/
def refusalName (a b : Char) : String :=
  match qism a b with
  | .mithlMumtani => "MANI_HAMZA_ALIF"
  | .maskut => "MASKUT_NOT_ATTESTED"
  | .izhar => "NO_SABAB"
  | _ => match mawani a b with
    | .hamzaAlif :: _ => "MANI_HAMZA_ALIF"
    | .mafarr :: _ => "MANI_MAFARR"
    | .safir :: _ => "MANI_SAFIR"
    | .lin :: _ => "MANI_LIN"
    | .halq :: _ => "MANI_HALQ"
    | [] => "NO_SABAB"

/-! ## ٤. قانونُ الموضع: الابتداء والوصل والوقف -/

/-- ما قبل الحرف الأوّل. -/
inductive Qabl where
  | ibtida | mutaharrik | madd | sakin
  deriving DecidableEq, Repr

/-- الحكمُ على موضع الإدغام. -/
inductive Hukm where
  | idgham (cells : List Cell)
  | needsWasl (cells : List Cell)
  | refused (name : String)
  deriving DecidableEq, Repr

/-- الصورةُ المدغمة: الأوّلُ ساكنٌ من جنس الثاني، ثمّ الثاني بحركته. -/
def merged (b : Char) (h : Haraka) : List Cell := [atom b .sukun, atom b h]

/-- **قانونُ الموضع**، بترتيب الباب: الثاني الساكن لا يُدغم فيه (الوقف)، ثمّ ما ليس من R، ثمّ الساكنُ قبل الأوّل،
ثمّ الابتداء. -/
def idghamAt (q : Qabl) (a b : Char) (h : Haraka) : Hukm :=
  if h == .sukun then .refused "IDGHAM_SECOND_SAKIN"
  else if !R a b then .refused (refusalName a b)
  else match q with
    | .sakin => .refused "SAKIN_BEFORE_FIRST"
    | .ibtida => .needsWasl (merged b h)
    | _ => .idgham (merged b h)

/-- **الصورةُ زوجُ إدغام** بمعنى `Hadd.idghamPair`. -/
theorem result_geminate (b : Char) (h : Haraka) :
    Hadd.idghamPair (atom b .sukun) (atom b h) = true := by
  simp [Hadd.idghamPair, atom]

/-- **الوقف**: لا إدغامَ في ساكنٍ ثانٍ — وفي الوقف يُسكَّن الآخر. -/
theorem waqf_law (q : Qabl) (a b : Char) : idghamAt q a b .sukun = .refused "IDGHAM_SECOND_SAKIN" := by
  simp [idghamAt]

/-- أصنافُ ما قبل الأوّل في نظام الجوار الثلاثيّ. -/
def qablK : Qabl → List Stages.K
  | .ibtida => []
  | .mutaharrik => [.cv]
  | .madd => [.cv, .v]
  | .sakin => [.cv, .c]

/-- **الابتداء**: الصورةُ المدغمة تبدأ بساكن فلا تُبتدأ في نظام الجوار، فيُحكم بهمزة الوصل. -/
theorem ibtida_law (a b : Char) (h : Haraka) (hh : h ≠ .sukun) (hR : R a b = true) :
    idghamAt .ibtida a b h = .needsWasl (merged b h) ∧
    licWasl ternary (qablK .ibtida ++ [.c, .cv]) = false := by
  refine ⟨?_, by decide⟩
  cases h <;> simp_all [idghamAt]

/-- **الوصل: شرطُ الباب هو قانونُ الجوار الثلاثيّ** — بعد متحرّكٍ أو مدٍّ يُدغم، وبعد ساكنٍ لا؛ وفي الثلاثة يطابق ذلك
ترخيصَ `ternary` لما قبل الأوّل ثمّ الساكنِ ثمّ المتحرّك. -/
theorem wasl_law_is_ternary (q : Qabl) (hq : q ≠ .ibtida) (a b : Char) (h : Haraka) (hh : h ≠ .sukun)
    (hR : R a b = true) :
    (idghamAt q a b h = .idgham (merged b h)) ↔ licWasl ternary (qablK q ++ [.c, .cv]) = true := by
  cases q <;> cases h <;> simp_all [idghamAt, qablK] <;> decide

/-- **الابتداءُ ثمّ همزةُ الوصل**: ما يُحكم فيه ابتداءً بهمزة الوصل يُدغم بعينه حين يتقدّمه متحرّك — والهمزةُ متحرّكة. -/
theorem ibtida_then_wasl (a b : Char) (h : Haraka) (hh : h ≠ .sukun) (hR : R a b = true) :
    idghamAt .ibtida a b h = .needsWasl (merged b h) ∧ idghamAt .mutaharrik a b h = .idgham (merged b h) := by
  cases h <;> simp_all [idghamAt]

/-- **الحدُّ الأدنى المكتمل**: الساكنُ الأوّلُ يُكمل مقطعًا بعد متحرّكٍ أو مدّ (مرخَّصٌ وقفًا)، ووحدَه لا يُكمل شيئًا. -/
theorem mukhtamal :
    licWaqf ternary (qablK .mutaharrik ++ [.c]) = true ∧ licWaqf ternary (qablK .madd ++ [.c]) = true ∧
    licWaqf ternary (qablK .ibtida ++ [.c]) = false := by
  decide

/-- **الوقفُ بعد الإدغام**: المدغمُ في الطرف (رَدّْ) مرخَّصٌ وقفًا لا وصلًا؛ والإدغامُ وصلًا قبله مرخَّص. -/
theorem waqf_after_idgham :
    licWaqf ternary [.cv, .c, .c] = true ∧ licWasl ternary [.cv, .c, .c] = false ∧
    licWasl ternary [.cv, .c, .cv] = true := by
  decide

/-- **نافذةُ الموضع حدٌّ أدنى**: كلُّ واحدٍ من مكوّناتها الأربعة (ما قبل، الأوّل، الثاني، حركةُ الثاني) يغيّر الحكمَ وحدَه. -/
theorem window_minimal :
    idghamAt .mutaharrik 'ل' 'ر' .fatha ≠ idghamAt .sakin 'ل' 'ر' .fatha ∧
    idghamAt .mutaharrik 'ب' 'م' .fatha ≠ idghamAt .mutaharrik 'ف' 'م' .fatha ∧
    idghamAt .mutaharrik 'ل' 'ر' .fatha ≠ idghamAt .mutaharrik 'ل' 'ك' .fatha ∧
    idghamAt .mutaharrik 'ل' 'ر' .fatha ≠ idghamAt .mutaharrik 'ل' 'ر' .sukun := by
  decide

def qablAll : List Qabl := [.ibtida, .mutaharrik, .madd, .sakin]
def harakatAll : List Haraka := [.fatha, .damma, .kasra, .sukun]

/-- نوافذُ الموضع لِما قبلٍ واحد: الأوّل × الثاني × حركةُ الثاني (29 × 29 × 4). -/
def windowsQ : List (Char × Char × Haraka) :=
  huruf.flatMap fun a => huruf.flatMap fun b => harakatAll.map fun h => (a, b, h)

def label : Hukm → String
  | .idgham _ => "IDGHAM"
  | .needsWasl _ => "NEEDS_WASL"
  | .refused n => n

def labels : List String :=
  ["IDGHAM", "NEEDS_WASL", "IDGHAM_SECOND_SAKIN", "SAKIN_BEFORE_FIRST", "MANI_HAMZA_ALIF", "MANI_MAFARR", "MANI_SAFIR",
   "MANI_LIN", "MANI_HALQ", "NO_SABAB", "MASKUT_NOT_ATTESTED"]

/-- عددُ نوافذ ما قبلٍ واحد بكلّ حكم. -/
def tally (q : Qabl) : List Nat :=
  labels.map fun l => (windowsQ.filter fun (a, b, h) => label (idghamAt q a b h) == l).length

/-! ### الاستنفادُ بالشرط على الموضع: كلُّ نافذةٍ (‎4 × 3,364 = 13,456‎) بحكمٍ واحدٍ من أحد عشر، ولكلّ ما قبلٍ عدُّه -/

theorem istinfad_ibtida : windowsQ.length = 3364 ∧ tally .ibtida = [0, 360, 841, 0, 51, 60, 63, 33, 18, 1872, 66] := by
  decide +kernel

theorem istinfad_mutaharrik : tally .mutaharrik = [360, 0, 841, 0, 51, 60, 63, 33, 18, 1872, 66] := by
  decide +kernel

theorem istinfad_madd : tally .madd = [360, 0, 841, 0, 51, 60, 63, 33, 18, 1872, 66] := by
  decide +kernel

theorem istinfad_sakin : tally .sakin = [0, 0, 841, 360, 51, 60, 63, 33, 18, 1872, 66] := by
  decide +kernel

/-- كلُّ نافذةٍ حكمُها من الأحد عشر. -/
theorem labels_closed :
    qablAll.all (fun q => windowsQ.all (fun (a, b, h) => labels.contains (label (idghamAt q a b h)))) = true := by
  decide +kernel

/-! ## ٥. تعارضٌ مسمًّى مع قيد الحدّ -/

open Haraka in
/-- «إِنَّ الْمَالْ» بلامٍ مسكَّنةٍ للإدغام (`ءِ نْ نَ لْ مَ اْ لْ`). -/
def innalmaal : List Cell :=
  [atom 'ء' kasra, atom 'ن' sukun, atom 'ن' fatha, atom 'ل' sukun, atom 'م' fatha, atom 'ا' sukun, atom 'ل' sukun]

open Haraka in
/-- «لَكَ». -/
def laka : List Cell := [atom 'ل' fatha, atom 'ك' fatha]

/-- **«إنّ المال لك» … «فإن الإدغام حسن لأن حرف المد بمنزلة متحرك في الإدغام»**: قانونُ الموضع يُدغم، و`strictB` على
الموصول يقبل، و`strictJoinB` يرفض لأنّ قافيةَ المدّ (اْ لْ) يقطعها الحدّ. -/
theorem mal_laka_refused :
    idghamAt .madd 'ل' 'ل' .fatha = .idgham (merged 'ل' .fatha) ∧
    Hadd.strictB (innalmaal ++ laka) = true ∧ Hadd.strictJoinB innalmaal laka = false := by
  have hk : Hadd.kindOf (innalmaal ++ laka) = Stages.flat .none [.CVC, .CVC, .CVVC, .CV, .CV] := by decide
  refine ⟨by decide, ?_, ?_⟩
  · simp only [Hadd.strictB, hk, Hadd.continueB_flat]; decide
  · simp only [Hadd.strictJoinB, Hadd.strictB, hk, Hadd.continueB_flat]; decide

end A116.MakharijIdgham
