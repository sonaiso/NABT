import Nabt.AlignedAcquisition

/-!
Additive finite article readings under an explicit word-initial onset policy.
The registry and source scope are frozen in ARTICLE_ACQUISITION_V2_SPEC.md.
This is a representation law, not a proof of lexical identity or spoken Arabic.
Every source span and every unchanged decision is inherited from acquisition v1.
-/
namespace Nabt.AlignedAcquisitionV2

open Nabt.AlignedAcquisition (Entry Span Ending Status)

set_option maxRecDepth 20000
set_option maxHeartbeats 2000000

def lawId := "nabt.aligned-acquisition.v2"
def alphabetId := Nabt.AlignedAcquisition.alphabetId

inductive Onset | wordInitial | connected deriving DecidableEq, Repr
inductive ArticleReading | haqq | qawm | ghulam deriving DecidableEq, Repr

def ArticleReading.rule : ArticleReading → String
  | .haqq => "ARTICLE_HAQQ_INITIAL"
  | .qawm => "ARTICLE_QAWM_INITIAL"
  | .ghulam => "ARTICLE_GHULAM_INITIAL"

structure Request where
  base : Nabt.AlignedAcquisition.Request
  onset : Onset
  deriving DecidableEq, Repr

def initialAlif (raw : List Char) : Bool :=
  raw == ['ا'] || raw == ['ٱ'] || raw == ['ا', 'َ'] || raw == ['ٱ', 'َ']

def caseVowel (c : Char) : Bool := c == 'َ' || c == 'ُ' || c == 'ِ'

def ordinaryCase (head : Char) (raw : List Char) : Bool :=
  match raw with
  | [c, v] => c == head && caseVowel v
  | _ => false

def haqqFinal (raw : List Char) : Bool :=
  match raw with
  | ['ق', 'ّ', v] => caseVowel v
  | ['ق', v, 'ّ'] => caseVowel v
  | _ => false

/-- Entire, finite vocalized word signatures; a prefix alone is not a witness. -/
def articleReading (ps : List Span) : Option ArticleReading :=
  match ps.map Span.raw with
  | [a, l, h, q] =>
    if initialAlif a && l == ['ل', 'ْ'] && h == ['ح', 'َ'] && haqqFinal q
    then some .haqq else none
  | [a, l, q, w, m] =>
    if initialAlif a && l == ['ل', 'ْ'] && q == ['ق', 'َ'] &&
        w == ['و', 'ْ'] && ordinaryCase 'م' m
    then some .qawm else none
  | [a, l, gh, la, al, m] =>
    if initialAlif a && l == ['ل', 'ْ'] && gh == ['غ', 'ُ'] &&
        la == ['ل', 'َ'] && al == ['ا'] && ordinaryCase 'م' m
    then some .ghulam else none
  | _ => none

def articleShaped (ps : List Span) : Bool :=
  match ps with
  | a :: l :: _ =>
    (a.raw.head? == some 'ا' || a.raw.head? == some 'ٱ') && l.raw.head? == some 'ل'
  | _ => false

def onsetCells : List Atom := [Nabt.AlignedAcquisition.atom ⟨28, by decide⟩ ⟨0, by decide⟩]

def protectedEntry (e : Entry) : Bool :=
  e.decision.status == .boundary || e.decision.status == .invalid

def deferEntry (rule : String) (e : Entry) : Entry :=
  if protectedEntry e then e else { e with decision := Nabt.AlignedAcquisition.deferred rule }

def installOnset (reading : ArticleReading) : List Entry → List Entry
  | [] => []
  | e :: rest =>
    (if protectedEntry e then e else
      { e with decision := Nabt.AlignedAcquisition.licensed reading.rule onsetCells }) :: rest

def transformGroup (onset : Onset) (es : List Entry) : List Entry :=
  if onset == .connected then es.map (deferEntry "CONNECTED_ONSET_NOT_IMPLEMENTED")
  else if (Nabt.AlignedAcquisition.debt (es.map Entry.span)).isSome then es
  else match articleReading (es.map Entry.span) with
  | some reading => installOnset reading es
  | none => if articleShaped (es.map Entry.span) then
      es.map (deferEntry "ARTICLE_READING_NOT_LICENSED") else es

structure Result where
  request : Request
  groups : List (List Entry)
  deriving DecidableEq, Repr

def acquire (r : Request) : Result :=
  ⟨r, (Nabt.AlignedAcquisition.acquire r.base).groups.map (transformGroup r.onset)⟩

