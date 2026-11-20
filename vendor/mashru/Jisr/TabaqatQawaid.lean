import Jisr.Intrubiya

/-!
# طبقةُ القواعد بين القانون والاستعمال: القاعدةُ آلةٌ على الخلايا تُقرن بآلة القانون

**الطلب.** رسالةُ المالك 2026-10-28: صدرُها في سجلّ الجلسة مقطوعًا عند نحو مئتي حرف، وباقيها ووقتُها (12:11 بتوقيت عمّان) وإجاباتُه
من ملخّص الجلسة بعد ضغطها. ولفظُها فيه:
«حاول مرة أخرى تنظيم الانتروبيا انت تدير مجموعة وكلاء … وتحويل الالفية الى lean داخل الشيفرة الام وفق افضل الممارسات»
ثمّ اختار من ثلاثة أسئلةٍ متعدّدة الخيارات نصُّها من البنّاء، و«(موصى به)» وسمُ البنّاء في كلٍّ:
- «الاثنان (موصى به)»: إنجاحُ #94 على CI، ثمّ طبقةُ القواعد بين القانون والاستعمال.
- «أبوابُ الصوت والبنية (موصى به)».
- «على آلة القانون وخلاياها (موصى به)».

والتصميمُ قرارُ البنّاء. والقطعةُ قطعةُ بنية لا تحكم على لفظٍ من مصدر، فعدُّها خارج الضابط المجمَّد قراءةُ البنّاء، تنتظر إمضاءَ المالك.

**موضعُها** (`Jisr/الإنتروبيا.md` §٨): القاعدةُ آلةٌ على الخلايا، والقانونُ والقاعدةُ معًا آلةٌ واحدة (`maan`) تقبل ما يقبلانه كلاهما
(`qabul_maan`). وتسميتُها طبقةً «بين القانون والاستعمال» رأيُ البنّاء: لا مبرهنةَ هنا تربط لغةَ القاعدة بالاستعمال.

**العدد:** القاعدةُ لا توسّع (`adad_maan_le`): عددُ كلمات الطول `n` من الأبجديّة التي تقبلها الآلتان معًا من حالتي البدء لا يزيد على عدد
القانون من حالته. ويساويه إذا وفقط إذا لم تردّ القاعدةُ من حالتها كلمةً بذلك الطول من الأبجديّة يقبلها القانونُ من حالته
(`adad_maan_eq_iff`). فالقاعدةُ الفارغة لا تغيّر العدد (`adad_fargh`). وتسميةُ ما تحذفه القاعدةُ «معرفة» رأيُ البنّاء (كما في
`Jisr/الإنتروبيا.md` §٦). والعددُ لطولٍ غيرُ معدّل النموّ (`log₂ρ`) الذي يقيس به §٢ الطبقات: قاعدةٌ تحذف من كلّ طولٍ قد لا تغيّره، ولا
مبرهنةَ هنا على المعدّل.

**القاعدة** (`Qayd`): ما يُحفظ ممّا مضى صنفٌ من `k` يتجدّد بكلّ خليّة (`awwalSinf` بعد الأولى، و`sinf` بعدها)، وتُمنع الخليّةُ بعد صنفٍ
(`mamnu`) أو أوّلَ الكلمة (`bidaya`)، ويُمنع أن تنتهي الكلمةُ على صنف (`khatima`). وآلتُها (`Qayd.ala`) تساوي مواصفتَها على الكلمة
(`Qayd.tasmah`) لكلّ كلمة (`ala_iff`).
- الخليّةُ الممنوعةُ بعد الصنف الذي بلغته الكلمةُ قبلها تردّ الكلمةَ في أيّ موضعٍ بعد الأوّل (`tasmah_mamnu`).
- وفي القاعدة المحلّيّة (`Qayd.mahalli`: صنفُ الخليّة لا يتعلّق بما قبلها) الزوجُ المتجاورُ الممنوع يردّها حيثما وقع (`tasmah_zawj`).
- والقانونُ والقاعدةُ معًا يقبلان ما يقبله القانونُ وتسمح به القاعدة (`maan_tasmah`)، وقاعدتان معًا ما تسمح به كلٌّ منهما (`tasmah_ithnan`).

