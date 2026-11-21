import A116.Khawass

/-!
# اقترانُ الدالّ بالمدلول: الوضعُ علاقةٌ، والقيودُ تقطعها، والمنطوقُ ثلاثيّ، والمفهومُ بشاهد واقع (ADR ٩٨)

أمرُ المالك (2026-10-17): «المتاح من 116 يمكّن من تغطية المنطوق، والمعجمُ والوضعُ يغطّيان المفهوم؛ حلّل الثنائيّ وجسورَ
الدالّ وحده لربطه بالمدلول وحده، واعمل اقترانَ الدالّ بالمدلول للوصول إلى المنطوق مع جسرٍ إلى المفهوم… أوجد حلولًا
إبداعيّة».

## السند (الأسطرُ 1-based)

* ج1 س16: «وتتكون هذه المفاهيم من ربط الواقع بالمعلومات»، و«فتوجَد بذلك للشخص عقلية تفهم الألفاظ والجمل، وتدرك
  المعاني بواقعها المشخَّص».
* ج1 س15: المعنى مفهومٌ «إذا كان لهذا المعنى الذي تضمنه اللفظ واقع يقع عليه الحس أو يتصوره الذهن كشيء محسوس ويصدقه»،
  وغيرُه «أن يفهم معاني الجمل كما تدل عليه من حيث هي».
* ج3 س393: «يحتاج إلى قرينة مبينة تعيِّن المعنى المراد».

## ما يُبنى

١. **الثنائيّ** (`ramz`): 116 خانةً و12 علامةَ قانونٍ تملأ سبعَ بتّات بلا ضياع (‎116 + 12 = 2⁷‎)؛ فالسيلُ الثنائيُّ يحمل
   النصَّ وقانونَه معًا (الحدّ، والابتداء، والوصل، والوقف، وأوجه الإصلاح الثلاثة) ويُردّ بعينه.
٢. **الاقتران** (`iqtiran`): مرشَّحو الوضع لكلّ دالّ (علاقة، `Wad`) تقطعهم قيودٌ من كلّ طبقة — الحركاتُ من الدالّ نفسه،
   والصيغة، وخواصُّ الجنس، والقرينة — والنتيجةُ سليمةٌ تامّة، لا يغيّرها ترتيبُ القيود، ولا يزيدها قيدٌ.
٣. **المنطوق ثلاثيّ** (`mantuq`): معيَّنٌ إن بقي واحد، ومحتمَلٌ بقائمته إن بقي أكثر، و«لا حكم» إن لم يبقَ شيء —
   فالتغطيةُ تامّةٌ حكمًا (لكلّ مدخلٍ حكمٌ من ثلاثة) لا إصابةً.
٤. **المرتبة** (`martaba`): «مفهوم» لا يكون إلّا لمعيَّنٍ له شاهدُ واقع؛ والمعجمُ لا يصنعه — يصنع «معلومة».
-/

namespace A116.Iqtiran

/-! ## ١. الثنائيّ: سبعُ بتّات للخانة وعلامة القانون -/

/-- علاماتُ القانون في السيل: الحدّ، والابتداء، والوصل، والوقف، وأوجهُ الإصلاح الثلاثة (`Iltiqa`)، وخمسٌ فارغة. -/
inductive Alama | hadd | ibtida | wasl | waqf | farq | madd | kasr | f1 | f2 | f3 | f4 | f5
  deriving DecidableEq, Repr

def Alama.all : List Alama := [.hadd, .ibtida, .wasl, .waqf, .farq, .madd, .kasr, .f1, .f2, .f3, .f4, .f5]

def Alama.idx : Alama → Nat
  | .hadd => 0 | .ibtida => 1 | .wasl => 2 | .waqf => 3 | .farq => 4 | .madd => 5 | .kasr => 6
  | .f1 => 7 | .f2 => 8 | .f3 => 9 | .f4 => 10 | .f5 => 11

/-- رمزُ السيل: خانةٌ (أقلّ من 116) أو علامة. -/
inductive Ramz | khana (i : Fin 116) | alama (a : Alama)
  deriving DecidableEq, Repr

