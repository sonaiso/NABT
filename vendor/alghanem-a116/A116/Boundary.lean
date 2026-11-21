import A116.Pause

/-!
# قانونُ الحدّ: الابتداءُ والوصلُ والوقف

الكلمةُ المرخَّصةُ (`Admissible`) نموذجُ **وصل**؛ وللحدّين قانونان من سيبويه:
**«لا يُبتدأ بساكن، ولا يُوقف على متحرّك»**. وهذه الوحدةُ تجعلهما مبرهناتٍ على الخانات، وتضيف
الوصلَ بين كلمتين وهمزةَ الوصل.

## السياق
`Entry = start | joined` و`Exit = continue | pause` — عينُ ما تحمله `gate.contextual.Context`.

## ما يُبرهَن

* `no_start_with_sukun`: المرخَّصُ لا يبدأ بساكن (الابتداء) — من تعريف `Admissible`.
* `pause_ends_with_sukun`: الوقفُ يُسكِّن الآخر، ووقفُ المرخَّص مرخَّصٌ وقفًا (`Pause.pause_admissible`).
* `join_iff`: وصلُ كلمتين مرخَّصتين مرخَّصٌ **إذا وفقط إذا** كان حدُّهما جائزًا: إن انتهت الأولى بساكنٍ
  فالثانية مرخَّصةٌ كما هي، وإن انتهت بمتحرّكٍ فيكفي ألّا يتجاور ساكنان في الثانية (`Junction.admissible_append`).
* `wasl_dropped_needs_moving_left`: همزةُ الوصل تسقط في الوصل، فتصير الكلمةُ مبدوءةً بساكن (لْحَمْدُ)،
  فلا تُرخَّص إلّا موصولةً بكلمةٍ **تنتهي بمتحرّك** — وهذا هو قانونُ همزة الوصل.
* `pause_then_join_is_not_join`: الوقفُ ثمّ الوصلُ ليس وصلًا: ما وُقف عليه بساكنٍ ثمّ وُصل بكلمةٍ تبدأ
  بساكن (بعد سقوط الوصل) غيرُ مرخَّص — فالقارئُ إمّا يقف وإمّا يصل.

ولا يُبرهَن هنا أنّ `gate.contextual.project` ينفّذ هذه المشغّلات بعينها؛ ذلك ما تفحصه المطابقة.
-/

namespace A116.Boundary

open A116 A116.Junction A116.Pause A116.Ladder

inductive Entry where | start | joined deriving DecidableEq, Repr
inductive Exit where | continue | pause deriving DecidableEq, Repr

/-- **الابتداء:** المرخَّصُ لا يبدأ بساكن. -/
theorem no_start_with_sukun {c : Cell} {w : List Cell} (h : Admissible (c :: w)) :
    c.isSukun = false := by
  obtain ⟨hhead, _⟩ := h
  simpa [HeadNotSukun] using hhead

/-- **الوقف:** مشغّلُ الوقف يُسكِّن الآخر، والناتجُ مرخَّصٌ وقفًا. -/
theorem pause_ends_with_sukun (v : List Cell) (c : Cell) (hv : v ≠ []) (h : Admissible (v ++ [c])) :
    (pause (v ++ [c])).getLast? = some ⟨c.carrier, .sukun⟩ ∧ PauseAdmissible (pause (v ++ [c])) := by
  refine ⟨?_, pause_admissible v c hv h⟩
  rw [pause_snoc]; simp

/-- **الوصل:** وصلُ ‎a‎ (المنتهية بـ‎c‎) بـ‎b‎ مرخَّصٌ ⇔ حدُّهما جائز. -/
theorem join_iff (a : List Cell) (c : Cell) (b : List Cell) (ha : Admissible (a ++ [c])) :
    Admissible ((a ++ [c]) ++ b) ↔ (if c.isSukun then Admissible b else NoAdjacentSukun b) :=
  admissible_append a c b ha

/-- إسقاطُ همزة الوصل: الخانةُ الأولى تسقط في الوصل. -/
def dropWasl : List Cell → List Cell
  | [] => []
  | _ :: t => t

