import SLGE.Root

/-!
# ولادةُ الجذر بالحساب الصنفيّ، والحدُّ الأدنى المكتمل

قولُ المالك في الجلسة (2026-11-01، لفظُه ووقتُه 12:19 من ملخّص الجلسة بعد ضغطها):
«نحتاج برهان ولادة الجذر جبريا وفق استقراء قانون الاستنفاد انت لم تأخذ في الاعتبار كيف بنينا البرهان من المخارج ورخصنا الاحرف داخل المخرج وبنينا الشيفرة ومن يفسر كل شيء اذا وضع قانون التجاور وفق قانون الابتداء وقانون الوصل وقانون الفصل وقانون الوقف وبالحد الأدنى المكتمل …»
ثمّ (12:40): «… ولكن يجب ان نوحد الحساب من الان وصاعدا بقانون واحد جبري».

**الولادة.** آلةُ الجذر `Mroot` للمالك (`SLGE/Root.lean`) كما هي، وعدُّها `Mroot.lev` بالاستنفاد (`SLGE/Count.lean`).
والأصنافُ من جدول المخارج ووسيط حروف العلّة (`weak`، `SLGE/Law.lean`) واستبعاد الألف: صنفُ الحامل عددُ ما يتجاور معه
(`conflict`: من مخرجه، ولا تجاورَ لحروف العلّة) — `sinf`، فالحوامل غيرُ الألف تسعةٌ بلا مجاور
(ق ك ض ل ن ر ف ي و)، وعشرةٌ بمجاورٍ واحد (ء ه، ع ح، غ خ، ج ش، ب م)، وتسعةٌ بمجاورَين (ط د ت، ز س ص، ظ ذ ث) — `asnaf`.
وحالاتُ الآلة بعد الحامل تتكافأ بصنفه، وحسابُها الصنفيّ في ملفّ المالك منذ 2026-11-01 (`SLGE.Law.HisabJadhr`، `hisabJadhr`؛ وكان هنا في #119)، فيعدّ
الجذورَ على خمسة أصناف، ومنه التكرار لكلّ طول (`wilada`):
`R(k+4) = 25·R(k+3) + 54·R(k+2) + 18·R(k+1)`، وأوّلُه 28 و756 و20430 (`wilada_awwal`)،
وعددا المالك للرباعيّ والخماسيّ (`SLGE.Law.root4`، `root5`) مبرهنان بالحساب الصنفيّ في `SLGE/Root.lean`، و`jadhr_bil_qanun` يشتقّهما
ثانيةً من التكرار وبعدهما السداسيّ.

**الحدُّ الأدنى المكتمل** (§٣). الصورتان من رأس ملفّ المالك `SLGE/Root.lean` (س8: «‎فَعْل‎ للثاني والثالث، و‎يَفْعَل‎ للأوّل والثاني»)، ومبرهنتُه `tajawur_root` تثبت أنّ التجاور يمتنع فيهما (لا امتناعَ الألف). و`kamil3` يُتمّه
بالاتّجاهين: قانونُ الجذر الثلاثيّ هو قانونُ الوصل نفسُه على الصورتين معًا؛ ولا تكفي إحداهما (`la_yakfi_wahid`).

**التعيين** (البنّاء): الأصنافُ الخمسةُ وصفوفُها؛ وضمّةُ الثالث في الصورتين (رأسُ المالك بلا حركةٍ للآخر)؛ وتسميةُ `kamil3` بقول المالك «بالحد الأدنى المكتمل» — قراءتي تنتظر إمضاءك.

المبرهنات هنا: 13 بالمعيار الموحَّد: لكلّ 3 (`wilada`، `tawlid`، `d96`)؛ وتعريفيّة 1 (`r30`)؛ وعلى الشاهد 6 برهانُها decide (`sinfT_sinf`، `asnaf`،
`wasl_khatwa`، `r1`، `r2`، `la_yakfi_wahid`)؛ و3 على الشاهد خارجَ حرف المعيار، معلَن (`wilada_awwal`: omega على مبرهنات؛ `jadhr_bil_qanun`: `tawlid`
على `wilada`؛ `kamil3`: على المجال المنتهي ‎a b c < 29‎ ببرهانٍ بالحالات لا بـ decide). وعشرُ مبرهناتٍ كانت هنا نُقلت بأسمائها إلى
`SLGE.Law.HisabJadhr` (`hawkama/الحساب_الصنفي.md`).
-/

namespace Dal.WiladaJadhr
open SLGE SLGE.Law SLGE.Law.HisabJadhr

/-! ## ١. الأصنافُ من جدول المخارج ووسيط حروف العلّة -/

/-- صنفُ الحامل: عددُ الحوامل غيرِ الألف التي تتجاور معه (`conflict`: من مخرجه، ولا تجاورَ لحروف العلّة)، فيمتنع أن تليه. -/
def sinf (c : Nat) : Nat := ((List.range 29).filter fun b => b != 2 && conflict c b).length

theorem sinfT_sinf : ∀ c < 29, sinfT.getD c 0 = sinf c := by decide +kernel

/-- **الأصناف:** تسعةُ حوامل بلا مجاور، وعشرةٌ بمجاورٍ واحد، وتسعةٌ بمجاورَين؛ والممنوعُ مرتَّبًا 28 زوجًا. -/
theorem asnaf : ((List.range 29).filter fun c => c != 2 && sinf c == 0).length = 9 ∧
    ((List.range 29).filter fun c => c != 2 && sinf c == 1).length = 10 ∧
    ((List.range 29).filter fun c => c != 2 && sinf c == 2).length = 9 ∧
    ((List.range 29).map fun c => if c = 2 then 0 else sinf c).sum = 28 := by decide +kernel

/-! ## ٢. قانونُ الولادة -/

/-- **قانونُ الولادة (لكلّ k):** `R(k+4) = 25·R(k+3) + 54·R(k+2) + 18·R(k+1)`، ومعاملاتُه من صفوف الأصناف وحدها. -/
theorem wilada (k : Nat) : Mroot.lev 3 0 (k + 4) = 25 * Mroot.lev 3 0 (k + 3) + 54 * Mroot.lev 3 0 (k + 2) +
    18 * Mroot.lev 3 0 (k + 1) := by
  simp only [lev_jadhr]
  obtain ⟨a0, a1, a2, a3⟩ := jadhr_khatwa k
  obtain ⟨b0, b1, b2, b3⟩ := jadhr_khatwa (k + 1)
  obtain ⟨c0, c1, c2, c3⟩ := jadhr_khatwa (k + 2)
  obtain ⟨d0, d1, d2, d3⟩ := jadhr_khatwa (k + 3)
  simp only [Nat.add_assoc, Nat.reduceAdd] at b0 b1 b2 b3 c0 c1 c2 c3 d0 d1 d2 d3
  omega

/-- **أوّلُ الولادة:** 28 و756 و20430، و`R(3) = 25·R(2) + 54·R(1) + 18`. -/
theorem wilada_awwal : Mroot.lev 3 0 1 = 28 ∧ Mroot.lev 3 0 2 = 756 ∧ Mroot.lev 3 0 3 = 20430 ∧
    Mroot.lev 3 0 3 = 25 * Mroot.lev 3 0 2 + 54 * Mroot.lev 3 0 1 + 18 := by
  simp only [lev_jadhr]
  obtain ⟨z1, z2, z3⟩ := jadhr_shahid
  obtain ⟨a0, a1, a2, a3⟩ := jadhr_khatwa 0
  obtain ⟨b0, b1, b2, b3⟩ := jadhr_khatwa 1
  obtain ⟨c0, c1, c2, c3⟩ := jadhr_khatwa 2
  simp only [Nat.reduceAdd] at a0 a1 a2 a3 b0 b1 b2 b3 c0 c1 c2 c3
  refine ⟨by omega, by omega, by omega, by omega⟩

/-- **التكرارُ يولّد ما بعده:** كلُّ متتاليةٍ على التكرار وأوّلُها 28 و756 و20430 بعدها 552078 و14918778 و403149402. -/
theorem tawlid (R : Nat → Nat) (h : ∀ k, R (k + 4) = 25 * R (k + 3) + 54 * R (k + 2) + 18 * R (k + 1))
    (h1 : R 1 = 28) (h2 : R 2 = 756) (h3 : R 3 = 20430) :
    R 4 = 552078 ∧ R 5 = 14918778 ∧ R 6 = 403149402 := by
  have w0 := h 0
  have w1 := h 1
  have w2 := h 2
  simp only [Nat.reduceAdd] at w0 w1 w2
  refine ⟨by omega, by omega, by omega⟩

/-- **عددا المالك من القانون:** الرباعيُّ 552078 والخماسيُّ 14918778 (`SLGE.Law.root4`، `root5`) يُشتقّان بالولادة أيضًا — وقضيّتاه
في `SLGE/Root.lean` مبرهنتان بالحساب الصنفيّ نفسِه —، وبعدهما السداسيُّ 403149402. -/
theorem jadhr_bil_qanun : Mroot.lev 3 0 4 = 552078 ∧ Mroot.lev 3 0 5 = 14918778 ∧ Mroot.lev 3 0 6 = 403149402 :=
  tawlid (fun k => Mroot.lev 3 0 k) wilada wilada_awwal.1 wilada_awwal.2.1 wilada_awwal.2.2.1

/-! ## ٣. الحدُّ الأدنى المكتمل: قانونُ الجذر الثلاثيّ هو قانونُ الوصل على صورتين -/

/-- «يَفْعَلُ»: الياءُ مفتوحةً، ثمّ الأوّلُ ساكنًا، ثمّ الثاني مفتوحًا، ثمّ الثالثُ مضمومًا. -/
def yafal (a b c : Nat) : List Nat := [4 * 11 + 0, 4 * a + 3, 4 * b + 0, 4 * c + 1]
/-- «فَعْلُ»: الأوّلُ مفتوحًا، ثمّ الثاني ساكنًا، ثمّ الثالثُ مضمومًا. -/
def fal (a b c : Nat) : List Nat := [4 * a + 0, 4 * b + 3, 4 * c + 1]

theorem wasl_khatwa :
    δ 0 44 = 1 ∧
    (∀ a < 29, δ 1 (4 * a + 3) = if a = 2 then 4 else 67 + a) ∧
    (∀ a < 29, ∀ b < 29, δ (if a = 2 then 4 else 67 + a) (4 * b + 0) =
      if b = 2 ∨ (a ≠ 2 ∧ conflict a b = true) then 96 else 1) ∧
    (∀ c < 29, δ 1 (4 * c + 1) = if c = 2 then 96 else 2) ∧
    (∀ a < 29, δ 0 (4 * a + 0) = if a = 2 then 96 else 1) ∧
    (∀ b < 29, ∀ c < 29, δ (if b = 2 then 4 else 67 + b) (4 * c + 1) =
      if c = 2 ∨ (b ≠ 2 ∧ conflict b c = true) then 96 else 2) := by
  refine ⟨by decide +kernel, by decide +kernel, by decide +kernel, by decide +kernel, by decide +kernel, by decide +kernel⟩

theorem r1 : ∀ a < 29, δr 0 a = if a = 2 then 30 else a + 1 := by decide +kernel
theorem r2 : ∀ a < 29, ∀ b < 29, δr (a + 1) b = if b = 2 ∨ conflict a b = true then 30 else b + 1 := by
  decide +kernel
theorem r30 (x : Nat) : δr 30 x = 30 := by simp [δr]
theorem d96 (x : Nat) : δ 96 x = 96 := δ_big x (Nat.le_refl 96)

/-- **الحدُّ الأدنى المكتمل (الثلاثيّ):** يرخّص قانونُ الجذر الجذرَ إذا وفقط إذا رخّص قانونُ الوصل «يَفْعَلُ» و«فَعْلُ» معًا. -/
theorem kamil3 (a b c : Nat) (ha : a < 29) (hb : b < 29) (hc : c < 29) :
    Mroot.F ([a, b, c].foldl δr 0) = true ↔
      (Fwasl (run 0 (yafal a b c)) = true ∧ Fwasl (run 0 (fal a b c)) = true) := by
  obtain ⟨e1, e2, e3, e4, f1, f3⟩ := wasl_khatwa
  simp only [yafal, fal, List.foldl, run]
  rw [e1, e2 a ha, e3 a ha b hb, f1 a ha]
  rw [r1 a ha]
  by_cases h1 : a = 2
  · subst h1; simp [r30, d96, Mroot, Fwasl]
  · rw [if_neg h1, if_neg h1, r2 a ha b hb, e2 b hb]
    by_cases h2 : b = 2 ∨ conflict a b = true
    · rw [if_pos h2]
      have : (b = 2 ∨ (a ≠ 2 ∧ conflict a b = true)) := by
        rcases h2 with h | h
        · exact Or.inl h
        · exact Or.inr ⟨h1, h⟩
      rw [if_pos this]; simp [r30, d96, Mroot, Fwasl]
    · rw [if_neg h2]
      have h2' : ¬ (b = 2 ∨ (a ≠ 2 ∧ conflict a b = true)) := fun h => h2 (by
        rcases h with h | h
        · exact Or.inl h
        · exact Or.inr h.2)
      rw [if_neg h2', e4 c hc, f3 b hb c hc]
      have hb2 : b ≠ 2 := fun h => h2 (Or.inl h)
      rw [r2 b hb c hc]
      by_cases h3 : c = 2 ∨ conflict b c = true
      · rw [if_pos h3]
        rcases h3 with h | h
        · subst h; simp [r30, d96, Mroot, Fwasl]
        · rw [if_pos (Or.inr ⟨hb2, h⟩)]; by_cases hc2 : c = 2 <;> simp [hc2, r30, d96, Mroot, Fwasl]
      · rw [if_neg h3]
        have hc2 : c ≠ 2 := fun h => h3 (Or.inl h)
        have h3' : ¬ (c = 2 ∨ (b ≠ 2 ∧ conflict b c = true)) := fun h => h3 (by
          rcases h with h | h
          · exact Or.inl h
          · exact Or.inr h.2)
        rw [if_neg hc2, if_neg h3']
        simp [Mroot, Fwasl]; omega

/-- **ولا تكفي إحداهما:** «يَفْعَلُ» يقبل «لطد» و«فَعْلُ» يقبل «طدل» (الطاءُ والدالُ متجاوران)، وكلاهما مرفوضٌ جذرًا.
ل = 13، ط = 16، د = 17. -/
theorem la_yakfi_wahid :
    Fwasl (run 0 (yafal 13 16 17)) = true ∧ Mroot.F ([13, 16, 17].foldl δr 0) = false ∧
    Fwasl (run 0 (fal 16 17 13)) = true ∧ Mroot.F ([16, 17, 13].foldl δr 0) = false := by decide +kernel

end Dal.WiladaJadhr
