/-
  Aql/Waqi.lean — جدولُ «الواقع المختوم»: المشاهدةُ صفًّا، والحكمُ الثلاثيُّ عليها بشرط الختم، وقانونُ النموّ.

  **القرار.** قولُ المالك في الجلسة (2026-10-22، 01:57 بتوقيت عمّان): «… اعطيني وفق الدستور جدولا قابلة للنمو وفق المعلومات
  السابقة المنظمة الاولية يكون نواة للتوسع التلقائي بالتعلم … جدول الواقع المختوم من الأساس ما هو الوكيل وما هو جيت هب وما
  هوmashru وما مكوناته وما تعريفاته وما إطار عمله وكيف تتم عملياته وما هو بايثون وما هو الدستور وكل ما يؤسس لجدول الواقع المختوم
  القابل للتعلم والنمو لتغطية كل جوانب المعرفة». وصوغُ المشاهدة ووجهيها والحكمِ عليها وحدِّ الاستقلال تعيينُ البنّاء (يُعرض على المالك).

  **السند** (الدستور كما في `CLAUDE.md` ودستور الوكيل):
  * م12: لا مودَع بلا نوع، والأنواعُ أربعة: واقعٌ مختوم، وضع، معلوماتٌ سابقة، مرجعٌ محجوب (`Idaa.Naw`).
  * م14: الأركانُ الأربعة: الواقع (مودَعٌ مختوم ببصمته)، والحسّ (مدخلٌ ينقله بلا تخمين)، والمعلوماتُ السابقة، والدماغ.
  * م15–م16: «مفهوم» معنًى له واقعٌ مودَعٌ مشهود — محسوسٌ في الواقع المختوم، أو مسلَّمٌ به بتواتر شهودٍ مستقلّين؛ ولا «مفهوم» لمعنًى
    لا يحمل شاهدَ واقعٍ باسمه في مودَعٍ مختوم؛ ولا يرفع التكرارُ معلومةً إلى مفهوم؛ والغيابُ ليس امتناعًا.

  **التعيين** (رأي البنّاء):
  * الحاسّةُ أداةٌ مسجَّلةٌ بأمرها الحرفيّ (الحسّ في م14). والمشاهدةُ صفٌّ: دفعتُه وموضعُه، والحاسّة، والمصدر (الراوي الفعليّ: البرنامجُ
    أو الحزمةُ أو المستودعُ الناشر — لا مسارُ الملفّ: ملفّاتُ المشروع كلُّها مصدرٌ واحد؛ ولا الشخصُ الكاتب: نصوصُ المشروع ونسخةُ دستور
    الوكيل مصدران بالنشر وكاتبُهما واحد، حدٌّ معلَن يقرّره المالك)، والشيء، والخاصّة، والقيمة كما خرجت، والوجه. وفي المودَع معها بصمةُ
    المخرج الخامّ ووقتُ المشاهدة (لا تدخل الحكمَ هنا).
  * **الوجهان:** «قياس» إذا كانت القيمةُ خاصّةً للبايتات أو للعمليّة المشهودة نفسها (بصمةٌ، عددٌ، محتوى شجرة، مخرجُ تشغيلٍ على مدخلٍ
    معيَّن، رمزُ خروج)؛ و«رواية» إذا كانت قولًا عن غير البايتات الحاضرة أو عن القائل نفسه (إصدارٌ، تاريخ، رابط، وصف، تعريف، ما يرويه
    خادم). وكلُّ صفٍّ — قياسًا كان أو رواية — حكايةٌ بمعنى `Idaa.Wajh.hikaya` (بايتاتُه تطابَق ببصمتها)؛ والروايةُ مضمونُها بدرجة خبرها
    كـ `Idaa.martabaMadmun`: الآحاد لا يرفع، والتواترُ من مصدرين مختلفين يرفع (حدُّه اثنان كـ `Hawass.tasdiq` — تعيين).
  * **الحكم** على قضيّة (شيء، خاصّة، قيمة) بسجلّ المودَعات: «مفهوم» إذا كان في **الصفوف المختومة** منها قياسٌ أو روايتان من مصدرين؛
    و«معلومة» إذا طابقها صفٌّ ولم يستوفِ ذلك (ومنه كلُّ صفٍّ لم تُختم دفعتُه)؛ و«لا حكم» إذا لم يطابقها صفّ — لا «ممتنع».
  * **الزمن:** الحكمُ على «ما شوهد أو رُوي» في وقته لا على «ما هو الآن»؛ و`akhir` آخرُ ما رُصد للشيء والخاصّة، بلا نظرٍ في ختمٍ ولا
    وجه (فليس حكمًا: حكمُ قيمته بـ `hukm`).
  * **النموّ:** المودَعُ يزيد ولا يُحرَّر: دفعةٌ جديدة تُختم بإذن المالك وتُضاف إلى السجلّ؛ فلا يُنزل النموُّ حكمًا.

  **ما ثبت** (بالمعيار الموحَّد في `Nizam/Asas.lean`): 11 مبرهنة —
  * لكلّ (9): `laHukm_iff`، `la_mafhum_bila_khatm`، `qiyas_makhtum_mafhum`، `riwayatan_mafhum`، `masdar_wahid_la_yarfa`،
    `numuw_la_yunzil`، `khatm_la_yunzil`، `jisr_iff`، `akhir_numuw`.
  * تعريفيّة (2): `la_hukm_bila_mushahada`، `mutabiq_append`.
  ومعها مساعدٌ خاصّ `rutba_ratiba` (لا يُعدّ ولا يُدقَّق باسمه؛ يستعمله `numuw_la_yunzil` و`khatm_la_yunzil`).
  وشواهدُ الدفعة الأولى في `Aql/WaqiShawahid.lean` على المولَّد `Aql/WaqiJadwal.lean`.
  بلا sorry ولا axiom ولا native_decide.
