import A116.Jadwal
import A116.Numbering
import A116.Field112

/-!
# المراكبُ الثلاثة: ترتيبُ الخانة رقمًا، وترجمةُ n بينها، والوحدةُ تحمل مركبَها (ADR ٩٩)

أمرُ المالك (2026-10-17): «نفّذ أفضلَ ما في هذه الرؤية على مستودع الغانم … واعمل على بوّابة الغانم واعمل تكاملًا مع باقي
المستودعات وفق هذه المنهجيّة في توظيف معادلات الـbinary في كلّ شيء».

## الخلل: الخانةُ واحدة والرقمُ ثلاثة

الصيغةُ ‎4·حامل + حالة‎ واحدة، والحاملُ مرقَّمٌ بثلاثة ترتيباتٍ في الأسرة نفسها:

* **الخانات** (`Cells`، ا0 … ي27 ء28): وهو ترتيبُ حقل hamil (`Field112`: حقلُه الـ112 هو الخاناتُ الأولى بعينها).
* **الجسر** (`Numbering.bridgeIndex`، ء0 … ا28 بتبديل صفّين): ترتيبُ البوّابة (`gate/bridge.py` `ALPHABET`) والشهادة،
  وترتيبُ `alghanem-constitution` (`src/alghanem_bridge.py` `ALPHABET`).
* **المخارج** (`Jadwal.khanat`، من «الكتاب» المختوم برواية السيرافيّ للّام): ءهاعحغخقكجشيضلنرطدتزسصظذثفبمو.

فرقمٌ بلا مركبه يُقرأ في مركبٍ آخر حروفًا أخرى (`khalt_shahid`).

## ما يُبرهن

١. **كلُّ مركبٍ تقابلٌ** بين الخانات الـ116 و‎[0, 116)‎ (`cellAt_index`، `index_cellAt`، `index_lt`، `index_injective`)،
   والجداولُ الثلاثة تبديلاتٌ للخانات نفسها (`tabadil`)؛ والجسرُ هنا هو `bridgeIndex` بعينه (`index_jisr`).
٢. **النقلُ بين المراكب** ‎naql m m'‎ زُمرةٌ صغيرة: الهويّة، والتركيب، والعكس (`naql_id`، `naql_comp`، `naql_inv`)،
   ويحفظ الحاملَ والحالة لأنّه الخانةُ نفسها (`naql_khana`).
٣. **عددُ الكلمة في كلّ مركب** ‎F m w = foldAny 116 0 (w.map (index m))‎ تقابلٌ إلى ℕ (`F_injective`، `F_surjective`)،
   و‎F jisr‎ هو `atomNumber` بعينه (`F_jisr`) — أي عددُ الذرّات في شهادة البوّابة.
٤. **ترجمةُ n** ‎tarjim m m'‎: ‎tarjim m m' (F m w) = F m' w‎ لكلّ كلمة (`tarjim_spec`)، وهي زُمرةٌ صغيرة (`tarjim_id`،
   `tarjim_comp`)، فلا رقمَ يُقارَن بين مركبين إلّا بها.
٥. **الوحدةُ تحمل مركبَها:** ‎wahda m w = P(رقمُ المركب، F m w)‎ تباينٌ في الزوج (`wahda_injective`) — فلا خلط.
٦. **الشواهد:** ترتيبُ المخارج هو السلسلةُ أعلاه (`makharij_order`)، وعددُ «كَتَبَ» في المراكب الثلاثة (`kataba`).
-/

namespace A116.Marakib

open A116 A116.Numbering A116.Fold

/-- المراكبُ الثلاثة. -/
inductive Markab | khanat | jisr | makharij
  deriving DecidableEq, Repr

def Markab.all : List Markab := [.khanat, .jisr, .makharij]

def Markab.n : Markab → Nat
  | .khanat => 0
  | .jisr => 1
  | .makharij => 2

/-- رقمُ الخانة بترتيب `Cells`. -/
def cellsIndex (c : Cell) : Nat := 4 * c.carrier.val + c.haraka.index

/-- رقمُ الخانة في كلّ مركب. -/
def index : Markab → Cell → Nat
  | .khanat, c => cellsIndex c
  | .jisr, c => bridgeIndex c
  | .makharij, c => Jadwal.khanat.idxOf c

/-- جدولُ كلّ مركب: الخانةُ في موضع رقمها. -/
def table : Markab → List Cell
  | .khanat => cells
  | .jisr => (List.range 116).map bridgeCell
  | .makharij => Jadwal.khanat

def nul : Cell := ⟨⟨0, by decide⟩, .fatha⟩

def cellAt (m : Markab) (k : Nat) : Cell := (table m).getD k nul

