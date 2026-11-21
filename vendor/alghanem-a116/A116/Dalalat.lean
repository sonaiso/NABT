import A116.Malumat

/-!
# الدلالاتُ الثلاث والعلّةُ بالوصف المفهم (ADR ٩٣، أمرُ المالك 2026-10-17: «حلّل وقارن وأوجد حلًّا علميًّا»)

المرفقُ ربط المطابقةَ بالجامد، والتضمّنَ بـ«الخواصّ الفيزيائيّة الحتميّة» وبأوزان المطاوعة، والالتزامَ بالمشتقّ
والعلّة («وزنُ فاعل… يعقل النظامُ منه العلّيّة»). والحلُّ هنا من النصّين المختومين بأسطرهما (1-based):

الشخصيّة ج3:
* س371: المطابقةُ «دلالةُ اللفظ على تمام مسمّاه»، والتضمّنُ «على جزء المسمّى»، والالتزامُ «على لازمه… والمعتبرُ
  باللزوم هو اللزومُ الذهنيّ»، «ولا يأتي ذلك في اللازم الخارجيّ فقط»، و«اللزومُ شرطٌ وليس بموجب… بل السببُ هو
  إطلاقُ اللفظ».
* س375–376: الاسمُ «لا يلزم منه الزمانُ… لبنيته»، والكلّيُّ جنسٌ (ذاتٌ غيرُ معيّنة) ومشتقٌّ (ذو صفةٍ معيّنة).
* س874: شروطُ العلّة القياسيّة ثلاثة: «كونُها وصفًا لا جامدًا… وصفًا مفهمًا… دالًّا على وجه العلّيّة»، فالربا
  «ينحصر… بهذه الأشياء الستّة».
* س551: «للسائل حقّ» — وصفٌ غيرُ مفهم، «لأنّه لا ينتقل الذهنُ إليه عند سماع اللفظ، ولا يفيد العلّيّة».
* س871: «وهو غضبان» وصفٌ مفهمٌ ومفهمٌ وجهَ العلّيّة «لما فيه من تشويش الفكر».
* س223: «القتلُ العمد العدوان… مانعٌ للابن القاتل من ميراث أبيه، مع أنّ البنوّة تقتضي الميراث».
* س550: لا يُعمل بمفهوم الاسم، فالتنصيصُ على الستّة «لا يدلّ على إباحته في غير هذا الصنف».

الكتاب (JK006989):
* س16543–16548: «باب ما طاوع الذي فعله على فعل وهو يكون على انفعل وافتعل… كسرته فانكسر… وربما استغنى عن انفعل…
  طردته فذهب ولا يقولون فانطرد».

## ما يُبنى

* الدلالةُ سببُها الإطلاق وشرطُها اللزومُ الذهنيّ (`dalala`).
* **الوصفُ المفهمُ هو الالتزامُ بعينه**: العلّيّةُ لازمٌ ذهنيٌّ للوصف (س551 يقيس بمعيار س371).
* العلّةُ تحتاج الثلاثة؛ والوزنُ المشتقّ شرطٌ لا يكفي، والوزنُ لا يعيّن المطاوعة.
* التضمّنُ جزءُ المسمّى، فالخاصّةُ الخارجةُ عن الأجزاء ليست تضمّنًا، ورتبتُها في المودَع ظنّيّة (ADR ٨٧).

وما لا يُبرهَن: أنّ أجزاءَ كلّ مسمّى ولوازمَه كذلك. ذلك مُدخَلٌ من الشواهد (`MUSAMMA_IS_INPUT`).
-/

namespace A116.Dalalat

/-! ## ١. الدلالاتُ الثلاث (ج3 س371) -/

/-- المسمّى: أجزاؤه، ولوازمُه الذهنيّة، ولوازمُه الخارجيّة. -/
structure Musamma where
  ajza : List String
  dhihni : List String
  khariji : List String
  deriving DecidableEq, Repr

inductive Dalala | mutabaqa | tadammun | iltizam
  deriving DecidableEq, Repr

