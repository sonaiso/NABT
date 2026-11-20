import A116.Qabil

/-!
# خواصُّ الجنس شرطُ الحقيقة: الكلامُ والنطقُ والفهمُ (ADR ٩٦، أمرُ المالك 2026-10-17)

نصُّ المالك: «الكلامُ والنطقُ والفهمُ مصدر، وهو إذا اقترن بالإنسان حقيقة، سواءٌ اقترانُ مصدرٍ أو مشتقّاتِ أسماءٍ أو
مشتقّاتِ أفعال؛ ولكن إذا اقترن مصدرُ الكلام والنطق والفهم مع الحجر أو الكلب أو القمر فهذا اقترانٌ يجعل الحقيقةَ ممتنعة،
لأنّ خواصّ الحجر وخواصّ الكلب وخواصّ القمر تجعل الحقيقةَ ممتنعة، ولذلك تُحمل على المجاز».

ورفض المالكُ صيغةً سابقة («صفةُ المشتقّ جنسُ المصدر») بأنّها هلوسة: ليست في المستودع، والخاصّةُ للجنس الذي يُسند إليه
الحدث لا للمصدر. فالصيغةُ هنا: **المصدرُ يشترط خاصّةً في دوره، والجنسُ يحمل خواصّه، والحقيقةُ ⟺ الشرطُ في الخواصّ**.

## السند (الأسطرُ 1-based)

شرحُ السيرافيّ (Sham19Y0017726):
* س23550–23552: «جعلت العربُ لما يعقل… اختصاصًا… لما اختصّ به ما يعقل بأنّه يخاطِب ويخاطَب، ويأمر، ويؤمر، وتخبر وتخبر
  عنه. وما لا يعقل ليس له من ذلك إلّا أنّه يُخبر عنه» — شرطُ المصدر في دوره.
* س4160–4161: «لأنّ الجمع بالواو لما يعقل، وهم الثقلانُ والملائكة».
* س4161–4166: «وربّما ذُكر لما لا يعقل فعلٌ يكون الأغلبُ فيه أن يكون لما يعقل، فيُجعل لفظُه كلفظ ما يعقل تشبيهًا…
  رأيتهم لي ساجدين، فجمع الشمسَ والقمرَ والكواكب بالياء والنون؛ وذلك لأنّه وصفها بالسجود الذي يكون ممّا يعقل، ولو
  أجراها على معناها وحقِّها من اللفظ لقال ساجدات».
* س4166–4168: «قالت نملة… ولم يقل ادخلن… لأنّه أخبر عنهنّ بالخطاب الذي يكون لما يعقل».
* س4156: «البراغيث ممّا لا يعقل»؛ س1797–1799: «الذي يمشي على أربع… نحو الخيل والبغال والحمير والأنعام وسائر ذوات الأربع»
  ليس ممّا يعقل، والحيّات كذلك؛ س23548: «ولا تقول جمالُك ذاهبون».

الكتاب (JK006989): س4892–4894: «رأيتهم لي ساجدين… فزعم أنّه بمنزلة ما يعقل ويسمع لما ذكرهم بالسجود، وصار النملُ بتلك
المنزلة حين حدّثت عنه كما تحدّث عن الأناسى»؛ س4899: «فجاز هذا حيث صارت هذه الأشياءُ عندهم تؤمر وتطيع وتفهم».

الشخصيّة ج3: س371: «كدلالة الإنسان على الحيوان الناطق» — النطقُ فصلُ الإنسان.

التفكير: س23: «العقلُ غيرُ موجودٍ إلّا عند الإنسان… الغرائزُ… موجودةٌ عند الإنسان وعند الحيوان… وإنّما هو تمييزٌ غريزيٌّ
ليس غير».

## ما يُبنى

* `shart`: شرطُ المصدر في دوره — يحتاج ما يعقل، أو لا يحتاجه («يُخبر عنه»)، أو لا نصّ.
* `aqilOf`: خاصّةُ الجنس من صفٍّ بنصّه، أو بحصر التفكير س23 («إلّا عند الإنسان»)، أو بوراثةٍ من كلّيٍّ معلَنة.
* `hukm`: الحقيقةُ ⟺ الشرطُ في الخواصّ؛ والمجازُ ⟺ الشرطُ يحتاج ما يعقل والجنسُ معلومٌ لا يعقل؛ وغيرُ ذلك «لا حكم».
* المصدرُ ومشتقّاتُ الأسماء والأفعال حكمُها حكمُ المصدر في الدور نفسِه (ADR ٩٤)، والصيغةُ ربطٌ ثانٍ (ADR ٩٥).
* اللفظُ شاهد: جمعُ ما يعقل على ما لا يعقل («ساجدين») قرينةٌ في اللفظ توافق حكمَ الخاصّة.
-/