**أقربُ الموجود:** `Jisr.Iqtiran.Qayd` (`Jisr/Iqtiran.lean`) قيدٌ باسمه يقبل مرشَّحًا أو يردّه، ومعه `qayd_la_yazid` و`tabaqat`، ومن قيوده
`qaydTaanith` على رموز الخلايا من القطر. والفرقُ: ذاك محمولٌ على مرشَّحٍ واحد، وهذا آلةٌ على سلسلة الخلايا تُقرن بآلة القانون فيُعدّ
ما تقبلانه معًا بكلّ طول. و`Qayd` هنا بلا حقل اسمٍ ولا سند.

**الحدّان لمعدّل النموّ على أيّ آلة** (`hadd_aala_amm`، `hadd_adna_amm`): على صورة `Jisr.Intrubiya.hadd_aala`/`hadd_adna`، لأيّ آلةٍ
بمجموعة حالاتٍ مغلقة بالانتقال (ولا مبرهنةَ تشتقّ تلك منهما). ويمكن بهما أن تُكتب للقانون مع قاعدةٍ شهادةٌ كشهادة
`Jisr/IntrubiyaShahada.lean` (لم تُبنَ).

**على آلة القانون وخلايا Mashru** (`qanun_qaida_le`، `qanun_qaida_eq_iff`): القاعدةُ `Qayd Dal.Khaliya` مقرونةً بـ`alaMashru` لا يزيد
عددُها على `lawCount`، ويساويه لطولٍ إذا وفقط إذا لم تردّ كلمةً من خلايا Mashru بذلك الطول يقبلها القانون.

**المبرهنات** (23، بالمعيار الموحَّد في `Nizam/Asas.lean`): كلُّها لكلّ — برهانُها استقراءٌ أو استدعاءُ مبرهنةٍ من الملفّ أو تطبيقُ فرضٍ
كمّيٍّ على معطيات — ولا تعريفيّة ولا شيء على الشاهد.

**ما لا تقوله.**
- أنّ قاعدةً ما صحيحةٌ لغةً، ولا ما تحذفه في المصحف: القواعدُ بعدها، وقياسُ ما تحذفه في `scripts/intrubiya.py` بعدها.
- و`Qayd` يقبل الكلمةَ أو يردّها ولا يُخرج صورة. فما في أبواب الصوت والبنية من تحويلٍ (الإبدال والإدغام والإمالة والإعلال) لا يُكتب
  عليه إلّا قيدًا على الصورة السطحيّة: يردّ الصورةَ التي يمنعها الحكم، ولا يُخرج الصورةَ التي يوجبها.
-/

namespace Jisr.TabaqatQawaid

open Jisr.Intrubiya

variable {Q P A : Type}

/-! ## ١. الآلتان معًا -/

/-- القانونُ والقاعدةُ آلةً واحدة: حالتُها زوجُ حالتيهما، والكلفةُ كلفةُ الأولى، والقبولُ قبولُهما كلتيهما. -/
def maan (M : Nabt.Machine Q A) (R : Nabt.Machine P A) : Nabt.Machine (Q × P) A :=
  ⟨fun s a => (M.step s.1 a, R.step s.2 a), fun s a => M.cost s.1 a, fun s => M.final s.1 && R.final s.2⟩

theorem run_maan (M : Nabt.Machine Q A) (R : Nabt.Machine P A) :
    ∀ (xs : List A) (q : Q) (p : P), (maan M R).run (q, p) xs = (M.run q xs, R.run p xs)
  | [], _, _ => rfl
  | a :: xs, q, p => run_maan M R xs (M.step q a) (R.step p a)

/-- لغةُ الآلتين معًا تقاطعُ لغتيهما. -/
theorem qabul_maan (M : Nabt.Machine Q A) (R : Nabt.Machine P A) (xs : List A) (q : Q) (p : P) :
    (maan M R).final ((maan M R).run (q, p) xs) = (M.final (M.run q xs) && R.final (R.run p xs)) := by
  rw [run_maan]; rfl

theorem length_filter_and_le (l : List A) (f g : A → Bool) :
    (l.filter (fun x => f x && g x)).length ≤ (l.filter f).length := by
  induction l with
  | nil => simp
  | cons a l ih =>
    by_cases hf : f a = true <;> by_cases hg : g a = true <;>
      simp [hf, hg] <;> omega