/-- الدلالة: السببُ الإطلاق، ثمّ التمام، ثمّ الجزء، ثمّ اللازمُ الذهنيّ وحدَه. -/
def dalala (itlaq : Bool) (m : Musamma) (madlul : List String) : Option Dalala :=
  if !itlaq then none
  else if madlul = m.ajza then some .mutabaqa
  else if madlul ≠ [] ∧ madlul.all (fun x => m.ajza.contains x) then some .tadammun
  else match madlul with
    | [x] => if m.dhihni.contains x then some .iltizam else none
    | _ => none

def insan : Musamma := ⟨["الحيوان", "الناطق"], [], []⟩
def asad : Musamma := ⟨["الأسد"], ["الشجاعة"], []⟩
def sarir : Musamma := ⟨["السرير"], ["الارتفاع"], ["الارتفاع"]⟩
def ama : Musamma := ⟨["العمى"], ["البصر"], []⟩

/-- الشواهد: الإنسانُ على الحيوان الناطق مطابقة، وعلى أحدهما تضمّن، والأسدُ على الشجاعة التزام، والسريرُ على
الارتفاع (لازمٌ في الذهن والخارج) والعمى على البصر (في الذهن وحدَه) التزام. -/
theorem shawahid_dalala :
    dalala true insan ["الحيوان", "الناطق"] = some .mutabaqa ∧
    dalala true insan ["الحيوان"] = some .tadammun ∧
    dalala true insan ["الناطق"] = some .tadammun ∧
    dalala true asad ["الشجاعة"] = some .iltizam ∧
    dalala true sarir ["الارتفاع"] = some .iltizam ∧
    dalala true ama ["البصر"] = some .iltizam := by decide

/-- **اللزومُ شرطٌ وليس بموجب**: بلا إطلاقٍ لا دلالة، وإن كان اللزوم. -/
theorem la_dalala_bila_itlaq (m : Musamma) (d : List String) : dalala false m d = none := by
  simp [dalala]

/-- **لا يأتي في اللازم الخارجيّ فقط**: ما يلزم في الخارج ولا ينتقل إليه الذهن لا دلالةَ عليه. -/
theorem khariji_faqat (m : Musamma) (x : String) (hj : [x] ≠ m.ajza) (ha : m.ajza.contains x = false)
    (hd : m.dhihni.contains x = false) : dalala true m [x] = none := by
  have ha' : x ∉ m.ajza := by simpa using ha
  have hd' : x ∉ m.dhihni := by simpa using hd
  simp [dalala, hj, ha', hd']

