import Nabt.AlignedAcquisitionV2

/-! Sourceful finite citation/connected projection. Authored source interpretation,
JSON/compiler refinement, acoustics and unrestricted Arabic remain outside this law. -/
namespace Nabt.ConnectedAcquisitionV3
open Nabt.AlignedAcquisition (Entry Span Ending Status)
set_option maxRecDepth 20000
set_option maxHeartbeats 4000000

def lawId := "nabt.sourced-acquisition.v3"
def alphabetId := Nabt.AlignedAcquisition.alphabetId
abbrev Onset := Nabt.AlignedAcquisitionV2.Onset
inductive Article | none | moon | sun deriving DecidableEq, Repr
structure Reading where
  id : String
  canonical : String
  article : Article
  surfaces : List String
  passages : List String
  deriving DecidableEq, Repr

-- Generated from the frozen authored source/specification, not from evaluation cases.
def registry : List Reading := [
  ⟨"ARTICLE_HAQQ_U", "الْحَقُّ", .moon, ["الْحَقُّ", "اَلْحَقُّ", "ٱلْحَقُّ", "ٱَلْحَقُّ", "الْحَقُّ", "اَلْحَقُّ", "ٱلْحَقُّ", "ٱَلْحَقُّ"], ["sibawayhi_haqq_article", "mukhtar_haqq", "sibawayhi_article_initial_fatha", "qatr_case_marks"]⟩,
  ⟨"ARTICLE_QAWM_U", "الْقَوْمُ", .moon, ["الْقَوْمُ", "اَلْقَوْمُ", "ٱلْقَوْمُ", "ٱَلْقَوْمُ"], ["sibawayhi_article_initial_fatha", "mukhtar_qawm", "qatr_case_marks"]⟩,
  ⟨"ARTICLE_GHULAM_U", "الْغُلَامُ", .moon, ["الْغُلَامُ", "اَلْغُلَامُ", "ٱلْغُلَامُ", "ٱَلْغُلَامُ"], ["qatr_wasl_fatha", "mukhtar_ghulam", "qatr_case_marks"]⟩,
  ⟨"ARTICLE_RAJUL_U", "الرَّجُلُ", .sun, ["الرَّجُلُ", "اَلرَّجُلُ", "ٱلرَّجُلُ", "ٱَلرَّجُلُ", "الرَّجُلُ", "اَلرَّجُلُ", "ٱلرَّجُلُ", "ٱَلرَّجُلُ"], ["sibawayhi_article_sun", "sibawayhi_article_initial_fatha", "qatr_case_marks"]⟩,
  ⟨"ARTICLE_WALAD_U", "الْوَلَدُ", .moon, ["الْوَلَدُ", "اَلْوَلَدُ", "ٱلْوَلَدُ", "ٱَلْوَلَدُ", "الولدُ"], ["mukhtar_walad_and_awlad", "qatr_case_marks"]⟩,
  ⟨"ARTICLE_AWLAD_U", "الْأَوْلَادُ", .moon, ["الْأَوْلَادُ", "اَلْأَوْلَادُ", "ٱلْأَوْلَادُ", "ٱَلْأَوْلَادُ", "الأولادُ"], ["mukhtar_walad_and_awlad", "sibawayhi_awlad_occurrence", "qatr_case_marks"]⟩,
  ⟨"ARTICLE_AYN_U", "الْعَيْنُ", .moon, ["الْعَيْنُ", "اَلْعَيْنُ", "ٱلْعَيْنُ", "ٱَلْعَيْنُ"], ["natural_eye_senses", "natural_eye_definition", "natural_spring_definition", "qatr_case_marks"]⟩,
  ⟨"ARTICLE_JARIYA_U", "الْجَارِيَةُ", .moon, ["الْجَارِيَةُ", "اَلْجَارِيَةُ", "ٱلْجَارِيَةُ", "ٱَلْجَارِيَةُ"], ["natural_eye_senses", "natural_spring_definition", "qatr_case_marks"]⟩,
  ⟨"ARTICLE_BASIRA_U", "الْبَاصِرَةُ", .moon, ["الْبَاصِرَةُ", "اَلْبَاصِرَةُ", "ٱلْبَاصِرَةُ", "ٱَلْبَاصِرَةُ"], ["natural_eye_senses", "qatr_case_marks"]⟩,
  ⟨"ARTICLE_HAQQ_A", "الْحَقَّ", .moon, ["الْحَقَّ", "اَلْحَقَّ", "ٱلْحَقَّ", "ٱَلْحَقَّ", "الْحَقَّ", "اَلْحَقَّ", "ٱلْحَقَّ", "ٱَلْحَقَّ"], ["sibawayhi_haqq_article", "mukhtar_haqq", "sibawayhi_article_initial_fatha", "qatr_case_marks"]⟩,
  ⟨"ARTICLE_QAWM_A", "الْقَوْمَ", .moon, ["الْقَوْمَ", "اَلْقَوْمَ", "ٱلْقَوْمَ", "ٱَلْقَوْمَ"], ["sibawayhi_article_initial_fatha", "mukhtar_qawm", "qatr_case_marks"]⟩,
  ⟨"ARTICLE_GHULAM_A", "الْغُلَامَ", .moon, ["الْغُلَامَ", "اَلْغُلَامَ", "ٱلْغُلَامَ", "ٱَلْغُلَامَ"], ["qatr_wasl_fatha", "mukhtar_ghulam", "qatr_case_marks"]⟩,
  ⟨"ARTICLE_RAJUL_A", "الرَّجُلَ", .sun, ["الرَّجُلَ", "اَلرَّجُلَ", "ٱلرَّجُلَ", "ٱَلرَّجُلَ", "الرَّجُلَ", "اَلرَّجُلَ", "ٱلرَّجُلَ", "ٱَلرَّجُلَ"], ["sibawayhi_article_sun", "sibawayhi_article_initial_fatha", "qatr_case_marks"]⟩,
  ⟨"ARTICLE_WALAD_A", "الْوَلَدَ", .moon, ["الْوَلَدَ", "اَلْوَلَدَ", "ٱلْوَلَدَ", "ٱَلْوَلَدَ"], ["mukhtar_walad_and_awlad", "qatr_case_marks"]⟩,
  ⟨"ARTICLE_AWLAD_A", "الْأَوْلَادَ", .moon, ["الْأَوْلَادَ", "اَلْأَوْلَادَ", "ٱلْأَوْلَادَ", "ٱَلْأَوْلَادَ"], ["mukhtar_walad_and_awlad", "sibawayhi_awlad_occurrence", "qatr_case_marks"]⟩,
  ⟨"ARTICLE_AYN_A", "الْعَيْنَ", .moon, ["الْعَيْنَ", "اَلْعَيْنَ", "ٱلْعَيْنَ", "ٱَلْعَيْنَ"], ["natural_eye_senses", "natural_eye_definition", "natural_spring_definition", "qatr_case_marks"]⟩,
  ⟨"ARTICLE_JARIYA_A", "الْجَارِيَةَ", .moon, ["الْجَارِيَةَ", "اَلْجَارِيَةَ", "ٱلْجَارِيَةَ", "ٱَلْجَارِيَةَ"], ["natural_eye_senses", "natural_spring_definition", "qatr_case_marks"]⟩,
  ⟨"ARTICLE_BASIRA_A", "الْبَاصِرَةَ", .moon, ["الْبَاصِرَةَ", "اَلْبَاصِرَةَ", "ٱلْبَاصِرَةَ", "ٱَلْبَاصِرَةَ"], ["natural_eye_senses", "qatr_case_marks"]⟩,
  ⟨"ARTICLE_HAQQ_I", "الْحَقِّ", .moon, ["الْحَقِّ", "اَلْحَقِّ", "ٱلْحَقِّ", "ٱَلْحَقِّ", "الْحَقِّ", "اَلْحَقِّ", "ٱلْحَقِّ", "ٱَلْحَقِّ"], ["sibawayhi_haqq_article", "mukhtar_haqq", "sibawayhi_article_initial_fatha", "qatr_case_marks"]⟩,
  ⟨"ARTICLE_QAWM_I", "الْقَوْمِ", .moon, ["الْقَوْمِ", "اَلْقَوْمِ", "ٱلْقَوْمِ", "ٱَلْقَوْمِ"], ["sibawayhi_article_initial_fatha", "mukhtar_qawm", "qatr_case_marks"]⟩,
  ⟨"ARTICLE_GHULAM_I", "الْغُلَامِ", .moon, ["الْغُلَامِ", "اَلْغُلَامِ", "ٱلْغُلَامِ", "ٱَلْغُلَامِ"], ["qatr_wasl_fatha", "mukhtar_ghulam", "qatr_case_marks"]⟩,
  ⟨"ARTICLE_RAJUL_I", "الرَّجُلِ", .sun, ["الرَّجُلِ", "اَلرَّجُلِ", "ٱلرَّجُلِ", "ٱَلرَّجُلِ", "الرَّجُلِ", "اَلرَّجُلِ", "ٱلرَّجُلِ", "ٱَلرَّجُلِ"], ["sibawayhi_article_sun", "sibawayhi_article_initial_fatha", "qatr_case_marks"]⟩,
  ⟨"ARTICLE_WALAD_I", "الْوَلَدِ", .moon, ["الْوَلَدِ", "اَلْوَلَدِ", "ٱلْوَلَدِ", "ٱَلْوَلَدِ"], ["mukhtar_walad_and_awlad", "qatr_case_marks"]⟩,
  ⟨"ARTICLE_AWLAD_I", "الْأَوْلَادِ", .moon, ["الْأَوْلَادِ", "اَلْأَوْلَادِ", "ٱلْأَوْلَادِ", "ٱَلْأَوْلَادِ"], ["mukhtar_walad_and_awlad", "sibawayhi_awlad_occurrence", "qatr_case_marks"]⟩,
  ⟨"ARTICLE_AYN_I", "الْعَيْنِ", .moon, ["الْعَيْنِ", "اَلْعَيْنِ", "ٱلْعَيْنِ", "ٱَلْعَيْنِ"], ["natural_eye_senses", "natural_eye_definition", "natural_spring_definition", "qatr_case_marks"]⟩,
  ⟨"ARTICLE_JARIYA_I", "الْجَارِيَةِ", .moon, ["الْجَارِيَةِ", "اَلْجَارِيَةِ", "ٱلْجَارِيَةِ", "ٱَلْجَارِيَةِ"], ["natural_eye_senses", "natural_spring_definition", "qatr_case_marks"]⟩,
  ⟨"ARTICLE_BASIRA_I", "الْبَاصِرَةِ", .moon, ["الْبَاصِرَةِ", "اَلْبَاصِرَةِ", "ٱلْبَاصِرَةِ", "ٱَلْبَاصِرَةِ"], ["natural_eye_senses", "qatr_case_marks"]⟩,
  ⟨"ARTICLE_WALAD_DUAL", "الْوَلَدَانِ", .moon, ["الْوَلَدَانِ", "اَلْوَلَدَانِ", "ٱلْوَلَدَانِ", "ٱَلْوَلَدَانِ", "الولدانِ"], ["mukhtar_walad_and_awlad", "qatr_dual_plural_endings", "qatr_case_marks"]⟩,
  ⟨"QUMT_SPEAKER", "قُمْتُ", .none, ["قُمْتُ", "قمتُ"], ["qatr_qumt_pronoun", "sabban_ta_person"]⟩,
  ⟨"QUMT_ADDRESSEE_M", "قُمْتَ", .none, ["قُمْتَ", "قمتَ"], ["qatr_qumt_pronoun", "sabban_ta_person"]⟩,
  ⟨"QUMT_ADDRESSEE_F", "قُمْتِ", .none, ["قُمْتِ", "قمتِ"], ["qatr_qumt_pronoun", "sabban_ta_person"]⟩,
  ⟨"DHAHIB_SINGULAR", "ذَاهِبٌ", .none, ["ذَاهِبٌ", "ذاهبٌ"], ["ibn_aqil_dhahib"]⟩,
  ⟨"DHAHIB_DUAL", "ذَاهِبَانِ", .none, ["ذَاهِبَانِ", "ذاهبانِ"], ["ibn_aqil_dhahib", "qatr_dual_plural_endings"]⟩,
  ⟨"DHAHIB_PLURAL", "ذَاهِبُونَ", .none, ["ذَاهِبُونَ", "ذاهبونَ"], ["ibn_aqil_dhahib", "qatr_dual_plural_endings"]⟩
]

