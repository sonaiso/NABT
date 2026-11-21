import A116.Majaz

/-!
# الحقيقةُ بالقابليّة: المصدرُ على الصيغة وعلى جنسٍ يقبله (ADR ٩٥، أمرُ المالك 2026-10-17)

نصُّ المالك: «الحقيقةُ ربطُ المصدر المشتقّ بالصيغة أي الوزن، وربطُ المصدر بالأجناس التي لها خواصّ تجعل القابليّاتِ
حقيقة؛ وإن لم تكن هناك قابليّاتٌ على الحقيقة تُحمل على المجاز».

## السند (الأسطرُ 1-based)

الكتاب (JK006989):
* س2109–2110: «هذا باب استعمال الفعل في اللفظ لا في المعنى لاتساعهم في الكلام والإيجاز والاختصار».
* س2112: «صيد عليه يومان، وإنما المعنى صيد عليه الوحش» في اليومين.
* س2119–2122: «واسأل القرية… إنما يريد أهل القرية فاختصر»، و«بل مكر الليل والنهار… وإنما المعنى بل مكركم في الليل
  والنهار».
* س2328–2329: «ويخزل الذي يقع به الفعل اختصارًا واتساعًا، وقد علم أنّ الضرب لا يُضرب».

شرحُ السيرافيّ (Sham19Y0017726):
* س16594–16595: «وهو مجازٌ واتساع؛ لأنّ اليوم لا يصاد، وإنّما يصاد فيه».
* س16616–16618: «على أنّ بعض الناس يزعم أنّ ذلك على الحقيقة… لأنّ القرية يجوز أن تخاطبه إذ كان نبيًّا».
* س17212–17213: «والضربُ لا يُضرب… كما قال نهارك صائم والنهارُ لا يصوم».
* س21487–21488: «بل مكر الليل والنهار، وهما لا يمكران وإنّما يُمكر فيهما… والنهارُ لا يُبصر وإنّما يُبصر فيه».

الشخصيّة ج3:
* س398: «إسنادُ الإشابة والإفناء إلى كرّ الغداة ومرّ العشيّ إسنادٌ لغير من قام بهما، فهو مجاز».
* س400: «السببيّةُ القابليّة، وهي تسميةُ الشيء باسم قابله، مثل قولهم سال الوادي».

التفكير: س14: «الانعكاسُ يحتاج إلى وجود قابليّة الانعكاس في الشيء… كالمرآة… وهذا غيرُ موجودٍ لا في الدماغ».

## ما يُبنى

* **الحقيقةُ ربطان**: الصيغةُ على دورها (`Majaz.hukmSigha`، ADR ٩٤) والمصدرُ على جنسٍ له قابليّتُه في دوره.
* **انتفاءُ القابليّة المعلومُ قرينةُ المجاز** («وقد علم أنّ الضرب لا يُضرب»)، والمرادُ مقدَّرٌ فيه أو أهلُه؛ وثبوتُها
  حقيقة؛ وغيابُ الصفّ «لا حكم».
* **تقييدُ ADR ٩٢**: «الامتناعُ ليس قرينة» صحيحٌ على مستوى الثلاثيّ وحدَه: «حملتُ الجبل» قابليّةُ الجنس للحمل قائمة،
  والامتناعُ في المفعول، فهو حقيقةٌ كاذبة (سيبويه، السيرافيّ). أمّا انتفاءُ قابليّة الجنس للحدث نفسِه فقرينةُ مجاز.

وما لا يُبرهَن: أنّ هذه القابليّاتِ صادقةٌ في الواقع. هي صفوفٌ من أسطرٍ مختومة، ومرتبتُها ظنّيّة (ADR ٨٧).
-/

namespace A116.Qabil

open A116.Majaz (Hukm Sigha hukmSigha)

/-! ## ١. مودَعُ القابليّة -/

/-- الدورُ الذي يُسند إليه المصدر: فاعلٌ أو واقعٌ عليه الفعل. -/
inductive Dawr | faail | mafool
  deriving DecidableEq, Repr

/-- صفُّ قابليّة: الجنس، والمصدر، والدور، والإيجاب، والمقدَّرُ عند الانتفاء، والنصّ وسطرُه. -/
structure Saff where
  jins : String
  masdar : String
  dawr : Dawr
  ijab : Bool
  taqdir : Option String
  nass : String
  satr : Nat
  deriving DecidableEq, Repr