/-- **ما ليس جزءًا ليس تضمّنًا**: الخاصّةُ خارجَ أجزاء المسمّى لا تكون دلالةَ تضمّن. -/
theorem la_tadammun_kharij_ajza (m : Musamma) (x : String) (ha : m.ajza.contains x = false) :
    dalala true m [x] ≠ some .tadammun := by
  have ha' : x ∉ m.ajza := by simpa using ha
  by_cases h : [x] = m.ajza
  · rw [← h] at ha'; simp at ha'
  · by_cases hd : x ∈ m.dhihni <;> simp [dalala, h, ha', hd]

/-- والخاصّةُ في المودَع ظنّيّةٌ صائبةٌ حتى تُعارَض (ADR ٨٧)، لا «حتميّةٌ لا تتخلّف». -/
theorem khassa_zanni : Malumat.martaba .khassa = some .zanni := rfl

/-! ## ٢. الجنسُ والمشتقّ (س375–376) -/

inductive Kulli | jins | mushtaq
  deriving DecidableEq, Repr

/-- الاسمُ كلُّه «لا يلزم منه الزمانُ… لبنيته» (س375): الزمانُ لا يفصل الجنسَ من المشتقّ. -/
def zamanBiBinya : Kulli → Bool := fun _ => false

theorem zaman_la_yafsil : zamanBiBinya .jins = zamanBiBinya .mushtaq := rfl

/-! ## ٣. العلّة: وصفٌ، مفهمٌ، بوجه العلّيّة (س551، س833، س850، س871، س874) -/

/-- الوصفُ في نصّه: لفظُه، وقسمُه الكلّيّ، ومسمّاه في تركيبه، وهل فُهم وجهُ العلّيّة. -/
structure Wasf where
  lafz : String
  kulli : Kulli
  m : Musamma
  wajh : Bool
  deriving DecidableEq, Repr

/-- **المفهمُ هو الالتزام**: العلّيّةُ لازمٌ ذهنيٌّ للوصف في تركيبه (س551 بمعيار س371). -/
def mufhim (w : Wasf) : Bool := dalala true w.m ["العلية"] == some .iltizam

/-- العلّة: وصفٌ لا جامدٌ ومفهم (س833، س850). -/
def illa (w : Wasf) : Bool := w.kulli == .mushtaq && mufhim w

/-- القياس: الثلاثةُ معًا (س874). -/
def qiyas (w : Wasf) : Bool := illa w && w.wajh

theorem shuroot_thalatha (w : Wasf) :
    qiyas w = true ↔ w.kulli = .mushtaq ∧ mufhim w = true ∧ w.wajh = true := by
  cases hk : w.kulli <;> simp [qiyas, illa, hk]

/-- **الجامدُ لا يُعلَّل مطلقًا** (س874). -/
theorem jamid_la_yuallal (w : Wasf) (h : w.kulli = .jins) : illa w = false := by
  simp [illa, h]

def jamid (l : String) : Wasf := ⟨l, .jins, ⟨[l], [], []⟩, false⟩

/-- الأصنافُ الستّة (س874). -/
def sitta : List Wasf :=
  ["الذهب", "الفضة", "التمر", "البر", "الملح", "الشعير"].map jamid

theorem sitta_la_qiyas : ∀ w ∈ sitta, qiyas w = false := by decide

/-- السائل (س551): مشتقٌّ على فاعل، والعلّيّةُ ليست لازمًا ذهنيًّا له. -/
def sail : Wasf := ⟨"السائل", .mushtaq, ⟨["ذات", "السؤال"], [], []⟩, false⟩
/-- المحتجر (س551). -/
def muhtajir : Wasf := ⟨"محتجر", .mushtaq, ⟨["ذات", "الاحتجار"], [], []⟩, false⟩
/-- غضبان (س871): العلّيّةُ لازمٌ ذهنيٌّ ووجهُها تشويشُ الفكر. -/
def ghadban : Wasf := ⟨"غضبان", .mushtaq, ⟨["ذات", "الغضب"], ["العلية"], []⟩, true⟩
/-- بادٍ (س871): جهالةُ السعر. -/
def badi : Wasf := ⟨"باد", .mushtaq, ⟨["ذات", "البداوة"], ["العلية"], []⟩, true⟩

/-- **المشتقُّ شرطٌ لا يكفي**: السائلُ والمحتجرُ مشتقّان ولا علّة؛ والغضبانُ والبادي علّتان يُقاس عليهما. -/
theorem mushtaq_la_yakfi :
    sail.kulli = .mushtaq ∧ illa sail = false ∧ illa muhtajir = false ∧
    qiyas ghadban = true ∧ qiyas badi = true := by decide

/-- **القسمُ لا يعيّن العلّيّة**: لا دالّةَ من الجنس/المشتقّ وحدَه تطابق العلّةَ على الشواهد. -/
theorem kulli_la_yuayyin : ¬ ∃ f : Kulli → Bool, ∀ w ∈ [sail, ghadban], illa w = f w.kulli := by
  rintro ⟨f, hf⟩
  have h1 := hf sail (by simp)
  have h2 := hf ghadban (by simp)
  have e : sail.kulli = ghadban.kulli := rfl
  rw [e] at h1
  have : illa sail = illa ghadban := h1.trans h2.symm
  exact absurd this (by decide)

/-! ## ٤. المانع (س223) ومفهومُ الاسم (س550) -/

/-- الميراث: البنوّةُ سبب، والقتلُ العمدُ العدوانُ مانع. -/
def irth (bunuwwa amd udwan : Bool) : Bool := bunuwwa && !(amd && udwan)

/-- **القتلُ مانعٌ لا علّة، والوزنُ وحدَه لا يكفي**: القاتلُ عمدًا عدوانًا لا يرث، والقاتلُ خطأً يرث — واللفظُ «قاتل» فيهما. -/
theorem qatil_mani :
    irth true true true = false ∧ irth true false true = true ∧ irth true true false = true ∧
    irth false false false = false := by decide

def sittaNames : List String := ["الذهب", "الفضة", "التمر", "البر", "الملح", "الشعير"]

/-- حكمُ الربا من النصّ وحدَه: محرَّمٌ في المنصوص، و«لا حكم» في غيره — لا إباحةَ بمفهوم الاسم (س550). -/
def ribaNass (x : String) : Option Bool := if sittaNames.contains x then some true else none

/-- **الحصرُ بلا مفهوم**: غيرُ الستّة لا يُحرَّم بالنصّ ولا بالقياس، ولا يُباح بالمفهوم. -/
theorem ghayr_sitta (x : String) (h : sittaNames.contains x = false) :
    ribaNass x = none ∧ (∀ w ∈ sitta, qiyas w = false) := by
  have h' : x ∉ sittaNames := by simpa using h
  exact ⟨by simp [ribaNass, h'], sitta_la_qiyas⟩

theorem la_ibaha_bil_mafhum (x : String) : ribaNass x ≠ some false := by
  unfold ribaNass; split <;> simp

/-! ## ٥. المطاوعة (الكتاب س16543–16548): نقلٌ لا خاصّة -/

/-- الفعلُ ووزنُه ومطاوعُه المنقول (أو لا مطاوعَ مستعمل). -/
structure Mutawaa where
  fil : String
  wazn : String
  mutawi : Option String
  deriving DecidableEq, Repr

def mutawaat : List Mutawaa :=
  [⟨"كسر", "فعل", some "انكسر"⟩, ⟨"حطم", "فعل", some "انحطم"⟩,
   ⟨"صرف", "فعل", some "انصرف"⟩, ⟨"قطع", "فعل", some "انقطع"⟩,
   ⟨"طرد", "فعل", none⟩]

/-- **الوزنُ لا يعيّن المطاوعة**: «كسرته فانكسر» و«طردته فذهب ولا يقولون فانطرد» على وزنٍ واحد. -/
theorem wazn_la_yuayyin_mutawaa :
    ¬ ∃ f : String → Bool, ∀ r ∈ mutawaat, r.mutawi.isSome = f r.wazn := by
  rintro ⟨f, hf⟩
  have h1 := hf ⟨"كسر", "فعل", some "انكسر"⟩ (by simp [mutawaat])
  have h2 := hf ⟨"طرد", "فعل", none⟩ (by simp [mutawaat])
  simp at h1 h2
  rw [h1] at h2
  exact absurd h2 (by decide)

/-! ## المراسي -/

/-- (النصّ، السطر 1-based، النصّ بعينه). -/
def marasi : List (String × Nat × String) :=
  [("j3", 371, "أحدها دلالة المطابقة، وهي دلالة اللفظ على تمام مسماه"),
   ("j3", 371, "والمعتبر باللزوم هو اللزوم الذهني"),
   ("j3", 371, "وهذا اللزوم شرط وليس بموجب"),
   ("j3", 371, "كالعمى والبصر"),
   ("j3", 375, "ولا يلزم منه الزمان الخارج عن معناه لبنيته"),
   ("j3", 376, "وإن دل الكلي على ذي صفة معينة فهو المشتق"),
   ("j3", 223, "مثل القتل العمد العدوان، فإنه مانع للابن القاتل من ميراث أبيه"),
   ("j3", 550, "فإنه لا يدل على إباحته في غير هذا الصنف"),
   ("j3", 551, "«لِلسَّائِلِ"),
   ("j3", 551, "لأنه لا ينتقل الذهن إليه عند سماع اللفظ، ولا يفيد العلية"),
   ("j3", 833, "فلو كانت العلة وصفاً طردياً"),
   ("j3", 871, "لما فيه من تشويش الفكر واضطراب الحال"),
   ("j3", 874, "الأول: كونها وصفاً لا جامداً"),
   ("j3", 874, "فينحصر تحريم الربا بهذه الأشياء الستة"),
   ("kitab", 16543, "هذا باب ما طاوع الذي فعله على فعل وهو يكون على انفعل وافتعل"),
   ("kitab", 16544, "وذلك قولك كسرته فانكسر وحطمته فانحطم"),
   ("kitab", 16547, "وربما استغنى عن انفعل في هذا الباب فلم يستعمل"),
   ("kitab", 16548, "طردته فذهب ولا يقولون فانطرد")]

end A116.Dalalat
