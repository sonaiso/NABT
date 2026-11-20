import A116.Atf
import A116.SidqSirafi

/-!
# أدواتُ المعاني بوّاباتٌ بسببٍ وشرطٍ ومانع (ADR ٩٠، أمرُ المالك 2026-10-17)

نصُّ المالك: «أدواتُ المعاني بوّاباتُ المنطق، وتخضع لسببٍ وشرطٍ ومانع: and، or، nor، xor، if…then، مع ADR ٨٩».

## السند (الأسطرُ 1-based)

شرحُ ابن عقيل المختوم:
* س6458: «فالواو لمطلق الجمع». وس6471: «تدلّ الفاء على تأخّر المعطوف عن المعطوف عليه متّصلًا به».
* س6505–6510: «أو» للتخيير «خذ من مالي درهمًا أو دينارًا»، وللإباحة «جالس الحسن أو ابن سيرين»، و«الإباحةُ لا تمنع
  الجمع والتخييرُ يمنعه»، وللإبهام وللشكّ «جاء زيد أو عمرو».
* س6529–6533: «إنّما يُعطف بلكن بعد النفي… وبعد النهي»، و«يُعطف بلا بعد النداء… والأمر… وبعد الإثبات، ولا يُعطف بلا
  بعد النفي… ولا يُعطف بلكن في الإثبات».
* س6537–6541: «بل» في النفي والنهي «كلكن»، وفي الخبر المثبت والأمر «تفيد الإضراب عن الأوّل وتنقل الحكم إلى الثاني
  حتّى يصير الأوّلُ كأنّه مسكوتٌ عنه».

الشخصيّة ج3 المختومة:
* س541: «مفهومُ الشرط هو تعليقُ الحكم على الشيء بكلمة "إن"… فإنّه يدلّ على نفي الحكم عند عدم تحقّق الشرط».
* س543: «لا خلافَ في ثبوت المشروط عند ثبوت الشرط اللغويّ… ولا خلافَ في عدم المشروط عند عدم الشرط اللغويّ».
* س554: «لا يُعمل بمفهوم المخالفة إذا ورد نصٌّ من الكتاب أو السنّة يعطّله».

وشرحُ السيرافيّ (ADR ٨٩): لا صدقَ ولا كذبَ في غير الخبر.

## ما يُبنى

القيمُ ثلاث: صادقٌ وكاذبٌ و«لا حكم»، وهي حكمُ `SidqSirafi`. فالبوّاباتُ على منطقٍ ثلاثيّ القيم، و«لا حكم» فيه لا يصير
صدقًا ولا كذبًا إلّا بما يحسمه.

لكلّ أداة:
* **سبب**: الأداةُ ومعناها المنقول، وهو جدولُها.
* **شرط**: الخبرُ للصدق والكذب، والسياقُ الذي يجيزها (لكنْ بعد النفي، لا بعد الإثبات)، والرتبةُ للفاء وثمّ.
* **مانع**: ما يمنع عملها: الطلب، أو فقدُ شرط السياق، أو معنًى لم يتعيّن. وفي الشرط: نصٌّ يعطّل المفهوم.

وما لا يُبرهَن: أنّ هذه معاني العربيّة. ذلك مرويُّ الشرح وج3 بأسطرهما.
-/

namespace A116.Bawwabat

open A116.Atf

/-- القيمة: `some true` صادق، `some false` كاذب، `none` لا حكم. -/
abbrev Q := Option Bool

def ofHukm : SidqSirafi.Hukm → Q
  | .sadiq _ => some true
  | .kadhib _ => some false
  | .laHukm => none

/-- الجمع (and): الكاذبُ يغلب، والصادقان صادق، وما سوى ذلك لا حكم. -/
def wa : Q → Q → Q
  | some false, _ => some false
  | _, some false => some false
  | some true, some true => some true
  | _, _ => none

/-- أحدُهما (or): الصادقُ يغلب، والكاذبان كاذب. -/
def aw : Q → Q → Q
  | some true, _ => some true
  | _, some true => some true
  | some false, some false => some false
  | _, _ => none

/-- النفي. -/
def nafy : Q → Q := Option.map (!·)

/-- الخلافُ الحصريّ (xor): لا يُحسم إلّا بالطرفين. -/
def xor3 : Q → Q → Q
  | some x, some y => some (x != y)
  | _, _ => none

