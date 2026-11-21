/-!
# السلسلةُ كلمةً كلمة: لكلّ كلمةٍ حكمٌ ثلاثيٌّ في كلّ طبقة (ADR ١١٤، المهمّة ٣ من `docs/protocol/khitta.md`)

نصُّ الخطّة (STEP-0004): «ربطُ السلسلة كلمةً كلمة: الشهادة ← القسم ← الصيغة والجنس ← الحمل ← الحكم الثلاثيّ»، وشرطُ
قبولها «مبرهنةُ شمول (لكلّ كلمةٍ حكمٌ أو «لا حكم» باسمه)».

والمادّة ٢٣: «١٠٠٪» تغطيةُ حكمٍ لا إصابة — لكلّ وحدةٍ حكمٌ ثلاثيّ (معيَّن، أو محتمَلٌ بقائمته، أو «لا حكم» باسمه) في كلّ
طبقة. فهذه الوحدة تبني ذلك مبرهنًا:

* `Hal`: الحكمُ الثلاثيّ، و«لا حكم» يحمل سببَه من قائمةٍ مغلقة (`Sabab`): رفضٌ باسمه، أو سقوطُ ما دونه، أو لا قارئ،
  أو خارجُ مجال القارئ.
* `Tabaqa`: قارئٌ يرى الكلمةَ وحكمَ الطبقة التي دونه، أو لا قارئ (طبقةٌ لم تُكتب بعد).
* `silsila`: لكلّ كلمةٍ أحكامُها طبقةً طبقة، وما سقط في طبقةٍ سقط فيما فوقها باسم `dunaha` ولا يُستدعى قارئُه.

ما يُبرهن (لكلّ كلمةٍ وطبقات): لكلّ كلمةٍ حكمٌ في كلّ طبقة (`ahkam_length`، و`shumul` لطبقاتٍ واحدة لكلّ الكلمات)؛
وسريانُ السقوط صعودًا؛ والقمعُ لكلّ كلمةٍ وعددًا على الكلمات. وتعريفيّاتٌ: لا تعيينَ بلا قارئ، وما عيّنته طبقةٌ فقارئُها
عيّنه. والقرّاءُ أنفسُهم خارجَ هذه الوحدة (`tools/gen_silsila.py`)، وقد يرى القارئُ سياقَ الكلمة: فالأداةُ تبني لكلّ كلمةٍ
طبقاتِها، وما ينطبق عليها `ahkam_length` و`suqut_ba3d` و`qam` لكلّ كلمة.
-/

namespace A116.Silsila

/-- سببُ «لا حكم»: رفضٌ مسمًّى من القارئ، أو سقوطُ الطبقة التي دونه، أو لا قارئَ لهذه الطبقة (طبقةٌ لم تُكتب بعد)،
أو قارئٌ موجودٌ والكلمةُ خارج مجاله (`kharij`: قارئُ أفعالٍ والقسمُ لا فعلَ فيه). -/
inductive Sabab
  | rafd (ism : String)
  | dunaha
  | laQari
  | kharij
  deriving DecidableEq, Repr

/-- الحكمُ الثلاثيّ في طبقة. -/
inductive Hal
  | muayyan (v : String)
  | muhtamal (vs : List String)
  | laHukm (s : Sabab)
  deriving DecidableEq, Repr

def Hal.saqit : Hal → Bool
  | .laHukm _ => true
  | _ => false

/-- طبقةٌ: اسمُها وقارئُها (الكلمةُ وحكمُ ما دونها ← حكمها)، أو لا قارئ. -/
structure Tabaqa where
  ism : String
  qari : Option (String → Hal → Hal)

/-- خطوةُ الطبقة: ما سقط دونها سقط فيها باسم `dunaha`، وبلا قارئ «لا حكم» باسم `laQari`، وإلّا فحكمُ قارئها. -/
def khutwa (w : String) (dun : Hal) (t : Tabaqa) : Hal :=
  if dun.saqit then .laHukm .dunaha
  else match t.qari with
    | none => .laHukm .laQari
    | some q => q w dun

/-- أحكامُ كلمةٍ طبقةً طبقة، والطبقةُ الأولى ترى `asl` حكمًا لما دونها. -/
def ahkam (w : String) (asl : Hal) : List Tabaqa → List Hal
  | [] => []
  | t :: ts => let h := khutwa w asl t; h :: ahkam w h ts

/-- السلسلة: لكلّ كلمةٍ أحكامُها، والأصلُ معيَّنٌ بالكلمة نفسها. -/
def silsila (ts : List Tabaqa) (ws : List String) : List (List Hal) :=
  ws.map (fun w => ahkam w (.muayyan w) ts)

/-- طولُ أحكام الكلمة عددُ الطبقات. -/
theorem ahkam_length (w : String) (a : Hal) (ts : List Tabaqa) : (ahkam w a ts).length = ts.length := by
  induction ts generalizing a with
  | nil => rfl
  | cons t ts ih => simp [ahkam, ih]