/-- **القاعدةُ لا توسّع:** عددُ كلمات الطول `n` من الأبجديّة التي تقبلها الآلتان معًا لا يزيد على ما يقبله القانون وحده. -/
theorem adad_maan_le (M : Nabt.Machine Q A) (R : Nabt.Machine P A) (alphabet : List A) (n : Nat) (q : Q) (p : P) :
    lenCount (maan M R) alphabet n (q, p) ≤ lenCount M alphabet n q := by
  rw [lenCount_eq_spec, lenCount_eq_spec, lenSpec, lenSpec]
  have : (exactWords alphabet n).filter (fun xs => (maan M R).final ((maan M R).run (q, p) xs)) =
      (exactWords alphabet n).filter (fun xs => M.final (M.run q xs) && R.final (R.run p xs)) := by
    apply List.filter_congr; intro xs _; exact qabul_maan M R xs q p
  rw [this]
  exact length_filter_and_le _ _ _

/-- وإن قبلت القاعدةُ كلَّ كلمةٍ من حالتها فالعددُ عددُ القانون بعينه. -/
theorem adad_maan_eq (M : Nabt.Machine Q A) (R : Nabt.Machine P A) (alphabet : List A) (n : Nat) (q : Q) (p : P)
    (h : ∀ xs, R.final (R.run p xs) = true) :
    lenCount (maan M R) alphabet n (q, p) = lenCount M alphabet n q := by
  rw [lenCount_eq_spec, lenCount_eq_spec, lenSpec, lenSpec]
  congr 1
  apply List.filter_congr; intro xs _
  rw [qabul_maan, h xs, Bool.and_true]