/-! ## السبب: الجدول -/

/-- الجداولُ امتدادٌ للبوليّة: على الصادق والكاذب هي and وor وnot وxor بعينها. -/
theorem imtidad (x y : Bool) :
    wa (some x) (some y) = some (x && y) ∧ aw (some x) (some y) = some (x || y) ∧
    nafy (some x) = some (!x) ∧ xor3 (some x) (some y) = some (x != y) := by
  cases x <;> cases y <;> decide

/-- الكاذبُ وحدَه يحسم الجمع ولو كان الآخرُ «لا حكم»، والصادقُ وحدَه لا يحسمه. -/
theorem wa_kadhib_yaghlib :
    wa (some false) none = some false ∧ wa none (some false) = some false ∧
    wa (some true) none = none := by decide

/-- الصادقُ وحدَه يحسم «أحدُهما»، والكاذبُ وحدَه لا يحسمه. -/
theorem aw_sadiq_yaghlib :
    aw (some true) none = some true ∧ aw none (some true) = some true ∧
    aw (some false) none = none := by decide

/-- nor: «لا هذا ولا ذاك» نفيُ «أحدِهما»، على القيم الثلاث (دي مورغان). -/
theorem nor (a c : Q) : wa (nafy a) (nafy c) = nafy (aw a c) := by
  cases a with
  | none => cases c with
    | none => rfl
    | some y => cases y <;> rfl
  | some x => cases x <;> cases c <;> (try rfl) <;> rename_i y <;> cases y <;> rfl

/-- xor لا يُحسم بطرفٍ واحد. -/
theorem xor_yahtaj_tarafayn (x : Bool) : xor3 (some x) none = none ∧ xor3 none (some x) = none := by
  cases x <;> decide

/-! ## الشرط والمانع -/

/-- سياقُ الأداة: ما قبلها. -/
inductive Siyaq | ithbat | nafy | amr | nahy | nida
  deriving DecidableEq, Repr

/-- شرطُ السياق (س6529–6533، س6537–6541). -/
def shartSiyaq : Harf → Siyaq → Bool
  | .lakin, s => s == .nafy || s == .nahy
  | .la, s => s == .ithbat || s == .amr || s == .nida
  | _, _ => true

/-- المانعُ المسمّى. -/
inductive Mani
  | laysaKhabar
  | shartSiyaqFaqid
  | maanaGhayrMutayyan
  deriving DecidableEq, Repr

/-- مخرجُ البوّابة: قيمةٌ أو مانعٌ باسمه. -/
inductive Natija
  | qima (v : Q)
  | mani (m : Mani)
  deriving DecidableEq, Repr

/-- البوّابة: الأداةُ وسياقُها، وهل الكلامُ خبر. -/
structure Bawwaba where
  harf : Harf
  siyaq : Siyaq
  khabar : Bool
  deriving DecidableEq, Repr

/-- العمل: الطرفان `a` و`c`، و`r` صدقُ الرتبة التي تشترطها الأداة. -/
def amal (b : Bawwaba) (a c r : Q) : Natija :=
  if !b.khabar then .mani .laysaKhabar
  else if !shartSiyaq b.harf b.siyaq then .mani .shartSiyaqFaqid
  else match b.harf with
    | .wa => .qima (wa a c)
    | .fa | .thumma | .hatta => .qima (wa (wa a c) r)
    | .aw => .qima (aw a c)
    | .am => .mani .maanaGhayrMutayyan
    | .la => .qima (wa a (nafy c))
    | .lakin => .qima (wa a c)
    | .bal => if b.siyaq == .ithbat then .qima c else .qima (wa a c)

/-- لا عملَ للبوّابة في غير الخبر (ADR ٨٩). -/
theorem talab_mani (h : Harf) (s : Siyaq) (a c r : Q) :
    amal ⟨h, s, false⟩ a c r = .mani .laysaKhabar := rfl

/-- الواو لا تقرأ الرتبة، والفاءُ تشترطها: يتّفقان إن صدقت الرتبة ويفترقان إن كذبت. -/
theorem fa_wa_bi_shart :
    amal ⟨.wa, .ithbat, true⟩ (some true) (some true) (some true) =
      amal ⟨.fa, .ithbat, true⟩ (some true) (some true) (some true) ∧
    amal ⟨.wa, .ithbat, true⟩ (some true) (some true) (some false) = .qima (some true) ∧
    amal ⟨.fa, .ithbat, true⟩ (some true) (some true) (some false) = .qima (some false) := by decide