def Result.toV1 (r : Result) : Nabt.AlignedAcquisition.Result := ⟨r.request.base, r.groups⟩
def Result.entries (r : Result) : List Entry := r.groups.flatten
def wordEntries (r : Result) : List (List Entry) := Nabt.AlignedAcquisition.wordEntries r.toV1
def Result.status (r : Result) : String := r.toV1.status
def Result.reason (r : Result) : String := r.toV1.reason

private theorem deferEntry_span (rule : String) (e : Entry) :
    (deferEntry rule e).span = e.span := by
  unfold deferEntry
  split <;> rfl

private theorem installOnset_spans (reading : ArticleReading) (es : List Entry) :
    (installOnset reading es).map Entry.span = es.map Entry.span := by
  cases es with
  | nil => rfl
  | cons e es =>
    simp only [installOnset, List.map_cons]
    split <;> rfl

private theorem deferEntries_spans (rule : String) (es : List Entry) :
    (es.map (deferEntry rule)).map Entry.span = es.map Entry.span := by
  simp only [List.map_map]
  apply List.map_congr_left
  intro e _
  exact deferEntry_span rule e

private theorem transformGroup_spans (onset : Onset) (es : List Entry) :
    (transformGroup onset es).map Entry.span = es.map Entry.span := by
  unfold transformGroup
  split
  · exact deferEntries_spans _ _
  · split
    · rfl
    · split
      · exact installOnset_spans _ _
      · split
        · exact deferEntries_spans _ _
        · rfl

private theorem transformGroups_spans (onset : Onset) (gs : List (List Entry)) :
    ((gs.map (transformGroup onset)).flatten.map Entry.span) = gs.flatten.map Entry.span := by
  induction gs with
  | nil => rfl
  | cons g gs ih =>
    simp only [List.map_cons, List.flatten_cons, List.map_append, transformGroup_spans, ih]

/-- A v2 representation decision neither creates nor removes a source span. -/
theorem acquire_spans (r : Request) :
    (acquire r).entries.map Entry.span = Nabt.AlignedAcquisition.locate 0 0 (Nabt.AlignedAcquisition.pieceTexts r.base.text.toList) := by
  simp only [acquire, Result.entries, transformGroups_spans]
  exact Nabt.AlignedAcquisition.acquire_spans r.base

theorem acquire_restores_source (r : Request) :
    String.ofList (((acquire r).entries.map (fun e => e.span.raw)).flatten) = r.base.text := by
  have h := congrArg (List.map Span.raw) (acquire_spans r)
  simp only [List.map_map, Nabt.AlignedAcquisition.locate_raw, Function.comp_def] at h
  rw [h, Nabt.AlignedAcquisition.pieceTexts_restore, String.ofList_toList]

theorem acquire_offsets_contiguous (r : Request) :
    Nabt.AlignedAcquisition.Contiguous 0 0 ((acquire r).entries.map Entry.span) := by
  rw [acquire_spans]
  exact Nabt.AlignedAcquisition.locate_contiguous _ _ _

theorem acquired_no_pending {r : Result} (h : r.status = "ACQUIRED") :
    ∀ e ∈ r.entries, e.decision.status = .licensed ∨ e.decision.status = .boundary :=
  Nabt.AlignedAcquisition.acquired_no_pending h

private theorem deferred_head_not_licensed (rule : String) (e : Entry) :
    (deferEntry rule e).decision.status ≠ .licensed := by
  unfold deferEntry protectedEntry
  split
  next hp =>
    simp only [Bool.or_eq_true, beq_iff_eq] at hp
    rcases hp with hp | hp <;> simp [hp]
  · simp [Nabt.AlignedAcquisition.deferred]

/-- Every *new* licensed first entry requires an exact finite reading witness.
The unchanged v1 entries remain governed by v1, not by an article-prefix guess. -/
theorem licensed_override_has_finite_witness (es : List Entry) (e : Entry) (rest : List Entry)
    (changed : transformGroup .wordInitial es ≠ es)
    (out : transformGroup .wordInitial es = e :: rest)
    (licensed : e.decision.status = .licensed) :
    ∃ reading, articleReading (es.map Entry.span) = some reading ∧
      transformGroup .wordInitial es = installOnset reading es ∧
      e.decision = Nabt.AlignedAcquisition.licensed reading.rule onsetCells := by
  by_cases hd : (Nabt.AlignedAcquisition.debt (es.map Entry.span)).isSome = true
  · simp [transformGroup, hd] at changed
  · cases hr : articleReading (es.map Entry.span) with
    | none =>
      by_cases ha : articleShaped (es.map Entry.span) = true
      · simp [transformGroup, hd, hr, ha] at out
        cases es with
        | nil => simp at out
        | cons first tail =>
          have he := (List.cons.inj out).1
          have hl : (deferEntry "ARTICLE_READING_NOT_LICENSED" first).decision.status = .licensed := by
            rw [he]
            exact licensed
          exact False.elim (deferred_head_not_licensed _ _ hl)
      · simp [transformGroup, hd, hr, ha] at changed
    | some reading =>
      have ht : transformGroup .wordInitial es = installOnset reading es := by
        simp [transformGroup, hd, hr]
      refine ⟨reading, rfl, ht, ?_⟩
      rw [ht] at out changed
      cases es with
      | nil => simp [installOnset] at out
      | cons first tail =>
        by_cases hp : protectedEntry first = true
        · simp [installOnset, hp] at changed
        · simp only [installOnset, hp] at out
          have he := (List.cons.inj out).1
          exact congrArg Entry.decision he.symm

