/-
  Nizam/Qiyas.lean — عقدُ العدّ: ما يُعدّ حين يُحكم على المحرّك بمرجع، مبرهنًا قبل أيّ رقم.
  الوثيقة: `hawkama/معايير_القياس.md` §١ (قولُ المالك 2026-10-22، 16:10: «حلل المعايير قبل اعتمادها … حلل وفق المبرهنات ونعتمد
  وثيقة المعايير داخل خارطة الطريق وجزء من المستودع»). وهو من الحزمة P6 في `hawkama/خطة_الإطلاق_التجريبي.md` (§٤أ: «أربعة محاور لا تختلط»).

  ما يُبرهن هنا خواصُّ تعريفات العدّ، لا أرقامُ قياس:
  ١. الدقّةُ لا تُحسب بلا جوابٍ محسوم: «غير قابل للحساب» لا 100% (`diqqa_none_iff`، `kull_imtina_la_diqqa`).
  ٢. الامتناعُ لا يغيّر الدقّة (`imtina_la_yughayyir_diqqa`)، والخطأُ يكبّر مقامها (`tahwil_khata_imtina`) ولا يرفعها (`khata_la_yarfa`، بالضرب
     التبادليّ): فتحويلُ خطأٍ إلى امتناعٍ لا يُنقصها إن كان قبله محسوم؛ ولذلك لا تُنشر إلّا مع التغطية. وامتناعٌ عن كلّ بندٍ — وفيها بندٌ كافٍ — تغطيتُه صفر (`imtina_taghtiya_sifr`).
  ٣. قاعدةُ التسجيل بعتبة t = a/b، مضروبةً في b لتبقى أعدادًا صحيحة: صحيح b − a، خطأ −a، امتناع 0 (وخطأُ الإدخال يُعدّ وحده ولا
     يُسجَّل). الخطأُ دون الامتناع (a > 0) والامتناعُ دون الصحيح (a < b) (`khata_dun_imtina`، `imtina_dun_sahih`). ومجموعُ نقاط البنود هو
     `majmu` على عدّها (`majmuBunud_eq`)، وهو موجبٌ إن وفقط إن (المحسوم)·a < (الصحيح)·b (`jawab_afdal_bunud`؛ والعامّةُ على الأعداد
     الصحيحة `jawab_afdal_iff`). وقراءتُه «الدقّةُ فوق t» تصحّ حين b > 0 والمحسومُ غيرُ صفر — حسابٌ في الكسور لا مبرهنة هنا؛ وهو حكمٌ على
     المجموع، لا قاعدةُ قرارٍ لكلّ بند.
  وما لا يُبرهن هنا ولم يُبنَ بعد: McNemar وκ (لا سكربت لهما في المستودع)؛ وفترةُ ولسن في `tahaqquq/qiyas_d.py` ويفحصها
  `tahaqquq/test_qiyas_d.py`.
  بلا sorry ولا axiom ولا native_decide.
-/

namespace Nizam.Qiyas

/-- نتيجةُ بندٍ واحد مقابل المرجع: جوابٌ يوافقه، أو يخالفه، أو امتناعٌ («لا حكم»)، أو خطأُ إدخالٍ أو تحميل (يُعدّ وحده). -/
inductive Natija | sahih | khata | imtina | khataIdkhal
deriving DecidableEq, Repr

/-- البند: نتيجتُه، وهل يكفي دليلُه للحسم بحكم المرجع (`kafin`). -/
structure Band where
  natija : Natija
  kafin  : Bool
deriving DecidableEq, Repr

/-- عددُ البنود بنتيجةٍ بعينها. -/
def adad (n : Natija) (xs : List Band) : Nat := (xs.filter (·.natija == n)).length

/-- المحسوم: الصحيح والخطأ (لا الامتناع ولا خطأ الإدخال). -/
def mahsum (b : Band) : Bool := b.natija == .sahih || b.natija == .khata

/-- الدقّة: (الصحيح، المحسوم)؛ ولا دقّة بلا محسوم. -/
def diqqa (xs : List Band) : Option (Nat × Nat) :=
  if adad .sahih xs + adad .khata xs = 0 then none else some (adad .sahih xs, adad .sahih xs + adad .khata xs)

/-- التغطية: من البنود الكافية دليلًا، (المحسوم منها، عددُها)؛ ولا تغطية بلا بندٍ كافٍ. -/
def taghtiya (xs : List Band) : Option (Nat × Nat) :=
  let k := xs.filter (·.kafin)
  if k.length = 0 then none else some ((k.filter mahsum).length, k.length)

/-! ## ١. لا دقّة بلا محسوم -/

