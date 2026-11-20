import A116.Makharij
import A116.MakharijIdgham
import A116.Alif
import A116.Hadd
import A116.Maqayis

/-!
# جدولُ المخارج والصفات: البرجُ مخرجٌ ⊃ صفةٌ ⊃ حرفٌ ⊃ حركة (116)، أساسًا للحساب الرياضيّ للاقتران (ADR ٧٣)

**أمرُ المالك (2026-10-16):** «القانون المنقول عن سيبويه وابن جنّي والخليل والجزريّ … يجب بناء R داخل البرهان وفق قانون
الابتداء وقانون الوصل وقانون الوقف والاستنفاد بالشرط والاستنفاد بالسبب ومانع الاستنفاد وفق الحدّ الأدنى المكتمل؛ أريد جدولًا
للمخارج والصفات يكون أساس الحساب الرياضيّ للاقتران».

**المصادر** مختومةٌ في `corpora/kitab/` (`tools/gen_kitab.py`): «الكتاب» (JK006989) ونقلُ السيرافيّ لمخرج اللام، و«العين»
للخليل (JK000930)، و«سرّ صناعة الإعراب» لابن جنّي بنسختين (Shamela0012017 للمخارج — وفي JK001326 سقطَ مخرجُ القاف؛
وJK001326 للصفات — وفي Shamela0012017 سقطت الكافُ من قائمة الشديدة)، و«المقدّمة الجزريّة». كلُّ صفٍّ مرساةٌ منقولة،
يتحقّق `tests/test_makharij.py` أنّها تقع في نصّها مرّةً واحدة وأنّ حروفَ الصفّ ما تسمّيه أو ما تجمعه كلمتُها الجامعة
(«فحثه شخص سكت»…).

## ما يُبرهَن

* **الأنظمةُ الأربعة**: ابنُ جنّي يطابق سيبويه صفًّا صفًّا (`ibnJinni_eq_sibawayh`)؛ والجزريُّ هو سيبويه بعد نقل الألف
  وأختيها إلى الجوف (`jazari_refines`)؛ وأحيازُ الخليل تجمع مخارجَ سيبويه على الحروف الصحاح (`khalil_coarsens_sahih`) لا
  بترتيبها (`khalil_order_differs`)، والهمزةُ عنده في الهواء لا حيزَ لها (`khalil_hamza`).
* **الصفات**: اتّفاقُ النصوص على كلّ صفةٍ إلّا اثنتين (`ittifaq`)، والخلافُ مسمًّى: الانحرافُ عند الجزريّ اللامُ والراء
  وعند سيبويه وابن جنّي اللامُ وحدها (`ikhtilaf_inhiraf`)، والمتوسّطةُ عند ابن جنّي ثمانيةٌ والجزريُّ خمسةٌ — والفرقُ
  حروفُ الجوف بعينها (`ikhtilaf_tawassut`)؛ والأضدادُ قِسَمٌ تامّة (`addad`).
* **البرج** (`jadwal`، `khanat`): 29 حرفًا بمخارجها الثلاثة وصفاتها الأربعَ عشرة، ولكلّ حرفٍ أربعُ حركات — 116 خانةً بلا
  تكرار هي خاناتُ الشبكة بعينها (`khanat_cells`)؛ و**الحدُّ الأدنى المكتمل للفصل**: المخرجُ وأربعُ صفاتٍ تفصل الحروفَ كلَّها،
  ولا ثلاثَ تفصلها (`fasl_four`، `no_three`)، والصفتان اللازمتان في كلّ فاصلٍ رباعيٍّ الهمسُ والشدّة (`fasl_minimal_all`).
* **القوانينُ الثلاثة على الخانة**: المرخَّصُ 113، والمبتدَأُ به 84، والموقوفُ عليه 29 (`ibtida_wasl_waqf_counts`)؛ والجوفُ
  عند الجزريّ هو دورُ المدّ `v` في `Hadd.kindOne` بعينه لكلّ خانةٍ ولكلّ ما قبلها (`jawf_iff_v`) إلّا الألفَ بعد غير الفتحة
  (`alif_jawf_gap`، الدَّين `ALIF_CLOSER_NOT_REFUSED`)، واللينُ ساكنٌ مُغلِق (`lin_is_c`).
* **الاقتران** (`Iqtiran`): قانونُ ابن جنّي «كلّما تباعدت في التأليف كانت أحسن، وإذا تقارب الحرفان في مخرجيهما قبح
  اجتماعهما، ولا سيّما حروف الحلق» محسوبًا على جذور «مقاييس اللغة» المختومة (`Maqayis.roots`): المتجاورُ من مخرجٍ واحدٍ
  (حرفين مختلفين) أقلُّ من أساس الاستقلال، والحلقيُّ أقلّ (`iqtiran_qurb`، `iqtiran_halq`)؛ وقانونُ الذلاقة عند الخليل وابن
  جنّي بسببه ومانعه وما يجبر المانع (`dhalaq_law`).