def candidateReadings (raw : String) : List Reading := registry.filter (fun r => r.surfaces.contains raw)
def select (raw : String) : Option Reading := match candidateReadings raw with | [r] => some r | _ => none
def rawWord (es : List Entry) : String := String.ofList (es.flatMap (fun e => e.span.raw))
def reading (es : List Entry) : Option Reading := select (rawWord es)
def isWord (es : List Entry) : Bool := !es.isEmpty && !es.any (fun e => e.decision.status == .boundary)
def words (gs : List (List Entry)) := gs.filter isWord

def sourceSpans (text : String) : List Span :=
  Nabt.AlignedAcquisition.locate 0 0 (Nabt.AlignedAcquisition.pieceTexts text.toList)

def canonicalEntries (r : Reading) (pause : Bool) : List Entry :=
  let es := Nabt.AlignedAcquisition.classifyWord none pause true none (sourceSpans r.canonical)
  match es with
  | [] => []
  | e :: rest =>
    if r.article == .none then es else
    let first := {e with decision := Nabt.AlignedAcquisition.licensed "ARTICLE_INITIAL" [⟨112, by decide⟩]}
    let rest := if r.article == .sun then
      match rest with
      | [] => []
      | l :: tail => {l with decision := Nabt.AlignedAcquisition.licensed "ARTICLE_SUN_LAM" []} :: tail
      else rest
    first :: rest

