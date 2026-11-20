import A116.Iqtiran
import A116.Malumat
import A116.NaqlData

/-!
# شهادةُ أصحاب المعاجم: مفهومُ الوضع برتبة شهادته (ADR ١٠٠، ١٠٤)

أمرُ المالك (2026-10-17): «بناء المعجم مع lean دالة الوضع سيبني شبكة مفاهيم معجمية بشهادة بشريه من صاحب المعجم
المقاييس او ابن منظور او لدالفراهيدي فجميع شهاداتهم مقبولة وكذلك معاجمهم مقبولة والشهادات تعاضد بعضها وهذا هو النقل
الذي تعرف بها اللغة راجع النبهاني نفذ ابني مفاهيم من معاني الألفاظ وفق الوضع وشهادة البشر أصحاب المعاجم».

وقرارُه (2026-10-18، ADR ١٠٤): «النقل عن الوضع ليس بالضرورة تويتر»، و«نقبلها شاهد برتبة الشهادة فليس كل رتبة تشترط
التواتر وليس المطلوب التواتر لكل لفظ وضع لمعنى». فعُدّلت المادّتان ١٥ و١٦ من الدستور بنصّه.

## السند: ج3 المختوم س367 (الأسطرُ 1-based في `corpora/nabhani/shakhsiyya_j3.txt.gz`)

* الواضعُ العرب: «اللغة العربية اصطلاح اصطلح عليه العرب»، و«فإذا قالوا هم إن لفظ كذا موضوع لمعنى كذا… فيقبل قولهم،
  ويسلم به».
* والطريقُ إليهم طريقان، كلاهما طريق: «ومن هنا كانت طريق معرفة اللغة العربية هي النقل المتواتر وخبر الآحاد».
* «فالنقل المتواتر هو ما كان معلوماً بحيث لا يتشكك فيه مع التشكيك»، والآحادُ «فطريق تحصيل الظن به إنما هو أخبار الآحاد،
  أي نقل الآحاد، كالألفاظ المروية المعنعنة عن الأدباء الباحثين عن اللغة، كالخليل».
* «وأما العقل فلا ينفع في معرفة اللغة العربية، ولا قيمة له».

## ما يُبنى: الجسرُ المعمَّم بشرط كفايةٍ ورتبة

`jisr q kafi tawatur ws`: الطرقُ المقبولة `q`، وشرطُ الكفاية `kafi`، وحكمُ التواتر `tawatur`.
* لا شهادةَ مقبولة: «معلومة» بلا شاهد.
* مقبولةٌ لا تكفي: «معلومةٌ مشهودة» تحمل شهاداتِها.
* مقبولةٌ تكفي: «مفهوم» برتبته — قطعيٌّ بالتواتر وظنّيٌّ بالآحاد — والمُنشئ يحمل شاهدًا بالنوع (المادّة ١٦).

والجسران مثولان له:
* `jisrWaqi`: الحسُّ من الواقع المختوم، والواحدُ يكفي، قطعيّ. هو `Iqtiran.martaba` بعد الإسقاط، على المعيَّن.
* `jisrWad t`: النقلُ من مودَع «وضع» أو «معلومات سابقة»، والواحدُ يكفي (`wahid_yakfi`)، ورتبتُه ظنّيّةٌ إلّا بحكم تواتر
  (`qati_bi_tawatur`، `kathra_la_tuwatir`). والمرجعُ المحجوب ليس شاهدًا (`marja_la_yashhad`، المادّة ١٢).

وهذا مفهومُ **الوضع**، لا وجودِ المسمّى: النقلُ لا يشهد للمسمّى (`naql_la_yashhad_lilmusamma`).
-/

namespace A116.Naql

/-! ## ١. الشهادة والحكمُ بشاهده ورتبته -/

/-- طريقُ المعرفة: النقلُ (روايةٌ عن الواضع)، والحسُّ (واقعٌ مودَع)، والعقل. -/
inductive Tariq | naql | hiss | aql
  deriving DecidableEq, Repr