-/

namespace A116.Jadwal

open A116 A116.Nizam A116.Makharij A116.Ladder

/-! ## ١. المصادر والصفوف -/

inductive Masdar where
  | kitab | sirafi | khalil | ibnJinniJK | ibnJinniSh | jazari
  deriving DecidableEq, Repr

structure Saff where
  masdar : Masdar
  anchor : String
  letters : List Char

/-- **أحيازُ الخليل** بترتيبه في «العين»: أحدَ عشرَ صفًّا. -/
def khalil : List Saff := [
  ⟨.khalil, "فأقصى الحروف كلها العين ثم الحاء", ['ع', 'ح', 'ه']⟩,
  ⟨.khalil, "ثم الخاء والغين في حيز واحد كلهن حلقية", ['خ', 'غ']⟩,
  ⟨.khalil, "ثم القاف والكاف لهويتان", ['ق', 'ك']⟩,
  ⟨.khalil, "ثم الجيم والشين والضاء في حيز واحد", ['ج', 'ش', 'ض']⟩,
  ⟨.khalil, "ثم الصاد والسين والزاء في حيز واحد", ['ص', 'س', 'ز']⟩,
  ⟨.khalil, "ثم الطاء والدال والتاء في حيز واحد", ['ط', 'د', 'ت']⟩,
  ⟨.khalil, "ثم الظاء والذال والثاء في حيز واحد", ['ظ', 'ذ', 'ث']⟩,
  ⟨.khalil, "ثم الراء واللام والنون في حيز واحد", ['ر', 'ل', 'ن']⟩,
  ⟨.khalil, "ثم الفاء والباء والميم في حيز واحد", ['ف', 'ب', 'م']⟩,
  ⟨.khalil, "ثم الألف والواو والياء في حيز واحد", ['ا', 'و', 'ي']⟩,
  ⟨.khalil, "والهمزة في الهواء لم يكن لها حيز تنسب إليه", ['ء']⟩]

/-- **أسماءُ الأحياز عند الخليل**: تسعة. -/
def khalilAsma : List Saff := [
  ⟨.khalil, "فالعين والحاء والخاء والغين حلقية", ['ع', 'ح', 'خ', 'غ', 'ه']⟩,
  ⟨.khalil, "والقاف والكاف لهويتان", ['ق', 'ك']⟩,
  ⟨.khalil, "والجيم والشين والضاد شجرية", ['ج', 'ش', 'ض']⟩,
  ⟨.khalil, "والصاد والسين والزاء أسلية", ['ص', 'س', 'ز']⟩,
  ⟨.khalil, "والطاء والتاء والدال نطعية", ['ط', 'ت', 'د']⟩,
  ⟨.khalil, "والظاء والذال والثاء لثوية", ['ظ', 'ذ', 'ث']⟩,
  ⟨.khalil, "والراء واللام والنون ذلقية", ['ر', 'ل', 'ن']⟩,
  ⟨.khalil, "والفاء والباء والميم شفوية", ['ف', 'ب', 'م']⟩,
  ⟨.khalil, "والياء والواو والألف والهمزة هوائية في حيز واحد", ['ي', 'و', 'ا', 'ء']⟩]

/-- **مخارجُ ابن جنّي** (Shamela0012017): ستّةَ عشر. -/
def ibnJinni : List Saff := [
  ⟨.ibnJinniSh, "مخرج الهمزة والألف والهاء", ['ء', 'ا', 'ه']⟩,
  ⟨.ibnJinniSh, "ومن وسط الحلق مخرج العين والحاء", ['ع', 'ح']⟩,
  ⟨.ibnJinniSh, "مع أول الفم، مخرج الغين والخاء", ['غ', 'خ']⟩,
  ⟨.ibnJinniSh, "من أقصى اللسان، مخرج القاف", ['ق']⟩,
  ⟨.ibnJinniSh, "وأدنى إلى مقدم الفم مخرج الكاف", ['ك']⟩,
  ⟨.ibnJinniSh, "وسط الحنك الأعلى، مخرج الجيم والشين والياء", ['ج', 'ش', 'ي']⟩,
  ⟨.ibnJinniSh, "وما يليها من الأضراس مخرج الضاد", ['ض']⟩,
  ⟨.ibnJinniSh, "مما فويق الضاحك والناب والرباعية والثنية", ['ل']⟩,
  ⟨.ibnJinniSh, "بينه وبين ما فويق الثنايا، مخرج النون", ['ن']⟩,
  ⟨.ibnJinniSh, "لانحرافه إلى اللام، مخرج الراء", ['ر']⟩,
  ⟨.ibnJinniSh, "وأصول الثنايا، مخرج الطاء والدال والتاء", ['ط', 'د', 'ت']⟩,
  ⟨.ibnJinniSh, "وطرف اللسان، مخرج الصاد والزاي والسين", ['ص', 'ز', 'س']⟩,
  ⟨.ibnJinniSh, "وأطراف الثنايا، مخرج الظاء والذال والثاء", ['ظ', 'ذ', 'ث']⟩,
  ⟨.ibnJinniSh, "وأطراف الثنايا العلى، مخرج الفاء", ['ف']⟩,
  ⟨.ibnJinniSh, "ومما بين الشفتين مخرج الباء والميم والواو", ['ب', 'م', 'و']⟩,
  ⟨.ibnJinniSh, "ومن الخياشيم مخرج النون الخفية", []⟩]

