import A116.HarfBridge.Takafu
import A116.NizamLine
import A116.Iltiqa
import A116.Harf.Satr
import A116.Harf.Thunai

/-!
# الجسر على السطر: الحدُّ حرفٌ في آلة Algebra هو `strictLineB` في الغانم (ADR ٤)

* `strictLineB_lineX`: ترخيصُ السطر في الغانم (`strictB` تسطيحًا و`seamsOK` على قطعه) هو قبولُ آلةٍ جاريةٍ
  واحدة (`lineX`) على خانات الغانم: آلةُ `strictB` بنمط مدّ الفرق، وذيلُ أصناف القطعة الجارية (آخرُ صنفين)،
  وفحصُ الحدّ بالذيل وصنفِ أوّل الكلمة التالية — لكلّ سطرٍ كلماتُه غيرُ فارغة.
* **`line_eq_strictLineB`**، **`lineWaqf_eq_strictLinePauseB`**: آلةُ Algebra على السطر هي ترخيصُ السطر في الغانم.
* **`join_eq_strictJoinB`**، **`joinWaqf_eq_strictJoinPauseB`**: والكلمتان هما `strictJoinB` بعينه (عبر `line_two`).
* `line_mutant_refuted`: حدٌّ لا يمنع المدَّ قبل ساكنٍ في الكلمة التالية (`MUTANT_MADD_ACROSS_HADD`) يقبل
  «يَا + الشَّافِعِينَ» ويرفضه `strictJoinB`.
* `binB_eq_strict`: الثنائيُّ (`src/entry.py::licensed`) هو `strictB` مقصورًا على ما لا يتجاور فيه ساكنان.
-/

set_option autoImplicit false

namespace HarfBridge

open A116 A116.Stages A116.Ternary A116.Hadd A116.Ladder A116.NizamHadd A116.NizamLine

/-! ## ١. الآلةُ الجارية على خانات الغانم -/

def resetFarq (m : Nat) (s : FS) (x : Cell) : FS :=
  if m = 2 ∧ x.carrier = carrierOf 'ل' then { s with g := .none } else s

def modeNext (m : Nat) (x : Cell) : Nat :=
  if m = 0 ∧ x = atom 'ء' .fatha then 1 else if m = 1 ∧ x = atom 'ا' .sukun then 2 else 3

structure XS where
  s : FS
  m : Nat
  t : List K
  deriving DecidableEq, Repr

/-- آخرُ صنفين. -/
def push : List K → K → List K
  | [], k => [k]
  | [a], k => [a, k]
  | [_, b], k => [b, k]
  | _, k => [k]

def pushAll (t : List K) (ks : List K) : List K := ks.foldl push t

def stepX (d : St → K → St) : Option XS → Cell → Option XS
  | none, _ => none
  | some ⟨s, m, t⟩, x =>
    (stepF d (some (resetFarq m s x)) x).map fun s' => ⟨s', modeNext m x, push t (kindOne s.prev x)⟩

def cellsX (d : St → K → St) : Option XS → List Cell → Option XS
  | o, [] => o
  | o, x :: t => cellsX d (stepX d o x) t

def acceptX (e : Pend → Bool) : Option XS → Bool
  | none => false
  | some ⟨s, _, _⟩ => s.st != .dead && e s.g

def crossT (t : List K) (y : K) : Bool := (t.getLast? == some .v && y == .c) || t == [.v, .c]

def boundX : Option XS → Cell → Option XS
  | none, _ => none
  | some ⟨s, m, t⟩, y => if crossT t (kindOne s.prev y) then none else some ⟨s, m, []⟩

def lineX (d : St → K → St) (e : Pend → Bool) : Option XS → List (List Cell) → Bool
  | o, [] => acceptX e o
  | o, [w] => acceptX e (cellsX d o w)
  | o, w :: v :: rest =>
    lineX d e (match v with
      | [] => cellsX d o w
      | y :: _ => boundX (cellsX d o w) y) (v :: rest)

def initX : XS := ⟨initS, 0, []⟩

/-! ## ٢. خواصُّ الجري -/

theorem cellsX_none (d : St → K → St) : ∀ w, cellsX d none w = none
  | [] => rfl
  | _ :: t => cellsX_none d t

theorem cellsX_append (d : St → K → St) : ∀ (o : Option XS) (a b : List Cell),
    cellsX d o (a ++ b) = cellsX d (cellsX d o a) b
  | _, [], _ => rfl
  | o, x :: t, b => cellsX_append d (stepX d o x) t b

theorem lineX_none (d : St → K → St) (e : Pend → Bool) : ∀ ws, lineX d e none ws = false
  | [] => rfl
  | [w] => by simp [lineX, cellsX_none, acceptX]
  | w :: v :: rest => by
    cases v with
    | nil => simp only [lineX, cellsX_none]; exact lineX_none d e _
    | cons y v' => simp only [lineX, cellsX_none, boundX]; exact lineX_none d e _