/-! ## ١. كلُّ مركبٍ تقابل -/

/-- **الجداولُ الثلاثة تبديلاتٌ للخانات:** 116 بلا تكرار، وفيها كلُّ خانة. -/
theorem tabadil : Markab.all.all (fun m =>
    (table m).length == 116 && (table m).Nodup && cells.all (table m).contains) = true := by
  decide +kernel

theorem index_cellAt_all : Markab.all.all (fun m =>
    (List.range 116).all (fun k => index m (cellAt m k) == k)) = true := by decide +kernel

theorem cellAt_index_all : Markab.all.all (fun m =>
    cells.all (fun c => cellAt m (index m c) == c && decide (index m c < 116))) = true := by decide +kernel

theorem mem_all (m : Markab) : m ∈ Markab.all := by cases m <;> decide

/-- **الفكّ يردّ الخانة** في كلّ مركب. -/
theorem cellAt_index (m : Markab) (c : Cell) : cellAt m (index m c) = c := by
  have h := List.all_eq_true.mp cellAt_index_all m (mem_all m)
  have := List.all_eq_true.mp h c (mem_cells c)
  simp only [Bool.and_eq_true, beq_iff_eq] at this
  exact this.1

theorem index_lt (m : Markab) (c : Cell) : index m c < 116 := by
  have h := List.all_eq_true.mp cellAt_index_all m (mem_all m)
  have := List.all_eq_true.mp h c (mem_cells c)
  simp only [Bool.and_eq_true, decide_eq_true_eq] at this
  exact this.2

theorem index_cellAt (m : Markab) (k : Nat) (hk : k < 116) : index m (cellAt m k) = k := by
  have h := List.all_eq_true.mp index_cellAt_all m (mem_all m)
  have := List.all_eq_true.mp h k (List.mem_range.mpr hk)
  simpa using this

theorem index_injective (m : Markab) {c d : Cell} (h : index m c = index m d) : c = d := by
  rw [← cellAt_index m c, ← cellAt_index m d, h]

/-- **مركبُ الجسر هو `bridgeIndex` بعينه.** -/
theorem index_jisr (c : Cell) : index .jisr c = bridgeIndex c := rfl

/-! ## ٢. النقلُ بين المراكب -/