/-- **مخارجُ الجزريّ**: سبعةَ عشر، أوّلُها الجوف. -/
def jazari : List Saff := [
  ⟨.jazari, "فألف الجوف وأختاها", ['ا', 'و', 'ي']⟩,
  ⟨.jazari, "ثم لأقصى الحلق همز هاء", ['ء', 'ه']⟩,
  ⟨.jazari, "ثم لوسطه فعين حاء", ['ع', 'ح']⟩,
  ⟨.jazari, "أدناه غين خاؤها", ['غ', 'خ']⟩,
  ⟨.jazari, "والقاف ... أقصى اللسان فوق", ['ق']⟩,
  ⟨.jazari, "ثم الكاف أسفل", ['ك']⟩,
  ⟨.jazari, "والوسط فجيم الشين يا", ['ج', 'ش', 'ي']⟩,
  ⟨.jazari, "والضاد من حافته", ['ض']⟩,
  ⟨.jazari, "واللام أدناها لمنتهاها", ['ل']⟩,
  ⟨.jazari, "والنون من طرفه تحت اجعلوا", ['ن']⟩,
  ⟨.jazari, "والرا يدانيه لظهر أدخل", ['ر']⟩,
  ⟨.jazari, "والطاء والدال وتا منه", ['ط', 'د', 'ت']⟩,
  ⟨.jazari, "الصفير مستكن", ['ص', 'ز', 'س']⟩,
  ⟨.jazari, "والظاء والذال وثا للعليا", ['ظ', 'ذ', 'ث']⟩,
  ⟨.jazari, "فالفا مع اطراف الثنايا المشرفه", ['ف']⟩,
  ⟨.jazari, "للشفتين الواو باء ميم", ['و', 'ب', 'م']⟩,
  ⟨.jazari, "وغنة مخرجها الخيشوم", []⟩]

/-- مجموعتان متساويتان على الحروف التسعة والعشرين. -/
def same (l m : List Char) : Bool := huruf.all fun c => l.contains c == m.contains c

/-- **ابنُ جنّي يطابق سيبويه** صفًّا صفًّا (سيبويه بصفّ اللام من نقل السيرافيّ). -/
theorem ibnJinni_eq_sibawayh :
    ibnJinni.length = 16 ∧ (ibnJinni.zip makharij16).all (fun (r, s) => same r.letters s.2) = true := by
  decide

/-- **الجزريُّ سيبويه بعد نقل حروف المدّ إلى الجوف**: سبعةَ عشر، أوّلُها الألفُ وأختاها، والباقي صفوفُ سيبويه بترتيبها
بلا الألف. -/
theorem jazari_refines :
    jazari.length = 17 ∧ same (jazari.head?.map (·.letters) |>.getD []) ['ا', 'و', 'ي'] = true ∧
    ((jazari.drop 1).zip makharij16).all (fun (r, s) => same r.letters (s.2.erase 'ا')) = true := by
  decide

/-- رقمُ الصفّ الذي فيه الحرف. -/
def rowOf (rs : List Saff) (c : Char) : Nat := (rs.findIdx? fun r => r.letters.contains c).getD 99

def sahih : List Char := huruf.filter fun c => !(['ء', 'ا', 'و', 'ي'].contains c)

/-- **أحيازُ الخليل تجمع مخارجَ سيبويه على الصحاح**: حرفان صحيحان من مخرجٍ واحدٍ في حيزٍ واحد. -/
theorem khalil_coarsens_sahih :
    sahih.all (fun a => sahih.all (fun b =>
      makhrajOf a != makhrajOf b || rowOf khalilAsma a == rowOf khalilAsma b)) = true := by
  decide

/-- **ولا بترتيبها**: اللامُ قبل الطاء عند سيبويه، وحيزُ اللام بعد حيز الطاء عند الخليل. -/
theorem khalil_order_differs :
    makhrajOf 'ل' < makhrajOf 'ط' ∧ rowOf khalil 'ط' < rowOf khalil 'ل' := by decide