/-- Source spans always come from the original input, never the canonical template. -/
def copyDecisions (r : Reading) : List Entry → List Entry → List Entry
  | [], _ => []
  | e :: es, [] => {e with decision := Nabt.AlignedAcquisition.deferred "TEMPLATE_ALIGNMENT_FAILED"} :: copyDecisions r es []
  | e :: es, c :: cs =>
    {e with decision := {c.decision with rule := "FINITE:" ++ r.id ++ ":" ++ c.decision.rule}} :: copyDecisions r es cs

def deferGroup (reason : String) (es : List Entry) : List Entry :=
  es.map (Nabt.AlignedAcquisitionV2.deferEntry reason)

def citationGroup (pause : Bool) (es : List Entry) : List Entry :=
  if !isWord es || es.any (fun e => e.decision.status == .invalid) ||
      (Nabt.AlignedAcquisition.debt (es.map Entry.span)).isSome then es
  else match reading es with
  | some r =>
    let canonical := canonicalEntries r pause
    if canonical.length == es.length then copyDecisions r es canonical
    else deferGroup "TEMPLATE_ALIGNMENT_FAILED" es
  | none => if Nabt.AlignedAcquisitionV2.articleShaped (es.map Entry.span) then
      deferGroup "ARTICLE_READING_NOT_LICENSED" es else es