-/
import Aql.Maratib

namespace Waqi

/-- وجهُ المشاهدة: «قياس» خاصّةٌ للبايتات أو للعمليّة المشهودة، و«رواية» قولُ مصدر. -/
inductive Wajh | qiyas | riwaya
deriving DecidableEq, Repr

/-- صفُّ المشاهدة: دفعتُه، وموضعُه فيها، والحاسّة، والمصدر، والشيء، والخاصّة، والقيمة، والوجه. -/
structure Mushahada where
  dafa : Nat
  raqm : Nat
  hassa : String
  masdar : String
  mawdu : String
  sifa : String
  qima : String
  wajh : Wajh
deriving DecidableEq, Repr

/-- الحكمُ الثلاثيّ (م15): لا «ممتنع» فيه. -/
inductive Hukm | mafhum | maaluma | laHukm
deriving DecidableEq, Repr

/-- رتبةُ الحكم: لا حكم < معلومة < مفهوم. -/
def Hukm.rutba : Hukm → Nat
  | .laHukm => 0
  | .maaluma => 1
  | .mafhum => 2

/-- الصفوفُ المطابقة لقضيّة (شيء، خاصّة، قيمة). -/
def mutabiq (T : List Mushahada) (mawdu sifa qima : String) : List Mushahada :=
  T.filter fun r => r.mawdu == mawdu && r.sifa == sifa && r.qima == qima

/-- الدفعةُ مختومةٌ «واقعًا» في السجلّ: بشرط `Maratib.shuhudMutabara` نفسه (قيدٌ غيرُ فارغ هو بادئةُ بصمتها، ونوعُه «واقع مختوم»). -/
def makhtum (sijill : List (String × Idaa.Naw)) (b : String) : Bool :=
  sijill.any fun e => !e.1.isEmpty && b.startsWith e.1 && e.2 == .waqiMakhtum

/-- صفوفُ الدفعات المختومة. -/
def makhtuma (sijill : List (String × Idaa.Naw)) (basmaOf : Nat → String) (l : List Mushahada) : List Mushahada :=
  l.filter fun r => makhtum sijill (basmaOf r.dafa)

/-- قياسٌ في الصفوف. -/
def fiihiQiyas (l : List Mushahada) : Bool := l.any fun r => r.wajh == .qiyas

/-- روايتان من مصدرين مختلفين (حدُّ الاستقلال اثنان — تعيينٌ). -/
def tawatur (l : List Mushahada) : Bool :=
  l.any fun a => l.any fun b => a.wajh == .riwaya && b.wajh == .riwaya && a.masdar != b.masdar

/-- **الحكم على قضيّة** بسجلّ المودَعات وبصماتِ الدفعات. -/
def hukm (sijill : List (String × Idaa.Naw)) (basmaOf : Nat → String) (T : List Mushahada) (mawdu sifa qima : String) : Hukm :=
  let l := mutabiq T mawdu sifa qima
  let k := makhtuma sijill basmaOf l
  if fiihiQiyas k || tawatur k then .mafhum
  else if l.isEmpty then .laHukm
  else .maaluma