/-- نوعُ المودَع (المادّة ١٢): واقعٌ مختوم، ووضع، ومعلوماتٌ سابقة، ومرجعٌ محجوب. -/
inductive Mawda | waqiMakhtum | wad | malumat | marjaMahjub
  deriving DecidableEq, Repr

/-- الشهادة: راويها (المعجم)، وقائلُها، وطريقُها، ونوعُ مودَعها، وسطرُها في المودَع. -/
structure Shahada where
  rawi : String
  qail : String
  tariq : Tariq
  mawda : Mawda
  satr : Nat
  deriving DecidableEq, Repr

abbrev Rutba := Malumat.Martaba

/-- الحكم: «من حيث هي»، أو «معلومة» بشهاداتها، أو «مفهوم» برتبته وشاهدٍ وقائمةٍ بعده. -/
inductive Hukm | minHaythuHiya | maluma (shuhud : List Shahada)
  | mafhum (r : Rutba) (s : Shahada) (ss : List Shahada)
  deriving DecidableEq, Repr

/-- الشهاداتُ التي يقبلها الجسر. -/
def maqbul (q : Tariq → Bool) (ws : List Shahada) : List Shahada := ws.filter (fun s => q s.tariq)

/-- **الجسرُ المعمَّم**: المقبولُ الكافي مفهومٌ برتبته، والمقبولُ غيرُ الكافي معلومةٌ تحمله، ولا مقبولَ فمعلومةٌ بلا شاهد. -/
def jisr (q : Tariq → Bool) (kafi tawatur : List Shahada → Bool) (ws : List Shahada) : Hukm :=
  match maqbul q ws with
  | [] => .maluma []
  | s :: ss =>
    if kafi (s :: ss) then .mafhum (if tawatur (s :: ss) then .qati else .zanni) s ss
    else .maluma (s :: ss)

def wad (t : Tariq) : Bool := t == .naql
def waqi (t : Tariq) : Bool := t == .hiss

/-- كفايةُ النقل (المادّة ١٥ معدَّلةً): كلُّ الشهود من مودَع «وضع» أو «معلومات سابقة». -/
def kafiNaql (ss : List Shahada) : Bool :=
  ss.all (fun s => s.mawda == .wad || s.mawda == .malumat)

/-- جسرُ الوضع: النقلُ، ويكفي بـ`kafiNaql`، ورتبتُه بحكم التواتر `t`. -/
def jisrWad (t : List Shahada → Bool) : List Shahada → Hukm := jisr wad kafiNaql t
/-- جسرُ المسمّى: الحسُّ من الواقع المختوم، والواحدُ يكفي، قطعيّ (المادّة ١٥: «محسوس»). -/
def jisrWaqi : List Shahada → Hukm :=
  jisr waqi (fun ss => ss.all (fun s => s.mawda == .waqiMakhtum)) (fun _ => true)

/-- **لا مفهومَ بلا شاهد** (المادّة ١٦): شاهدُ المفهوم من الشهادات، وطريقُه مقبول، والكفايةُ قائمة. -/
theorem mafhum_bishahid (q : Tariq → Bool) (k t : List Shahada → Bool) (ws : List Shahada) (r : Rutba)
    (s : Shahada) (ss : List Shahada) (h : jisr q k t ws = .mafhum r s ss) :
    s ∈ ws ∧ q s.tariq = true ∧ k (s :: ss) = true := by
  unfold jisr at h
  split at h
  · cases h
  · rename_i s' ss' hm
    cases hk : k (s' :: ss') <;> simp [hk] at h
    obtain ⟨_, rfl, rfl⟩ := h
    have hs : s' ∈ maqbul q ws := by rw [hm]; exact List.mem_cons_self
    exact ⟨(List.mem_filter.mp hs).1, (List.mem_filter.mp hs).2, hk⟩