def citationGroups (ending : Ending) : List (List Entry) → List (List Entry)
  | [] => []
  | es :: rest => citationGroup (ending == .waqf && !rest.any isWord) es :: citationGroups ending rest

structure Request where
  base : Nabt.AlignedAcquisition.Request
  onset : Onset
  deriving DecidableEq, Repr

def citation (r : Request) : Nabt.AlignedAcquisition.Result :=
  ⟨r.base, citationGroups r.base.ending (Nabt.AlignedAcquisition.acquire r.base).groups⟩

def continuous (r : Request) (gs : List (List Entry)) : Bool :=
  !(words gs).isEmpty && r.base.text == String.intercalate " " ((words gs).map rawWord)

def shortFinal (es : List Entry) : Bool :=
  Nabt.AlignedAcquisition.complete es && (es.getLast?.any fun e =>
    match Nabt.AlignedAcquisition.rawVowels e.span with
    | [v] => (Nabt.AlignedAcquisition.ordinary v).any fun m =>
      m.val < 3 && e.decision.cells.getLast?.any (fun a => a.val % 4 == m.val)
    | _ => false)

def elide (es : List Entry) : List Entry :=
  match es with
  | [] => []
  | e :: rest => {e with decision := Nabt.AlignedAcquisition.licensed "ARTICLE_WASL_ELISION" []} :: rest

def realizeWord (onset : Onset) (joined : Bool) (previous : Option (List Entry))
    (es : List Entry) : List Entry :=
  if onset == .wordInitial then es
  else if !joined then deferGroup "BOUNDARY_CONTINUITY_UNLICENSED" es
  else match previous with
  | none => es
  | some prev =>
    if !shortFinal prev then deferGroup "CONTACT_REPAIR_NOT_IMPLEMENTED" es
    else match reading es with
    | some r => if r.article != .none then elide es else es
    | none => es

def realizeGroups (onset : Onset) (joined : Bool) :
    Option (List Entry) → List (List Entry) → List (List Entry)
  | _, [] => []
  | prev, es :: rest =>
    if isWord es then realizeWord onset joined prev es :: realizeGroups onset joined (some es) rest
    else es :: realizeGroups onset joined prev rest