/-- **الدقّةُ غيرُ قابلةٍ للحساب** إن وفقط إن لم يُحسم بند. -/
theorem diqqa_none_iff (xs : List Band) : diqqa xs = none ↔ adad .sahih xs + adad .khata xs = 0 := by
  unfold diqqa
  by_cases h : adad .sahih xs + adad .khata xs = 0
  · simp only [h, ite_true]
  · simp only [h, ite_false, reduceCtorEq]

theorem adad_imtina_sahih (ys : List Band) (hy : ∀ b ∈ ys, b.natija = .imtina) : adad .sahih ys = 0 := by
  unfold adad
  rw [List.length_eq_zero_iff, List.filter_eq_nil_iff]
  intro b hb; rw [hy b hb]; decide

theorem adad_imtina_khata (ys : List Band) (hy : ∀ b ∈ ys, b.natija = .imtina) : adad .khata ys = 0 := by
  unfold adad
  rw [List.length_eq_zero_iff, List.filter_eq_nil_iff]
  intro b hb; rw [hy b hb]; decide

/-- **محرّكٌ يمتنع عن كلّ بندٍ لا دقّة له** — «غير قابل للحساب»، لا 100%. -/
theorem kull_imtina_la_diqqa (xs : List Band) (h : ∀ b ∈ xs, b.natija = .imtina) : diqqa xs = none := by
  rw [diqqa_none_iff, adad_imtina_sahih xs h, adad_imtina_khata xs h]

/-! ## ٢. الامتناع لا يغيّر الدقّة، ويُسقط التغطية -/

theorem adad_append (n : Natija) (xs ys : List Band) : adad n (xs ++ ys) = adad n xs + adad n ys := by
  unfold adad; rw [List.filter_append, List.length_append]

/-- **الامتناعُ لا يغيّر الدقّة**: إلحاقُ أيّ عددٍ من الامتناعات بأيّ بنود يُبقي دقّتها. فالدقّةُ وحدها لا تميّز محرّكًا يسكت عمّا يصعب،
    ولا تُنشر إلّا مع التغطية. -/
theorem imtina_la_yughayyir_diqqa (xs ys : List Band) (hy : ∀ b ∈ ys, b.natija = .imtina) :
    diqqa (xs ++ ys) = diqqa xs := by
  unfold diqqa
  simp only [adad_append, adad_imtina_sahih ys hy, adad_imtina_khata ys hy, Nat.add_zero]