def ramz : Ramz → Fin 128
  | .khana i => ⟨i.val, by omega⟩
  | .alama a => ⟨116 + a.idx, by cases a <;> simp [Alama.idx]⟩

def fakk (b : Fin 128) : Option Ramz :=
  if h : b.val < 116 then some (.khana ⟨b.val, h⟩)
  else (Alama.all.find? (fun a => 116 + a.idx == b.val)).map .alama

/-- **سبعُ بتّاتٍ تامّة**: 116 خانةً و12 علامة هي ‎2⁷‎ بعينها، فلا رمزَ ضائع. -/
theorem saa_tamma : 116 + Alama.all.length = 2 ^ 7 := by decide

/-- **الردّ بعينه**: كلُّ رمزٍ يُفكّ إلى نفسه، فالسيلُ يحمل النصّ وقانونه بلا ضياع. -/
theorem fakk_ramz (r : Ramz) : fakk (ramz r) = some r := by
  cases r with
  | khana i => simp [fakk, ramz, i.isLt]
  | alama a => cases a <;> decide

/-- والترميزُ متباين. -/
theorem ramz_inj (r s : Ramz) (h : ramz r = ramz s) : r = s := by
  have := fakk_ramz r; rw [h, fakk_ramz s] at this; exact (Option.some.inj this).symm

/-! ## ٢. الاقتران: مرشَّحو الوضع وقيودُ الطبقات -/

/-- قيدٌ من طبقة: اسمُه وما يقبله. -/
structure Qayd (M : Type) where
  ism : String
  yaqbal : M → Bool

/-- الاقتران: مرشَّحو الوضع الذين تقبلهم القيودُ كلُّها. -/
def iqtiran {M : Type} (marashshahun : List M) (quyud : List (Qayd M)) : List M :=
  marashshahun.filter (fun m => quyud.all (fun q => q.yaqbal m))

/-- **سليمٌ تامّ**: الباقي ⟺ مرشَّحٌ من الوضع تقبله القيودُ كلُّها — فلا معنى من خارج الوضع، ولا يُسقط قيدٌ ما يقبله. -/
theorem iqtiran_iff {M : Type} (c : List M) (q : List (Qayd M)) (m : M) :
    m ∈ iqtiran c q ↔ m ∈ c ∧ ∀ r ∈ q, r.yaqbal m = true := by
  simp [iqtiran, List.all_eq_true]

/-- **ترتيبُ القيود لا يغيّر**: أيُّ الطبقتين حكمت أوّلًا فالباقي واحد. -/
theorem tartib_la_yughayyir {M : Type} (c : List M) (q₁ q₂ : List (Qayd M)) :
    iqtiran c (q₁ ++ q₂) = iqtiran c (q₂ ++ q₁) := by
  unfold iqtiran; congr 1; funext m; simp [List.all_append, Bool.and_comm]

/-- **القيدُ لا يزيد**: إضافةُ قيدٍ تُبقي بعضَ ما كان. -/
theorem qayd_la_yazid {M : Type} (c : List M) (q : List (Qayd M)) (r : Qayd M) (m : M)
    (h : m ∈ iqtiran c (q ++ [r])) : m ∈ iqtiran c q := by
  rw [iqtiran_iff] at *; exact ⟨h.1, fun x hx => h.2 x (List.mem_append_left _ hx)⟩

/-- **والاقترانُ طبقةً بعد طبقة هو الاقترانُ بالقيود مجموعة**. -/
theorem tabaqat {M : Type} (c : List M) (q₁ q₂ : List (Qayd M)) :
    iqtiran (iqtiran c q₁) q₂ = iqtiran c (q₁ ++ q₂) := by
  simp [iqtiran, List.filter_filter, List.all_append, Bool.and_comm]

/-! ## ٣. المنطوقُ ثلاثيّ -/

inductive Mantuq (M : Type) | muayyan (m : M) | muhtamal (ms : List M) | laHukm
  deriving DecidableEq, Repr

def mantuq {M : Type} : List M → Mantuq M
  | [] => .laHukm
  | [m] => .muayyan m
  | ms => .muhtamal ms

