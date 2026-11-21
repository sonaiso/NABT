import A116.QismDaraja
import A116.Marakib
import A116.Mufrad
import A116.Field112
import A116.IhalaHasr

/-!
# مقارنةُ الوحدة بوحدة SLGE، وربطُ القسم بقسمة ج3 (ADR ١٠٩)

أمرُ المالك: «UNIT_IS_HUDUD_N_NOT_SLGE … اعمل مقارنة انت خبير رياضيات … ومراجعة الشخصية الإسلامية ج٣ بعمق … لعمل الربط
وفق افضل الممارسات».

**المصدر.** تعريفاتُ SLGE هنا **منقولةٌ** من ملفّات المالك كما قُرئت في الجلسة (مستودعُ SLGE نفسُه لم يُبلَغ؛ قُرئت نسختُها
في مجلّد `SLGE/` بمستودعٍ آخر للمالك، ولا يُستورد منه شيء):
* `Core.lean`: ‎`pair u r = tri(u+r) + r`‎، و‎`encS [] = 0`، `encS (a :: l) = 1 + pair a (encS l)`‎.
* `Ladder.lean`: ‎`cellEnc c s = mixEnc 1 4 c 0 s = 4c + s`‎ (فتحة 0، ضمّة 1، كسرة 2، سكون 3).
* `Category.lean`: ‎`roles ind tim = (ind && !tim, ind)`‎، و`kindOf`: ‎(true, _) ← اسم، (false, true) ← فعل، (false, false) ← حرف‎.

**وفروقُ النقل (معلنة):**
* ترتيبُ الحوامل في SLGE تعليقُ توثيقٍ في `Ladder.lean` يسمّيه SLGE «المعلَن (شاهدٌ لا قانون)»، ولا دالّةَ فيه من الحرف إلى رقمه.
  فـ`slgeIndex` بناءٌ هنا على ذلك الترتيب.
* `slgePair` صيغةُ `pair` المغلقة لا `tri` بعينه، و`encS` هنا على `A116.Numbering.pair` لا `SLGE.pair` (وهما واحد: `pair_slge`).
* `kindOf` هنا يُخرج `Tarkib.Qism` لا `SLGE.Kind`.
* **ولا وحدةَ في SLGE تقترن فيها الخاناتُ بالجنس.** فـ`nSlge` بناءٌ هنا من ترميز SLGE للكلمة (`encS` على أرقام الخانات بترتيب
  المخارج، كما في `Tarkib.sEnc`) مقترنًا بالجنس.

**ما يثبت هنا** (و`pair_slge`، `slgeOrder_eq_makharij`، `nPair_injective`، `tarjama_n` تعريفيّة أو نتائجُ مباشرة):
١. **الخانة:** رقمُ SLGE للخانة ‎4c + s‎ بترتيب حوامله هو رقمُ مركب المخارج في `Marakib` بعينه، على الخانات الـ116 كلّها
   (`cell_slge_eq_makharij`).
٢. **الاقتران:** اقترانُ SLGE هو `Numbering.pair` بعينه (`pair_slge`)، و`encS` تباين (`encS_injective`).
٣. **الوحدة:** عددُ الكلمة بترميز SLGE ‎`encS (w.map slgeIndex)`‎ تباين (`slgeF_injective`)، والوحدةُ عليه ‎P(F_SLGE, j)‎ تباين
   (`nSlge_injective`). **وهي تفصل الوحداتِ نفسَها التي يفصلها `Hudud.n`** (`nSlge_iff_n`): فالفرقُ بين العددين ترميزٌ لا معلومة.
   وكلاهما يُسقط الرتبة: كلمتان بخاناتٍ واحدة وجنسٍ واحد وحدةٌ واحدة، و`Hudud.certHadd` يفصلهما (`wahda_tusqit_rutba`).
٤. **القسم:** قسمةُ ج3 (`Mufrad.qismOf` على الاستقلال والدلالة بالهيئة على الزمان) هي `kindOf ∘ roles` في SLGE بعينها
   (`j3_eq_slge`)؛ فالقسمُ من صفات المدلول لا من الخانات.
٥. **السلامة:** إن كان المرجعُ قسمةَ ج3 على صفاتٍ معطاة ولم تخطئ علامة، فمعيَّنُ القارئ قسمُ ج3 بعينه (`muayyan_j3`،
   نتيجةٌ مباشرة لـ`muayyan_sahih`؛ والمرجعُ المقيس QAC لا قسمةُ ج3).