/-- **همزةُ الوصل:** إن سقطت وبقيت الكلمةُ مبدوءةً بساكنٍ (لْحَمْدُ) فلا ترخيصَ لها إلّا موصولةً بما
ينتهي بمتحرّك. -/
theorem wasl_dropped_needs_moving_left (a : List Cell) (c : Cell) (h : Cell) (t : List Cell)
    (ha : Admissible (a ++ [c])) (hs : h.isSukun = true) (ht : NoAdjacentSukun (h :: t)) :
    Admissible ((a ++ [c]) ++ dropWasl (⟨h.carrier, .fatha⟩ :: h :: t)) ↔ c.isSukun = false := by
  simp only [dropWasl]
  rw [join_iff a c (h :: t) ha]
  constructor
  · intro hj
    cases hc : c.isSukun
    · rfl
    · rw [hc] at hj; simp only [↓reduceIte] at hj
      have := no_start_with_sukun hj; simp_all
  · intro hc; simp [hc, ht]

/-- **الوقفُ ثمّ الوصلُ ليس وصلًا:** ما وُقف عليه (ساكنُ الآخر) لا يُوصل بما سقطت وصلُه. -/
theorem pause_then_join_is_not_join (v : List Cell) (c : Cell) (h : Cell) (t : List Cell)
    (hs : h.isSukun = true) :
    ¬ Admissible (pause (v ++ [c]) ++ (h :: t)) := by
  rw [pause_snoc]
  intro hj
  have hpre : Admissible (v ++ [⟨c.carrier, .sukun⟩]) := admissible_prefix hj
  rw [join_iff v _ (h :: t) hpre] at hj
  simp only [Cell.isSukun, Haraka.isSukun, ↓reduceIte] at hj
  have := no_start_with_sukun hj
  simp_all

/-! ## أسماءُ الرفض وهمزةُ الوصل بحركتها (سجلُّ الرفض، ADR ٦)

* **`INITIAL_SUKUN_WITHOUT_REPAIR`**: الرفضُ الذي تُطلقه البوّابة حين تبدأ الكلمةُ بساكنٍ ابتداءً ولا إصلاحَ
  مسمًّى لها — هو «لا يُبتدأ بساكن» بعينه: `initialSukun` يصدق على كلمةٍ أوّلُها ساكن، ولا مرخَّصةَ كذلك
  (`initialSukun_not_admissible`، من `no_start_with_sukun`).
* **همزةُ الوصل بحركتها** (الكتاب س17530–17531: «الألف الموصولة … في الابتداء مكسورة أبدا إلا أن يكون
  الحرف الثالث مضموما فتضمها»؛ وس17573): `waslVowel` دالّةٌ في الثاني والثالث — فتحةٌ قبل لام «ال»،
  وضمّةٌ إن كان الثالثُ مضمومًا **في الفعل**، وإلّا كسرة (س17573: «مكسورة أبدا في الأسماء والأفعال إلا في
  الفعل المضموم الثالث» — فالأسماءُ الموصولة ابن/اسم/امرؤ/اثنان مكسورةٌ ولو ضُمّ ثالثُها، وأيمن مفتوحة؛
  قائمتُها المغلقة معلَنةٌ في `gate/residue.py` `WASL_NOUNS` لا هنا)؛ لا تكون سكونًا أبدًا (`waslVowel_ne_sukun`)، وضمُّها إذا
  وفقط إذا كان الثالثُ مضمومًا في غير «ال» (`waslVowel_damm_iff`) — مرآةُ `Slge.Sawabiq.wasl_state_damm_iff`
  في الغانم، ومرآتُها في البوّابة قاعدةُ الرسم `WASL` (`gate/residue.py`). و**ثبوتُ الضمّة** شرطُ الضمّ
  (س17570–17573: «ليست ضمة تثبت في هذا البناء على كل حال… لأن الضمة فيهن ثابتة»): ضمّةُ ثالثِ أمرِ الناقص
  اليائيّ قبل واو الجماعة عارضةٌ (اِمْشِ ← اِمْشُوا، اِقْضُوا، اِبْنُوا) فالهمزةُ مكسورة، والواويُّ ثابتةٌ (اُدْعُ ← اُدْعُوا)
  فمضمومة — `waslVowelStable` تأخذ الثبوتَ معاملًا لأنّه حكمٌ على البناء لا على الخانة: تقرّره البوّابةُ من فهرس
  الأفعال على جذور المقاييس (`gate.mabni_verbs.verb_index`) لا تخمينًا، وما لم يُقرَّر ثبوتُه كُتبت وصلتُه ساكنةً
  فرُفض. وما لا ثالثَ له أو كُتبت وصلتُه بسكونٍ صريح أو لم يُعلم ثبوتُ ضمّة ثالثه لا تُقرَّر حركتُه فيُرفض باسم
  `START_VOWEL_OF_WASL_IS_UNKNOWN`. -/