namespace A116.Khawass

open A116.Majaz (Hukm Sigha hukmSigha)
open A116.Qabil (Dawr jam)

/-! ## ١. شرطُ المصدر في دوره (السيرافيّ س23550–23552) -/

/-- المصادرُ: الخطابُ (الكلامُ والقولُ)، والأمرُ، والإخبارُ، والنطقُ، والفهمُ، والسجود. -/
inductive Masdar | khitab | amr | ikhbar | nutq | fahm | sujud
  deriving DecidableEq, Repr

/-- `some true`: يحتاج ما يعقل؛ `some false`: لا يحتاجه؛ `none`: لا نصّ في هذا الدور.
* «يخاطِب ويخاطَب، ويأمر ويؤمر، وتخبر» — الخطابُ والأمرُ في الدورين، والإخبارُ فاعلًا (س23551–23552).
* «إلّا أنّه يُخبر عنه» — المُخبَرُ عنه لا يحتاج (س23552).
* النطقُ فصلُ الإنسان (ج3 س371)، والفهمُ («تفهم»، الكتاب س4899)، والسجودُ «الذي يكون ممّا يعقل» (س4165) فاعلًا. -/
def shart : Masdar → Dawr → Option Bool
  | .khitab, _ => some true
  | .amr, _ => some true
  | .ikhbar, .faail => some true
  | .ikhbar, .mafool => some false
  | .nutq, .faail => some true
  | .fahm, .faail => some true
  | .sujud, .faail => some true
  | _, .mafool => none

/-! ## ٢. خواصُّ الجنس -/

/-- أصلُ الصفّ: نصٌّ يذكر الجنسَ في سطره، أو حصرُ التفكير س23، أو وراثةٌ من كلّيٍّ معلَنة. -/
inductive Asl | nass | hasr | isa (abb : String)
  deriving DecidableEq, Repr

structure Saff where
  jins : String
  aqil : Bool
  asl : Asl
  nass : String
  satr : Nat
  deriving DecidableEq, Repr

/-- الصفوف. «الكلب» مندرجٌ في «ذوات الأربع» بإعلان المالك (`KALB_ISA_DECLARED`)، و«الحجر» تحت حصر التفكير
(`HASR_DOMAIN_DECLARED`). -/
def sufuf : List Saff :=
  [⟨"الإنسان", true, .nass, "tafkir", 23⟩,
   ⟨"الثقلان", true, .nass, "sirafi", 4161⟩,
   ⟨"الملائكة", true, .nass, "sirafi", 4161⟩,
   ⟨"الحيوان", false, .nass, "tafkir", 23⟩,
   ⟨"ذوات الأربع", false, .nass, "sirafi", 1799⟩,
   ⟨"الحيات", false, .nass, "sirafi", 1798⟩,
   ⟨"البراغيث", false, .nass, "sirafi", 4156⟩,
   ⟨"الشمس", false, .nass, "sirafi", 4163⟩,
   ⟨"القمر", false, .nass, "sirafi", 4163⟩,
   ⟨"الكواكب", false, .nass, "sirafi", 4164⟩,
   ⟨"النمل", false, .nass, "kitab", 4893⟩,
   ⟨"جمالك", false, .nass, "sirafi", 23548⟩,
   ⟨"الحجر", false, .hasr, "tafkir", 23⟩,
   ⟨"الكلب", false, .isa "ذوات الأربع", "owner", 0⟩]

def saffOf (j : String) : Option Saff := sufuf.find? (fun r => r.jins == j)

/-- خاصّةُ العقل للجنس: من صفّه، والوراثةُ تقرأ صفَّ الكلّيّ؛ وما لا صفَّ له `none`. -/
def aqilOf (j : String) : Option Bool :=
  match saffOf j with
  | some ⟨_, _, .isa p, _, _⟩ => (saffOf p).map (·.aqil)
  | some r => some r.aqil
  | none => none