ومراسي ج3 (الشخصيّة ج3 المختومة): س373 القسمة، س375 حدُّ الاسم، س377 الضميرُ والحرف، س467 حدُّ الحرف — تُفحص في
`tests/test_qism_khanat4.py`.
-/

namespace A116.WahdaMuqarana

open A116 A116.Numbering A116.QismKhanat

/-! ## ١. الخانة -/

/-- ترتيبُ حوامل SLGE (`Ladder.lean`). -/
def slgeOrder : List Char := "ءهاعحغخقكجشيضلنرطدتزسصظذثفبمو".toList

/-- `SLGE.Ladder.cellEnc` منسوخًا: ‎mixEnc 1 4 c 0 s = (c·1 + 0)·4 + s‎. -/
def slgeCellEnc (c s : Nat) : Nat := (c * 1 + 0) * 4 + s

/-- رقمُ الخانة عند SLGE: موضعُ حاملها في ترتيبه، وحالتُها. -/
def slgeIndex (c : Cell) : Nat := slgeCellEnc (slgeOrder.idxOf (Field112.carrierChar c.carrier)) c.haraka.index

theorem slgeOrder_eq_makharij : slgeOrder = Makharij.placed16 := by decide

/-- **رقمُ SLGE للخانة هو رقمُ مركب المخارج** على الخانات كلّها. -/
theorem cell_slge_eq_makharij_all : cells.all (fun c => slgeIndex c == Marakib.index .makharij c) = true := by
  decide +kernel

theorem cell_slge_eq_makharij (c : Cell) : slgeIndex c = Marakib.index .makharij c := by
  have := List.all_eq_true.mp cell_slge_eq_makharij_all c (mem_cells c)
  simpa using this

/-- فالكلمةُ عند SLGE خاناتٍ هي عددُها في مركب المخارج. -/
theorem word_slge (w : List Cell) : w.map slgeIndex = w.map (Marakib.index .makharij) :=
  List.map_congr_left fun c _ => cell_slge_eq_makharij c

/-! ## ٢. الاقتران والقوائم -/

/-- `SLGE.Core.pair` بصيغته المغلقة. -/
def slgePair (u r : Nat) : Nat := (u + r) * (u + r + 1) / 2 + r

theorem pair_slge (u r : Nat) : slgePair u r = pair u r := (pair_closed u r).symm

/-- `SLGE.Core.encS` منسوخًا. -/
def encS : List Nat → Nat
  | [] => 0
  | a :: l => 1 + pair a (encS l)

