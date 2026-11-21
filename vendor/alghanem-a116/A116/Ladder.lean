import A116.Count
import A116.Field112

/-!
# سلّمُ الأنماط: ما يصحّ من «برهان السلّم» وما لا يصحّ، مفحوصًا بالنواة

النموذجُ لا يرى من الخانة إلّا: أمتحرّكةٌ هي (M) أم ساكنة (S)
(`step_depends_only_on_sukun`). فنمطُ الكلمة `pat w` هو كلُّ ما يراه.

## المبرهنات

* `run_depends_only_on_pattern`: كلمتان بنمطٍ واحد لهما الأثرُ نفسُه في النموذج، بأيّ طول.
* `U_eq_pow_mul_g`: ‎U(n) = 29ⁿ·g(n)‎ لكلّ n، و‎g(n+2) = 3g(n+1) + 3g(n)‎، ‎g(0)=1، g(1)=3‎.
* `pattern_count_fib`: عددُ الأنماط الجائزة بطول n (تبدأ بـM ولا SS) هو ‎fib(n+1)‎
  (‎fib 0 = 0، fib 1 = 1‎)؛ فهو ‎F(n+1)‎ لا ‎F(n+2)‎. والتقابلُ بين الأنماط والأعداد هو
  `Fold.fold`/`Fold.unfold` بـ‎f = 1، b = 1‎.
* `admissible_patterns_3`: الأنماطُ الجائزةُ بطول 3 ثلاثةٌ بالضبط: MMM، MMS، MSM؛
  والمستبعَدُ خمسة.
* `U3_by_pattern`: ‎87³ + 87²·29 + 87·29·87 = U(3) = 1,097,505‎.
* `patterns_of_the_cited_words`: أنماطُ الكلمات المستشهَد بها كما يُخرجها الجسر
  (`canonical116.bridge`، والمطابقةُ يفحصها `tests/tools/test_lean_ladder_conformance.py`):
  كَتَبَ MMM؛ كَانَ ولَيْسَ ولَيْتَ وإِنَّ MSM؛ لَعَلَّ وكَأَنَّ ولَكِنَّ MMSM.
* `kana_and_inna_are_indistinguishable`: كَانَ وإِنَّ بنمطٍ واحد، فلا يفرّق النموذجُ بين
  الفعل الناسخ والحرف الناسخ.
* `kana_is_not_kataba`: كَانَ وكَتَبَ نمطان مختلفان.
-/

namespace A116.Ladder

open A116 A116.Fold A116.Field112

/-- النمط: ‎true = M‎ (متحرّكة)، ‎false = S‎ (ساكنة). -/
def pat (w : List Cell) : List Bool := w.map fun c => !c.isSukun