/-- شواهدُ القضيّة لمراتب المخرج: مواضعُ صفوفها المختومة إذا كان حكمُها «مفهوم»، وإلّا لا شاهد. -/
def shuhud (sijill : List (String × Idaa.Naw)) (basmaOf : Nat → String) (T : List Mushahada) (m s q : String) :
    List Maratib.ShahidWaqi :=
  if hukm sijill basmaOf T m s q = .mafhum then
    (makhtuma sijill basmaOf (mutabiq T m s q)).map fun r => ⟨basmaOf r.dafa, r.raqm⟩
  else []

/-- آخرُ ما رُصد للشيء والخاصّة (بلا نظرٍ في ختمٍ ولا وجه؛ حكمُ القيمة بـ `hukm`). -/
def akhir (T : List Mushahada) (mawdu sifa : String) : Option String :=
  ((T.filter fun r => r.mawdu == mawdu && r.sifa == sifa).getLast?).map (·.qima)

/-! ## ١. الحكم -/

/-- **لا حكمَ بلا مشاهدة** — لا «ممتنع»: الغيابُ ليس نفيًا (م16). -/
theorem la_hukm_bila_mushahada (sijill : List (String × Idaa.Naw)) (basmaOf : Nat → String) (T : List Mushahada)
    (m s q : String) (h : mutabiq T m s q = []) : hukm sijill basmaOf T m s q = .laHukm := by
  simp [hukm, h, makhtuma, fiihiQiyas, tawatur]

/-- «لا حكم» إذا وفقط إذا لم يطابق القضيّةَ صفّ. -/
theorem laHukm_iff (sijill : List (String × Idaa.Naw)) (basmaOf : Nat → String) (T : List Mushahada) (m s q : String) :
    hukm sijill basmaOf T m s q = .laHukm ↔ mutabiq T m s q = [] := by
  constructor
  · intro h
    unfold hukm at h
    cases hl : mutabiq T m s q with
    | nil => rfl
    | cons r rs =>
      rw [hl] at h
      by_cases hc : (fiihiQiyas (makhtuma sijill basmaOf (r :: rs)) || tawatur (makhtuma sijill basmaOf (r :: rs))) = true
      · simp [hc] at h
      · simp [hc] at h
  · exact la_hukm_bila_mushahada sijill basmaOf T m s q

/-- **لا مفهومَ بلا ختم** (م16): ما لم يكن في السجلّ قيدٌ «واقع مختوم» فلا «مفهوم»، أيًّا كانت المشاهدات. -/
theorem la_mafhum_bila_khatm (sijill : List (String × Idaa.Naw)) (hs : ∀ e ∈ sijill, e.2 ≠ .waqiMakhtum)
    (basmaOf : Nat → String) (T : List Mushahada) (m s q : String) : hukm sijill basmaOf T m s q ≠ .mafhum := by
  have hk : makhtuma sijill basmaOf (mutabiq T m s q) = [] := by
    simp only [makhtuma, List.filter_eq_nil_iff]
    intro r _
    simp only [makhtum, Bool.not_eq_true, List.any_eq_false]
    intro e he
    have := hs e he
    cases h : e.2 <;> simp_all
  unfold hukm
  simp only [hk]
  by_cases he : (mutabiq T m s q).isEmpty = true <;> simp [he, fiihiQiyas, tawatur]

/-- **القياسُ المختوم يرفع إلى مفهوم.** -/
theorem qiyas_makhtum_mafhum (sijill : List (String × Idaa.Naw)) (basmaOf : Nat → String) (T : List Mushahada)
    (r : Mushahada) (hr : r ∈ T) (hq : r.wajh = .qiyas) (hk : makhtum sijill (basmaOf r.dafa) = true) :
    hukm sijill basmaOf T r.mawdu r.sifa r.qima = .mafhum := by
  have hm : r ∈ makhtuma sijill basmaOf (mutabiq T r.mawdu r.sifa r.qima) := by
    simp [makhtuma, mutabiq, hr, hk]
  have : fiihiQiyas (makhtuma sijill basmaOf (mutabiq T r.mawdu r.sifa r.qima)) = true :=
    List.any_eq_true.mpr ⟨r, hm, by simp [hq]⟩
  simp [hukm, this]