/-- **الهمزةُ عند الخليل في الهواء**، وعند سيبويه في أقصى الحلق مع الهاء. -/
theorem khalil_hamza :
    rowOf khalil 'ء' ≠ rowOf khalil 'ه' ∧ makhrajOf 'ء' = makhrajOf 'ه' := by decide

/-- أحيازُ الخليل الأحدَ عشر قسمةٌ تامّة على الـ29، وأسماؤه التسعة كذلك. -/
theorem khalil_partition :
    (khalil.flatMap (·.letters)).Nodup ∧ (khalil.flatMap (·.letters)).length = 29 ∧
    (khalilAsma.flatMap (·.letters)).Nodup ∧ (khalilAsma.flatMap (·.letters)).length = 29 := by
  decide

/-! ## ٢. الصفات -/

inductive Sifa where
  | hams | shidda | tawassut | istila | itbaq | idhlaq | safir | qalqala | lin | inhiraf | takrir | tafashi
  | istitala | ghunna
  deriving DecidableEq, Repr

def sifaAll : List Sifa :=
  [.hams, .shidda, .tawassut, .istila, .itbaq, .idhlaq, .safir, .qalqala, .lin, .inhiraf, .takrir, .tafashi,
   .istitala, .ghunna]

structure Nass where
  sifa : Sifa
  masdar : Masdar
  anchor : String
  letters : List Char

/-- **نصوصُ الصفات** بمراسيها: ما لسيبويه منقولٌ من `Makharij` بمرساته هناك. -/
def nusus : List Nass := [
  ⟨.hams, .kitab, mahmusa.1, mahmusa.2⟩,
  ⟨.hams, .ibnJinniJK, "ستشحثك خصفة", ['س', 'ت', 'ش', 'ح', 'ث', 'ك', 'خ', 'ص', 'ف', 'ه']⟩,
  ⟨.hams, .jazari, "فحثه شخص سكت", ['ف', 'ح', 'ث', 'ه', 'ش', 'خ', 'ص', 'س', 'ك', 'ت']⟩,
  ⟨.shidda, .kitab, (manners.getD 0 ("", [])).1, (manners.getD 0 ("", [])).2⟩,
  ⟨.shidda, .ibnJinniJK, "أجدت طبقك", ['ء', 'ج', 'د', 'ت', 'ط', 'ب', 'ق', 'ك']⟩,
  ⟨.shidda, .ibnJinniJK, "فالشديدة ثمانية أحرف وهي الهمزة والقاف والكاف والجيم والطاء والدال والتاء والباء",
    ['ء', 'ق', 'ك', 'ج', 'ط', 'د', 'ت', 'ب']⟩,
  ⟨.shidda, .jazari, "أجد قط بكت", ['ء', 'ج', 'د', 'ق', 'ط', 'ب', 'ك', 'ت']⟩,
  ⟨.tawassut, .ibnJinniJK, "لم يرو عنا", ['ل', 'م', 'ي', 'ر', 'و', 'ع', 'ن', 'ا']⟩,
  ⟨.tawassut, .jazari, "لن عمر", ['ل', 'ن', 'ع', 'م', 'ر']⟩,
  ⟨.istila, .ibnJinniJK, "فالمستعلية سبعة وهي الخاء والغين والقاف والضاد والطاء والصاد والظاء",
    ['خ', 'غ', 'ق', 'ض', 'ط', 'ص', 'ظ']⟩,
  ⟨.istila, .jazari, "خص ضغط قظ", ['خ', 'ص', 'ض', 'غ', 'ط', 'ق', 'ظ']⟩,
  ⟨.itbaq, .kitab, mutbaqa.1, mutbaqa.2⟩,
  ⟨.itbaq, .ibnJinniJK, "فالمطبقة أربعة وهي الضاد والطاء والصاد والظاء", ['ض', 'ط', 'ص', 'ظ']⟩,
  ⟨.itbaq, .jazari, "وصاد ضاد طاء ظاء مطبقه", ['ص', 'ض', 'ط', 'ظ']⟩,
  ⟨.idhlaq, .khalil, "إعلم أن الحروف الذلق والشفوية ستة وهي ر ل ن ف ب م", ['ر', 'ل', 'ن', 'ف', 'ب', 'م']⟩,
  ⟨.idhlaq, .ibnJinniJK, "ومنها حروف الذلاقة وهي ستة اللام والراء والنون والفاء والباء والميم",
    ['ل', 'ر', 'ن', 'ف', 'ب', 'م']⟩,
  ⟨.idhlaq, .jazari, "فر من لب", ['ف', 'ر', 'م', 'ن', 'ل', 'ب']⟩,
  ⟨.safir, .kitab, "لأنهن حروف الصفير وهن أندى في السمع", ['ص', 'س', 'ز']⟩,
  ⟨.safir, .jazari, "صفيرها صاد وزاي سين", ['ص', 'ز', 'س']⟩,
  ⟨.qalqala, .ibnJinniJK, "القلقلة وهي القاف والجيم والطاء والدال والباء", ['ق', 'ج', 'ط', 'د', 'ب']⟩,
  ⟨.qalqala, .jazari, "قطب جد", ['ق', 'ط', 'ب', 'ج', 'د']⟩,
  ⟨.lin, .kitab, (manners.getD 6 ("", [])).1, (manners.getD 6 ("", [])).2⟩,
  ⟨.lin, .jazari, "واو وياء سكنا وانفتحا ... قبلهما", ['و', 'ي']⟩,
  ⟨.inhiraf, .kitab, (manners.getD 3 ("", [])).1, (manners.getD 3 ("", [])).2⟩,
  ⟨.inhiraf, .ibnJinniJK, "فويقهما وهو اللام", ['ل']⟩,
  ⟨.inhiraf, .jazari, "والانحراف صححا في اللام والرا", ['ل', 'ر']⟩,
  ⟨.takrir, .kitab, (manners.getD 5 ("", [])).1, (manners.getD 5 ("", [])).2⟩,
  ⟨.takrir, .ibnJinniJK, "ومنها المكرر وهو الراء", ['ر']⟩,
  ⟨.takrir, .jazari, "وبتكرير جعل", ['ر']⟩,
  ⟨.tafashi, .jazari, "وللتفشي الشين", ['ش']⟩,
  ⟨.istitala, .kitab, "لأن الضاد استطالت لرخاوتها حتى اتصلت بمخرج اللام", ['ض']⟩,
  ⟨.istitala, .jazari, "ضادا استطل", ['ض']⟩,
  ⟨.ghunna, .kitab, "إلا أن النون والميم قد يعتمد لهما في الفم والخياشيم", ['ن', 'م']⟩,
  ⟨.ghunna, .ibnJinniJK, "غير أن الميم والنون من جملة المجهورة قد يعتمد لهما في الفم والخياشيم", ['م', 'ن']⟩]