/-! ## ٣. الحكمُ: الشرطُ في الخواصّ -/

def hukm (j : String) (m : Masdar) (d : Dawr) : Hukm :=
  match shart m d, aqilOf j with
  | some true, some true => .haqiqa
  | some true, some false => .majaz
  | some false, some _ => .haqiqa
  | _, _ => .laHukm

/-- **الحقيقةُ ⟺ الشرطُ في الخواصّ** (والجنسُ معلوم). -/
theorem haqiqa_iff (j : String) (m : Masdar) (d : Dawr) :
    hukm j m d = .haqiqa ↔
      (shart m d = some true ∧ aqilOf j = some true) ∨
      (shart m d = some false ∧ aqilOf j ≠ none) := by
  unfold hukm
  cases hs : shart m d with
  | none => simp
  | some b =>
    cases b <;> cases ha : aqilOf j with
    | none => simp
    | some a => cases a <;> simp

/-- **المجازُ ⟺ المصدرُ يحتاج ما يعقل والجنسُ معلومٌ لا يعقل** — نصُّ المالك: «خواصُّه تجعل الحقيقةَ ممتنعة». -/
theorem majaz_iff (j : String) (m : Masdar) (d : Dawr) :
    hukm j m d = .majaz ↔ shart m d = some true ∧ aqilOf j = some false := by
  unfold hukm
  cases hs : shart m d with
  | none => simp
  | some b =>
    cases b <;> cases ha : aqilOf j with
    | none => simp
    | some a => cases a <;> simp

/-- **لا تخمين**: جنسٌ لا صفَّ له لا حقيقةَ ولا مجاز. -/
theorem ghiyab_la_hukm (j : String) (m : Masdar) (d : Dawr) (h : aqilOf j = none) :
    hukm j m d = .laHukm := by
  unfold hukm; rw [h]; cases shart m d with
  | none => rfl
  | some b => cases b <;> rfl

/-! ## ٤. المصدرُ ومشتقّاتُ الأسماء والأفعال -/

/-- نوعُ الكلمة من المصدر: المصدرُ، واسمُ الفاعل، واسمُ المفعول، والفعلُ للمعلوم، والفعلُ للمجهول. -/
inductive Naw | masdar | ismFaail | ismMafool | filMaloom | filMajhul
  deriving DecidableEq, Repr

def toSigha : Dawr → Sigha
  | .faail => .faail
  | .mafool => .mafool

/-- ربطُ الصيغة (ADR ٩٤): المصدرُ يسمّي الحدثَ والجنسُ يتّصل به بدوره، فلا مخالفةَ؛ والمشتقُّ وزنُه دورُه، والفعلُ
للمعلوم يُسند إلى فاعله وللمجهول إلى نائبه (`FIL_WAZN_DECLARED`). -/
def sighaLink : Naw → Dawr → Hukm
  | .masdar, _ => .haqiqa
  | .ismFaail, d => hukmSigha .faail (toSigha d)
  | .ismMafool, d => hukmSigha .mafool (toSigha d)
  | .filMaloom, d => hukmSigha .faail (toSigha d)
  | .filMajhul, d => hukmSigha .mafool (toSigha d)

/-- الحكمُ التامّ: الربطان معًا (`Qabil.jam`). -/
def hukmTam (j : String) (m : Masdar) (n : Naw) (d : Dawr) : Hukm :=
  jam (sighaLink n d) (hukm j m d)

/-- الدورُ الموافقُ للصيغة. -/
def muwafiq : Naw → Dawr → Bool
  | .masdar, _ => true
  | .ismFaail, .faail | .filMaloom, .faail => true
  | .ismMafool, .mafool | .filMajhul, .mafool => true
  | _, _ => false

/-- **الإنسانُ حقيقةٌ في كلّ صيغة**: مصدرًا ومشتقَّ اسمٍ ومشتقَّ فعل، في كلّ دورٍ له نصّ. -/
theorem insan_kull_sigha (m : Masdar) (n : Naw) (d : Dawr)
    (hm : muwafiq n d = true) (hs : shart m d ≠ none) :
    hukmTam "الإنسان" m n d = .haqiqa := by
  revert hm hs
  cases m <;> cases n <;> cases d <;> decide