/-- **المعلومةُ لا تُسقط شاهدًا**: ما لم يكفِ فالمعلومةُ تحمل المقبولَ كلَّه بعينه. -/
theorem maluma_tahmil (q : Tariq → Bool) (k t : List Shahada → Bool) (ws : List Shahada)
    (vs : List Shahada) (h : jisr q k t ws = .maluma vs) : vs = maqbul q ws := by
  unfold jisr at h
  split at h
  · rename_i hm; cases h; exact hm.symm
  · rename_i s ss hm
    cases hk : k (s :: ss) <;> simp [hk] at h
    rw [hm, h]

/-- **لا شاهدَ مقبولًا ⟺ معلومةٌ بلا شاهد**. -/
theorem bila_shahid_iff (q : Tariq → Bool) (k t : List Shahada → Bool) (ws : List Shahada) :
    jisr q k t ws = .maluma [] ↔ ∀ s ∈ ws, q s.tariq = false := by
  constructor
  · intro h s hs
    have hv := maluma_tahmil q k t ws [] h
    cases hq : q s.tariq
    · rfl
    · have : s ∈ maqbul q ws := List.mem_filter.mpr ⟨hs, hq⟩
      rw [← hv] at this; cases this
  · intro h
    have : maqbul q ws = [] := List.filter_eq_nil_iff.mpr (fun s hs => by simp [h s hs])
    simp [jisr, this]

/-- **العقلُ لا يشهد** (ج3 س367 «فلا ينفع … ولا قيمة له»): شهادةٌ لا يقبل الجسرُ طريقَها لا تغيّر الحكم. -/
theorem ghayr_maqbul_la_yughayyir (q : Tariq → Bool) (k t : List Shahada → Bool) (ws : List Shahada)
    (s : Shahada) (h : q s.tariq = false) : jisr q k t (ws ++ [s]) = jisr q k t ws := by
  have : maqbul q (ws ++ [s]) = maqbul q ws := by simp [maqbul, List.filter_append, h]
  unfold jisr; rw [this]

theorem aql_la_yashhad (t : List Shahada → Bool) (ws : List Shahada) (s : Shahada)
    (h : s.tariq = .aql) :
    jisrWad t (ws ++ [s]) = jisrWad t ws ∧ jisrWaqi (ws ++ [s]) = jisrWaqi ws :=
  ⟨ghayr_maqbul_la_yughayyir _ _ _ _ _ (by simp [wad, h]),
   ghayr_maqbul_la_yughayyir _ _ _ _ _ (by simp [waqi, h])⟩

/-- **الواحدُ يكفي** («فيقبل قولهم»؛ و«خبر الآحاد» طريقٌ، ج3 س367): شهادةُ نقلٍ واحدة من مودَع «وضع» بلا تواترٍ
مفهومُ وضعٍ ظنّيّ. -/
theorem wahid_yakfi (s : Shahada) (hs : s.tariq = .naql) (hm : s.mawda = .wad) :
    jisrWad (fun _ => false) [s] = .mafhum .zanni s [] := by
  simp [jisrWad, jisr, maqbul, wad, kafiNaql, hs, hm]

/-- **القطعيُّ بالتواتر وحدَه**. -/
theorem qati_bi_tawatur (t : List Shahada → Bool) (ws : List Shahada) (s : Shahada) (ss : List Shahada)
    (h : jisrWad t ws = .mafhum .qati s ss) : t (s :: ss) = true := by
  unfold jisrWad jisr at h
  split at h
  · cases h
  · rename_i s' ss' _
    cases hk : kafiNaql (s' :: ss') <;> cases ht : t (s' :: ss') <;> simp [hk, ht] at h
    obtain ⟨rfl, rfl⟩ := h; exact ht