def nususOf (s : Sifa) : List Nass := nusus.filter (·.sifa == s)

/-- **الاتّفاق**: لكلّ صفةٍ نصّان فأكثر، وكلُّ نصوصها متّفقةٌ على حروفها، إلّا الانحرافَ والتوسّط. -/
theorem ittifaq :
    sifaAll.all (fun s => s == .tafashi || (nususOf s).length ≥ 2) = true ∧
    (sifaAll.filter (fun s => s != .inhiraf && s != .tawassut)).all (fun s =>
      (nususOf s).all (fun n => (nususOf s).all (fun m => same n.letters m.letters))) = true := by
  decide

/-- **الخلافُ في الانحراف**: الجزريُّ يزيد الراء. -/
theorem ikhtilaf_inhiraf :
    (nususOf .inhiraf).map (·.letters) = [['ل'], ['ل'], ['ل', 'ر']] := by decide

def tawIJ : List Char := ((nususOf .tawassut).head?.map (·.letters)).getD []
def tawJ : List Char := ((nususOf .tawassut).getLast?.map (·.letters)).getD []

/-- **الخلافُ في التوسّط**: كلُّ متوسّطٍ عند الجزريّ متوسّطٌ عند ابن جنّي، وما زاده ابنُ جنّي حروفُ الجوف بعينها. -/
theorem ikhtilaf_tawassut :
    tawJ.all tawIJ.contains = true ∧ same (tawIJ.filter fun c => !tawJ.contains c) ['ا', 'و', 'ي'] = true := by
  decide

/-- الحرفُ المعتمَد لكلّ صفة: نصُّ الجزريّ إن سمّى حروفًا، وإلّا أوّلُ نصوصها. -/
def canon (s : Sifa) : List Char :=
  match (nususOf s).find? (fun n => n.masdar == .jazari && !n.letters.isEmpty) with
  | some n => n.letters
  | none => ((nususOf s).head?.map (·.letters)).getD []

def has (s : Sifa) (c : Char) : Bool := (canon s).contains c

/-- **الأضدادُ قِسَمٌ تامّة** («صفاتها جهر ورخو مستفل منفتح مصمتة والضد قل»): الشدّةُ والتوسّطُ لا يجتمعان، وكلُّ صفةٍ
حروفُها من الـ29 بلا تكرار. -/
theorem addad :
    huruf.all (fun c => !(has .shidda c && has .tawassut c)) = true ∧
    sifaAll.all (fun s => (canon s).Nodup && (canon s).all huruf.contains) = true := by
  decide

/-! ## ٣. البرج: مخرجٌ ⊃ صفةٌ ⊃ حرفٌ ⊃ حركة -/