/-- **روايتان مختومتان من مصدرين مختلفين ترفعان إلى مفهوم** (تواترٌ بحدّ اثنين — تعيين). -/
theorem riwayatan_mafhum (sijill : List (String × Idaa.Naw)) (basmaOf : Nat → String) (T : List Mushahada)
    (a b : Mushahada) (ha : a ∈ T) (hb : b ∈ T) (hwa : a.wajh = .riwaya) (hwb : b.wajh = .riwaya)
    (hka : makhtum sijill (basmaOf a.dafa) = true) (hkb : makhtum sijill (basmaOf b.dafa) = true)
    (hs : b.mawdu = a.mawdu) (hf : b.sifa = a.sifa) (hv : b.qima = a.qima) (hd : a.masdar ≠ b.masdar) :
    hukm sijill basmaOf T a.mawdu a.sifa a.qima = .mafhum := by
  have hma : a ∈ makhtuma sijill basmaOf (mutabiq T a.mawdu a.sifa a.qima) := by simp [makhtuma, mutabiq, ha, hka]
  have hmb : b ∈ makhtuma sijill basmaOf (mutabiq T a.mawdu a.sifa a.qima) := by
    simp [makhtuma, mutabiq, hb, hkb, hs, hf, hv]
  have : tawatur (makhtuma sijill basmaOf (mutabiq T a.mawdu a.sifa a.qima)) = true := by
    unfold tawatur
    exact List.any_eq_true.mpr ⟨a, hma, List.any_eq_true.mpr ⟨b, hmb, by simp [hwa, hwb, hd]⟩⟩
  simp [hukm, this]

/-- **المصدرُ الواحد لا يرفع** (م16: التكرارُ لا يرفع): إذا كانت كلُّ الصفوف المطابقة رواياتٍ من مصدرٍ واحد فلا «مفهوم»،
    مهما كثرت ومهما خُتمت. -/
theorem masdar_wahid_la_yarfa (sijill : List (String × Idaa.Naw)) (basmaOf : Nat → String) (T : List Mushahada)
    (m s q src : String) (h : ∀ r ∈ mutabiq T m s q, r.wajh = .riwaya ∧ r.masdar = src) :
    hukm sijill basmaOf T m s q ≠ .mafhum := by
  have hk : ∀ r ∈ makhtuma sijill basmaOf (mutabiq T m s q), r.wajh = .riwaya ∧ r.masdar = src := by
    intro r hr
    simp only [makhtuma, List.mem_filter] at hr
    exact h r hr.1
  have h1 : fiihiQiyas (makhtuma sijill basmaOf (mutabiq T m s q)) = false := by
    simp only [fiihiQiyas, List.any_eq_false]
    intro r hr
    simp [(hk r hr).1]
  have h2 : tawatur (makhtuma sijill basmaOf (mutabiq T m s q)) = false := by
    simp only [tawatur, List.any_eq_false]
    intro a ha
    simp only [List.any_eq_true, not_exists, not_and]
    intro b hb
    simp [(hk a ha).2, (hk b hb).2]
  unfold hukm
  simp only [h1, h2, Bool.or_false, Bool.false_eq_true, ite_false]
  by_cases he : (mutabiq T m s q).isEmpty = true <;> simp [he]

/-! ## ٢. النموّ -/