/-- **الكثرةُ لا تُواتِر**: بلا حكم تواترٍ فالمفهومُ ظنّيٌّ ولو كثرت شهاداتُه (التواترُ «لا يتشكك فيه»، لا عدد). -/
theorem kathra_la_tuwatir (ws : List Shahada) (r : Rutba) (s : Shahada) (ss : List Shahada)
    (h : jisrWad (fun _ => false) ws = .mafhum r s ss) : r = .zanni := by
  unfold jisrWad jisr at h
  split at h
  · cases h
  · rename_i s' ss' _
    cases hk : kafiNaql (s' :: ss') <;> simp [hk] at h
    exact h.1.symm

/-- **المرجعُ المحجوب لا يشهد للوضع** (المادّة ١٢: «ولا يُستعمل أحدُهما في موضع الآخر»). -/
theorem marja_la_yashhad (t : List Shahada → Bool) (ws : List Shahada) (x : Shahada)
    (hx : x ∈ ws) (hn : x.tariq = .naql) (hm : x.mawda = .marjaMahjub) (r : Rutba) (s : Shahada)
    (ss : List Shahada) : jisrWad t ws ≠ .mafhum r s ss := by
  intro h
  unfold jisrWad jisr at h
  split at h
  · cases h
  · rename_i s' ss' hmq
    have hxm : x ∈ s' :: ss' := by rw [← hmq]; exact List.mem_filter.mpr ⟨hx, by simp [wad, hn]⟩
    have hk : kafiNaql (s' :: ss') = false := by
      simp only [kafiNaql, List.all_eq_false]
      exact ⟨x, hxm, by simp [hm]⟩
    simp [hk] at h

/-- **والمحسوسُ يكفي بواحد**: شهادةُ حسٍّ واحدة من الواقع المختوم مفهومٌ قطعيٌّ على جسر المسمّى. -/
theorem hiss_yakfi (s : Shahada) (hs : s.tariq = .hiss) (hm : s.mawda = .waqiMakhtum) :
    jisrWaqi [s] = .mafhum .qati s [] := by
  simp [jisrWaqi, jisr, maqbul, waqi, hs, hm]

/-- **النقلُ لا يشهد للمسمّى** (بتعريف `waqi`): شهاداتٌ كلُّها نقلٌ تُبقي وجودَ المسمّى «معلومة» بلا شاهد. -/
theorem naql_la_yashhad_lilmusamma (ws : List Shahada) (h : ∀ s ∈ ws, s.tariq = .naql) :
    jisrWaqi ws = .maluma [] :=
  (bila_shahid_iff waqi _ _ ws).mpr (fun s hs => by simp [waqi, h s hs])

/-! ## ٢. التعاضد: قوّةُ الشهادة عددُ القائلين المستقلّين -/

/-- القوّة: عددُ القائلين من قائمةٍ معلومة (`shuyukh`) الذين في الشهادات المقبولة. -/
def quwwa (shuyukh : List String) (q : Tariq → Bool) (ws : List Shahada) : Nat :=
  (shuyukh.filter (fun a => (maqbul q ws).any (fun s => s.qail == a))).length