/-- قبولُ الآلة لا يقرأ الذيل. -/
theorem cellsX_tail (d : St → K → St) : ∀ (s : FS) (m : Nat) (t t' : List K) (w : List Cell),
    (cellsX d (some ⟨s, m, t⟩) w).map (fun x => (x.s, x.m)) =
      (cellsX d (some ⟨s, m, t'⟩) w).map (fun x => (x.s, x.m))
  | _, _, _, _, [] => rfl
  | s, m, t, t', x :: w => by
    simp only [cellsX, stepX]
    cases stepF d (some (resetFarq m s x)) x with
    | none => simp [cellsX_none]
    | some s' => exact cellsX_tail d s' _ _ _ w

theorem acceptX_tail (d : St → K → St) (e : Pend → Bool) (s : FS) (m : Nat) (t t' : List K)
    (w : List Cell) : acceptX e (cellsX d (some ⟨s, m, t⟩) w) = acceptX e (cellsX d (some ⟨s, m, t'⟩) w) := by
  have h := cellsX_tail d s m t t' w
  revert h
  cases cellsX d (some ⟨s, m, t⟩) w <;> cases cellsX d (some ⟨s, m, t'⟩) w <;> simp_all [acceptX]

/-- ما تحمله الآلةُ بعد كلمة: حالةُ آخرها، وذيلُ أصنافها. -/
theorem cellsX_some (d : St → K → St) : ∀ (s : FS) (m : Nat) (t : List K) (w : List Cell) (x : XS),
    cellsX d (some ⟨s, m, t⟩) w = some x → x.s.prev = lastH s.prev w ∧ x.t = pushAll t (kindGo s.prev w)
  | s, m, t, [], x, h => by simp [cellsX] at h; subst h; simp [lastH, kindGo, pushAll]
  | s, m, t, y :: w, x, h => by
    simp only [cellsX, stepX] at h
    cases hs : stepF d (some (resetFarq m s y)) y with
    | none => rw [hs] at h; simp only [Option.map] at h; rw [cellsX_none] at h; cases h
    | some s' =>
      rw [hs] at h; simp only [Option.map] at h
      have hp : s'.prev = some y.haraka := by
        simp only [stepF] at hs; split at hs <;> simp_all; rw [← hs]
      have := cellsX_some d s' _ _ w x h
      rw [hp] at this
      have hk : kindOne (resetFarq m s y).prev y = kindOne s.prev y := by
        unfold resetFarq; split <;> rfl
      exact ⟨by simpa [lastH] using this.1, by simpa [kindGo, pushAll, List.foldl] using this.2⟩

/-! ## ٣. `strictB` بلا تفريع: نمطُ مدّ الفرق في الآلة -/

theorem runF_none (d : St → K → St) (e : Pend → Bool) (w : List Cell) : runF d e none w = false := by
  cases w <;> rfl

theorem accept_cons (d : St → K → St) (e : Pend → Bool) (s : FS) (m : Nat) (t : List K) (x : Cell)
    (w : List Cell) : acceptX e (cellsX d (some ⟨s, m, t⟩) (x :: w)) =
      match stepF d (some (resetFarq m s x)) x with
      | none => false
      | some s' => acceptX e (cellsX d (some ⟨s', modeNext m x, push t (kindOne s.prev x)⟩) w) := by
  simp only [cellsX, stepX]
  cases stepF d (some (resetFarq m s x)) x <;> simp [cellsX_none, acceptX]

theorem runF_cons' (d : St → K → St) (e : Pend → Bool) (s : FS) (x : Cell) (w : List Cell) :
    runF d e (some s) (x :: w) = match stepF d (some s) x with
      | none => false
      | some s' => runF d e (some s') w := by
  rw [runF_cons]; cases stepF d (some s) x <;> simp [runF_none]

theorem reset_ne2 (m : Nat) (s : FS) (x : Cell) (h : m ≠ 2) : resetFarq m s x = s := by
  simp [resetFarq, h]

theorem reset_lam (s : FS) (x : Cell) (h : x.carrier = carrierOf 'ل') :
    resetFarq 2 s x = { s with g := .none } := by simp [resetFarq, h]

theorem reset_nolam (s : FS) (x : Cell) (h : x.carrier ≠ carrierOf 'ل') : resetFarq 2 s x = s := by
  simp [resetFarq, h]

theorem mode3 (x : Cell) : modeNext 3 x = 3 := by simp [modeNext]
theorem mode2 (x : Cell) : modeNext 2 x = 3 := by simp [modeNext]
theorem mode0_h : modeNext 0 (atom 'ء' .fatha) = 1 := by simp [modeNext]
theorem mode0 (x : Cell) (h : x ≠ atom 'ء' .fatha) : modeNext 0 x = 3 := by simp [modeNext, h]
theorem mode1_a : modeNext 1 (atom 'ا' .sukun) = 2 := by simp [modeNext]
theorem mode1 (x : Cell) (h : x ≠ atom 'ا' .sukun) : modeNext 1 x = 3 := by simp [modeNext, h]

theorem cellsX_mode3 (d : St → K → St) (e : Pend → Bool) : ∀ (s : FS) (t : List K) (w : List Cell),
    acceptX e (cellsX d (some ⟨s, 3, t⟩) w) = runF d e (some s) w
  | s, t, [] => rfl
  | s, t, x :: w => by
    rw [accept_cons, runF_cons', reset_ne2 3 s x (by decide), mode3]
    cases stepF d (some s) x with
    | none => rfl
    | some s' => exact cellsX_mode3 d e s' _ w

theorem mode_flat (d : St → K → St) (e : Pend → Bool) (T : List Cell → Bool)
    (hT : ∀ w, T w = if isFarq w then runF d e (some farqS) (w.drop 2) else runF d e (some initS) w)
    (h1 : stepF d (some initS) (atom 'ء' .fatha) = some ⟨some .fatha, .n, .none⟩)
    (h2 : stepF d (some ⟨some .fatha, .n, .none⟩) (atom 'ا' .sukun) = some ⟨some .sukun, .nv, .afterV⟩)
    (h0 : T [] = acceptX e (some initX)) :
    ∀ w, T w = acceptX e (cellsX d (some initX) w) := by
  intro w
  match w with
  | [] => exact h0
  | x :: t =>
    rw [hT]
    by_cases hx : x = atom 'ء' .fatha
    · subst hx
      rw [initX, accept_cons, reset_ne2 0 _ _ (by decide), h1, mode0_h]
      dsimp only
      match t with
      | [] => simp [isFarq, h1, acceptX, cellsX, runF]
      | y :: t =>
        rw [accept_cons]
        by_cases hy : y = atom 'ا' .sukun
        · subst hy
          rw [reset_ne2 1 _ _ (by decide), h2, mode1_a]
          dsimp only
          match t with
          | [] => simp [isFarq, runF_cons', h1, h2, acceptX, cellsX, runF]
          | z :: t =>
            rw [accept_cons]
            by_cases hz : z.carrier = carrierOf 'ل'
            · have hf : isFarq (atom 'ء' .fatha :: atom 'ا' .sukun :: z :: t) = true := by
                simp [isFarq, hz]
              simp only [hf, ↓reduceIte]
              rw [reset_lam _ _ hz, mode2]
              simp only [List.drop, runF_cons']
              have : ({ prev := some Haraka.sukun, st := St.nv, g := Pend.afterV, .. } : FS)
                  = ⟨some .sukun, .nv, .afterV⟩ := rfl
              show _ = match stepF d (some farqS) z with
                | none => false
                | some s' => acceptX e (cellsX d (some ⟨s', 3, _⟩) t)
              cases stepF d (some farqS) z with
              | none => rfl
              | some s' => exact (cellsX_mode3 d e s' _ t).symm
            · have hf : isFarq (atom 'ء' .fatha :: atom 'ا' .sukun :: z :: t) = false := by
                simp [isFarq, hz]
              simp only [hf, Bool.false_eq_true, ↓reduceIte]
              rw [reset_nolam _ _ hz, mode2, runF_cons', h1]
              simp only
              rw [runF_cons', h2]
              simp only
              rw [runF_cons']
              cases stepF d (some ⟨some .sukun, .nv, .afterV⟩) z with
              | none => rfl
              | some s' => exact (cellsX_mode3 d e s' _ t).symm
        · have hf : isFarq (atom 'ء' .fatha :: y :: t) = false := by
            cases t <;> simp [isFarq, hy]
          simp only [hf, Bool.false_eq_true, ↓reduceIte]
          rw [reset_ne2 1 _ _ (by decide), mode1 y hy, runF_cons', h1]
          simp only
          rw [runF_cons']
          cases stepF d (some ⟨some .fatha, .n, .none⟩) y with
          | none => rfl
          | some s' => exact (cellsX_mode3 d e s' _ t).symm
    · have hf : isFarq (x :: t) = false := by
        match t with
        | [] => rfl
        | [_] => rfl
        | _ :: _ :: _ => simp [isFarq, hx]
      simp only [hf, Bool.false_eq_true, ↓reduceIte]
      rw [initX, accept_cons, reset_ne2 0 _ _ (by decide), mode0 x hx,
        runF_cons']
      cases stepF d (some initS) x with
      | none => rfl
      | some s' => exact (cellsX_mode3 d e s' _ t).symm

/-! ## ٤. الحدودُ على القطع بذيل الأصناف -/

def chunksFrom : Option Haraka → List (List Cell) → List (List Role)
  | _, [] => []
  | p, w :: ws => (kindGo p w).zip w :: chunksFrom (lastH p w) ws

theorem splitBy_chunks : ∀ (p : Option Haraka) (ws : List (List Cell)),
    splitBy (ws.map List.length) ((kindGo p ws.flatten).zip ws.flatten) = chunksFrom p ws
  | _, [] => rfl
  | p, w :: ws => by
    simp only [List.map_cons, splitBy, List.flatten_cons, chunksFrom]
    have hk : (kindGo p w).length = w.length := kindGo_length p w
    rw [A116.Iltiqa.kindGo_append, List.zip_append hk]
    have hl : ((kindGo p w).zip w).length = w.length := by simp [hk]
    rw [List.take_left' hl, List.drop_left' hl, splitBy_chunks]

theorem chunks_from (ws : List (List Cell)) : chunks ws = chunksFrom none ws := by
  unfold chunks roles kindOf
  exact splitBy_chunks none ws

def endsK : List K → Bool
  | [a, b] => a == .v && b == .c
  | _ :: b :: b2 :: t => endsK (b :: b2 :: t)
  | _ => false

theorem endsVC_cons3 (a b b2 : Role) (r : List Role) : endsVC (a :: b :: b2 :: r) = endsVC (b :: b2 :: r) := by
  simp only [endsVC, azwaj, List.getLast?_cons_cons]

def crossK (ks : List K) (k2 : K) : Bool := (ks.getLast? == some .v && k2 == .c) || endsK ks

theorem endsVC_zip : ∀ (ks : List K) (cs : List Cell), ks.length = cs.length →
    endsVC (ks.zip cs) = endsK ks
  | [], _, _ => rfl
  | [a], [x], _ => rfl
  | [a, b], [x, y], _ => by simp [endsVC, azwaj, isVC, endsK]
  | a :: b :: b2 :: t, x :: y :: z :: u, h => by
    have ih := endsVC_zip (b :: b2 :: t) (y :: z :: u) (by simpa using h)
    simp only [List.zip_cons_cons] at ih ⊢
    rw [endsVC_cons3, ih]; rfl
  | [_], [], h | [_], _ :: _ :: _, h | [_, _], [], h | [_, _], [_], h | [_, _], _ :: _ :: _ :: _, h
  | _ :: _ :: _ :: _, [], h | _ :: _ :: _ :: _, [_], h | _ :: _ :: _ :: _, [_, _], h => by
    simp at h

theorem getLast_zip_fst : ∀ (ks : List K) (cs : List Cell), ks.length = cs.length →
    ((ks.zip cs).getLast?).map Prod.fst = ks.getLast?
  | [], _, _ => rfl
  | [a], [x], _ => rfl
  | a :: b :: t, x :: y :: u, h => by
    have ih := getLast_zip_fst (b :: t) (y :: u) (by simpa using h)
    simpa [List.getLast?_cons_cons] using ih
  | [_], [], h | [_], _ :: _ :: _, h | _ :: _ :: _, [], h | _ :: _ :: _, [_], h => by simp at h

theorem crossStr_zip (ks : List K) (cs : List Cell) (h : ks.length = cs.length) (hne : ks ≠ [])
    (k2 : K) (y : Cell) (r : List Role) :
    crossStr (ks.zip cs) ((k2, y) :: r) = crossK ks k2 := by
  have hl := getLast_zip_fst ks cs h
  have he := endsVC_zip ks cs h
  unfold crossStr crossK
  cases hz : (ks.zip cs).getLast? with
  | none =>
    rw [hz] at hl; simp at hl
    exact absurd (List.getLast?_eq_none_iff.mp hl.symm) hne
  | some x =>
    rw [hz] at hl; simp at hl
    simp only [List.head?_cons, isVC, he, ← hl]
    cases x.1 <;> cases k2 <;> simp

theorem push_push (t : List K) (a b : K) : push (push t a) b = [a, b] := by
  match t with
  | [] => rfl
  | [_] => rfl
  | [_, _] => rfl
  | _ :: _ :: _ :: _ => rfl

theorem crossT_two : ∀ (a b : K) (rest : List K) (k2 : K),
    crossT (pushAll [a, b] rest) k2 = crossK (a :: b :: rest) k2
  | a, b, [], k2 => by cases a <;> cases b <;> cases k2 <;> rfl
  | a, b, b2 :: r, k2 => by
    have ih := crossT_two b b2 r k2
    simp only [pushAll, List.foldl] at ih ⊢
    rw [show push [a, b] b2 = [b, b2] from rfl, ih]
    rfl

theorem crossT_pushAll (ks : List K) (hne : ks ≠ []) (k2 : K) :
    crossT (pushAll [] ks) k2 = crossK ks k2 := by
  match ks with
  | [a] => cases a <;> cases k2 <;> rfl
  | a :: b :: rest =>
    have : pushAll [] (a :: b :: rest) = pushAll [a, b] rest := by
      simp only [pushAll, List.foldl]; rw [push_push]
    rw [this, crossT_two]

def headK (p : Option Haraka) : List Cell → K
  | [] => .cv
  | y :: _ => kindOne p y

def seamsKT : Option Haraka → List (List Cell) → Bool
  | _, [] => true
  | _, [_] => true
  | p, w :: v :: rest => !crossK (kindGo p w) (headK (lastH p w) v) && seamsKT (lastH p w) (v :: rest)

theorem seams_from : ∀ (p : Option Haraka) (ws : List (List Cell)), (∀ w ∈ ws, w ≠ []) →
    seamsOK (chunksFrom p ws) = seamsKT p ws
  | _, [], _ => rfl
  | _, [_], _ => rfl
  | p, w :: v :: rest, hne => by
    obtain ⟨y, v', rfl⟩ : ∃ y v', v = y :: v' := by
      cases v with
      | nil => exact absurd rfl (hne [] (by simp))
      | cons y v' => exact ⟨y, v', rfl⟩
    have hw : w ≠ [] := hne w (by simp)
    have hk : kindGo p w ≠ [] := by
      intro h; have := kindGo_length p w; rw [h] at this; cases w <;> simp_all
    simp only [chunksFrom, seamsOK, seamsKT, kindGo, List.zip_cons_cons, headK]
    rw [crossStr_zip _ _ (kindGo_length p w) hk, ← seams_from (lastH p w) (_ :: rest)
      (fun u hu => hne u (by simp_all))]
    simp only [chunksFrom, kindGo, List.zip_cons_cons]

/-! ## ٥. السطرُ آلةً جاريةً واحدة -/

theorem lineX_split (d : St → K → St) (e : Pend → Bool) : ∀ (ws : List (List Cell)) (s : FS) (m : Nat),
    (∀ w ∈ ws, w ≠ []) →
    lineX d e (some ⟨s, m, []⟩) ws = (acceptX e (cellsX d (some ⟨s, m, []⟩) ws.flatten) && seamsKT s.prev ws)
  | [], _, _, _ => by simp [lineX, cellsX, seamsKT]
  | [w], _, _, _ => by simp [lineX, seamsKT]
  | w :: v :: rest, s, m, hne => by
    obtain ⟨y, v', rfl⟩ : ∃ y v', v = y :: v' := by
      cases v with
      | nil => exact absurd rfl (hne [] (by simp))
      | cons y v' => exact ⟨y, v', rfl⟩
    have hw : w ≠ [] := hne w (by simp)
    simp only [lineX, List.flatten_cons, cellsX_append, seamsKT, headK]
    cases hc : cellsX d (some ⟨s, m, []⟩) w with
    | none => simp [boundX, lineX_none, cellsX_none, acceptX]
    | some x =>
      obtain ⟨hp, ht⟩ := cellsX_some d s m [] w x hc
      rcases x with ⟨xs, xm, xt⟩
      simp only at hp ht
      have hk : kindGo s.prev w ≠ [] := by
        intro h; have := kindGo_length s.prev w; rw [h] at this; cases w <;> simp_all
      have hx := crossT_pushAll _ hk (kindOne xs.prev y)
      rw [← ht, hp] at hx
      simp only [boundX, hp]
      rw [ht] at hx ⊢
      by_cases hcr : crossT (pushAll [] (kindGo s.prev w)) (kindOne (lastH s.prev w) y) = true
      · simp only [hcr, ↓reduceIte, lineX_none]
        rw [hx] at hcr; simp [hcr]
      · simp only [hcr, Bool.false_eq_true, ↓reduceIte]
        rw [lineX_split d e ((y :: v') :: rest) xs xm (fun u hu => hne u (by simp_all))]
        rw [hx] at hcr
        simp only [Bool.not_eq_true] at hcr
        rw [← cellsX_append, ← List.flatten_cons, hcr,
          acceptX_tail d e xs xm (pushAll [] (kindGo s.prev w)) [], ← hp]
        simp

/-! ## ٦. ترخيصُ السطر في الغانم هو الآلةُ الجارية -/

theorem strictLineB_lineX (ws : List (List Cell)) (hne : ∀ w ∈ ws, w ≠ []) :
    strictLineB ws = lineX δC endW (some initX) ws := by
  unfold strictLineB
  rw [mode_flat δC endW strictB strictB_runF (by decide) (by decide)
      (by rw [strictB_runF]; rfl) ws.flatten,
    chunks_from, seams_from none ws hne, initX, lineX_split δC endW ws initS 0 hne]
  rfl

theorem strictLinePauseB_lineX (ws : List (List Cell)) (hne : ∀ w ∈ ws, w ≠ []) :
    strictLinePauseB ws = lineX δ endP (some initX) ws := by
  unfold strictLinePauseB
  rw [mode_flat δ endP strictPauseB strictPauseB_runF (by decide) (by decide)
      (by rw [strictPauseB_runF]; rfl) ws.flatten,
    chunks_from, seams_from none ws hne, initX, lineX_split δ endP ws initS 0 hne]
  rfl

/-! ## ٧. حالُ Algebra في الآلة الجارية -/

open Harf in
def modeOf : Hal → Nat
  | .bad' => 0
  | .hamzaAwwal => 1
  | .farq => 2
  | _ => 3

open Harf in
/-- ذيولُ الأصناف الممكنة لكلّ حال (آخرُ صنفين في القطعة الجارية). -/
def tailsOf : Hal → List (List K)
  | .bad' => [[]]
  | .hamzaAwwal => [[.cv]]
  | .farq => [[.cv, .v], [.v]]
  | .nawah _ => [[.cv], [.cv, .cv], [.v, .cv], [.c, .cv]]
  | .madd => [[.cv, .v], [.v]]
  | .qasir => [[.cv, .c], [.c]]
  | .tawilFarq => [[.v, .c]]
  | .tawil _ => [[.v, .c]]
  | .khatm => [[.c, .c], [.c]]
  | .maddHadd => []
  | .mayyit => [[]]

/-- صورُ الحال في الآلة الجارية؛ والختمُ (`khatm`) لا يكون إلّا وقفًا (`wq`). -/
def simX (wq : Bool) (a : Harf.Hal) : List (Option XS) :=
  match sim a with
  | none => [none]
  | some s => if a = .khatm ∧ wq = false then [none] else (tailsOf a).map fun t => some ⟨s, modeOf a, t⟩

def rel (wq : Bool) (a : Harf.Hal) (o : Option XS) : Bool := (simX wq a).contains o

theorem rel_wasl_cell : ∀ a ∈ Harf.Hal.all, ∀ o ∈ simX false a, ∀ x ∈ Harf.Khana.all,
    rel false (Harf.wasl a x) (stepX δC o (proj x)) = true := by decide +kernel

theorem rel_wasl_hadd : ∀ a ∈ Harf.Hal.all, a ≠ .bad' → ∀ o ∈ simX false a, ∀ x ∈ Harf.Khana.all,
    rel false (Harf.wasl (Harf.hadd a) x) (stepX δC (boundX o (proj x)) (proj x)) = true := by decide +kernel

theorem rel_wasl_acc : ∀ a ∈ Harf.Hal.all, ∀ o ∈ simX false a, Harf.qabilWasl a = acceptX endW o := by
  decide +kernel

theorem rel_waqf_cell : ∀ a ∈ Harf.Hal.all, ∀ o ∈ simX true a, ∀ x ∈ Harf.Khana.all,
    rel true (Harf.waqf a x) (stepX δ o (proj x)) = true := by decide +kernel

theorem rel_waqf_hadd : ∀ a ∈ Harf.Hal.all, a ≠ .bad' → ∀ o ∈ simX true a, ∀ x ∈ Harf.Khana.all,
    rel true (Harf.waqf (Harf.hadd a) x) (stepX δ (boundX o (proj x)) (proj x)) = true := by decide +kernel

theorem rel_waqf_acc : ∀ a ∈ Harf.Hal.all, ∀ o ∈ simX true a, Harf.qabilWaqf a = acceptX endP o := by
  decide +kernel

theorem not_bad' : ∀ a ∈ Harf.Hal.all, ∀ x ∈ Harf.Khana.all,
    Harf.wasl a x ≠ .bad' ∧ Harf.waqf a x ≠ .bad' := by decide +kernel

theorem init_rel (wq : Bool) : rel wq .bad' (some initX) = true := by cases wq <;> decide

theorem mem_of_rel {wq : Bool} {a : Harf.Hal} {o : Option XS} (h : rel wq a o = true) : o ∈ simX wq a := by
  simpa [rel] using h

/-! ## ٨. السطرُ كلُّه -/

section
variable (wq : Bool) (f : Harf.Hal → Harf.Khana → Harf.Hal) (d : St → K → St) (e : Pend → Bool)
  (q : Harf.Hal → Bool)
  (hcell : ∀ a ∈ Harf.Hal.all, ∀ o ∈ simX wq a, ∀ x ∈ Harf.Khana.all, rel wq (f a x) (stepX d o (proj x)) = true)
  (hhadd : ∀ a ∈ Harf.Hal.all, a ≠ .bad' → ∀ o ∈ simX wq a, ∀ x ∈ Harf.Khana.all,
    rel wq (f (Harf.hadd a) x) (stepX d (boundX o (proj x)) (proj x)) = true)
  (hacc : ∀ a ∈ Harf.Hal.all, ∀ o ∈ simX wq a, q a = acceptX e o)
  (hnb : ∀ a x, f a x ≠ .bad')

include hcell in
theorem cells_rel : ∀ (a : Harf.Hal) (o : Option XS) (w : List Harf.Khana), o ∈ simX wq a →
    cellsX d o (projW w) ∈ simX wq (Harf.run f a w)
  | _, _, [], h => h
  | a, o, x :: t, h => by
    simp only [projW, List.map_cons, cellsX, Harf.run]
    exact cells_rel _ _ t (mem_of_rel (hcell a (Harf.Hal.mem_all a) o h x (Harf.Khana.mem_all x)))

theorem run_ne_bad' (hnb : ∀ a x, f a x ≠ .bad') : ∀ (a : Harf.Hal) (w : List Harf.Khana), w ≠ [] →
    Harf.run f a w ≠ .bad'
  | _, [], h => absurd rfl h
  | a, [x], _ => by simpa [Harf.run] using hnb a x
  | a, x :: y :: t, _ => by
    simp only [Harf.run]; exact run_ne_bad' hnb _ (y :: t) (by simp)

include hcell hhadd hacc hnb in
/-- بعد حدٍّ معلَّق: الحالُ `hadd b` وما يقابله `boundX ob` قبل أوّل خانةٍ من الكلمة التالية. -/
theorem pending : ∀ (rest : List (List Harf.Khana)) (b : Harf.Hal) (ob : Option XS) (y : Harf.Khana)
    (v' : List Harf.Khana), ob ∈ simX wq b → b ≠ .bad' → (∀ w ∈ rest, w ≠ []) →
    q (Harf.runLine f (Harf.hadd b) ((y :: v') :: rest)) =
      lineX d e (boundX ob (proj y)) ((proj y :: projW v') :: rest.map projW)
  | [], b, ob, y, v', hob, hb, _ => by
    simp only [Harf.runLine, Harf.run, List.map_nil, lineX, cellsX]
    have h1 := mem_of_rel (hhadd b (Harf.Hal.mem_all b) hb ob hob y (Harf.Khana.mem_all y))
    have h2 := cells_rel wq f d hcell _ _ v' h1
    exact hacc _ (Harf.Hal.mem_all _) _ h2
  | (y2 :: v2) :: rest, b, ob, y, v', hob, hb, hne => by
    have h1 := mem_of_rel (hhadd b (Harf.Hal.mem_all b) hb ob hob y (Harf.Khana.mem_all y))
    have h2 := cells_rel wq f d hcell _ _ v' h1
    have hb2 : Harf.run f (f (Harf.hadd b) y) v' ≠ .bad' := by
      cases v' with
      | nil => simpa [Harf.run] using hnb (Harf.hadd b) y
      | cons _ _ => exact run_ne_bad' f hnb _ _ (by simp)
    have ih := pending rest _ _ y2 v2 h2 hb2 (fun w hw => hne w (by simp [hw]))
    simp only [Harf.runLine, Harf.run, List.map_cons, lineX, cellsX] at ih ⊢
    exact ih
  | [] :: rest, _, _, _, _, _, _, hne => absurd rfl (hne [] (by simp))

include hcell hhadd hacc hnb in
theorem line_rel (ws : List (List Harf.Khana)) (hne : ∀ w ∈ ws, w ≠ []) :
    q (Harf.runLine f .bad' ws) = lineX d e (some initX) (ws.map projW) := by
  match ws with
  | [] => exact hacc _ (Harf.Hal.mem_all _) _ (mem_of_rel (init_rel wq))
  | [w] =>
    simp only [Harf.runLine, List.map_cons, List.map_nil, lineX]
    exact hacc _ (Harf.Hal.mem_all _) _ (cells_rel wq f d hcell _ _ w (mem_of_rel (init_rel wq)))
  | w :: (y :: v') :: rest =>
    have hw : w ≠ [] := hne w (by simp)
    have h1 := cells_rel wq f d hcell _ _ w (mem_of_rel (init_rel wq))
    have := pending wq f d e q hcell hhadd hacc hnb rest (Harf.run f .bad' w) _ y v' h1
      (run_ne_bad' f hnb _ w hw) (fun u hu => hne u (by simp [hu]))
    simp only [Harf.runLine, List.map_cons, lineX]
    exact this
  | w :: [] :: rest => exact absurd rfl (hne [] (by simp))

end

/-! ## ٩. التكافؤُ على السطر وعلى الكلمتين -/

def projL (ws : List (List Harf.Khana)) : List (List Cell) := ws.map projW

theorem projL_ne (ws : List (List Harf.Khana)) (hne : ∀ w ∈ ws, w ≠ []) : ∀ w ∈ projL ws, w ≠ [] := by
  intro w hw
  simp only [projL, List.mem_map] at hw
  obtain ⟨u, hu, rfl⟩ := hw
  have := hne u hu
  cases u <;> simp_all [projW]

/-- **السطرُ وصلًا**: لكلّ سطرٍ كلماتُه غيرُ فارغة، آلةُ Algebra هي `strictLineB`. -/
theorem line_eq_strictLineB (ws : List (List Harf.Khana)) (hne : ∀ w ∈ ws, w ≠ []) :
    Harf.lineB ws = strictLineB (projL ws) := by
  rw [strictLineB_lineX _ (projL_ne ws hne), projL]
  exact line_rel false Harf.wasl δC endW Harf.qabilWasl
    (fun a ha o ho x hx => rel_wasl_cell a ha o ho x hx)
    (fun a ha hb o ho x hx => rel_wasl_hadd a ha hb o ho x hx)
    (fun a ha o ho => rel_wasl_acc a ha o ho)
    (fun a x => (not_bad' a (Harf.Hal.mem_all a) x (Harf.Khana.mem_all x)).1) ws hne

/-- **السطرُ وقفًا**. -/
theorem lineWaqf_eq_strictLinePauseB (ws : List (List Harf.Khana)) (hne : ∀ w ∈ ws, w ≠ []) :
    Harf.lineWaqfB ws = strictLinePauseB (projL ws) := by
  rw [strictLinePauseB_lineX _ (projL_ne ws hne), projL]
  exact line_rel true Harf.waqf δ endP Harf.qabilWaqf
    (fun a ha o ho x hx => rel_waqf_cell a ha o ho x hx)
    (fun a ha hb o ho x hx => rel_waqf_hadd a ha hb o ho x hx)
    (fun a ha o ho => rel_waqf_acc a ha o ho)
    (fun a x => (not_bad' a (Harf.Hal.mem_all a) x (Harf.Khana.mem_all x)).2) ws hne

theorem projW_ne {w : List Harf.Khana} (h : w ≠ []) : projW w ≠ [] := by
  cases w <;> simp_all [projW]

/-- **الكلمتان وصلًا**: آلةُ Algebra هي `strictJoinB` بعينه. -/
theorem join_eq_strictJoinB (l r : List Harf.Khana) (hl : l ≠ []) (hr : r ≠ []) :
    Harf.joinB l r = strictJoinB (projW l) (projW r) := by
  rw [Harf.joinB, line_eq_strictLineB [l, r] (by simp [hl, hr]), projL]
  exact line_two _ _ (projW_ne hl) (projW_ne hr)

/-- **الكلمتان وقفًا**: آلةُ Algebra هي `strictJoinPauseB` بعينه. -/
theorem joinWaqf_eq_strictJoinPauseB (l r : List Harf.Khana) (hl : l ≠ []) (hr : r ≠ []) :
    Harf.joinWaqfB l r = strictJoinPauseB (projW l) (projW r) := by
  rw [Harf.joinWaqfB, lineWaqf_eq_strictLinePauseB [l, r] (by simp [hl, hr]), projL]
  exact line_two_pause _ _ (projW_ne hl) (projW_ne hr)

/-! ## ١٠. الطفرة على الحدّ -/

open Harf in
/-- `MUTANT_MADD_ACROSS_HADD`: حدٌّ لا يمنع المدَّ قبل ساكنٍ في الكلمة التالية. -/
def haddMutant : Hal → Hal
  | .tawil _ | .tawilFarq => .mayyit
  | a => a

def joinMutantB (l r : List Harf.Khana) : Bool :=
  Harf.qabilWasl (Harf.run Harf.wasl (haddMutant (Harf.run Harf.wasl .bad' l)) r)

theorem line_mutant_refuted :
    joinMutantB Harf.yaa Harf.shshafiina = true ∧
    strictJoinB (projW Harf.yaa) (projW Harf.shshafiina) = false ∧
    ¬ ∀ l r, joinMutantB l r = strictJoinB (projW l) (projW r) := by
  have h : joinMutantB Harf.yaa Harf.shshafiina = true ∧
      strictJoinB (projW Harf.yaa) (projW Harf.shshafiina) = false := by decide +kernel
  exact ⟨h.1, h.2, fun hall => by
    have := hall Harf.yaa Harf.shshafiina; rw [h.1, h.2] at this; simp at this⟩

/-! ## ١١. الثنائيُّ (`src/entry.py::licensed`) بالنسبة إلى `strictB` -/

/-- **الحلّ**: الثنائيُّ هو `strictB` مقصورًا على ما لا يتجاور فيه ساكنان — لا تكافؤ، بل تقييدٌ مبرهَن. -/
theorem binB_eq_strict (w : List Harf.Khana) :
    Harf.binB w = (strictB (projW w) && Harf.noAdjFrom false w) := by
  rw [Harf.binB_eq, wasl_eq_strictB]

theorem binary_strict_sound (w : List Harf.Khana) (h : Harf.binB w = true) : strictB (projW w) = true := by
  rw [← wasl_eq_strictB]; exact Harf.binary_sound w h

theorem binary_strictly_smaller :
    strictB (projW Harf.hajja) = true ∧ Harf.binB Harf.hajja = false := by
  rw [← wasl_eq_strictB]; exact Harf.hajja_separates

end HarfBridge