/-- الصفوفُ من الأسطر المختومة بأعيانها. -/
def sufuf : List Saff :=
  [⟨"اليوم", "صيد", .mafool, false, some "فيه", "sirafi", 16595⟩,
   ⟨"النهار", "صوم", .faail, false, some "فيه", "sirafi", 17213⟩,
   ⟨"الليل", "مكر", .faail, false, some "فيه", "sirafi", 21487⟩,
   ⟨"النهار", "إبصار", .faail, false, some "فيه", "sirafi", 21488⟩,
   ⟨"الضرب", "ضرب", .mafool, false, some "الذي يقع به", "kitab", 2329⟩,
   ⟨"القرية", "سؤال", .mafool, false, some "أهل", "kitab", 2120⟩,
   ⟨"كر الغداة", "إشابة", .faail, false, some "الله", "j3", 398⟩,
   ⟨"الوادي", "سيلان", .faail, false, some "الماء الذي فيه", "j3", 400⟩,
   ⟨"المرآة", "انعكاس", .faail, true, none, "tafkir", 14⟩,
   ⟨"الدماغ", "انعكاس", .faail, false, none, "tafkir", 14⟩]

def lookup (rows : List Saff) (j m : String) (d : Dawr) : Option Saff :=
  rows.find? (fun r => r.jins == j && r.masdar == m && r.dawr == d)

/-! ## ٢. الحكمُ بالقابليّة -/

/-- القابليّة: ثبوتُها حقيقة، وانتفاؤها المعلومُ مجازٌ بالاتّساع، وغيابُ الصفّ «لا حكم». -/
def hukmQ (rows : List Saff) (j m : String) (d : Dawr) : Hukm :=
  match lookup rows j m d with
  | some r => if r.ijab then .haqiqa else .majaz
  | none => .laHukm

/-- **المجازُ ⟺ انتفاءُ القابليّة في المودَع.** -/
theorem majaz_iff (rows : List Saff) (j m : String) (d : Dawr) :
    hukmQ rows j m d = .majaz ↔ ∃ r, lookup rows j m d = some r ∧ r.ijab = false := by
  unfold hukmQ
  cases h : lookup rows j m d with
  | none => simp
  | some r => cases hr : r.ijab <;> simp [hr]

/-- **الحقيقةُ ⟺ ثبوتُ القابليّة.** -/
theorem haqiqa_iff (rows : List Saff) (j m : String) (d : Dawr) :
    hukmQ rows j m d = .haqiqa ↔ ∃ r, lookup rows j m d = some r ∧ r.ijab = true := by
  unfold hukmQ
  cases h : lookup rows j m d with
  | none => simp
  | some r => cases hr : r.ijab <;> simp [hr]

/-- **لا تخمين**: ما لا صفَّ له لا حقيقةَ ولا مجاز. -/
theorem ghiyab_la_hukm (rows : List Saff) (j m : String) (d : Dawr) (h : lookup rows j m d = none) :
    hukmQ rows j m d = .laHukm := by simp [hukmQ, h]

/-- **القابليّةُ تحدّد**: صفّان لا يختلفان إلّا في الإيجاب يحكمان حقيقةً ومجازًا (والقريةُ تخاطب نبيًّا، س16616–16618). -/
theorem qabiliyya_tuhaddid (r : Saff) :
    hukmQ [{ r with ijab := true }] r.jins r.masdar r.dawr = .haqiqa ∧
    hukmQ [{ r with ijab := false }] r.jins r.masdar r.dawr = .majaz := by
  simp [hukmQ, lookup]

/-- كلُّ صفٍّ منفيٍّ له مقدَّر: المرادُ فيه أو أهلُه أو فاعلُه («يخزل الذي يقع به الفعل»). -/
theorem manfi_lahu_taqdir : ∀ r ∈ sufuf, r.ijab = false → r.taqdir.isSome ∨ r.nass = "tafkir" := by
  decide

/-- الشواهد: «صيد عليه يومان»، «نهارك صائم»، «بل مكر الليل»، «واسأل القرية»، «كرّ الغداة»، «سال الوادي» مجاز؛
والانعكاسُ في المرآة حقيقة، وفي الدماغ منفيّ. -/
theorem shawahid :
    hukmQ sufuf "اليوم" "صيد" .mafool = .majaz ∧ hukmQ sufuf "النهار" "صوم" .faail = .majaz ∧
    hukmQ sufuf "الليل" "مكر" .faail = .majaz ∧ hukmQ sufuf "القرية" "سؤال" .mafool = .majaz ∧
    hukmQ sufuf "كر الغداة" "إشابة" .faail = .majaz ∧ hukmQ sufuf "الوادي" "سيلان" .faail = .majaz ∧
    hukmQ sufuf "المرآة" "انعكاس" .faail = .haqiqa ∧ hukmQ sufuf "الدماغ" "انعكاس" .faail = .majaz := by
  decide

/-! ## ٣. الحقيقةُ ربطان: الصيغةُ والقابليّة -/