def naql (m m' : Markab) (k : Nat) : Nat := index m' (cellAt m k)

theorem naql_id (m : Markab) (k : Nat) (hk : k < 116) : naql m m k = k := index_cellAt m k hk

theorem naql_comp (m m' m'' : Markab) (k : Nat) :
    naql m' m'' (naql m m' k) = naql m m'' k := by
  unfold naql; rw [cellAt_index]

theorem naql_inv (m m' : Markab) (k : Nat) (hk : k < 116) : naql m' m (naql m m' k) = k := by
  rw [naql_comp]; exact naql_id m k hk

/-- **النقلُ يحفظ الخانة** (حاملَها وحالتَها): المرقومُ واحدٌ والرقمُ وحدَه يتبدّل. -/
theorem naql_khana (m m' : Markab) (k : Nat) : cellAt m' (naql m m' k) = cellAt m k := cellAt_index m' _

/-! ## ٣. عددُ الكلمة في كلّ مركب -/

/-- ‎F m w‎: الترقيمُ العامّ لخانات الكلمة في المركب m. -/
def F (m : Markab) (w : List Cell) : Nat := foldAny 116 0 (w.map (index m))

theorem F_jisr (w : List Cell) : F .jisr w = atomNumber w := rfl

theorem map_index_lt (m : Markab) (w : List Cell) : ∀ x ∈ w.map (index m), x < 116 := by
  intro x hx
  obtain ⟨c, _, rfl⟩ := List.mem_map.1 hx
  exact index_lt m c

theorem map_index_injective (m : Markab) {w w' : List Cell} (h : w.map (index m) = w'.map (index m)) : w = w' := by
  have := congrArg (List.map (cellAt m)) h
  simpa [List.map_map, Function.comp_def, cellAt_index] using this

/-- **التباين:** في كلّ مركب، كلمتان بعددٍ واحدٍ هما واحدة. -/
theorem F_injective (m : Markab) {w w' : List Cell} (h : F m w = F m w') : w = w' :=
  map_index_injective m <| foldAny_injective 116 0
    ((valid_zero_iff 116 true _).2 (map_index_lt m w))
    ((valid_zero_iff 116 true _).2 (map_index_lt m w')) h

/-- **الشمول:** في كلّ مركب، كلُّ عددٍ عددُ كلمةٍ واحدة. -/
theorem F_surjective (m : Markab) (k : Nat) : ∃ w, F m w = k := by
  obtain ⟨l, hv, hk⟩ := foldAny_surjective 116 0 (by decide) k
  have hl := (valid_zero_iff 116 true l).1 hv
  refine ⟨l.map (cellAt m), ?_⟩
  have : (l.map (cellAt m)).map (index m) = l := by
    rw [List.map_map]
    conv => rhs; rw [← List.map_id l]
    apply List.map_congr_left
    intro x hx
    exact index_cellAt m x (hl x hx)
  rw [F, this, hk]

/-! ## ٤. ترجمةُ n -/

/-- **ترجمةُ عددٍ من مركبٍ إلى مركب:** عددُ الكلمة نفسِها في المركب الآخر. -/
noncomputable def tarjim (m m' : Markab) (k : Nat) : Nat := F m' (Classical.choose (F_surjective m k))

theorem tarjim_spec (m m' : Markab) (w : List Cell) : tarjim m m' (F m w) = F m' w := by
  unfold tarjim
  have h := Classical.choose_spec (F_surjective m (F m w))
  rw [F_injective m h]

theorem tarjim_id (m : Markab) (k : Nat) : tarjim m m k = k := by
  obtain ⟨w, rfl⟩ := F_surjective m k
  exact tarjim_spec m m w

theorem tarjim_comp (m m' m'' : Markab) (k : Nat) : tarjim m' m'' (tarjim m m' k) = tarjim m m'' k := by
  obtain ⟨w, rfl⟩ := F_surjective m k
  rw [tarjim_spec, tarjim_spec, tarjim_spec]

/-! ## ٥. الوحدةُ تحمل مركبَها -/

def wahda (m : Markab) (w : List Cell) : Nat := pair m.n (F m w)

theorem Markab.n_injective {m m' : Markab} (h : m.n = m'.n) : m = m' := by
  cases m <;> cases m' <;> first | rfl | (simp [Markab.n] at h)

/-- **لا خلط:** عددُ الوحدة يعيّن مركبَها وكلمتَها معًا. -/
theorem wahda_injective {m m' : Markab} {w w' : List Cell} (h : wahda m w = wahda m' w') : m = m' ∧ w = w' := by
  obtain ⟨h1, h2⟩ := pair_injective h
  have hm := Markab.n_injective h1
  subst hm
  exact ⟨rfl, F_injective m h2⟩

/-- **شاهدُ الخلط:** «اَ» في مركب الخانات و«ءَ» في مركب الجسر عددٌ واحد — فالرقمُ بلا مركبه يُقرأ حرفًا آخر. -/
theorem khalt_shahid :
    F .khanat [⟨⟨0, by decide⟩, .fatha⟩] = F .jisr [⟨⟨28, by decide⟩, .fatha⟩] ∧
    (⟨⟨0, by decide⟩, .fatha⟩ : Cell) ≠ ⟨⟨28, by decide⟩, .fatha⟩ := by decide

/-! ## ٦. الشواهد -/

/-- **ترتيبُ المخارج** كما بناه `Jadwal` من «الكتاب» المختوم. -/
theorem makharij_order : String.ofList Makharij.placed16 = "ءهاعحغخقكجشيضلنرطدتزسصظذثفبمو" := by decide

/-- **حقلُ hamil هو مركبُ الخانات بعينه:** لكلّ خانةٍ من الـ112 رقمُها في حقل hamil (‎4·موضعُ الحرف في letters28 + الحالة‎)
هو رقمُها في مركب الخانات. -/
theorem hamil_khanat : cells112.all (fun c =>
    4 * Field112.letters28.idxOf (Field112.carriers29.getD c.carrier.val ' ') + c.haraka.index == index .khanat c) = true := by
  decide +kernel

def ka : Cell := ⟨⟨21, by decide⟩, .fatha⟩
def ta : Cell := ⟨⟨2, by decide⟩, .fatha⟩
def ba : Cell := ⟨⟨1, by decide⟩, .fatha⟩

/-- **«كَتَبَ» في المراكب الثلاثة:** خاناتُها أرقامٌ ثلاثة، وعددُها ثلاثة، والترجمةُ تردّ كلًّا إلى كلّ. -/
theorem kataba :
    [ka, ta, ba].map (index .khanat) = [84, 8, 4] ∧ [ka, ta, ba].map (index .jisr) = [84, 8, 4] ∧
    [ka, ta, ba].map (index .makharij) = [32, 72, 104] ∧
    String.ofList ([ka, ta, ba].map (fun c => Field112.carriers29.getD c.carrier.val ' ')) = "كتب" := by
  decide +kernel

end A116.Marakib