/-- **الامتناعُ عن كلّ ما يكفي دليلُه تغطيتُه صفر** (إن وُجد بندٌ كافٍ). -/
theorem imtina_taghtiya_sifr (xs : List Band) (h : ∀ b ∈ xs, b.natija = .imtina)
    (hk : (xs.filter (·.kafin)).length ≠ 0) : taghtiya xs = some (0, (xs.filter (·.kafin)).length) := by
  unfold taghtiya
  simp only [hk, ite_false]
  congr
  rw [List.length_eq_zero_iff, List.filter_eq_nil_iff]
  intro b hb
  have hb' := (List.mem_filter.mp hb).1
  unfold mahsum; rw [h b hb']; decide

/-! ## ٣. قاعدةُ التسجيل بعتبةٍ t = a/b -/

/-- نقطةُ البند بعتبة a/b مضروبةً في b: صحيح b − a، خطأ −a، امتناع 0؛ وخطأُ الإدخال لا يُسجَّل هنا (يُعدّ وحده). -/
def nuqta (a b : Int) : Natija → Int
  | .sahih => b - a
  | .khata => -a
  | .imtina => 0
  | .khataIdkhal => 0

/-- **الخطأُ دون الامتناع** لكلّ عتبةٍ موجبة. -/
theorem khata_dun_imtina (a b : Int) (ha : 0 < a) : nuqta a b .khata < nuqta a b .imtina := by
  simp only [nuqta]; omega

/-- **والامتناعُ دون الصحيح** لكلّ عتبةٍ دون الواحد. -/
theorem imtina_dun_sahih (a b : Int) (hab : a < b) : nuqta a b .imtina < nuqta a b .sahih := by
  simp only [nuqta]; omega

/-- مجموعُ c صحيحًا من d جوابًا محسومًا. -/
def majmu (a b c d : Int) : Int := c * (b - a) + (d - c) * (-a)

theorem majmu_eq (a b c d : Int) : majmu a b c d = c * b - d * a := by
  unfold majmu
  simp only [Int.mul_sub, Int.sub_mul, Int.mul_neg]
  omega

/-- **المجموعُ موجبٌ إن وفقط إن c·b > d·a** على الأعداد الصحيحة، بلا فروض. وقراءتُه «الدقّةُ c/d فوق العتبة a/b» تصحّ حين b > 0 وd > 0
    (حسابٌ في الكسور لا مبرهنة هنا)، وهي على المجموع لا قاعدةُ قرارٍ لكلّ بند؛ وعلى البنود: `jawab_afdal_bunud`. -/
theorem jawab_afdal_iff (a b c d : Int) : 0 < majmu a b c d ↔ d * a < c * b := by
  rw [majmu_eq]; omega

/-- مجموعُ نقاط البنود بنتائجها. -/
def majmuBunud (a b : Int) (xs : List Band) : Int := (xs.map fun x => nuqta a b x.natija).sum

/-- **مجموعُ نقاط البنود هو `majmu` على عدّها**: c الصحيح، وd المحسوم (عددان طبيعيّان)؛ والامتناعُ وخطأُ الإدخال لا يُسجَّلان. -/
theorem majmuBunud_eq (a b : Int) (xs : List Band) :
    majmuBunud a b xs = majmu a b (adad .sahih xs) (adad .sahih xs + adad .khata xs) := by
  rw [majmu_eq]
  induction xs with
  | nil => simp [majmuBunud, adad]
  | cons x xs ih =>
    simp only [majmuBunud, List.map_cons, List.sum_cons] at ih ⊢
    rw [ih]
    obtain ⟨n, k⟩ := x
    cases n <;> simp [adad, nuqta, Int.add_mul, Int.natCast_add] <;> omega

/-- **على البنود**: المجموعُ موجبٌ إن وفقط إن (المحسوم)·a < (الصحيح)·b — وهو «الدقّةُ فوق t» قراءةً حين b > 0 والمحسومُ غيرُ صفر
    (حسابٌ في الكسور لا مبرهنة هنا). -/
theorem jawab_afdal_bunud (a b : Int) (xs : List Band) :
    0 < majmuBunud a b xs ↔ ((adad .sahih xs + adad .khata xs : Nat) : Int) * a < (adad .sahih xs : Int) * b := by
  rw [majmuBunud_eq, jawab_afdal_iff, Int.natCast_add]

/-- **الخطأُ يكبّر المقام والامتناعُ لا**: بندٌ يُلحق خطأً يزيد المحسومَ واحدًا والصحيحُ كما هو، ويُلحق امتناعًا فتبقى الدقّة.
    والمقارنةُ بين الدقّتين في `khata_la_yarfa`. -/
theorem tahwil_khata_imtina (xs : List Band) (k : Bool) :
    diqqa (xs ++ [⟨.khata, k⟩]) = some (adad .sahih xs, adad .sahih xs + adad .khata xs + 1) ∧
    diqqa (xs ++ [⟨.imtina, k⟩]) = diqqa xs := by
  refine ⟨?_, imtina_la_yughayyir_diqqa xs _ (by simp)⟩
  unfold diqqa
  simp [adad]
  omega

/-- **إلحاقُ خطأٍ لا يرفع الدقّة**: إن كانت الدقّة (s، h) فالمحسومُ موجب (0 < h)، وصارت بالخطأ (s، h + 1)، و s·h ≤ s·(h + 1).
    وقراءتُها s/(h+1) ≤ s/h حسابٌ في الكسور. فتحويلُ خطأٍ إلى امتناعٍ لا يُنقصها إن كان قبله محسوم؛ وإن لم يكن فالدقّةُ بالامتناع «غير قابل للحساب». -/
theorem khata_la_yarfa (xs : List Band) (k : Bool) (s h : Nat) (hd : diqqa xs = some (s, h)) :
    0 < h ∧ diqqa (xs ++ [⟨.khata, k⟩]) = some (s, h + 1) ∧ s * h ≤ s * (h + 1) := by
  have ht := (tahwil_khata_imtina xs k).1
  unfold diqqa at hd
  split at hd
  · exact absurd hd (by simp)
  · rename_i hne
    simp only [Option.some.injEq, Prod.mk.injEq] at hd
    obtain ⟨rfl, rfl⟩ := hd
    exact ⟨Nat.pos_of_ne_zero hne, ht, Nat.mul_le_mul_left _ (Nat.le_succ _)⟩

/-! ## ٤. على الشاهد -/

/-- **على الشاهد**: ثلاثةُ بنودٍ كافية — صحيحٌ وامتناعان: الدقّةُ 1 من 1، والتغطيةُ 1 من 3؛ ومحرّكٌ يمتنع عنها كلِّها لا دقّة له وتغطيتُه 0 من 3. -/
theorem shahid_diqqa_taghtiya :
    diqqa [⟨.sahih, true⟩, ⟨.imtina, true⟩, ⟨.imtina, true⟩] = some (1, 1) ∧
    taghtiya [⟨.sahih, true⟩, ⟨.imtina, true⟩, ⟨.imtina, true⟩] = some (1, 3) ∧
    diqqa [⟨.imtina, true⟩, ⟨.imtina, true⟩, ⟨.imtina, true⟩] = none ∧
    taghtiya [⟨.imtina, true⟩, ⟨.imtina, true⟩, ⟨.imtina, true⟩] = some (0, 3) := by
  decide

end Nizam.Qiyas