/-- صفُّ الحرف في الجدول. -/
structure Harf where
  c : Char
  makhraj : Nat
  hayyiz : Nat
  jazariMakhraj : Nat
  sifat : List Bool
  deriving DecidableEq, Repr

/-- مخرجُ الحرف الصامت عند الجزريّ (الألفُ لا صامتَ لها: الجوف). -/
def jazIdx (c : Char) : Nat :=
  match ((jazari.drop 1).findIdx? fun r => r.letters.contains c) with
  | some i => i + 1
  | none => 0

/-- **الجدول**: الحروفُ بترتيب المخارج الستّةَ عشر. -/
def jadwal : List Harf :=
  placed16.map fun c => ⟨c, makhrajOf c, rowOf khalil c, jazIdx c, sifaAll.map (has · c)⟩

def harakat : List Haraka := [.fatha, .damma, .kasra, .sukun]

/-- **الخانات**: لكلّ حرفٍ في الجدول حركاتُه الأربع. -/
def khanat : List Cell := jadwal.flatMap fun h => harakat.map (atom h.c ·)

/-- **البرجُ هو الشبكة**: 116 خانةً بلا تكرار، هي خاناتُ `cells` بعينها. -/
theorem khanat_cells :
    khanat.length = 116 ∧ khanat.Nodup ∧ cells.all khanat.contains = true := by
  decide +kernel

/-- مفتاحُ الفصل: المخرجُ ومجموعةٌ من الصفات. -/
def key (ss : List Sifa) (c : Char) : Nat × List Bool := (makhrajOf c, ss.map (has · c))

def separates (ss : List Sifa) : Bool := (placed16.map (key ss)).Nodup

def subsets : List Sifa → Nat → List (List Sifa)
  | _, 0 => [[]]
  | [], _ + 1 => []
  | s :: t, k + 1 => (subsets t k).map (s :: ·) ++ subsets t (k + 1)

/-- **أربعٌ تفصل**: المخرجُ والهمسُ والشدّةُ والتوسّطُ والاستعلاء. -/
theorem fasl_four : separates [.hams, .shidda, .tawassut, .istila] = true := by decide

/-- **ولا ثلاث**: لا مجموعةَ من ثلاث صفاتٍ أو أقلّ تفصل الحروفَ مع المخرج. -/
theorem no_three : ([0, 1, 2, 3].flatMap (subsets sifaAll)).all (fun ss => !separates ss) = true := by
  decide +kernel

/-- **كلُّ فاصلٍ رباعيٍّ** من الثمانية فيه الهمسُ والشدّة. -/
theorem fasl_minimal_all :
    ((subsets sifaAll 4).filter separates).length = 8 ∧
    ((subsets sifaAll 4).filter separates).all (fun ss => ss.contains .hams && ss.contains .shidda) = true := by
  decide +kernel

/-! ## ٤. القوانين الثلاثة على الخانة -/

def licensableCell (x : Cell) : Bool := !(x.carrier == carrierOf 'ا' && x.haraka != .sukun)

/-- **الابتداءُ والوصلُ والوقف عدًّا**: المرخَّصُ من البرج 113، وما يُبتدأ به (متحرّكٌ مرخَّص) 84، وما يوقف عليه
(ساكن) 29. -/
theorem ibtida_wasl_waqf_counts :
    (khanat.filter licensableCell).length = 113 ∧
    (khanat.filter fun x => licensableCell x && x.haraka != .sukun).length = 84 ∧
    (khanat.filter fun x => x.haraka == .sukun).length = 29 := by
  decide +kernel

/-- **الجوفُ عند الجزريّ**: «فألف الجوف وأختاها وهي حروف مدّ» — الألفُ الساكنة، والواوُ الساكنةُ بعد ضمّة، والياءُ الساكنةُ
بعد كسرة. -/
def jawfCell (prev : Option Haraka) (x : Cell) : Bool :=
  x.haraka == .sukun &&
    (x.carrier == carrierOf 'ا' ||
     (x.carrier == carrierOf 'و' && prev == some .damma) ||
     (x.carrier == carrierOf 'ي' && prev == some .kasra))

def prevs : List (Option Haraka) := none :: harakat.map some

/-- **الجوفُ هو دورُ المدّ بعينه** لكلّ خانةٍ غير الألف ولكلّ ما قبلها. -/
theorem jawf_iff_v :
    prevs.all (fun p => (khanat.filter (·.carrier != carrierOf 'ا')).all (fun x =>
      jawfCell p x == (Hadd.kindOne p x == .v))) = true := by
  decide

/-- **وفي الألف خلافٌ مسمًّى**: بعد غير الفتحة هي جوفٌ عند الجزريّ ومُغلِقٌ `c` في `kindOne` (`ALIF_CLOSER_NOT_REFUSED`). -/
theorem alif_jawf_gap :
    jawfCell (some .damma) (atom 'ا' .sukun) = true ∧ Hadd.kindOne (some .damma) (atom 'ا' .sukun) = .c ∧
    jawfCell (some .fatha) (atom 'ا' .sukun) = true ∧ Hadd.kindOne (some .fatha) (atom 'ا' .sukun) = .v := by
  decide