theorem run_depends_only_on_pattern :
    ∀ (q : State) (w w' : List Cell), pat w = pat w' → run q w = run q w'
  | _, [], [], _ => rfl
  | _, [], _ :: _, h => by simp [pat] at h
  | _, _ :: _, [], h => by simp [pat] at h
  | q, a :: t, a' :: t', h => by
    simp only [pat, List.map_cons, List.cons.injEq] at h
    have ha : a.isSukun = a'.isSukun := by
      cases hs : a.isSukun <;> cases hs' : a'.isSukun <;> simp_all
    simp only [run_cons]
    rw [step_depends_only_on_sukun q a a' ha]
    exact run_depends_only_on_pattern _ t t' h.2

/-! ## العدّ -/

/-- الوزنُ مقسومًا على الحوامل. -/
def g : Nat → Nat
  | 0 => 1
  | 1 => 3
  | n + 2 => 3 * g (n + 1) + 3 * g n

private theorem step_identity (a x y : Nat) :
    87 * (29 * a * x) + 87 * 29 * (a * y) = 29 * 29 * a * (3 * x + 3 * y) := by
  simp only [Nat.mul_add, Nat.mul_assoc, Nat.mul_left_comm a]
  omega

private theorem U_g_pair : ∀ n, U n = 29 ^ n * g n ∧ U (n + 1) = 29 ^ (n + 1) * g (n + 1)
  | 0 => ⟨rfl, rfl⟩
  | n + 1 => by
    obtain ⟨h0, h1⟩ := U_g_pair n
    refine ⟨h1, ?_⟩
    rw [U_succ_succ, h1, h0]
    simp only [g, Nat.pow_succ]
    have := step_identity (29 ^ n) (g (n + 1)) (g n)
    simp only [Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm] at this ⊢
    omega

theorem U_eq_pow_mul_g (n : Nat) : U n = 29 ^ n * g n := (U_g_pair n).1

theorem g_values : (List.range 7).map g = [1, 3, 12, 45, 171, 648, 2457] := by decide

/-- فيبوناتشي: ‎fib 0 = 0، fib 1 = 1‎. -/
def fib : Nat → Nat
  | 0 => 0
  | 1 => 1
  | n + 2 => fib (n + 1) + fib n

private theorem S11 : ∀ n, S 1 1 n true = fib (n + 2) ∧ S 1 1 n false = fib (n + 1)
  | 0 => ⟨rfl, rfl⟩
  | n + 1 => by
    obtain ⟨ht, hf⟩ := S11 n
    constructor
    · simp only [S, ht, hf, Nat.one_mul, fib]
    · simp only [S, ht, Nat.one_mul]

/-- عددُ الأنماط الجائزة بطول n — وهو بالتقابل `Fold.fold 1 1 false` عددُ الكلمات
`Valid 1 1 false` بطول n (`fold_lt` و`unfold_spec`). -/
theorem pattern_count_fib (n : Nat) : S 1 1 n false = fib (n + 1) := (S11 n).2

/-! ## الطولُ 3 -/

def allPats : Nat → List (List Bool)
  | 0 => [[]]
  | n + 1 => (allPats n).flatMap fun p => [p ++ [true], p ++ [false]]

def admissibleB : List Bool → Bool
  | [] => true
  | b :: t => b && noSS (b :: t)
where
  noSS : List Bool → Bool
    | a :: b :: t => (a || b) && noSS (b :: t)
    | _ => true

theorem admissible_patterns_3 :
    (allPats 3).filter admissibleB = [[true, true, true], [true, true, false], [true, false, true]] ∧
      ((allPats 3).filter fun p => !admissibleB p).length = 5 := by
  decide

theorem U3_by_pattern : 87 ^ 3 + 87 ^ 2 * 29 + 87 * 29 * 87 = U 3 ∧ U 3 = 1097505 := by
  decide

/-! ## الكلماتُ المستشهَد بها، بذرّات الجسر -/

/-- رقمُ الحامل من حرفه في `carriers29`. -/
def carrierOf (ch : Char) : Fin carrierCount :=
  ⟨carriers29.idxOf ch % carrierCount, Nat.mod_lt _ (by decide)⟩

def atom (ch : Char) (h : Haraka) : Cell := ⟨carrierOf ch, h⟩

/-- كلُّ حرفٍ مستعمَلٍ أدناه حاملٌ معلَن، فلا يسقط `idxOf` إلى الصفر صامتًا. -/
theorem cited_letters_are_carriers :
    ['ك', 'ت', 'ب', 'ا', 'ن', 'ل', 'ي', 'س', 'ء', 'ع'].all (carriers29.contains ·) = true := by
  decide

open Haraka in
def kataba : List Cell := [atom 'ك' fatha, atom 'ت' fatha, atom 'ب' fatha]
open Haraka in
def kana : List Cell := [atom 'ك' fatha, atom 'ا' sukun, atom 'ن' fatha]
open Haraka in
def laysa : List Cell := [atom 'ل' fatha, atom 'ي' sukun, atom 'س' fatha]
open Haraka in
def layta : List Cell := [atom 'ل' fatha, atom 'ي' sukun, atom 'ت' fatha]
open Haraka in
def inna : List Cell := [atom 'ء' kasra, atom 'ن' sukun, atom 'ن' fatha]
open Haraka in
def laalla : List Cell := [atom 'ل' fatha, atom 'ع' fatha, atom 'ل' sukun, atom 'ل' fatha]
open Haraka in
def kaanna : List Cell := [atom 'ك' fatha, atom 'ء' fatha, atom 'ن' sukun, atom 'ن' fatha]
open Haraka in
def lakinna : List Cell := [atom 'ل' fatha, atom 'ك' kasra, atom 'ن' sukun, atom 'ن' fatha]

theorem patterns_of_the_cited_words :
    pat kataba = [true, true, true] ∧
    pat kana = [true, false, true] ∧ pat laysa = [true, false, true] ∧
    pat layta = [true, false, true] ∧ pat inna = [true, false, true] ∧
    pat laalla = [true, true, false, true] ∧ pat kaanna = [true, true, false, true] ∧
    pat lakinna = [true, true, false, true] := by
  decide

theorem kana_and_inna_are_indistinguishable (q : State) : run q kana = run q inna :=
  run_depends_only_on_pattern q kana inna (by decide)

theorem kana_is_not_kataba : pat kana ≠ pat kataba := by decide

end A116.Ladder