theorem encS_injective : ∀ {l l' : List Nat}, encS l = encS l' → l = l'
  | [], [], _ => rfl
  | [], _ :: _, h => by simp [encS] at h <;> omega
  | _ :: _, [], h => by simp [encS] at h <;> omega
  | a :: l, b :: l', h => by
    simp only [encS] at h
    obtain ⟨h1, h2⟩ := pair_injective (by omega : pair a (encS l) = pair b (encS l'))
    rw [h1, encS_injective h2]

/-! ## ٣. الوحدة -/

/-- عددُ الكلمة بترميز SLGE: `encS` على أرقام خاناتها بترتيب حوامله. -/
def slgeF (w : List Cell) : Nat := encS (w.map slgeIndex)

theorem slgeF_eq (w : List Cell) : slgeF w = encS (w.map (Marakib.index .makharij)) := by
  unfold slgeF; rw [word_slge]

theorem slgeF_injective {w w' : List Cell} (h : slgeF w = slgeF w') : w = w' := by
  rw [slgeF_eq, slgeF_eq] at h
  exact Marakib.map_index_injective .makharij (encS_injective h)

/-- وحدةٌ مبنيّةٌ على ترميز SLGE: عددُ الكلمة مقترنًا بالجنس. -/
def nSlge (u : Hudud.Wahda) : Nat := pair (slgeF u.cells) (Hudud.jinsN u.jins)

theorem nSlge_injective {u v : Hudud.Wahda} (h : nSlge u = nSlge v) : u = v := by
  obtain ⟨h1, h2⟩ := pair_injective h
  have hj : u.jins = v.jins := by rw [← Hudud.ofN_jinsN u.jins, h2, Hudud.ofN_jinsN]
  have hc := slgeF_injective h1
  cases u; cases v; simp_all

/-- **العددان يفصلان الوحداتِ نفسَها.** -/
theorem nSlge_iff_n (u v : Hudud.Wahda) : nSlge u = nSlge v ↔ Hudud.n u = Hudud.n v :=
  ⟨fun h => by rw [nSlge_injective h], fun h => by rw [Hudud.n_inj h]⟩

/-- صيغةُ اقترانٍ على `atomNumber` الغانم (لا على ترميز SLGE): ‎P(F, j)‎. -/
def nPair (u : Hudud.Wahda) : Nat := pair (atomNumber u.cells) (Hudud.jinsN u.jins)

theorem nPair_injective {u v : Hudud.Wahda} (h : nPair u = nPair v) : u = v := by
  obtain ⟨h1, h2⟩ := pair_injective h
  have hj : u.jins = v.jins := by rw [← Hudud.ofN_jinsN u.jins, h2, Hudud.ofN_jinsN]
  have hc := atomNumber_injective h1
  cases u; cases v; simp_all

/-- الترجمةُ بين ‎11F + j‎ و‎P(F, j)‎ على F الغانم (تعريفيّة). -/
def tarjama (k : Nat) : Nat := pair (k / 11) (k % 11)

theorem tarjama_n (u : Hudud.Wahda) : tarjama (Hudud.n u) = nPair u := by
  unfold tarjama nPair; rw [Hudud.n_div, Hudud.n_mod]

/-- **الوحدةُ تُسقط الرتبة، و`certHadd` يحملها:** كلمتان من المجال بخاناتٍ واحدة وحدةٌ واحدة في العددين، وعددا حدّهما مختلفان. -/
theorem wahda_tusqit_rutba {α : Type} [DecidableEq α] {D : List α} {A : α → List Cell} (j : Hudud.Jins)
    {x y : α} (hx : x ∈ D) (hy : y ∈ D) (hxy : x ≠ y) (hA : A x = A y) :
    Hudud.n ⟨j, A x⟩ = Hudud.n ⟨j, A y⟩ ∧ nSlge ⟨j, A x⟩ = nSlge ⟨j, A y⟩ ∧
    Hudud.certHadd D A j x ≠ Hudud.certHadd D A j y := by
  refine ⟨by rw [hA], by rw [hA], fun h => hxy (Hudud.certHadd_injective hx hy h).2⟩

/-! ## ٤. القسم: ج3 = SLGE -/

/-- `SLGE.Cat.roles` منسوخًا. -/
def roles (ind tim : Bool) : Bool × Bool := (ind && !tim, ind)

/-- `SLGE.Cat.kindOf` منسوخًا، إلى أقسام `Tarkib`. -/
def kindOf : Bool × Bool → Tarkib.Qism
  | (true, _) => .ism
  | (false, true) => .fil
  | (false, false) => .harf

/-- **قسمةُ ج3 هي قسمةُ SLGE بعينها.** -/
theorem j3_eq_slge (s : Mufrad.Sifat) : kindOf (roles s.istiqlal s.zamanHaya) = Mufrad.qismOf s := by
  rcases s with ⟨i, t, _, _⟩
  cases i <;> cases t <;> rfl

/-- **ولا رابعة** في الصورتين. -/
theorem la_rabia (ind tim : Bool) : roles ind tim ≠ (true, false) := by
  cases ind <;> cases tim <;> decide

def ilaKhanat : Tarkib.Qism → QismKhanat.Qism
  | .ism => .ism
  | .fil => .fil
  | .harf => .harf

/-! ## ٥. السلامة على قسمة ج3 -/

/-- إن كان مرجعُ الكلمة قسمةَ ج3 على صفاتها ولم تخطئ علامة، فمعيَّنُ القارئ قسمُ ج3. -/
theorem muayyan_j3 {α : Type} (as : List (Alama α)) (sifa : α → Mufrad.Sifat) (x : α)
    (h : ∀ a ∈ as, khata a (x, ilaKhanat (Mufrad.qismOf (sifa x))) = false) (q : QismKhanat.Qism)
    (hq : qiraa as x = .muayyan q) : q = ilaKhanat (kindOf (roles (sifa x).istiqlal (sifa x).zamanHaya)) := by
  rw [j3_eq_slge]
  exact muayyan_sahih as (x, _) h q hq

/-! ## شواهد -/

/-- «كَتَبَ» عند SLGE ‎[32, 72, 104]‎، وفي القسمة: «هو» اسم، «قام» فعل، «من» حرف. -/
theorem shawahid :
    (cell "كَتَبَ").map slgeIndex = [32, 72, 104] ∧
    kindOf (roles Mufrad.huwa.istiqlal Mufrad.huwa.zamanHaya) = .ism ∧
    kindOf (roles Mufrad.qama.istiqlal Mufrad.qama.zamanHaya) = .fil ∧
    kindOf (roles Mufrad.min.istiqlal Mufrad.min.zamanHaya) = .harf := by
  decide +kernel

end A116.WahdaMuqarana