/-- **اللينُ ساكنٌ مُغلِق**: «واو وياء سكنا وانفتحا قبلهما» — دورُهما `c` لا `v`. -/
theorem lin_is_c :
    Hadd.kindOne (some .fatha) (atom 'و' .sukun) = .c ∧ Hadd.kindOne (some .fatha) (atom 'ي' .sukun) = .c := by
  decide

/-! ## ٥. الاقتران -/

/-- حرفُ الأصل ذي الرقم d من «مقاييس اللغة» (`RootGrade.toCarrier`: الحواملُ بعد الألف). -/
def cd (d : Nat) : Char := Field112.carriers29.getD (d + 1) ' '

def charOf (d : Fin 28) : Char := cd d.val

def pairs3 (r : List (Fin 28)) : List (Char × Char) :=
  match r with
  | [a, b, c] => [(charOf a, charOf b), (charOf b, charOf c)]
  | _ => []

/-- زوجٌ متقاربٌ: حرفان مختلفان من مخرجٍ واحد. -/
def qarib (p : Char × Char) : Bool := p.1 != p.2 && makhrajOf p.1 == makhrajOf p.2

def halqi (c : Char) : Bool := makhrajOf c ≤ 2

def asl : List Char := (List.range 28).map cd

/-- عددُ الأزواج المرتّبة من الحروف الأصول الثمانية والعشرين بشرطٍ ما (أساسُ الاستقلال، معلَن). -/
def baseCount (p : Char × Char → Bool) : Nat :=
  (asl.flatMap fun a => asl.map fun b => (a, b)).countP p

/-- مخارجُ الأصول بأرقامها، مطابَقةً لـ`makhrajOf` (`mkAsl_eq`). -/
def mkAsl : List Nat := [14, 10, 12, 5, 1, 2, 10, 12, 9, 11, 11, 5, 11, 6, 10, 12, 1, 2, 13, 3, 4, 7, 14, 8, 0, 14, 5, 0]

theorem mkAsl_eq : asl.map makhrajOf = mkAsl := by decide

def mkD (d : Nat) : Nat := mkAsl.getD d 99
def qaribD (p : Nat × Nat) : Bool := p.1 != p.2 && mkD p.1 == mkD p.2
def halqD (p : Nat × Nat) : Bool := qaribD p && decide (mkD p.1 ≤ 2)

/-- الأرقامُ والحروف: المتقاربُ والحلقيُّ على الأرقام هو على الحروف بعينه. -/
theorem qaribD_agrees :
    (List.range 28).all (fun i => (List.range 28).all (fun j =>
      qaribD (i, j) == qarib (cd i, cd j) && halqD (i, j) == (qarib (cd i, cd j) && halqi (cd i)))) = true := by
  decide

/-- الزوجان المتجاوران في جذرٍ ثلاثيٍّ عددُه n (الأصلُ الأوّلُ منزلةُ الآحاد: `RootGrade.num`). -/
def digitPairs (n : Nat) : List (Nat × Nat) := [(n % 28, n / 28 % 28), (n / 28 % 28, n / 28 / 28 % 28)]

/-- **والجذرُ نفسُه**: أزواجُ الجذر المسترَدّ من عدده هي أزواجُ أرقامه حروفًا. -/
theorem pairs3_unnum (n : Nat) :
    pairs3 (RootGrade.unnum 3 n) = (digitPairs n).map fun p => (cd p.1, cd p.2) := rfl

def obsD : List (Nat × Nat) := Maqayis.nums.flatMap digitPairs

/-- أزواجُ «مقاييس اللغة» المتجاورة حروفًا: هي أزواجُ جذورها (`Maqayis.roots`). -/
def obs : List (Char × Char) := Maqayis.roots.flatMap pairs3

theorem obs_eq : obs = obsD.map fun p => (cd p.1, cd p.2) := by
  simp only [obs, obsD, Maqayis.roots, List.flatMap_map, List.map_flatMap, pairs3_unnum]

theorem digits_lt : ∀ p ∈ obsD, p.1 < 28 ∧ p.2 < 28 := by
  intro p hp
  simp only [obsD, List.mem_flatMap, digitPairs, List.mem_cons, List.not_mem_nil, or_false] at hp
  obtain ⟨n, _, h | h⟩ := hp <;> subst h <;> exact ⟨Nat.mod_lt _ (by decide), Nat.mod_lt _ (by decide)⟩