/-- **الحجرُ والكلبُ والقمرُ: الحقيقةُ ممتنعة في كلّ صيغةٍ ودورٍ يحتاج ما يعقل، والحكمُ مجازٌ في الصيغة الموافقة.** -/
theorem imtina (m : Masdar) (n : Naw) (d : Dawr) (hs : shart m d = some true) :
    ∀ j ∈ ["الحجر", "الكلب", "القمر"],
      hukmTam j m n d ≠ .haqiqa ∧ (muwafiq n d = true → hukmTam j m n d = .majaz) := by
  revert hs
  cases m <;> cases n <;> cases d <;> decide

/-- الكلامُ والنطقُ والفهمُ على الثلاثة بأعيانها: «كلامُ الحجر»، «الكلبُ ناطق»، «القمرُ يفهم» مجاز؛ وعلى الإنسان حقيقة. -/
theorem shawahid :
    hukmTam "الحجر" .khitab .masdar .faail = .majaz ∧
    hukmTam "الكلب" .nutq .ismFaail .faail = .majaz ∧
    hukmTam "القمر" .fahm .filMaloom .faail = .majaz ∧
    hukmTam "الإنسان" .khitab .masdar .faail = .haqiqa ∧
    hukmTam "الإنسان" .nutq .ismFaail .faail = .haqiqa ∧
    hukmTam "الإنسان" .fahm .filMaloom .faail = .haqiqa := by decide

/-- «وما لا يعقل ليس له من ذلك إلّا أنّه يُخبر عنه»: «الحجرُ مُخبَرٌ عنه» حقيقة. -/
theorem yukhbar_anhu :
    hukmTam "الحجر" .ikhbar .ismMafool .mafool = .haqiqa ∧
    hukmTam "القمر" .ikhbar .filMajhul .mafool = .haqiqa := by decide

/-- **والصيغةُ ربطٌ ثانٍ** (ADR ٩٥): الخاصّةُ قائمةٌ في الإنسان، واسمُ الفاعل على الواقع عليه («ماءٍ دافق»، ADR ٩٤)
مجاز — فالخاصّةُ شرطٌ لا يكفي وحدَه. -/
theorem sigha_rabt_thani :
    hukm "الإنسان" .khitab .mafool = .haqiqa ∧ hukmTam "الإنسان" .khitab .ismFaail .mafool = .majaz := by decide

/-- والكلبُ يخاطَب مجازًا («يخاطِب ويخاطَب» لما يعقل). -/
theorem kalb_yukhatab : hukmTam "الكلب" .khitab .ismMafool .mafool = .majaz := by decide

/-! ## ٥. الحكمُ دالّةٌ في الثلاثة معًا — لا في المصدر وحدَه ولا في الجنس وحدَه -/

/-- **ليس الحكمُ صفةً للمصدر**: مصدرٌ واحدٌ ودورٌ واحد بجنسين حكمان. -/
theorem la_bil_masdar_wahdahu : hukm "الإنسان" .khitab .faail ≠ hukm "الحجر" .khitab .faail := by decide

/-- **ولا صفةً للجنس**: جنسٌ واحدٌ ومصدرٌ واحد بدورين حكمان («يخبر» / «يخبر عنه»). -/
theorem la_bil_jins_wahdahu : hukm "القمر" .ikhbar .faail ≠ hukm "القمر" .ikhbar .mafool := by decide

/-- ولا للمصدر والجنس دون الدور، ولا للجنس والدور دون المصدر. -/
theorem la_bila_masdar : hukm "القمر" .ikhbar .mafool ≠ hukm "القمر" .khitab .mafool := by decide

/-! ## ٦. الوراثةُ والحصر -/

/-- الكلبُ يرث خاصّةَ «ذوات الأربع» (السيرافيّ س1797–1799). -/
theorem kalb_yarith : aqilOf "الكلب" = aqilOf "ذوات الأربع" ∧ aqilOf "الكلب" = some false := by decide

/-- الحجرُ تحت حصر التفكير: «العقلُ غيرُ موجودٍ إلّا عند الإنسان». -/
theorem hajar_hasr : (saffOf "الحجر").map (·.asl) = some .hasr ∧ aqilOf "الحجر" = some false := by decide