theorem mutabiq_append (T T' : List Mushahada) (m s q : String) :
    mutabiq (T ++ T') m s q = mutabiq T m s q ++ mutabiq T' m s q := by
  simp [mutabiq]

/-- رتبةُ حكمٍ لا تنزل إذا زاد ما يستوفيه وزاد ما يطابقه. -/
private theorem rutba_ratiba (l l' k k' : List Mushahada) (hk : ∀ x ∈ k, x ∈ k') (hl : l.isEmpty = false → l'.isEmpty = false) :
    (if fiihiQiyas k || tawatur k then Hukm.mafhum else if l.isEmpty then .laHukm else .maaluma).rutba ≤
    (if fiihiQiyas k' || tawatur k' then Hukm.mafhum else if l'.isEmpty then .laHukm else .maaluma).rutba := by
  have hq : fiihiQiyas k = true → fiihiQiyas k' = true := by
    simp only [fiihiQiyas, List.any_eq_true]
    rintro ⟨x, hx, h⟩
    exact ⟨x, hk x hx, h⟩
  have ht : tawatur k = true → tawatur k' = true := by
    simp only [tawatur, List.any_eq_true]
    rintro ⟨a, ha, b, hb, h⟩
    exact ⟨a, hk a ha, b, hk b hb, h⟩
  by_cases h1 : (fiihiQiyas k || tawatur k) = true
  · have h1' : (fiihiQiyas k' || tawatur k') = true := by
      simp only [Bool.or_eq_true] at h1 ⊢
      exact h1.elim (fun h => Or.inl (hq h)) (fun h => Or.inr (ht h))
    simp [h1, h1']
  · simp only [h1]
    by_cases h2 : l.isEmpty = true
    · simp [h2, Hukm.rutba]
    · have h3 := hl (by simpa using h2)
      by_cases h4 : (fiihiQiyas k' || tawatur k') = true <;> simp [h2, h3, h4, Hukm.rutba]

/-- **النموُّ لا يُنزل حكمًا:** إضافةُ مشاهداتٍ لا تخفض رتبةَ أيّ قضيّة. -/
theorem numuw_la_yunzil (sijill : List (String × Idaa.Naw)) (basmaOf : Nat → String) (T T' : List Mushahada)
    (m s q : String) : (hukm sijill basmaOf T m s q).rutba ≤ (hukm sijill basmaOf (T ++ T') m s q).rutba := by
  unfold hukm
  apply rutba_ratiba
  · intro x hx
    simp only [makhtuma, List.mem_filter, mutabiq_append, List.mem_append] at hx ⊢
    exact ⟨Or.inl hx.1, hx.2⟩
  · intro h
    rw [mutabiq_append]
    cases hl : mutabiq T m s q with
    | nil => simp [hl] at h
    | cons _ _ => rfl

/-- **الختمُ لا يُنزل حكمًا:** سجلٌّ يحوي قيودَ سجلٍّ آخر (بزيادة ختمٍ أو بغيرها، أيًّا كان الترتيب) لا تنقص فيه رتبةُ أيّ قضيّة. -/
theorem khatm_la_yunzil (sijill sijill' : List (String × Idaa.Naw)) (hsub : ∀ e ∈ sijill, e ∈ sijill')
    (basmaOf : Nat → String) (T : List Mushahada) (m s q : String) :
    (hukm sijill basmaOf T m s q).rutba ≤ (hukm sijill' basmaOf T m s q).rutba := by
  unfold hukm
  apply rutba_ratiba
  · intro x hx
    simp only [makhtuma, List.mem_filter, makhtum, List.any_eq_true] at hx ⊢
    obtain ⟨hx1, e, he, h⟩ := hx
    exact ⟨hx1, e, hsub e he, h⟩
  · exact id

/-- **آخرُ ما رُصد من الأحدث:** إن رُصد الشيءُ والخاصّةُ في الدفعة المضافة فآخرُ ما رُصد لهما منها. -/
theorem akhir_numuw (T T' : List Mushahada) (m s : String)
    (h : (T'.filter fun r => r.mawdu == m && r.sifa == s) ≠ []) : akhir (T ++ T') m s = akhir T' m s := by
  unfold akhir
  rw [List.filter_append, List.getLast?_append]
  cases hl : (T'.filter fun r => r.mawdu == m && r.sifa == s).getLast? with
  | none => exact absurd (List.getLast?_eq_none_iff.mp hl) h
  | some x => simp

/-! ## ٣. الجسر إلى مراتب المخرج (`Aql/Maratib.lean`) -/

/-- **الجسر:** معنى القضيّة في `Maratib` «مفهوم» إذا وفقط إذا كان حكمُها هنا «مفهوم» — فلا ترفع `Maratib` روايةَ آحادٍ ولا دفعةً
    غيرَ مختومة. -/
theorem jisr_iff (sijill : List (String × Idaa.Naw)) (basmaOf : Nat → String) (T : List Mushahada) (m s q : String)
    (i : Nat) :
    (Maratib.martabatMaana i (Maratib.shuhudMutabara sijill (shuhud sijill basmaOf T m s q))).ism = "مفهوم" ↔
      hukm sijill basmaOf T m s q = .mafhum := by
  have hall : Maratib.shuhudMutabara sijill (shuhud sijill basmaOf T m s q) = shuhud sijill basmaOf T m s q := by
    simp only [Maratib.shuhudMutabara]
    rw [List.filter_eq_self]
    intro w hw
    unfold shuhud at hw
    split at hw
    · simp only [List.mem_map, makhtuma, List.mem_filter] at hw
      obtain ⟨r, ⟨_, hk⟩, rfl⟩ := hw
      exact hk
    · simp at hw
  rw [hall]
  constructor
  · intro h
    by_cases hm : hukm sijill basmaOf T m s q = .mafhum
    · exact hm
    · simp [shuhud, hm, Maratib.martabatMaana, Maratib.Mukhraj.ism] at h
  · intro hm
    have hne : makhtuma sijill basmaOf (mutabiq T m s q) ≠ [] := by
      intro he
      unfold hukm at hm
      simp only [he] at hm
      by_cases h2 : (mutabiq T m s q).isEmpty = true <;> simp [h2, fiihiQiyas, tawatur] at hm
    unfold shuhud
    simp only [hm, ite_true]
    cases hk : makhtuma sijill basmaOf (mutabiq T m s q) with
    | nil => exact absurd hk hne
    | cons w ws => simp [Maratib.martabatMaana, Maratib.Mukhraj.ism]

end Waqi