theorem agrees_at (i j : Nat) (hi : i < 28) (hj : j < 28) :
    qaribD (i, j) = qarib (cd i, cd j) ∧ halqD (i, j) = (qarib (cd i, cd j) && halqi (cd i)) := by
  have h := qaribD_agrees
  simp only [List.all_eq_true, List.mem_range, Bool.and_eq_true, beq_iff_eq] at h
  exact h i hi j hj

theorem count_bridge :
    obs.countP qarib = obsD.countP qaribD ∧
    obs.countP (fun p => qarib p && halqi p.1) = obsD.countP halqD := by
  rw [obs_eq, List.countP_map, List.countP_map]
  constructor
  · apply List.countP_congr
    intro p hp
    obtain ⟨h1, h2⟩ := digits_lt p hp
    simp [(agrees_at p.1 p.2 h1 h2).1]
  · apply List.countP_congr
    intro p hp
    obtain ⟨h1, h2⟩ := digits_lt p hp
    simp [(agrees_at p.1 p.2 h1 h2).2]

theorem obs_counts :
    obsD.length = 9012 ∧ obsD.countP qaribD = 160 ∧ obsD.countP halqD = 8 := by
  decide +kernel

/-- **قانونُ ابن جنّي محسوبًا**: في جذور «مقاييس اللغة» المختومة، المتجاورُ المتقاربُ (حرفان مختلفان من مخرجٍ واحد) 160
من 9,012 زوجًا، وأساسُ الاستقلال 36 من 784 — فالنسبةُ دونه (‎160 · 784 < 36 · 9,012‎). -/
theorem iqtiran_qurb :
    obs.length = 9012 ∧ obs.countP qarib = 160 ∧ baseCount qarib = 36 ∧
    obs.countP qarib * 784 < baseCount qarib * obs.length := by
  have hl : obs.length = 9012 := by rw [obs_eq, List.length_map]; exact obs_counts.1
  have hb : baseCount qarib = 36 := by decide +kernel
  rw [hl, count_bridge.1, obs_counts.2.1, hb]
  decide

/-- **«ولا سيّما حروف الحلق»**: المتقاربُ الحلقيُّ 8 وأساسُه 6، ونسبتُه إلى أساسه دون نسبة المتقارب كلّه إلى أساسه
(‎8 · 36 < 6 · 160‎). -/
theorem iqtiran_halq :
    obs.countP (fun p => qarib p && halqi p.1) = 8 ∧ baseCount (fun p => qarib p && halqi p.1) = 6 ∧
    obs.countP (fun p => qarib p && halqi p.1) * baseCount qarib <
      baseCount (fun p => qarib p && halqi p.1) * obs.countP qarib := by
  have hb : baseCount qarib = 36 := by decide +kernel
  have hh : baseCount (fun p => qarib p && halqi p.1) = 6 := by decide +kernel
  rw [count_bridge.2, obs_counts.2.2, hh, hb, count_bridge.1, obs_counts.2.1]
  decide

/-! ### قانونُ الذلاقة: السببُ والمانعُ وجابرُه -/

def idhlaq : List Char := canon .idhlaq

/-- **السبب**: الرباعيُّ والخماسيُّ فيه حرفٌ من الذلاقة؛ **المانع**: خلوُّه منها؛ **والجابر** عند الخليل وابن جنّي: العينُ
أو القافُ مع السين أو الدال («ولا سيما وهناك الدال والسين»). -/
def dhalaqHukm (w : List Char) : String :=
  if w.length < 4 then "LA_SHART"
  else if w.any idhlaq.contains then "SABAB"
  else if (w.contains 'ع' || w.contains 'ق') && (w.contains 'س' || w.contains 'د') then "MAJBUR"
  else "DAKHIL"

/-- **قانونُ الذلاقة على شواهد النصّين**: جعفر وسفرجل وفرزدق وقعضب بسببه؛ والعسجدُ والدهدقة مجبوران؛ والكشعثجُ وأخواتُه
دخيلٌ («مولّدات لا تجوز في كلام العرب»). -/
theorem dhalaq_law :
    ([['ج', 'ع', 'ف', 'ر'], ['س', 'ف', 'ر', 'ج', 'ل'], ['ف', 'ر', 'ز', 'د', 'ق'], ['ق', 'ع', 'ض', 'ب']].map dhalaqHukm) =
      ["SABAB", "SABAB", "SABAB", "SABAB"] ∧
    ([['ع', 'س', 'ج', 'د'], ['د', 'ه', 'د', 'ق']].map dhalaqHukm) = ["MAJBUR", "MAJBUR"] ∧
    ([['ك', 'ش', 'ع', 'ث', 'ج'], ['خ', 'ض', 'ع', 'ث', 'ج'], ['ك', 'ش', 'ع', 'ط', 'ج']].map dhalaqHukm) =
      ["DAKHIL", "DAKHIL", "DAKHIL"] := by
  decide

end A116.Jadwal