theorem length_filter_and_eq_iff (l : List A) (f g : A → Bool) :
    (l.filter (fun x => f x && g x)).length = (l.filter f).length ↔ ∀ x ∈ l, f x = true → g x = true := by
  induction l with
  | nil => simp
  | cons a l ih =>
    have hle := length_filter_and_le l f g
    by_cases hf : f a = true <;> by_cases hg : g a = true
    · simp [hf, hg, ih]
    · have hg' : g a = false := by simpa using hg
      simp only [List.filter_cons, hf, hg', Bool.and_false]
      simp only [Bool.false_eq_true, ite_false, ite_true, List.length_cons]
      constructor
      · intro h; omega
      · intro h; exact absurd (h a (List.mem_cons_self ..) hf) hg
    · simp [hf, ih]
    · simp [hf, ih]

/-- **العددُ لا يتغيّر إلّا بردّ:** عددُ الآلتين معًا لطول `n` من حالتي البدء هو عددُ القانون من حالته إذا وفقط إذا قبلت القاعدةُ
من حالتها كلَّ كلمةٍ بهذا الطول من الأبجديّة يقبلها القانونُ من حالته. -/
theorem adad_maan_eq_iff (M : Nabt.Machine Q A) (R : Nabt.Machine P A) (alphabet : List A) (n : Nat) (q : Q) (p : P) :
    lenCount (maan M R) alphabet n (q, p) = lenCount M alphabet n q ↔
      ∀ xs : List A, xs.length = n → (∀ a ∈ xs, a ∈ alphabet) →
        M.final (M.run q xs) = true → R.final (R.run p xs) = true := by
  rw [lenCount_eq_spec, lenCount_eq_spec, lenSpec, lenSpec]
  have : (exactWords alphabet n).filter (fun xs => (maan M R).final ((maan M R).run (q, p) xs)) =
      (exactWords alphabet n).filter (fun xs => M.final (M.run q xs) && R.final (R.run p xs)) := by
    apply List.filter_congr; intro xs _; exact qabul_maan M R xs q p
  rw [this, length_filter_and_eq_iff]
  constructor
  · intro h xs hl ha; exact h xs ((mem_exactWords alphabet n xs).2 ⟨hl, ha⟩)
  · intro h xs hx; have := (mem_exactWords alphabet n xs).1 hx; exact h xs this.1 this.2

/-! ## ٢. القاعدةُ: صنفُ ما مضى، والممنوعُ بعده، والممنوعُ أوّلًا وآخرًا -/

/-- قاعدةٌ على الخلايا: ما يُحفظ ممّا مضى صنفٌ من `k` يتجدّد بكلّ خليّة، وتُمنع الخليّةُ بعد صنفٍ (`mamnu`) أو أوّلَ الكلمة
(`bidaya`)، ويُمنع أن تنتهي الكلمةُ على صنف (`khatima`). -/
structure Qayd (A : Type) where
  /-- عددُ الأصناف. -/
  k : Nat
  /-- الصنفُ بعد الخليّة الأولى. -/
  awwalSinf : A → Fin k
  /-- الصنفُ بعد خليّةٍ، من الصنف قبلها. -/
  sinf : Fin k → A → Fin k
  /-- الخليّةُ الممنوعةُ بعد صنف. -/
  mamnu : Fin k → A → Bool
  /-- الخليّةُ الممنوعةُ أوّلَ الكلمة. -/
  bidaya : A → Bool
  /-- الصنفُ الذي لا تنتهي عليه الكلمة. -/
  khatima : Fin k → Bool

/-- حالُ آلة القاعدة: ميّتة، أو في أوّل الكلمة، أو بعد خليّةٍ بصنف. -/
inductive Hal (k : Nat) where
  | mayyit
  | awwal
  | baad (c : Fin k)

/-- آلةُ القاعدة. -/
def Qayd.ala (r : Qayd A) : Nabt.Machine (Hal r.k) A where
  step := fun s a => match s with
    | .mayyit => .mayyit
    | .awwal => if r.bidaya a then .mayyit else .baad (r.awwalSinf a)
    | .baad c => if r.mamnu c a then .mayyit else .baad (r.sinf c a)
  cost := fun _ _ => 0
  final := fun s => match s with
    | .mayyit => false
    | .awwal => true
    | .baad c => !r.khatima c

/-- المواصفةُ بعد صنف `c`: لا خليّةَ ممنوعةٌ فيما بقي، ولا تنتهي على صنفٍ ممنوع. -/
def Qayd.tasmahBaad (r : Qayd A) : Fin r.k → List A → Bool
  | c, [] => !r.khatima c
  | c, b :: ys => !r.mamnu c b && r.tasmahBaad (r.sinf c b) ys

/-- المواصفةُ على الكلمة. -/
def Qayd.tasmah (r : Qayd A) : List A → Bool
  | [] => true
  | a :: xs => !r.bidaya a && r.tasmahBaad (r.awwalSinf a) xs

/-- الصنفُ بعد سلسلةٍ من صنف `c`. -/
def Qayd.sira (r : Qayd A) (c : Fin r.k) (xs : List A) : Fin r.k := xs.foldl r.sinf c

/-- القاعدةُ محلّيّة إن لم يتعلّق صنفُ الخليّة بما قبلها: فما تمنعه بعد الأولى يمنعه الزوجُ المتجاور (`tasmah_zawj`)، مع `bidaya` و`khatima`. -/
def Qayd.mahalli (r : Qayd A) : Prop := ∀ c a, r.sinf c a = r.awwalSinf a

/-- الميّتةُ لا تحيا. -/
theorem mayyit_yabqa (r : Qayd A) : ∀ xs : List A, r.ala.run .mayyit xs = .mayyit
  | [] => rfl
  | _ :: xs => mayyit_yabqa r xs

theorem ala_baad (r : Qayd A) : ∀ (xs : List A) (c : Fin r.k),
    r.ala.final (r.ala.run (.baad c) xs) = r.tasmahBaad c xs
  | [], _ => rfl
  | b :: ys, c => by
    by_cases h : r.mamnu c b = true
    · have hs : r.ala.step (.baad c) b = .mayyit := by simp [Qayd.ala, h]
      simp only [Nabt.Machine.run, hs, mayyit_yabqa, Qayd.tasmahBaad, h]; rfl
    · have hs : r.ala.step (.baad c) b = .baad (r.sinf c b) := by simp [Qayd.ala, h]
      simp only [Nabt.Machine.run, hs, ala_baad r ys (r.sinf c b), Qayd.tasmahBaad]
      simp [h]

/-- **الآلةُ مواصفتُها:** آلةُ القاعدة من أوّل الكلمة تقبل الكلمةَ إذا وفقط إذا قبلتها المواصفة. -/
theorem ala_iff (r : Qayd A) : ∀ xs : List A, r.ala.final (r.ala.run .awwal xs) = r.tasmah xs
  | [] => rfl
  | a :: xs => by
    by_cases h : r.bidaya a = true
    · have hs : r.ala.step .awwal a = .mayyit := by simp [Qayd.ala, h]
      simp only [Nabt.Machine.run, hs, mayyit_yabqa, Qayd.tasmah, h]; rfl
    · have hs : r.ala.step .awwal a = .baad (r.awwalSinf a) := by simp [Qayd.ala, h]
      simp only [Nabt.Machine.run, hs, ala_baad, Qayd.tasmah]
      simp [h]

/-- الخليّةُ الممنوعةُ بعد الصنف الذي بلغته السلسلةُ تردّ ما بعدها كلَّه. -/
theorem tasmahBaad_mamnu (r : Qayd A) :
    ∀ (pre : List A) (c : Fin r.k) (b : A) (post : List A), r.mamnu (r.sira c pre) b = true →
      r.tasmahBaad c (pre ++ b :: post) = false
  | [], c, b, post, h => by simp [Qayd.tasmahBaad, Qayd.sira] at h ⊢; simp [h]
  | x :: pre, c, b, post, h => by
    simp only [List.cons_append, Qayd.tasmahBaad]
    rw [tasmahBaad_mamnu r pre (r.sinf c x) b post h, Bool.and_false]

/-- **الممنوعُ يردّ الكلمة** في أيّ موضعٍ بعد الأوّل: إن مُنعت الخليّةُ `b` بعد الصنف الذي بلغته الكلمةُ قبلها. -/
theorem tasmah_mamnu (r : Qayd A) (a : A) (pre : List A) (b : A) (post : List A)
    (h : r.mamnu (r.sira (r.awwalSinf a) pre) b = true) : r.tasmah (a :: pre ++ b :: post) = false := by
  simp only [List.cons_append, Qayd.tasmah]
  rw [tasmahBaad_mamnu r pre (r.awwalSinf a) b post h, Bool.and_false]

theorem sira_mahalli (r : Qayd A) (hm : r.mahalli) : ∀ (c : Fin r.k) (pre : List A) (x : A),
    r.sira c (pre ++ [x]) = r.awwalSinf x := by
  intro c pre x
  simp only [Qayd.sira, List.foldl_append, List.foldl_cons, List.foldl_nil]
  exact hm _ _

/-- **وفي القاعدة المحلّيّة الزوجُ المتجاورُ الممنوع يردّ الكلمة** حيثما وقع. -/
theorem tasmah_zawj (r : Qayd A) (hm : r.mahalli) (pre : List A) (a b : A) (post : List A)
    (h : r.mamnu (r.awwalSinf a) b = true) : r.tasmah (pre ++ a :: b :: post) = false := by
  cases pre with
  | nil =>
    have : r.mamnu (r.sira (r.awwalSinf a) []) b = true := h
    simpa using tasmah_mamnu r a [] b post this
  | cons x pre =>
    have : r.mamnu (r.sira (r.awwalSinf x) (pre ++ [a])) b = true := by rw [sira_mahalli r hm]; exact h
    have := tasmah_mamnu r x (pre ++ [a]) b post this
    simpa using this

/-- **القانونُ والقاعدةُ معًا:** يقبلان الكلمةَ إذا وفقط إذا قبلها القانونُ وسمحت بها القاعدة. -/
theorem maan_tasmah (M : Nabt.Machine Q A) (r : Qayd A) (q : Q) (xs : List A) :
    (maan M r.ala).final ((maan M r.ala).run (q, .awwal) xs) = (M.final (M.run q xs) && r.tasmah xs) := by
  rw [qabul_maan, ala_iff]

/-- **قاعدتان معًا** تقبلان ما تقبله كلٌّ منهما. -/
theorem tasmah_ithnan (r₁ r₂ : Qayd A) (xs : List A) :
    (maan r₁.ala r₂.ala).final ((maan r₁.ala r₂.ala).run (.awwal, .awwal) xs) = (r₁.tasmah xs && r₂.tasmah xs) := by
  rw [qabul_maan, ala_iff, ala_iff]

/-- القاعدةُ الفارغة: لا تمنع شيئًا. -/
def Qayd.fargh : Qayd A := ⟨1, fun _ => 0, fun _ _ => 0, fun _ _ => false, fun _ => false, fun _ => false⟩

theorem tasmahBaad_fargh :
    ∀ (c : Fin (Qayd.fargh : Qayd A).k) (xs : List A), (Qayd.fargh : Qayd A).tasmahBaad c xs = true
  | _, [] => rfl
  | c, b :: ys => by
    simp only [Qayd.tasmahBaad]; rw [tasmahBaad_fargh]; rfl

theorem tasmah_fargh : ∀ xs : List A, (Qayd.fargh : Qayd A).tasmah xs = true
  | [] => rfl
  | a :: ys => by
    simp only [Qayd.tasmah]; rw [tasmahBaad_fargh]; rfl

/-- **القاعدةُ الفارغة لا تغيّر العدد:** القانونُ معها يعدّ ما يعدّه القانونُ وحده لكلّ طولٍ وحالة. -/
theorem adad_fargh (M : Nabt.Machine Q A) (alphabet : List A) (n : Nat) (q : Q) :
    lenCount (maan M (Qayd.fargh : Qayd A).ala) alphabet n (q, .awwal) = lenCount M alphabet n q :=
  adad_maan_eq M _ alphabet n q _ (fun xs => by rw [ala_iff, tasmah_fargh])

/-! ## ٣. الحدّان لمعدّل النموّ على أيّ آلةٍ بحالاتٍ مغلقة -/

/-- مؤثّرُ الانتقال على آلةٍ وأبجديّة. -/
def Tm (M : Nabt.Machine Q A) (alphabet : List A) (f : Q → Nat) (q : Q) : Nat :=
  (alphabet.map fun a => f (M.step q a)).sum

/-- **الحدُّ الأعلى** على أيّ آلةٍ مجموعةُ حالاتها `S` مغلقةٌ بالانتقال: إن كان `d·Tv ≤ p·v` على `S` وكانت النهائيّةُ تحت `c·v`،
فـ`d^n·N_n(q) ≤ c·p^n·v(q)` لكلّ `q` في `S`. -/
theorem hadd_aala_amm (M : Nabt.Machine Q A) (alphabet : List A) (S : Q → Prop)
    (hS : ∀ q a, S q → S (M.step q a)) (v : Q → Nat) (c p d : Nat)
    (hv : ∀ q, S q → d * Tm M alphabet v q ≤ p * v q)
    (hf : ∀ q, S q → (if M.final q then 1 else 0) ≤ c * v q) :
    ∀ n q, S q → d ^ n * lenCount M alphabet n q ≤ c * p ^ n * v q
  | 0, q, hq => by simpa [lenCount] using hf q hq
  | n + 1, q, hq => by
    have ih : ∀ a ∈ alphabet, d ^ n * lenCount M alphabet n (M.step q a) ≤ c * p ^ n * v (M.step q a) :=
      fun a _ => hadd_aala_amm M alphabet S hS v c p d hv hf n _ (hS q a hq)
    have h1 : d ^ (n + 1) * lenCount M alphabet (n + 1) q =
        d * (alphabet.map fun a => d ^ n * lenCount M alphabet n (M.step q a)).sum := by
      rw [lenCount, sum_map_mul, Nat.pow_succ, Nat.mul_comm (d ^ n) d, Nat.mul_assoc]
    have h2 : (alphabet.map fun a => d ^ n * lenCount M alphabet n (M.step q a)).sum ≤ c * p ^ n * Tm M alphabet v q := by
      rw [Tm, ← sum_map_mul]
      exact sum_map_le alphabet _ _ ih
    rw [h1]
    calc d * (alphabet.map fun a => d ^ n * lenCount M alphabet n (M.step q a)).sum
        ≤ d * (c * p ^ n * Tm M alphabet v q) := Nat.mul_le_mul_left _ h2
      _ = c * p ^ n * (d * Tm M alphabet v q) := Nat.mul_left_comm _ _ _
      _ ≤ c * p ^ n * (p * v q) := Nat.mul_le_mul_left _ (hv q hq)
      _ = c * p ^ (n + 1) * v q := by rw [Nat.pow_succ]; simp only [Nat.mul_assoc]

/-- **الحدُّ الأدنى** على أيّ آلةٍ مجموعةُ حالاتها `S` مغلقة: إن كان `r·u ≤ s·Tu` على `S` وكان `e·u ≤ N_k`، فـ`e·r^n·u(q) ≤ s^n·N_(k+n)(q)`. -/
theorem hadd_adna_amm (M : Nabt.Machine Q A) (alphabet : List A) (S : Q → Prop)
    (hS : ∀ q a, S q → S (M.step q a)) (u : Q → Nat) (k r s e : Nat)
    (hu : ∀ q, S q → r * u q ≤ s * Tm M alphabet u q)
    (hb : ∀ q, S q → e * u q ≤ lenCount M alphabet k q) :
    ∀ n q, S q → e * r ^ n * u q ≤ s ^ n * lenCount M alphabet (k + n) q
  | 0, q, hq => by simpa using hb q hq
  | n + 1, q, hq => by
    have ih : ∀ a ∈ alphabet, e * r ^ n * u (M.step q a) ≤ s ^ n * lenCount M alphabet (k + n) (M.step q a) :=
      fun a _ => hadd_adna_amm M alphabet S hS u k r s e hu hb n _ (hS q a hq)
    have h2 : e * r ^ n * Tm M alphabet u q ≤
        s ^ n * (alphabet.map fun a => lenCount M alphabet (k + n) (M.step q a)).sum := by
      rw [Tm, ← sum_map_mul, ← sum_map_mul]
      exact sum_map_le alphabet _ _ ih
    have h1 : s ^ (n + 1) * lenCount M alphabet (k + (n + 1)) q =
        s * (s ^ n * (alphabet.map fun a => lenCount M alphabet (k + n) (M.step q a)).sum) := by
      rw [← Nat.add_assoc, lenCount, Nat.pow_succ, Nat.mul_comm (s ^ n) s, Nat.mul_assoc]
    rw [h1]
    calc e * r ^ (n + 1) * u q = e * r ^ n * (r * u q) := by
          rw [Nat.pow_succ]; simp only [Nat.mul_assoc]
      _ ≤ e * r ^ n * (s * Tm M alphabet u q) := Nat.mul_le_mul_left _ (hu q hq)
      _ = s * (e * r ^ n * Tm M alphabet u q) := Nat.mul_left_comm _ _ _
      _ ≤ s * (s ^ n * (alphabet.map fun a => lenCount M alphabet (k + n) (M.step q a)).sum) :=
          Nat.mul_le_mul_left _ h2

/-! ## ٤. على آلة القانون وخلايا Mashru -/

/-- **القاعدةُ على آلة القانون لا توسّع:** عددُ كلمات الطول `n` من خلايا Mashru التي يقبلها القانونُ (`alaMashru`) وتسمح بها
القاعدةُ لا يزيد على عدد القانون `lawCount`. -/
theorem qanun_qaida_le (mode : Bool) (r : Qayd Dal.Khaliya) (n : Nat) :
    lenCount (maan (alaMashru mode) r.ala) khalayaKull n (0, .awwal) ≤ lawCount mode n :=
  calc lenCount (maan (alaMashru mode) r.ala) khalayaKull n (0, .awwal)
      ≤ lenCount (alaMashru mode) khalayaKull n 0 := adad_maan_le _ _ _ _ _ _
    _ = lenCount (Nabt.Law.machine mode) Nabt.Law.alphabet n 0 := intrubiya_la_tataghayyar_bil_tamthil mode n 0
    _ = lawCount mode n := by rw [lawCount_eq, lenCount_eq_spec]

/-- **ولا تغيّر العددَ بطول `n` إلّا إذا ردّت كلمةً بهذا الطول يقبلها القانون:** العددُ عددُ القانون بعينه إذا وفقط إذا سمحت القاعدةُ
بكلّ كلمةٍ من خلايا Mashru بطول `n` يقبلها القانون. -/
theorem qanun_qaida_eq_iff (mode : Bool) (r : Qayd Dal.Khaliya) (n : Nat) :
    lenCount (maan (alaMashru mode) r.ala) khalayaKull n (0, .awwal) = lawCount mode n ↔
      ∀ xs : List Dal.Khaliya, xs.length = n → (∀ a ∈ xs, a ∈ khalayaKull) →
        (alaMashru mode).final ((alaMashru mode).run 0 xs) = true → r.tasmah xs = true := by
  have hq : lawCount mode n = lenCount (alaMashru mode) khalayaKull n 0 := by
    rw [intrubiya_la_tataghayyar_bil_tamthil, lawCount_eq, lenCount_eq_spec]
  rw [hq, adad_maan_eq_iff]
  simp only [ala_iff]

end Jisr.TabaqatQawaid