theorem filter_length_mono {α : Type} (l : List α) (p p' : α → Bool)
    (h : ∀ a, p a = true → p' a = true) : (l.filter p).length ≤ (l.filter p').length := by
  induction l with
  | nil => simp
  | cons a l ih =>
    cases hp : p a <;> cases hp' : p' a <;> simp [hp, hp'] <;> try omega
    exact absurd (h a hp) (by simp [hp'])

/-- **التعاضد**: شهادةٌ تُضاف لا تُنقص القوّة. -/
theorem taadud (sh : List String) (q : Tariq → Bool) (ws vs : List Shahada) :
    quwwa sh q ws ≤ quwwa sh q (ws ++ vs) := by
  unfold quwwa
  apply filter_length_mono
  intro a ha
  simp only [maqbul, List.filter_append, List.any_append, Bool.or_eq_true]
  exact Or.inl ha

/-- **نقلُ الواحد عن الواحد شاهدٌ واحد** («المعنعنة»): شهادةٌ قائلُها مشهودٌ من قبلُ لا تزيد القوّة. -/
theorem naql_an_wahid (sh : List String) (q : Tariq → Bool) (ws : List Shahada) (s : Shahada)
    (h : (maqbul q ws).any (fun x => x.qail == s.qail) = true) :
    quwwa sh q (ws ++ [s]) = quwwa sh q ws := by
  unfold quwwa
  congr 1
  apply List.filter_congr
  intro a _
  simp only [maqbul, List.filter_append, List.any_append]
  cases hq : q s.tariq <;> simp [hq]
  intro he
  subst he
  simpa [maqbul] using h

theorem filter_length_lt {α : Type} (l : List α) (p p' : α → Bool) (a : α) (hl : a ∈ l)
    (h : ∀ x, p x = true → p' x = true) (ha : p a = false) (ha' : p' a = true) :
    (l.filter p).length < (l.filter p').length := by
  induction l with
  | nil => cases hl
  | cons b l ih =>
    have mono := filter_length_mono l p p' h
    rcases List.mem_cons.mp hl with rfl | hl
    · simp [ha, ha']; omega
    · have := ih hl
      cases hp : p b <;> cases hp' : p' b <;> simp [hp, hp'] <;> try omega
      exact absurd (h b hp) (by simp [hp'])

/-- **القائلُ المستقلّ يزيد**: شهادةٌ مقبولةٌ قائلُها في القائمة ولم يُشهد من قبلُ تزيد القوّة. ولا يُحدّ قدرُ الزيادة
هنا: إن تكرّر اسمُه في القائمة زاد بعدد تكراره. -/
theorem mustaqill_yazid (sh : List String) (q : Tariq → Bool) (ws : List Shahada) (s : Shahada)
    (hq : q s.tariq = true) (hin : s.qail ∈ sh)
    (hnew : (maqbul q ws).any (fun x => x.qail == s.qail) = false) :
    quwwa sh q ws < quwwa sh q (ws ++ [s]) := by
  unfold quwwa
  apply filter_length_lt sh _ _ s.qail hin
  · intro a ha
    simp only [maqbul, List.filter_append, List.any_append, Bool.or_eq_true]
    exact Or.inl ha
  · exact hnew
  · simp [maqbul, List.filter_append, hq]

/-! ## ٣. النمطُ المعمَّم يحوي `Iqtiran.martaba` -/

/-- الإسقاطُ إلى المراتب الثلاث: يُسقط الشهادات. -/
def ilaMartaba : Hukm → Iqtiran.Martaba
  | .minHaythuHiya => .minHaythuHiya
  | .maluma _ => .maluma
  | .mafhum .. => .mafhum

/-- الجسرُ على المنطوق الثلاثيّ: للمعيَّن شهاداتُه، والمحتمَلُ معلومة، و«لا حكم» من حيث هي. -/
def jisrM {M : Type} (q : Tariq → Bool) (k t : List Shahada → Bool) (shuhud : M → List Shahada) :
    Iqtiran.Mantuq M → Hukm
  | .muayyan m => jisr q k t (shuhud m)
  | .muhtamal _ => .maluma []
  | .laHukm => .minHaythuHiya

/-- **`Iqtiran.martaba` مثولٌ للنمط**: بعد الإسقاط، شاهدُ الواقع الثنائيّ هو شهادةُ حسٍّ واحدة على جسر المسمّى.
والمساواةُ عملٌ على المعيَّن وحدَه؛ المحتمَلُ و«لا حكم» منسوخان بالتعريف. -/
theorem iqtiran_mithal {M : Type} (s : M → Bool) (w : Shahada) (hw : w.tariq = .hiss)
    (hm : w.mawda = .waqiMakhtum) (x : Iqtiran.Mantuq M) :
    Iqtiran.martaba s x =
      ilaMartaba (jisrM waqi (fun ss => ss.all (fun v => v.mawda == .waqiMakhtum)) (fun _ => true)
        (fun m => if s m then [w] else []) x) := by
  cases x with
  | muayyan m =>
    cases hs : s m <;> simp [Iqtiran.martaba, jisrM, jisr, maqbul, waqi, hs, hw, hm, ilaMartaba]
  | muhtamal _ => rfl
  | laHukm => rfl

/-! ## ٤. أصلُ ابن فارس: معنى اللفظ بشهادته -/

/-- حكمُ ابن فارس على الجذر (`RULE_ASL` في `tools/gen_naql.py`). -/
inductive Asl | wahid | usul (n : Nat) | kalima | laysa | laHukm
  deriving DecidableEq, Repr

def Asl.ofString : String → Nat → Asl
  | "wahid", _ => .wahid
  | "usul", n => .usul n
  | "kalima", _ => .kalima
  | "laysa", _ => .laysa
  | _, _ => .laHukm

/-- معنى لفظٍ من الجذر: الأصلُ الواحدُ أو الكلمةُ معيَّن، والأصولُ محتمَلةٌ بأرقامها، وما سواهما لا حكم. -/
def nisba (a : Asl) (jumla : String) : Iqtiran.Mantuq (String × Nat) :=
  match a with
  | .wahid | .kalima => .muayyan (jumla, 1)
  | .usul n => Iqtiran.mantuq ((List.range n).map (fun i => (jumla, i + 1)))
  | .laysa | .laHukm => .laHukm

/-- **لا تخمين**: معنى اللفظ يتعيّن بحكم ابن فارس على أصلٍ واحدٍ أو كلمةٍ واحدة، أو بأصولٍ عددُها واحد. -/
theorem la_takhmin_asl (a : Asl) (j : String) (m : String × Nat) (h : nisba a j = .muayyan m) :
    a = .wahid ∨ a = .kalima ∨ a = .usul 1 := by
  cases a with
  | wahid => exact Or.inl rfl
  | kalima => exact Or.inr (Or.inl rfl)
  | usul n =>
    refine Or.inr (Or.inr ?_)
    have hl := Iqtiran.la_takhmin _ m h
    have : ((List.range n).map (fun i => (j, i + 1))).length = 1 := by rw [hl]; rfl
    simp at this; rw [this]
  | laysa => cases h
  | laHukm => cases h

/-- **الأصولُ تحتمل**: أصلان فأكثر لا يتعيّن معهما معنى اللفظ. -/
theorem usul_muhtamal (n : Nat) (hn : 2 ≤ n) (j : String) (m : String × Nat) :
    nisba (.usul n) j ≠ .muayyan m := by
  intro h
  rcases la_takhmin_asl _ j m h with h | h | h <;> cases h
  omega

/-! ## ٥. المودَع: العين والمقاييس واللسان -/

/-- القائلون المعلومون: الخليل، وابنُ فارس، وابنُ منظور. -/
def shuyukh : List String := ["khalil", "ibn-faris", "ibn-manzur"]

/-- شاهدُ الصفّ شهادةُ نقلٍ من مودَع «وضع»: (المعجم، القائل، سطرُ المدخل). -/
def shahadaOf (w : String × String × Nat) : Shahada := ⟨w.1, w.2.1, .naql, .wad, w.2.2⟩

/-- مجموعُ الأزواج بعدد الشهود وبعدد المعاجم واحد، ومجموعُ أحكام ابن فارس عددُ الجذور. -/
theorem mawdu_count :
    NaqlData.biShuhud.foldl (· + ·) 0 = NaqlData.zawjCount ∧
    NaqlData.biMaajim.foldl (· + ·) 0 = NaqlData.zawjCount ∧
    NaqlData.hukmAsl.foldl (· + ·) 0 = NaqlData.jidhrCount ∧
    NaqlData.zawjCount = 108735 ∧ NaqlData.naqlAnWahid = 645 := by decide

/-- **على الشواهد** (`decide` على صفوف خمسة جذور): ورودُ كلّ لفظٍ تحت جذره مفهومُ وضعٍ ظنّيٌّ بشهادته (بلا حكم تواتر)،
وقوّتُه اثنان فأكثر، ووجودُ المسمّى «معلومة» بلا شاهد. -/
theorem shawahid_mafhum :
    NaqlData.shawahid.all (fun r =>
      let ws := r.2.2.2.map shahadaOf
      (match jisrWad (fun _ => false) ws with | .mafhum .zanni _ _ => true | _ => false) &&
      2 ≤ quwwa shuyukh wad ws &&
      jisrWaqi ws == .maluma []) = true := by decide +kernel

/-- **ورودُ «الكتاب» تحت «كتب»**: الخليلُ وابنُ فارس وابنُ منظور، كلٌّ في مدخله؛ والقاعدةُ تجعل «كتب» أصلًا واحدًا. -/
theorem kataba :
    ("كتب", "الكتاب", "kfm", [("k", "khalil", 30475), ("f", "ibn-faris", 3334), ("m", "ibn-manzur", 23989)])
      ∈ NaqlData.shawahid ∧
    (NaqlData.uslShawahid.find? (·.1 == "كتب")).map (fun u => Asl.ofString u.2.1 u.2.2.1) = some .wahid := by
  decide +kernel

def kitab : List Shahada :=
  [⟨"k", "khalil", .naql, .wad, 30475⟩, ⟨"f", "ibn-faris", .naql, .wad, 3334⟩,
   ⟨"m", "ibn-manzur", .naql, .wad, 23989⟩]

/-- **«الكتاب» برتبة شهادته**: مفهومُ وضعٍ ظنّيٌّ بثلاثة قائلين؛ ولو حكم المالكُ بمعيار تواترٍ «ثلاثةُ قائلين» لصار
قطعيًّا — والمعيارُ هنا فرضٌ يُري الرتبة، لا قرار. ووجودُ المسمّى معلومةٌ بلا شاهد. -/
theorem kitab_hukm :
    jisrWad (fun _ => false) kitab =
      .mafhum .zanni ⟨"k", "khalil", .naql, .wad, 30475⟩
        [⟨"f", "ibn-faris", .naql, .wad, 3334⟩, ⟨"m", "ibn-manzur", .naql, .wad, 23989⟩] ∧
    quwwa shuyukh wad kitab = 3 ∧
    jisrWad (fun ws => decide (3 ≤ quwwa shuyukh wad ws)) kitab =
      .mafhum .qati ⟨"k", "khalil", .naql, .wad, 30475⟩
        [⟨"f", "ibn-faris", .naql, .wad, 3334⟩, ⟨"m", "ibn-manzur", .naql, .wad, 23989⟩] ∧
    jisrWaqi kitab = .maluma [] := by decide

/-! ## المراسي -/

def marasi : List (String × Nat × String) :=
  [("j3", 367, "اللغة العربية اصطلاح اصطلح عليه العرب"),
   ("j3", 367, "فإذا قالوا هم إن لفظ كذا موضوع لمعنى كذا"),
   ("j3", 367, "فيقبل قولهم، ويسلم به"),
   ("j3", 367, "ومن هنا كانت طريق معرفة اللغة العربية هي النقل المتواتر وخبر الآحاد"),
   ("j3", 367, "كالألفاظ المروية المعنعنة عن الأدباء الباحثين عن اللغة، كالخليل"),
   ("j3", 367, "فالنقل المتواتر هو ما كان معلوماً بحيث لا يتشكك فيه مع التشكيك"),
   ("j3", 367, "وأما العقل فلا ينفع في معرفة اللغة العربية، ولا قيمة له")]

end A116.Naql