/-- لكنْ والواو جدولٌ واحد، ويفترقان بالشرط وحدَه: لكنْ لا تُعطف في الإثبات (س6532). -/
theorem lakin_wa_bi_shart (a c r : Q) :
    amal ⟨.lakin, .nafy, true⟩ a c r = amal ⟨.wa, .nafy, true⟩ a c r ∧
    amal ⟨.lakin, .ithbat, true⟩ a c r = .mani .shartSiyaqFaqid ∧
    amal ⟨.wa, .ithbat, true⟩ a c r = .qima (wa a c) := by
  refine ⟨rfl, rfl, rfl⟩

/-- لا تُعطف «لا» بعد النفي (س6531–6532). -/
theorem la_bad_nafy_mani (a c r : Q) :
    amal ⟨.la, .nafy, true⟩ a c r = .mani .shartSiyaqFaqid := rfl

/-- «بل» في الخبر المثبت تنقل الحكم إلى الثاني، فالأوّلُ كالمسكوت عنه (س6540–6541). -/
theorem bal_idrab (a c r : Q) : amal ⟨.bal, .ithbat, true⟩ a c r = .qima c := rfl

/-- و«بل» بعد النفي كلكن (س6537). -/
theorem bal_ka_lakin (a c r : Q) :
    amal ⟨.bal, .nafy, true⟩ a c r = amal ⟨.lakin, .nafy, true⟩ a c r := rfl

/-- «أم» لا تُحسب بلا تعيين معناها: متّصلةٌ في الاستفهام أو منقطعةٌ للإضراب (ADR ٨٢). -/
theorem am_mani (s : Siyaq) (a c r : Q) :
    amal ⟨.am, s, true⟩ a c r = .mani .maanaGhayrMutayyan := by
  cases s <;> rfl

/-! ## «أو» في الطلب: إذنٌ لا صدق -/

/-- التخييرُ xor والإباحةُ or، على إذن الجمع (س6505–6507). -/
theorem takhyir_xor_ibaha_or (x y : Bool) :
    ((x, y) ∈ jawaz .takhyir ↔ (x != y) = true) ∧
    ((x, y) ∈ jawaz .ibaha ↔ (x || y) = true) := by
  cases x <;> cases y <;> decide

/-- ومثالاهما أمرٌ («خذ»، «جالس»)، فلا صدقَ ولا كذبَ فيهما. -/
theorem aw_talab_bila_sidq (a c r : Q) :
    amal ⟨.aw, .amr, false⟩ a c r = .mani .laysaKhabar := rfl

/-! ## الشرط: if…then -/

/-- حكمُ المشروط من الشرط: يثبت بثبوته، ويُعدم بعدمه إن عُمل بالمفهوم، وإلّا فلا حكم (ج3 س541–543، س554). -/
def mashrut (mafhum : Bool) : Q → Q
  | some true => some true
  | some false => if mafhum then some false else none
  | none => none

/-- صدقُ الجملة الشرطيّة: بالمفهوم تكافؤٌ، وبلا مفهومٍ استلزام. -/
def shartiyya (mafhum : Bool) (s j : Q) : Q :=
  if mafhum then (match s, j with
    | some x, some y => some (x == y)
    | _, _ => none)
  else aw (nafy s) j

/-- «لا خلافَ في ثبوت المشروط عند ثبوت الشرط»، عُمل بالمفهوم أو لم يُعمل. -/
theorem thubut (m : Bool) : mashrut m (some true) = some true := by cases m <;> rfl

/-- «ولا خلافَ في عدم المشروط عند عدم الشرط» بالمفهوم، والنصُّ المعطِّلُ يرفعه إلى «لا حكم». -/
theorem adam_bil_mafhum :
    mashrut true (some false) = some false ∧ mashrut false (some false) = none := by decide

/-- التكافؤُ والاستلزامُ يفترقان في ثلاث حالاتٍ بأعيانها، ويتّفقان في الستّ الباقية. -/
theorem iff_vs_imp :
    [none, some true, some false].all (fun s => [none, some true, some false].all (fun j =>
      (shartiyya true s j != shartiyya false s j) ==
        ((s == some false && j == some true) || (s == none && j == some true) ||
         (s == some false && j == none)))) = true := by decide