/-- **التغطيةُ حكمًا**: لكلّ مدخلٍ واحدٌ من ثلاثة — المعيَّن بالبقاء وحدَه، و«لا حكم» بالخلوّ. -/
theorem kull_lahu_hukm {M : Type} (l : List M) :
    (∃ m, mantuq l = .muayyan m ∧ l = [m]) ∨ (mantuq l = .laHukm ∧ l = []) ∨
    (mantuq l = .muhtamal l ∧ 2 ≤ l.length) := by
  match l with
  | [] => exact .inr (.inl ⟨rfl, rfl⟩)
  | [m] => exact .inl ⟨m, rfl, rfl⟩
  | a :: b :: t => exact .inr (.inr ⟨rfl, by simp⟩)

/-- **لا تخمين**: ما لم يبقَ له مرشَّحٌ «لا حكم»، وما بقي له أكثرُ من واحدٍ لا يُعيَّن. -/
theorem la_takhmin {M : Type} (l : List M) (m : M) (h : mantuq l = .muayyan m) : l = [m] := by
  match l, h with
  | [x], h => cases h; rfl

/-! ## ٤. المرتبة: المعلومةُ من الوضع، والمفهومُ بشاهد واقع -/

inductive Martaba | minHaythuHiya | maluma | mafhum
  deriving DecidableEq, Repr

/-- المرتبة: «مفهوم» لمعيَّنٍ له شاهدُ واقع، و«معلومة» لمعيَّنٍ بلا شاهد أو لمحتمَل، و«من حيث هي» لما لا حكم له. -/
def martaba {M : Type} (shahid : M → Bool) : Mantuq M → Martaba
  | .muayyan m => if shahid m then .mafhum else .maluma
  | .muhtamal _ => .maluma
  | .laHukm => .minHaythuHiya

/-- **لا مفهومَ بلا شاهدِ واقع** — ج1 س15: «واقعٌ يقع عليه الحسّ… ويصدّقه». -/
theorem la_mafhum_bila_waqi {M : Type} (s : M → Bool) (x : Mantuq M) (h : martaba s x = .mafhum) :
    ∃ m, x = .muayyan m ∧ s m = true := by
  cases x with
  | muayyan m => exact ⟨m, rfl, by cases hs : s m <;> simp_all [martaba]⟩
  | muhtamal _ => simp [martaba] at h
  | laHukm => simp [martaba] at h

/-- **المعجمُ لا يصنع مفهومًا**: بلا شاهدٍ أيُّ مرشَّحين وأيُّ قيودٍ فالمرتبةُ دون المفهوم. -/
theorem mujam_la_yasna (c : List String) (q : List (Qayd String)) :
    martaba (fun _ => false) (mantuq (iqtiran c q)) ≠ .mafhum := by
  intro h; obtain ⟨_, _, hm⟩ := la_mafhum_bila_waqi _ _ h; simp at hm

/-! ## ٥. الشواهد: قيدُ الحركات، وقيدُ الخاصّة، وقيدُ القرينة -/

/-- معنًى مرشَّح: مفتاحُه بالحركات (خانات الدالّ)، وشرحُه، وجنسُ المسند إليه، وحقيقتُه أو مجازُه. -/
structure Mana where
  miftah : String
  sharh : String
  deriving DecidableEq, Repr

/-- **قيدُ الحركات من الدالّ نفسه**: لا يبقى إلّا معنًى مفتاحُه خاناتُ الكلمة بحركاتها. -/
def qaydHarakat (khanat : String) : Qayd Mana := ⟨"الحركات", fun m => m.miftah == khanat⟩

/-- «الحجر» بالرسم مرشَّحاها: الحَجَر والحِجْر (العقل). -/
def marashshahuHjr : List Mana := [⟨"حَجَر", "الصخر"⟩, ⟨"حِجْر", "العقل"⟩]