/-- **الشمول** (شرطُ قبول المهمّة ٣، والمادّة ٢٣): لكلّ كلمةٍ صفُّ أحكام، ولكلّ طبقةٍ حكم. لكلّ طبقاتٍ وكلمات. -/
theorem shumul (ts : List Tabaqa) (ws : List String) :
    (silsila ts ws).length = ws.length ∧ ∀ hs ∈ silsila ts ws, hs.length = ts.length := by
  refine ⟨by simp [silsila], ?_⟩
  intro hs h
  simp only [silsila, List.mem_map] at h
  obtain ⟨w, _, rfl⟩ := h
  exact ahkam_length _ _ _

/-- **كلُّ حكمٍ واحدٌ من ثلاثة، و«لا حكم» باسمه**. تعريفيّ (من النوع). -/
theorem thulathi (h : Hal) :
    (∃ v, h = .muayyan v) ∨ (∃ vs, h = .muhtamal vs) ∨ (∃ s, h = .laHukm s) := by
  cases h with
  | muayyan v => exact .inl ⟨v, rfl⟩
  | muhtamal vs => exact .inr (.inl ⟨vs, rfl⟩)
  | laHukm s => exact .inr (.inr ⟨s, rfl⟩)

/-- **ما سقط دون طبقةٍ سقط فيها وفيما فوقها كلِّه باسم `dunaha`**. لكلّ طبقات. -/
theorem suqut_yasri (w : String) (s : Sabab) (ts : List Tabaqa) :
    ∀ h ∈ ahkam w (.laHukm s) ts, h = .laHukm .dunaha := by
  induction ts generalizing s with
  | nil => simp [ahkam]
  | cons t ts ih =>
    intro h hm
    simp only [ahkam, khutwa, Hal.saqit, ite_true, List.mem_cons] at hm
    rcases hm with rfl | hm
    · rfl
    · exact ih .dunaha h hm

/-- **ما دون الطبقة يحكم ما فوقها**: إن سقطت الطبقة k فكلُّ ما بعدها `dunaha`. لكلّ كلمةٍ وطبقات. -/
theorem suqut_ba3d (w : String) (a : Hal) (ts : List Tabaqa) (k : Nat) (s : Sabab)
    (hk : (ahkam w a ts)[k]? = some (.laHukm s)) :
    ∀ j, k < j → ∀ h, (ahkam w a ts)[j]? = some h → h = .laHukm .dunaha := by
  induction ts generalizing a k with
  | nil => simp [ahkam] at hk
  | cons t ts ih =>
    intro j hj h hh
    cases k with
    | zero =>
      simp only [ahkam, List.getElem?_cons_zero, Option.some.injEq] at hk
      cases j with
      | zero => omega
      | succ j =>
        simp only [ahkam, List.getElem?_cons_succ] at hh
        rw [hk] at hh
        exact suqut_yasri w s ts h (List.mem_of_getElem? hh)
    | succ k =>
      cases j with
      | zero => omega
      | succ j =>
        simp only [ahkam, List.getElem?_cons_succ] at hk hh
        exact ih _ k hk j (by omega) h hh

/-- **لا تعيينَ بلا قارئ**: طبقةٌ بلا قارئٍ حكمُها «لا حكم» لكلّ كلمةٍ وما دونها. لكلّ مدخل. -/
theorem la_tayin_bila_qari (w : String) (dun : Hal) (n : String) :
    ∃ s, khutwa w dun ⟨n, none⟩ = .laHukm s := by
  unfold khutwa
  split <;> exact ⟨_, rfl⟩

/-- **ما عيّنته طبقةٌ فقارئُها عيّنه، وما دونها لم يسقط**. لكلّ مدخل. -/
theorem muayyan_min_qari (w : String) (dun : Hal) (t : Tabaqa) (v : String)
    (h : khutwa w dun t = .muayyan v) :
    dun.saqit = false ∧ ∃ q, t.qari = some q ∧ q w dun = .muayyan v := by
  unfold khutwa at h
  split at h
  · cases h
  · rename_i hs
    refine ⟨by simpa using hs, ?_⟩
    cases hq : t.qari with
    | none => rw [hq] at h; cases h
    | some q => rw [hq] at h; exact ⟨q, rfl, h⟩

/-- **طبقةٌ بلا قارئٍ «لا حكم» في موضعها من كلّ سلسلة**: إن كانت الطبقةُ k بلا قارئ فحكمُ كلّ كلمةٍ فيها «لا حكم» (`laQari`
أو `dunaha`). لكلّ كلمةٍ وأصلٍ وطبقات. -/
theorem la_hukm_fi_mawdi (w : String) (a : Hal) (ts : List Tabaqa) (k : Nat) (t : Tabaqa)
    (ht : ts[k]? = some t) (hq : t.qari = none) :
    ∃ s, (ahkam w a ts)[k]? = some (.laHukm s) := by
  induction ts generalizing a k with
  | nil => simp at ht
  | cons t0 ts ih =>
    cases k with
    | zero =>
      simp only [List.getElem?_cons_zero, Option.some.injEq] at ht
      subst ht
      simp only [ahkam, List.getElem?_cons_zero, Option.some.injEq]
      unfold khutwa
      split
      · exact ⟨_, rfl⟩
      · rw [hq]; exact ⟨_, rfl⟩
    | succ k =>
      simp only [List.getElem?_cons_succ] at ht
      simp only [ahkam, List.getElem?_cons_succ]
      exact ih _ k ht