/-- الجمع: حقيقةٌ ⟺ الربطان حقيقة؛ و«لا حكم» إن غاب أحدُهما؛ وإلّا مجاز. -/
def jam (sigha qabil : Hukm) : Hukm :=
  match sigha, qabil with
  | .haqiqa, .haqiqa => .haqiqa
  | .laHukm, _ | _, .laHukm => .laHukm
  | _, _ => .majaz

/-- **الحقيقةُ ربطان معًا** — نصُّ المالك. -/
theorem haqiqa_rabtan (s q : Hukm) : jam s q = .haqiqa ↔ s = .haqiqa ∧ q = .haqiqa := by
  cases s <;> cases q <;> simp [jam]

/-- «نهارك صائم» (س17213): الصيغةُ حقيقة (فاعلٌ على فاعل)، والنهارُ لا يقبل الصوم، فالكلُّ مجاز؛ ومثلُه «ماءٍ دافق»
بالعكس: الجنسُ يقبل والصيغةُ على غير دورها. -/
theorem nahar_saim :
    jam (hukmSigha .faail .faail) (hukmQ sufuf "النهار" "صوم" .faail) = .majaz ∧
    jam (hukmSigha .faail .mafool) .haqiqa = .majaz := by decide

/-- والمشتقُّ تابعٌ للمصدر (ADR ٩٤): «صائم» على النهار حكمُه حكمُ «صوم» على النهار. -/
theorem mushtaq_tabi :
    Majaz.hukmKalima .mushtaq .laHukm (hukmQ sufuf "النهار" "صوم" .faail) .laHukm = .majaz := by decide

/-! ## ٤. الفرقُ بين المجاز والكذب -/

/-- صفُّ قابليّة الإنسان للحمل مُعلَنٌ (`PAIR_ROW_DECLARED`)، لا من سطرٍ مختوم. -/
def insanHaml : Saff := ⟨"الإنسان", "حمل", .faail, true, none, "declared", 0⟩

/-- **«حملتُ الجبل»**: الجنسُ يقبل الحملَ فلا مجاز، والامتناعُ في المفعول فالحكمُ كذبٌ بالمسوّدة (ADR ٨٩) —
و«نهارك صائم»: الجنسُ لا يقبل الصومَ فمجاز، ولا يُحكم عليه بكذب. -/
theorem majaz_ghayr_kadhib :
    hukmQ [insanHaml] "الإنسان" "حمل" .faail = .haqiqa ∧
    Bawwabat.ofHukm (SidqSirafi.hukm SidqSirafi.musawwada .khabar [.fil .madi, .ism]
      (some ⟨"الإنسان", "حمل", "الجبل", true⟩) none) = some false ∧
    hukmQ sufuf "النهار" "صوم" .faail = .majaz := by decide

/-! ## المراسي -/

/-- (النصّ، السطر 1-based، النصّ بعينه). -/
def marasi : List (String × Nat × String) :=
  [("kitab", 2109, "هذا باب استعمال الفعل فى اللفظ لا فى المعنى لاتساعهم فى الكلام"),
   ("kitab", 2112, "فتقول صيد عليه يومان | وإنما المعنى صيد عليه"),
   ("kitab", 2120, "إنما يريد أهل القرية فاختصر"),
   ("kitab", 2122, "وإنما المعنى بل مكركم فى الليل والنهار"),
   ("kitab", 2328, "ويخزل الذى يقع به الفعل اختصارا واتساعا | وقد علم أن"),
   ("kitab", 2329, "الضرب لا يضرب"),
   ("sirafi", 16595, "واتساع؛ لأن \" اليوم \" لا يصاد، وإنما يصاد فيه"),
   ("sirafi", 16616, "على أن بعض الناس يزعم أن ذلك على الحقيقة"),
   ("sirafi", 16617, "لأن القرية يجوز أن تخاطبه؛ إذ كان"),
   ("sirafi", 17213, "قال: \" نهارك صائم \" والنهار لا يصوم"),
   ("sirafi", 21487, "وهما لا يمكران وإنما يمكر فيهما"),
   ("sirafi", 21488, "والنهار لا يبصر وإنما يبصر فيه"),
   ("j3", 398, "إسناد لغير من قام بهما، فهو مجاز"),
   ("j3", 400, "السببية القابلية، وهي تسمية الشيء باسم قابله، مثل قولهم سال الوادي"),
   ("tafkir", 14, "لأن الانعكاس يحتاج إلى وجود قابلية الانعكاس في الشيء الذي يعكس الأشياء كالمرآة"),
   ("tafkir", 14, "وهذا غير موجود، لا في الدماغ")]

end A116.Qabil