/-- كلمةٌ أوّلُها ساكن: ما يرفضه الجسرُ باسم `INITIAL_SUKUN_WITHOUT_REPAIR`. -/
def initialSukun : List Cell → Bool
  | c :: _ => c.isSukun
  | [] => false

theorem initialSukun_not_admissible {w : List Cell} (h : initialSukun w = true) : ¬ Admissible w := by
  intro ha
  cases w with
  | nil => simp [initialSukun] at h
  | cons c t =>
    simp only [initialSukun] at h
    exact absurd h (by simpa using no_start_with_sukun ha)

/-- حركةُ همزة الوصل من الثاني والثالث: فتحةٌ قبل اللام، وضمّةٌ إن ضُمّ الثالث، وإلّا كسرة. -/
def waslVowel (second third : Cell) : Haraka :=
  if second.carrier = carrierOf 'ل' then .fatha
  else if third.haraka = .damma then .damma else .kasra

theorem waslVowel_ne_sukun (s t : Cell) : waslVowel s t ≠ .sukun := by
  unfold waslVowel
  split
  · decide
  · split <;> decide

theorem waslVowel_damm_iff (s t : Cell) :
    waslVowel s t = .damma ↔ s.carrier ≠ carrierOf 'ل' ∧ t.haraka = .damma := by
  unfold waslVowel
  by_cases hl : s.carrier = carrierOf 'ل'
  · simp [hl]
  · by_cases hd : t.haraka = .damma
    · simp [hl, hd]
    · simp [hl, hd]

theorem waslVowel_lam (s t : Cell) (h : s.carrier = carrierOf 'ل') : waslVowel s t = .fatha := by
  simp [waslVowel, h]

/-- شواهد: اُكْتُبْ (ضمّ)، اِضْرِبْ (كسر)، اَلْحَمْدُ (فتح). -/
theorem waslVowel_witnesses :
    waslVowel (atom 'ك' .sukun) (atom 'ت' .damma) = .damma ∧
    waslVowel (atom 'ض' .sukun) (atom 'ر' .kasra) = .kasra ∧
    waslVowel (atom 'ل' .sukun) (atom 'ح' .fatha) = .fatha := by decide

/-- حركةُ همزة الوصل بشرط ثبوت الضمّة (س17570–17573): إن ثبتت ضمّةُ الثالث فالقاعدةُ `waslVowel`، وإلّا
فلا ضمَّ — فتحةٌ قبل اللام وكسرةٌ سواها. -/
def waslVowelStable (second third : Cell) (stable : Bool) : Haraka :=
  if stable then waslVowel second third
  else if second.carrier = carrierOf 'ل' then .fatha else .kasra

theorem waslVowelStable_true (s t : Cell) : waslVowelStable s t true = waslVowel s t := rfl

/-- الضمّةُ العارضة لا تضمّ الهمزةَ أبدًا. -/
theorem waslVowelStable_arid_ne_damma (s t : Cell) : waslVowelStable s t false ≠ .damma := by
  unfold waslVowelStable
  split
  · contradiction
  · split <;> decide

theorem waslVowelStable_ne_sukun (s t : Cell) (b : Bool) : waslVowelStable s t b ≠ .sukun := by
  unfold waslVowelStable
  split
  · exact waslVowel_ne_sukun s t
  · split <;> decide

/-- شاهدان: اِمْشُوا (ش مضمومةٌ عارضًا → كسر) واُدْعُوا (ع مضمومةٌ ثابتةً → ضمّ): الخانتان واحدةٌ شكلًا
والفرقُ في الثبوت وحدَه. -/
theorem waslVowelStable_witnesses :
    waslVowelStable (atom 'م' .sukun) (atom 'ش' .damma) false = .kasra ∧
    waslVowelStable (atom 'د' .sukun) (atom 'ع' .damma) true = .damma := by decide

end A116.Boundary