structure Result where
  request : Request
  citation : Nabt.AlignedAcquisition.Result
  realization : Nabt.AlignedAcquisition.Result
  deriving DecidableEq, Repr

def acquire (r : Request) : Result :=
  let c := citation r
  ⟨r, c, ⟨r.base, realizeGroups r.onset (continuous r c.groups) none c.groups⟩⟩

def Result.status (r : Result) : String :=
  if r.citation.status == "INVALID_INPUT" then "INVALID_INPUT"
  else if r.citation.status != "ACQUIRED" then "DEFER"
  else r.realization.status

def Result.phraseCells (r : Result) : List Atom :=
  if r.request.onset == .connected && r.status == "ACQUIRED" then
    Nabt.AlignedAcquisition.emitted r.realization.entries else []

def verify (expected : Request) (claimed : Result) : Bool := claimed == acquire expected

theorem select_has_finite_witness (raw : String) (r : Reading) (h : select raw = some r) :
    r ∈ registry ∧ raw ∈ r.surfaces := by
  unfold select at h
  split at h
  next row eq =>
    have hr : row = r := Option.some.inj h
    subst row
    have mem : r ∈ candidateReadings raw := by rw [eq]; simp
    simpa [candidateReadings] using mem
  next => contradiction

theorem canonical_moon_projection (r : Reading) (pause : Bool) (first : Entry) (rest : List Entry)
    (moon : r.article = .moon)
    (parsed : Nabt.AlignedAcquisition.classifyWord none pause true none (sourceSpans r.canonical) = first :: rest) :
    canonicalEntries r pause =
      {first with decision := Nabt.AlignedAcquisition.licensed "ARTICLE_INITIAL" [⟨112, by decide⟩]} :: rest := by
  simp [canonicalEntries, parsed, moon]

theorem canonical_sun_projection (r : Reading) (pause : Bool) (first lam : Entry) (tail : List Entry)
    (sun : r.article = .sun)
    (parsed : Nabt.AlignedAcquisition.classifyWord none pause true none (sourceSpans r.canonical) = first :: lam :: tail) :
    canonicalEntries r pause =
      {first with decision := Nabt.AlignedAcquisition.licensed "ARTICLE_INITIAL" [⟨112, by decide⟩]} ::
      {lam with decision := Nabt.AlignedAcquisition.licensed "ARTICLE_SUN_LAM" []} :: tail := by
  simp [canonicalEntries, parsed, sun]

theorem copy_decisions_spans (r : Reading) (es cs : List Entry) :
    (copyDecisions r es cs).map Entry.span = es.map Entry.span := by
  induction es generalizing cs with
  | nil => rfl
  | cons e es ih => cases cs <;> simp [copyDecisions, ih]

theorem deferred_spans (reason : String) (es : List Entry) :
    (deferGroup reason es).map Entry.span = es.map Entry.span := by
  induction es with
  | nil => rfl
  | cons e es ih =>
    simp only [deferGroup, List.map_cons] at *
    rw [ih]
    unfold Nabt.AlignedAcquisitionV2.deferEntry
    split <;> rfl

theorem citation_group_spans (pause : Bool) (es : List Entry) :
    (citationGroup pause es).map Entry.span = es.map Entry.span := by
  unfold citationGroup
  split
  · rfl
  · split
    · dsimp only
      split
      · exact copy_decisions_spans _ _ _
      · exact deferred_spans _ _
    · split
      · exact deferred_spans _ _
      · rfl

theorem citation_groups_spans (ending : Ending) (gs : List (List Entry)) :
    ((citationGroups ending gs).flatten.map Entry.span) = gs.flatten.map Entry.span := by
  induction gs with
  | nil => rfl
  | cons g gs ih => simp [citationGroups, citation_group_spans, ih]

theorem elision_preserves_spans (es : List Entry) :
    (elide es).map Entry.span = es.map Entry.span := by cases es <;> rfl

theorem elision_deletes_only_first_cells (e : Entry) (rest : List Entry) :
    Nabt.AlignedAcquisition.emitted (elide (e :: rest)) = Nabt.AlignedAcquisition.emitted rest := rfl

theorem elision_keeps_original_head (e : Entry) (rest : List Entry) :
    (elide (e :: rest)).head? = some {e with decision := Nabt.AlignedAcquisition.licensed "ARTICLE_WASL_ELISION" []} := rfl