/-- **«الْحَجَرَ» تتعيّن بحركاتها**، و«الْحِجْرَ» بحركاتها، والرسمُ وحدَه محتمَل. -/
theorem harakat_tuayyin :
    mantuq (iqtiran marashshahuHjr [qaydHarakat "حَجَر"]) = .muayyan ⟨"حَجَر", "الصخر"⟩ ∧
    mantuq (iqtiran marashshahuHjr [qaydHarakat "حِجْر"]) = .muayyan ⟨"حِجْر", "العقل"⟩ ∧
    mantuq (iqtiran marashshahuHjr []) = .muhtamal marashshahuHjr := by decide

/-- قراءةُ الإسناد: حقيقةٌ أو مجاز. -/
inductive Qiraa | haqiqa | majaz
  deriving DecidableEq, Repr

/-- **قيدُ الخاصّة** (ADR ٩٦): الحقيقةُ لا تبقى إلّا إذا كان حكمُ الخواصّ حقيقةً، والمجازُ إلّا إذا كان مجازًا. -/
def qaydKhassa (jins : String) (m : Khawass.Masdar) (d : Qabil.Dawr) : Qayd Qiraa :=
  ⟨"الخاصّة", fun r => match r, Khawass.hukm jins m d with
    | .haqiqa, .haqiqa | .majaz, .majaz => true
    | _, _ => false⟩

/-- **«يتكلّمُ الإنسانُ» حقيقةٌ معيَّنة، و«يتكلّمُ القمرُ» مجازٌ معيَّن، و«يتكلّمُ الغولُ» لا حكم.** -/
theorem khassa_tuayyin :
    mantuq (iqtiran [Qiraa.haqiqa, .majaz] [qaydKhassa "الإنسان" .khitab .faail]) = .muayyan .haqiqa ∧
    mantuq (iqtiran [Qiraa.haqiqa, .majaz] [qaydKhassa "القمر" .khitab .faail]) = .muayyan .majaz ∧
    mantuq (iqtiran [Qiraa.haqiqa, .majaz] [qaydKhassa "الغول" .khitab .faail]) = .laHukm := by decide

/-- **قيدُ القرينة** (ج3 س393): المشتركُ «قال» بمعنيين يتعيّن بقرينةٍ في حقل أحدهما. -/
def marashshahuQala : List Mana := [⟨"قَالَ", "من القول"⟩, ⟨"قَالَ", "من القيلولة"⟩]

def qaydQarina (haql : String) : Qayd Mana := ⟨"القرينة", fun m => m.sharh == haql⟩

theorem qarina_tuayyin :
    mantuq (iqtiran marashshahuQala [qaydHarakat "قَالَ"]) = .muhtamal marashshahuQala ∧
    mantuq (iqtiran marashshahuQala [qaydHarakat "قَالَ", qaydQarina "من القيلولة"]) =
      .muayyan ⟨"قَالَ", "من القيلولة"⟩ := by decide

/-- **والمرتبةُ على الشاهد**: «الحَجَر» المعيَّن «مفهوم» إن كان له شاهدُ واقعٍ مودَع، وإلّا «معلومة». -/
theorem martaba_shahid :
    martaba (fun m => m.miftah == "حَجَر") (mantuq (iqtiran marashshahuHjr [qaydHarakat "حَجَر"])) = .mafhum ∧
    martaba (fun _ => false) (mantuq (iqtiran marashshahuHjr [qaydHarakat "حَجَر"])) = .maluma ∧
    martaba (fun _ => true) (mantuq (iqtiran marashshahuHjr [])) = .maluma := by decide

/-! ## المراسي -/

def marasi : List (String × Nat × String) :=
  [("j1", 16, "وتتكون هذه المفاهيم من ربط الواقع بالمعلومات"),
   ("j1", 16, "فتوجَد بذلك للشخص عقلية تفهم الألفاظ والجمل، وتدرك المعاني بواقعها المشخَّص"),
   ("j1", 15, "إذا كان لهذا المعنى الذي تضمنه اللفظ واقع يقع عليه الحس أو يتصوره الذهن كشيء محسوس ويصدقه"),
   ("j1", 15, "أن يفهم معاني الجمل كما تدل عليه من حيث هي"),
   ("j3", 393, "يحتاج إلى قرينة مبينة تعيِّن المعنى المراد")]

end A116.Iqtiran