/-- لا صفَّ حصرٍ يثبت العقل، ولا يُحصر الإنسانُ نفسُه. -/
theorem hasr_nafy : ∀ r ∈ sufuf, r.asl = .hasr → r.aqil = false ∧ r.jins ≠ "الإنسان" := by decide

/-- وكلُّ وراثةٍ تقرأ كلّيًّا موجودًا بنصٍّ، وتوافقه. -/
def isaOK (r : Saff) : Bool :=
  match r.asl with
  | .isa p => sufuf.any (fun q => q.jins == p && q.asl == .nass && q.aqil == r.aqil)
  | _ => true

theorem isa_mutabiq : sufuf.all isaOK = true := by decide

/-! ## ٧. اللفظُ شاهد: جمعُ ما يعقل (السيرافيّ س4161–4166) -/

/-- الجمعُ السالم: بالواو والنون لما يعقل، وبالألف والتاء لما لا يعقل. -/
inductive Jam | wawNun | alifTa
  deriving DecidableEq, Repr

/-- «ولو أجراها على معناها وحقِّها من اللفظ لقال ساجدات». -/
def haqqJam (aqil : Bool) : Jam := if aqil then .wawNun else .alifTa

/-- حكمُ الجمع: حقُّه حقيقة، وخلافُه تنزيلٌ بمنزلة ما يعقل («تشبيهًا»)، والجنسُ المجهولُ «لا حكم». -/
def hukmJam (j : String) (used : Jam) : Hukm :=
  match aqilOf j with
  | some a => if used = haqqJam a then .haqiqa else .majaz
  | none => .laHukm

/-- **«ساجدين» على الشمس والقمر والكواكب مجاز، و«ساجدات» حقُّها؛ وعلى الإنسان حقيقة.** -/
theorem sajidin :
    hukmJam "القمر" .wawNun = .majaz ∧ hukmJam "القمر" .alifTa = .haqiqa ∧
    hukmJam "الشمس" .wawNun = .majaz ∧ hukmJam "الكواكب" .wawNun = .majaz ∧
    hukmJam "الإنسان" .wawNun = .haqiqa := by decide

/-- **القرينتان تتّفقان**: لكلّ جنسٍ في المودَع، السجودُ فاعلًا وجمعُ ما يعقل يحكمان حكمًا واحدًا. -/
theorem qarinatan_tattafiqan : ∀ r ∈ sufuf,
    hukm r.jins .sujud .faail = hukmJam r.jins .wawNun := by decide

/-! ## المراسي -/

/-- (النصّ، السطر 1-based، النصّ بعينه). -/
def marasi : List (String × Nat × String) :=
  [("sirafi", 23550, "قال أبو سعيد: جعلت العرب لما يعقل في مواضع اختصاصا في اللفظ"),
   ("sirafi", 23551, "لما اختص به ما يعقل بأنه يخاطب ويخاطب، ويأمر"),
   ("sirafi", 23552, "ويؤمر، وتخبر وتخبر عنه. وما لا يعقل ليس له من ذلك إلا أنه يخبر عنه"),
   ("sirafi", 4161, "يعقل، وهم الثقلان والملائكة، وربما ذكر لما لا يعقل فعل يكون الأغلب فيه"),
   ("sirafi", 4162, "أن يكون لما يعقل، فيجعل لفظه كلفظ ما يعقل تشبيها"),
   ("sirafi", 4165, "وذلك لأنه وصفها بالسجود، الذي يكون مما يعقل، ولو أجراها"),
   ("sirafi", 4166, "على معناها وحقها من اللفظ لقال: \" ساجدات \""),
   ("sirafi", 4168, "بالخطاب الذي يكون لما يعقل"),
   ("sirafi", 1797, "والذي يمشي على بطنه ليس مما يعقل ولا الذي يمشي على"),
   ("kitab", 4893, "أنه بمنزلة ما يعقل ويسمع لما ذكرهم بالسجود وصار النمل بتلك المنزلة"),
   ("kitab", 4899, "فجاز هذا حيث صارت هذه الأشياء عندهم تؤمر وتطيع وتفهم"),
   ("j3", 371, "كدلالة الإنسان على الحيوان الناطق"),
   ("tafkir", 23, "فإن العقل غير موجود إلا عند الإنسان"),
   ("tafkir", 23, "وإنما هو تمييز غريزي ليس غير")]

end A116.Khawass