theorem realize_word_spans (onset : Onset) (joined : Bool) (prev : Option (List Entry)) (es : List Entry) :
    (realizeWord onset joined prev es).map Entry.span = es.map Entry.span := by
  unfold realizeWord
  split
  · rfl
  · split
    · exact deferred_spans _ _
    · cases prev with
      | none => rfl
      | some prev =>
        simp only
        split
        · exact deferred_spans _ _
        · split
          · split
            · exact elision_preserves_spans _
            · rfl
          · rfl

theorem realization_groups_spans (onset : Onset) (joined : Bool) (prev : Option (List Entry))
    (gs : List (List Entry)) :
    ((realizeGroups onset joined prev gs).flatten.map Entry.span) = gs.flatten.map Entry.span := by
  induction gs generalizing prev with
  | nil => rfl
  | cons g gs ih =>
    simp only [realizeGroups]
    split <;> simp [realize_word_spans, ih]

theorem acquire_spans (r : Request) :
    (acquire r).realization.entries.map Entry.span = sourceSpans r.base.text := by
  simp only [acquire, Nabt.AlignedAcquisition.Result.entries, realization_groups_spans,
    citation, citation_groups_spans]
  exact Nabt.AlignedAcquisition.acquire_spans r.base

theorem acquire_restores_source (r : Request) :
    String.ofList (((acquire r).realization.entries.map (fun e => e.span.raw)).flatten) = r.base.text := by
  have h := congrArg (List.map Span.raw) (acquire_spans r)
  simp only [List.map_map, sourceSpans, Nabt.AlignedAcquisition.locate_raw, Function.comp_def] at h
  rw [h, Nabt.AlignedAcquisition.pieceTexts_restore, String.ofList_toList]

theorem acquire_offsets_contiguous (r : Request) :
    Nabt.AlignedAcquisition.Contiguous 0 0 ((acquire r).realization.entries.map Entry.span) := by
  rw [acquire_spans]
  exact Nabt.AlignedAcquisition.locate_contiguous _ _ _

theorem initial_word_retained (es : List Entry) : realizeWord .connected true none es = es := rfl

theorem unguarded_contact_deferred (prev es : List Entry) (h : shortFinal prev = false) :
    realizeWord .connected true (some prev) es = deferGroup "CONTACT_REPAIR_NOT_IMPLEMENTED" es := by
  simp [realizeWord, h]

theorem finite_article_connected_elision (prev es : List Entry) (r : Reading)
    (guard : shortFinal prev = true) (matchReading : reading es = some r) (article : r.article ≠ .none) :
    realizeWord .connected true (some prev) es = elide es := by
  simp [realizeWord, guard, matchReading, article]

theorem verified_binding {expected : Request} {claimed : Result} (h : verify expected claimed = true) :
    claimed = acquire expected ∧ claimed.request = expected := by
  have same : claimed = acquire expected := by simpa [verify] using h
  exact ⟨same, by rw [same]; rfl⟩

def checkedPhrase (r : Result) : Bool :=
  r.request.onset == .connected && r.status == "ACQUIRED" &&
    (Law.machine (r.request.base.ending == .wasl)).final
      ((Law.machine (r.request.base.ending == .wasl)).run 0 r.phraseCells)

theorem checked_phrase_sound (r : Result) (h : checkedPhrase r = true) :
    r.request.onset = .connected ∧ r.status = "ACQUIRED" ∧
      (Law.machine (r.request.base.ending == .wasl)).Licensed 0 r.phraseCells := by
  simpa [checkedPhrase, Bool.and_eq_true, and_assoc] using h

theorem verified_phrase_sourceful {expected : Request} {claimed : Result}
    (verified : verify expected claimed = true) (shape : checkedPhrase claimed = true) :
    claimed.request = expected ∧
    String.ofList ((claimed.realization.entries.map (fun e => e.span.raw)).flatten) = expected.base.text ∧
    (Law.machine (expected.base.ending == .wasl)).Licensed 0 claimed.phraseCells := by
  have binding := verified_binding verified
  refine ⟨binding.2, ?_, ?_⟩
  · rw [binding.1]
    exact acquire_restores_source expected
  · have licensed := (checked_phrase_sound claimed shape).2.2
    simpa [binding.2] using licensed

end Nabt.ConnectedAcquisitionV3