/-- The only inserted onset is the typed hamza+fatha cell; no silent-lām bypass. -/
theorem article_onset_cells (reading : ArticleReading) (e : Entry) (rest : List Entry)
    (h : protectedEntry e = false) :
    installOnset reading (e :: rest) =
      { e with decision := Nabt.AlignedAcquisition.licensed reading.rule [⟨112, by decide⟩] } :: rest := by
  simp only [installOnset, h, Bool.false_eq_true, ↓reduceIte]
  rfl

def verify (expected : Request) (claimed : Result) : Bool := claimed == acquire expected

/-- Replay binds all independent input fields, including onset and ending. -/
theorem verified_binding {expected : Request} {claimed : Result} (h : verify expected claimed = true) :
    claimed = acquire expected ∧ claimed.request = expected := by
  have he : claimed = acquire expected := by simpa only [verify, beq_iff_eq] using h
  exact ⟨he, by rw [he]; rfl⟩

def handoff (onset : Onset) (es : List Entry) : Option (List Atom) :=
  if onset == .wordInitial then Nabt.AlignedAcquisition.handoff es else none

/-- Connected mode cannot accidentally become a complete v1 word either:
its actual transformed entries contain no licensed piece. -/
theorem connected_no_handoff (es : List Entry) :
    Nabt.AlignedAcquisition.handoff (transformGroup .connected es) = none := by
  cases hh : Nabt.AlignedAcquisition.handoff (transformGroup .connected es) with
  | none => rfl
  | some cells =>
    have hc := Nabt.AlignedAcquisition.handoff_complete hh
    obtain ⟨e, he⟩ := List.exists_mem_of_ne_nil _ hc.1
    have hl := hc.2.1 e he
    simp only [transformGroup, beq_self_eq_true, ↓reduceIte, List.mem_map] at he
    obtain ⟨before, _, hb⟩ := he
    rw [← hb] at hl
    exact False.elim (deferred_head_not_licensed _ _ hl)

def checkedHandoff (onset : Onset) (wasl : Bool) (es : List Entry) : Bool :=
  match handoff onset es with
  | none => false
  | some cells => (Law.machine wasl).final ((Law.machine wasl).run 0 cells)

theorem checkedHandoff_sound {onset : Onset} {wasl : Bool} {es : List Entry}
    (h : checkedHandoff onset wasl es = true) :
    onset = .wordInitial ∧ ∃ cells, Nabt.AlignedAcquisition.handoff es = some cells ∧
      (Law.machine wasl).Licensed 0 cells ∧ es ≠ [] ∧
      (∀ e ∈ es, e.decision.status = .licensed) ∧ cells = Nabt.AlignedAcquisition.emitted es := by
  cases onset with
  | connected => simp [checkedHandoff, handoff] at h
  | wordInitial =>
    refine ⟨rfl, ?_⟩
    simp only [checkedHandoff, handoff, beq_self_eq_true, ↓reduceIte] at h
    cases he : Nabt.AlignedAcquisition.handoff es with
    | none => simp only [he, Bool.false_eq_true] at h
    | some cells =>
      simp only [he] at h
      have hc := Nabt.AlignedAcquisition.handoff_complete he
      exact ⟨cells, rfl, h, hc.1, hc.2.1, hc.2.2⟩

/-- The existing sound-shape machine rejects every silent initial cell,
regardless of the following cells. Citation acquisition does not relax this. -/
theorem silent_initial_rejected (wasl : Bool) (a : Atom) (tail : List Atom)
    (silent : a.val % 4 = 3) : (Law.machine wasl).run 0 (a :: tail) = 96 := by
  have hs : Law.step 0 a = 96 := by
    have hm : Law.toSlge a.val % 4 = 3 := (Law.permutation_mark a).trans silent
    simp [Law.step, Law.rawStep, hm]
  simp only [Machine.run, Law.machine, hs]
  exact Law.run_dead wasl tail

end Nabt.AlignedAcquisitionV2