/-- **القمعُ لكلمةٍ واحدة**: ما لم يسقط في طبقةٍ لم يسقط فيما دونها. لكلّ كلمةٍ وطبقات. -/
theorem qam (w : String) (a : Hal) (ts : List Tabaqa) (k : Nat) (h : Hal)
    (hh : (ahkam w a ts)[k + 1]? = some h) (hs : h.saqit = false) :
    ∃ h', (ahkam w a ts)[k]? = some h' ∧ h'.saqit = false := by
  have hlen : k < (ahkam w a ts).length := by
    have : (ahkam w a ts)[k + 1]? ≠ none := by rw [hh]; simp
    rw [ne_eq, List.getElem?_eq_none_iff] at this
    omega
  refine ⟨(ahkam w a ts)[k], List.getElem?_eq_getElem hlen, ?_⟩
  cases hc : (ahkam w a ts)[k] with
  | muayyan v => rfl
  | muhtamal vs => rfl
  | laHukm s =>
    have hk : (ahkam w a ts)[k]? = some (.laHukm s) := by
      rw [List.getElem?_eq_getElem hlen, hc]
    have := suqut_ba3d w a ts k s hk (k + 1) (by omega) h hh
    subst this
    simp [Hal.saqit] at hs

/-- غيرُ ساقطٍ في الموضع k (وما لا موضعَ له ساقط). -/
def qaimFi (k : Nat) (hs : List Hal) : Bool := (hs[k]?.map fun h => !h.saqit).getD false

/-- **القمعُ عددًا**: على أيّ كلماتٍ بطبقاتٍ لكلٍّ منها، عددُ ما لم يسقط في الطبقة ‎k+1‎ لا يزيد على عدده في k. لكلّ مدخل. -/
theorem qam_adad (xs : List (String × Hal × List Tabaqa)) (k : Nat) :
    (xs.map fun x => ahkam x.1 x.2.1 x.2.2).countP (qaimFi (k + 1)) ≤
      (xs.map fun x => ahkam x.1 x.2.1 x.2.2).countP (qaimFi k) := by
  apply List.countP_mono_left
  intro hs hm hq
  simp only [List.mem_map] at hm
  obtain ⟨⟨w, a, ts⟩, _, rfl⟩ := hm
  simp only [qaimFi] at hq ⊢
  cases hh : (ahkam w a ts)[k + 1]? with
  | none => rw [hh] at hq; simp at hq
  | some h =>
    rw [hh] at hq
    simp only [Option.map_some, Option.getD_some, Bool.not_eq_eq_eq_not, Bool.not_true] at hq
    obtain ⟨h', hk, hs'⟩ := qam w a ts k h hh (by simpa using hq)
    rw [hk]
    simp [hs']

/-- رمزُ الحكم سطرًا في جدول `silsila` (ليُطابَق بـ`tools/gen_silsila.py`). -/
def ramzSabab : Sabab → String
  | .rafd n => s!"rafd:{n}"
  | .dunaha => "dunaha"
  | .laQari => "laQari"
  | .kharij => "kharij"

def ramz : Hal → String
  | .muayyan v => s!"m:{v}"
  | .muhtamal vs => s!"p:{String.intercalate "|" vs}"
  | .laHukm s => s!"l:{ramzSabab s}"

/-! ## الشاهد: ثلاثُ طبقاتٍ على كلمتين -/

/-- قارئٌ مبنيٌّ للشاهد: يعيّن «كَتَبَ» ويرفض ما سواها باسم. -/
def shahadaMithal : Tabaqa := ⟨"الشهادة", some fun w _ => if w = "كَتَبَ" then .muayyan w else .laHukm (.rafd "REJECT")⟩
/-- قارئُ قسمٍ مبنيّ: يحتمل الفعلَ والاسم. -/
def qismMithal : Tabaqa := ⟨"القسم", some fun _ _ => .muhtamal ["فعل", "اسم"]⟩
/-- طبقةٌ لم يُكتب قارئُها. -/
def jinsMithal : Tabaqa := ⟨"الجنس", none⟩

/-- **الشاهد** (على الشاهد): «كَتَبَ» معيَّنةٌ شهادةً، محتمَلةٌ قسمًا، و«لا حكم» جنسًا بلا قارئ؛ و«كتب» بلا تشكيلٍ مرفوضةٌ
بالاسم فتسقط فوقها. -/
theorem shahid :
    silsila [shahadaMithal, qismMithal, jinsMithal] ["كَتَبَ", "كتب"] =
      [[.muayyan "كَتَبَ", .muhtamal ["فعل", "اسم"], .laHukm .laQari],
       [.laHukm (.rafd "REJECT"), .laHukm .dunaha, .laHukm .dunaha]] := by decide

end A116.Silsila