/-- وعلى الصادق والكاذب هما البوليّان بأعيانهما. -/
theorem shartiyya_bool (x y : Bool) :
    shartiyya true (some x) (some y) = some (x == y) ∧
    shartiyya false (some x) (some y) = some (!x || y) := by
  cases x <;> cases y <;> decide

/-! ## مع ADR ٨٩ -/

/-- «أتيتك أمس وحملتُ الجبل»: الطرفُ الأوّل لا حكمَ عليه، والثاني كاذبٌ بالمعلومات، فالجمعُ كاذب. -/
theorem murakkab_sirafi :
    amal ⟨.wa, .ithbat, true⟩
      (ofHukm (SidqSirafi.hukm SidqSirafi.musawwada .khabar (Istiqama.juz Istiqama.hasan) none none))
      (ofHukm (SidqSirafi.hukm SidqSirafi.musawwada .khabar [.fil .madi, .ism]
        (some ⟨"الإنسان", "حمل", "الجبل", true⟩) none))
      none = .qima (some false) := by decide

/-- وبلا صفوفٍ موقَّعة لا حكمَ على الجمع: الغيابُ لا يصير كذبًا بالبوّابة. -/
theorem murakkab_bila_sufuf :
    amal ⟨.wa, .ithbat, true⟩
      (ofHukm (SidqSirafi.hukm [] .khabar (Istiqama.juz Istiqama.hasan) none none))
      (ofHukm (SidqSirafi.hukm [] .khabar [.fil .madi, .ism]
        (some ⟨"الإنسان", "حمل", "الجبل", true⟩) none))
      none = .qima none := by decide

/-! ## المراسي -/

/-- (النصّ، السطر 1-based، النصّ بعينه). -/
def marasi : List (String × Nat × String) :=
  [("sharh", 6458, "فالواو لمطلق الجمع"),
   ("sharh", 6471, "تدل الفاء على تأخر المعطوف عن المعطوف عليه متصلا به"),
   ("sharh", 6505, "أي تستعمل أو للتخيير نحو خذ من مالي درهما أو دينارا وللإباحة نحو جالس"),
   ("sharh", 6507, "والتخيير يمنعه وللتقسيم نحو الكلمة اسم أو فعل أو حرف وللإبهام على السامع"),
   ("sharh", 6510, "زيد أو عمرو إذا كنت شاكا في إلجائي منهما وللإضراب كقوله"),
   ("sharh", 6529, "أي إنما يعطف بلكن بعد النفي نحو ما ضربت زيدا لكن عمرا وبعد النهي نحو"),
   ("sharh", 6530, "لا تضرب زيدا لكن عمرا ويعطف بلا بعد النداء نحو يا زيد لا عمرو والأمر نحو"),
   ("sharh", 6531, "اضرب زيدا لا عمرا وبعد الإثبات نحو جاء زيد لا عمرو ولا يعطف بلا بعد"),
   ("sharh", 6532, "النفي نحو ما جاء زيد لا عمرو ولا يعطف بلكن في الإثبات نحو جاء زيد لكن"),
   ("sharh", 6537, "يعطف ببل في النفي والنهي فتكون كلكن في أنها تقرر حكم ما قبلها وتثبت"),
   ("sharh", 6540, "ويعطف بها في الخبر المثبت والأمر فتفيد الإضراب عن الأول وتنقل الحكم"),
   ("sharh", 6541, "إلى الثاني حتى يصير الأول كأنه مسكوت عنه نحو قام زيد بل عمرو واضرب زيدا"),
   ("j3", 541, "مفهوم الشرط هو تعليق الحكم على الشيء بكلمة «إن» أو غيرها من الشروط اللغوية"),
   ("j3", 543, "إنه لا خلاف في ثبوت المشروط عند ثبوت الشرط اللغوي"),
   ("j3", 543, "ولا خلاف في عدم المشروط عند عدم الشرط اللغوي"),
   ("j3", 554, "وكذلك لا يعمل بمفهوم المخالفة إذا ورد نص من الكتاب أو السنة يعطله")]

end A116.Bawwabat
