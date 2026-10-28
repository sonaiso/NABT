import Nabt.EpistemicMeasurement

/-!
Source-bound lifecycle of a supplied evidence ledger. Sources, interpretations,
and lineage remain explicit premises. The added readiness filter is not a new
linguistic or world-truth license. The original EM law supplies all qualified
observation classification. Full episode binding distinguishes historical replay
from verification against an independently supplied current episode.
-/

namespace Nabt.EvidenceLifecycleV1

open EpistemicMeasurement

def lawId : String := "nabt.evidence-lifecycle.v1"
def schema : String := "nabt.evidence-lifecycle.episode.v1"

structure OriginBinding where
  originId : String
  source : Source
  rank : Nat
  deriving DecidableEq, Repr

structure SourceBoundContext where
  base : Context
  bindings : List OriginBinding
  deriving DecidableEq, Repr

def rankOf (bindings : List OriginBinding) (id : String) : Nat :=
  ((bindings.find? (fun binding => binding.originId == id)).map OriginBinding.rank).getD 0

def Ranked (ctx : SourceBoundContext) : Prop :=
  ∀ node ∈ ctx.base.origins, ∀ parent ∈ node.parents,
    rankOf ctx.bindings parent < rankOf ctx.bindings node.id

instance (ctx : SourceBoundContext) : Decidable (Ranked ctx) :=
  inferInstanceAs (Decidable (∀ node ∈ ctx.base.origins, ∀ parent ∈ node.parents, _))

/-- Structural validity is about the complete supplied graph, not its authenticity. -/
def WellFormed (ctx : SourceBoundContext) (query : Query) : Prop :=
  let ids := ctx.base.origins.map Origin.id
  ids.Nodup ∧ (ctx.bindings.map OriginBinding.originId).Nodup ∧
  (ctx.base.interpretations.map Evidence.id).Nodup ∧
  (ctx.base.activeSources.map (fun source => source.identity)).Nodup ∧
  query.origin ∈ ids ∧
  (∀ id ∈ ids, ∃ binding ∈ ctx.bindings, binding.originId = id) ∧
  (∀ binding ∈ ctx.bindings, binding.originId ∈ ids) ∧
  (∀ node ∈ ctx.base.origins, node.parents.Nodup ∧ ∀ parent ∈ node.parents, parent ∈ ids) ∧
  (∀ evidence ∈ ctx.base.interpretations,
    evidence.origin ∈ ids ∧ evidence.ancestry.Nodup ∧ ∀ id ∈ evidence.ancestry, id ∈ ids) ∧
  Ranked ctx

instance (ctx : SourceBoundContext) (query : Query) : Decidable (WellFormed ctx query) :=
  inferInstanceAs (Decidable (_ ∧ _ ∧ _ ∧ _ ∧ _ ∧ _ ∧ _ ∧ _ ∧ _ ∧ _))

def DependencyReady (ctx : SourceBoundContext) (evidence : Evidence) : Prop :=
  (∃ binding ∈ ctx.bindings,
    binding.originId = evidence.origin ∧ binding.source = evidence.source) ∧
  evidence.origin ∈ evidence.ancestry ∧
  ClosedAncestry ctx.base.origins evidence.ancestry ∧
  ∀ id ∈ evidence.ancestry, ∃ binding ∈ ctx.bindings,
    binding.originId = id ∧ binding.source ∈ ctx.base.activeSources

instance (ctx : SourceBoundContext) (evidence : Evidence) :
    Decidable (DependencyReady ctx evidence) :=
  inferInstanceAs (Decidable (_ ∧ _ ∧ _ ∧ ∀ id ∈ evidence.ancestry,
    ∃ binding ∈ ctx.bindings, _ ∧ _))

def dependencyReady (ctx : SourceBoundContext) (evidence : Evidence) : Bool :=
  decide (DependencyReady ctx evidence)

def projected (ctx : SourceBoundContext) : Context :=
  { ctx.base with interpretations := ctx.base.interpretations.filter (dependencyReady ctx) }

def readyIds (ctx : SourceBoundContext) : List String :=
  (ctx.base.interpretations.filter (dependencyReady ctx)).map Evidence.id

def blockedIds (ctx : SourceBoundContext) : List String :=
  (ctx.base.interpretations.filter (fun evidence => !dependencyReady ctx evidence)).map Evidence.id

def affectedIds (before after : SourceBoundContext) : List String :=
  (after.base.interpretations.filter (fun evidence =>
    dependencyReady before evidence != dependencyReady after evidence)).map Evidence.id

/-- Budget is charged to the original ledger, never the filtered projection. -/
def scopedReceipt (ctx : SourceBoundContext) (query : Query) (budget : Nat) : Receipt :=
  if ctx.base.interpretations.length ≤ budget then
    receipt (projected ctx) query budget
  else ⟨.resourceLimit, [], [], []⟩

inductive UpdateKind where
  | withdraw | activate | replace
  deriving DecidableEq, Repr

structure Update where
  eventId : String
  kind : UpdateKind
  source : Source
  replacement : Option Source
  reason : String
  deriving DecidableEq, Repr

structure Episode where
  episodeId : String
  query : Query
  initial : SourceBoundContext
  budget : Nat
  updates : List Update
  deriving DecidableEq, Repr

inductive Error where
  | invalid (reason : String)
  | resourceLimit (reason : String)
  deriving DecidableEq, Repr

structure SourceState where
  active : List Source
  registered : List Source
  deriving DecidableEq, Repr

def initialInventory (ctx : SourceBoundContext) : List Source :=
  ctx.base.activeSources ++ ctx.bindings.map OriginBinding.source ++
    ctx.base.interpretations.map Evidence.source

def ConsistentSources (sources : List Source) : Prop :=
  ∀ left ∈ sources, ∀ right ∈ sources,
    left.identity = right.identity → left.revision = right.revision → left.content = right.content

instance (sources : List Source) : Decidable (ConsistentSources sources) :=
  inferInstanceAs (Decidable (∀ left ∈ sources, ∀ right ∈ sources, _ → _ → _))

def withdrawSources (sources : List Source) (source : Source) : List Source :=
  sources.filter (fun current => decide (current ≠ source))

/-- Events change availability only. Old origin bindings and evidence are retained. -/
def advance (state : SourceState) (update : Update) : Except Error SourceState := do
  let next ← match update.kind with
    | .withdraw =>
      if update.replacement.isSome then .error (.invalid "withdraw has a replacement")
      else if update.source ∉ state.registered then .error (.invalid "unknown withdrawal target")
      else .ok { state with active := withdrawSources state.active update.source }
    | .activate =>
      if update.replacement.isSome then .error (.invalid "activate has a replacement")
      else if update.source ∉ state.registered then .error (.invalid "unknown activation target")
      else if update.source ∈ state.active then .ok state
      else if state.active.any (fun source => source.identity == update.source.identity) then
        .error (.invalid "another revision is active; replace explicitly")
      else .ok { state with active := state.active ++ [update.source] }
    | .replace => match update.replacement with
      | none => .error (.invalid "replacement is required")
      | some replacement =>
        if update.source ∉ state.active then .error (.invalid "replacement target is inactive")
        else if replacement.identity ≠ update.source.identity then .error (.invalid "replacement changes identity")
        else if replacement.revision = update.source.revision then .error (.invalid "replacement requires a new revision")
        else if ¬ ConsistentSources (state.registered ++ [replacement]) then
          .error (.invalid "source identity/revision content collision")
        else .ok ⟨withdrawSources state.active update.source ++ [replacement],
          state.registered ++ [replacement]⟩
  if next.active.length > 64 then .error (.resourceLimit "active source limit") else .ok next

def withActive (ctx : SourceBoundContext) (active : List Source) : SourceBoundContext :=
  { ctx with base := { ctx.base with activeSources := active } }

structure Step where
  step : Nat
  eventId : Option String
  activeSources : List Source
  receipt : Receipt
  dependencyReadyIds : Option (List String)
  dependencyBlockedIds : Option (List String)
  affectedIds : Option (List String)
  deriving DecidableEq, Repr

def makeStep (episode : Episode) (index : Nat) (event : Option String)
    (active : List Source) (previous : Option (List Source)) : Step :=
  let ctx := withActive episode.initial active
  let enough := ctx.base.interpretations.length ≤ episode.budget
  ⟨index, event, active, scopedReceipt ctx episode.query episode.budget,
    if enough then some (readyIds ctx) else none,
    if enough then some (blockedIds ctx) else none,
    if enough then some (match previous with
      | none => []
      | some before => affectedIds (withActive episode.initial before) ctx) else none⟩

def runUpdates (episode : Episode) : List Update → Nat → SourceState → Except Error (List Step)
  | [], _, _ => .ok []
  | update :: rest, index, state => do
    let next ← advance state update
    let tail ← runUpdates episode rest (index + 1) next
    return makeStep episode index (some update.eventId) next.active (some state.active) :: tail

def replay (episode : Episode) : Except Error (List Step) := do
  if ¬ WellFormed episode.initial episode.query then
    throw (.invalid "invalid origin graph, bindings, or ledger identities")
  if ¬ (episode.updates.map Update.eventId).Nodup then throw (.invalid "duplicate event identity")
  let inventory := initialInventory episode.initial
  if ¬ ConsistentSources inventory then throw (.invalid "source identity/revision content collision")
  let initial : SourceState := ⟨episode.initial.base.activeSources, inventory⟩
  let tail ← runUpdates episode episode.updates 1 initial
  return makeStep episode 0 none initial.active none :: tail

structure Report where
  binding : Episode
  steps : List Step
  deriving DecidableEq, Repr

def evaluate (episode : Episode) : Except Error Report := do
  return ⟨episode, ← replay episode⟩

def verify (episode : Episode) (report : Report) : Bool :=
  match evaluate episode with
  | .error _ => false
  | .ok actual => decide (actual = report)

theorem dependency_ready_exact (ctx : SourceBoundContext) (evidence : Evidence) :
    dependencyReady ctx evidence = true ↔ DependencyReady ctx evidence := by
  simp [dependencyReady]

theorem projected_admissible_exact (ctx : SourceBoundContext) (query : Query) (evidence : Evidence) :
    Admissible (projected ctx) query evidence ↔
      Admissible ctx.base query evidence ∧ DependencyReady ctx evidence := by
  simp [Admissible, projected, dependencyReady, and_assoc, and_left_comm, and_comm]

theorem selected_refines_em (ctx : SourceBoundContext) (query : Query) (evidence : Evidence)
    (selected : evidence ∈ EpistemicMeasurement.selected (projected ctx) query) :
    Admissible ctx.base query evidence :=
  ((projected_admissible_exact ctx query evidence).mp
    ((selected_exact (projected ctx) query evidence).mp selected)).1

theorem selected_is_dependency_ready (ctx : SourceBoundContext) (query : Query) (evidence : Evidence)
    (selected : evidence ∈ EpistemicMeasurement.selected (projected ctx) query) :
    DependencyReady ctx evidence :=
  ((projected_admissible_exact ctx query evidence).mp
    ((selected_exact (projected ctx) query evidence).mp selected)).2

theorem ready_transitive_source_active (ctx : SourceBoundContext) (evidence : Evidence)
    (ready : DependencyReady ctx evidence) (ancestor : String)
    (path : Path ctx.base.origins evidence.origin ancestor) :
    ∃ binding ∈ ctx.bindings, binding.originId = ancestor ∧ binding.source ∈ ctx.base.activeSources :=
  ready.2.2.2 ancestor (path_stays_in_closed_ancestry ctx.base.origins evidence.ancestry
    ready.2.2.1 ready.2.1 path)

/-- An inactive bound ancestor prevents readiness. Uniqueness prevents aliases
from substituting a different source for that same declared origin. -/
theorem inactive_ancestor_blocks (ctx : SourceBoundContext) (evidence : Evidence)
    (ancestor : String) (source : Source)
    (bindingExact : ∀ binding ∈ ctx.bindings, binding.originId = ancestor → binding.source = source)
    (path : Path ctx.base.origins evidence.origin ancestor)
    (inactive : source ∉ ctx.base.activeSources) : ¬ DependencyReady ctx evidence := by
  intro ready
  obtain ⟨binding, member, same, active⟩ := ready_transitive_source_active ctx evidence ready ancestor path
  exact inactive ((bindingExact binding member same) ▸ active)

theorem grammar_not_selected (ctx : SourceBoundContext) (query : Query) (evidence : Evidence)
    (grammar : evidence.kind = .grammar) :
    evidence ∉ EpistemicMeasurement.selected (projected ctx) query :=
  unlicensed_kinds_do_not_supply_evidence (projected ctx) query evidence (Or.inr (Or.inl grammar))

theorem ranked_parent_decreases (ctx : SourceBoundContext) (ranked : Ranked ctx)
    {child parent : String} (edge : Parent ctx.base.origins child parent) :
    rankOf ctx.bindings parent < rankOf ctx.bindings child := by
  obtain ⟨node, member, same, parentMember⟩ := edge
  exact same ▸ ranked node member parent parentMember

theorem ranked_path_nonincreasing (ctx : SourceBoundContext) (ranked : Ranked ctx)
    {child ancestor : String} (path : Path ctx.base.origins child ancestor) :
    rankOf ctx.bindings ancestor ≤ rankOf ctx.bindings child := by
  induction path with
  | refl => exact Nat.le_refl _
  | step edge _ ih => exact Nat.le_trans ih (Nat.le_of_lt (ranked_parent_decreases ctx ranked edge))

theorem ranked_no_cycle (ctx : SourceBoundContext) (ranked : Ranked ctx)
    {child parent : String} (edge : Parent ctx.base.origins child parent)
    (back : Path ctx.base.origins parent child) : False := by
  exact Nat.not_lt_of_ge (ranked_path_nonincreasing ctx ranked back)
    (ranked_parent_decreases ctx ranked edge)

theorem original_budget_preserved (ctx : SourceBoundContext) (query : Query) (budget : Nat)
    (insufficient : budget < ctx.base.interpretations.length) :
    scopedReceipt ctx query budget = ⟨.resourceLimit, [], [], []⟩ := by
  simp [scopedReceipt, Nat.not_le.mpr insufficient]

theorem availability_preserves_ledger (ctx : SourceBoundContext) (active : List Source) :
    (withActive ctx active).base.interpretations = ctx.base.interpretations ∧
    (withActive ctx active).base.origins = ctx.base.origins ∧
    (withActive ctx active).bindings = ctx.bindings := by
  exact ⟨rfl, rfl, rfl⟩

theorem withdrawn_source_absent (sources : List Source) (source : Source) :
    source ∉ withdrawSources sources source := by simp [withdrawSources]

theorem withdrawal_ready_refines (ctx : SourceBoundContext) (source : Source) (evidence : Evidence)
    (after : DependencyReady (withActive ctx (withdrawSources ctx.base.activeSources source)) evidence) :
    DependencyReady ctx evidence := by
  refine ⟨after.1, after.2.1, after.2.2.1, ?_⟩
  intro id member
  obtain ⟨binding, present, same, active⟩ := after.2.2.2 id member
  exact ⟨binding, present, same, (List.mem_filter.mp active).1⟩

theorem withdrawal_creates_no_selected_evidence (ctx : SourceBoundContext) (query : Query)
    (source : Source) (evidence : Evidence)
    (after : evidence ∈ EpistemicMeasurement.selected
      (projected (withActive ctx (withdrawSources ctx.base.activeSources source))) query) :
    evidence ∈ EpistemicMeasurement.selected (projected ctx) query := by
  obtain ⟨admissible, ready⟩ := (projected_admissible_exact _ _ _).mp ((selected_exact _ _ _).mp after)
  apply (selected_exact _ _ _).mpr
  apply (projected_admissible_exact _ _ _).mpr
  refine ⟨?_, withdrawal_ready_refines ctx source evidence ready⟩
  exact ⟨admissible.1, (List.mem_filter.mp admissible.2.1).1,
    admissible.2.2.1, admissible.2.2.2.1, admissible.2.2.2.2⟩

theorem withdrawal_creates_no_polarity (ctx : SourceBoundContext) (query : Query)
    (source : Source) (positive : Bool)
    (after : hasPolarity (projected (withActive ctx (withdrawSources ctx.base.activeSources source)))
      query positive = true) : hasPolarity (projected ctx) query positive = true := by
  obtain ⟨evidence, admissible, polarity⟩ := (hasPolarity_exact _ _ _).mp after
  apply (hasPolarity_exact _ _ _).mpr
  exact ⟨evidence, (selected_exact _ _ _).mp
    (withdrawal_creates_no_selected_evidence ctx query source evidence
      ((selected_exact _ _ _).mpr admissible)), polarity⟩

theorem withdrawal_does_not_invent_negation (ctx : SourceBoundContext) (query : Query)
    (source : Source) (absent : hasPolarity (projected ctx) query false = false) :
    hasPolarity (projected (withActive ctx (withdrawSources ctx.base.activeSources source))) query false = false := by
  cases after : hasPolarity (projected (withActive ctx (withdrawSources ctx.base.activeSources source))) query false with
  | false => rfl
  | true =>
    have before := withdrawal_creates_no_polarity ctx query source false after
    simp [absent] at before

theorem unaffected_ready_survives (ctx : SourceBoundContext) (source : Source) (evidence : Evidence)
    (before : DependencyReady ctx evidence)
    (unaffected : ∀ id ∈ evidence.ancestry, ∀ binding ∈ ctx.bindings,
      binding.originId = id → binding.source ≠ source) :
    DependencyReady (withActive ctx (withdrawSources ctx.base.activeSources source)) evidence := by
  refine ⟨before.1, before.2.1, before.2.2.1, ?_⟩
  intro id member
  obtain ⟨binding, present, same, active⟩ := before.2.2.2 id member
  refine ⟨binding, present, same, ?_⟩
  exact List.mem_filter.mpr ⟨active, by simpa using unaffected id member binding present same⟩

theorem replacement_does_not_reactivate_old (sources : List Source) (old replacement : Source)
    (differentRevision : old.revision ≠ replacement.revision) :
    old ∉ withdrawSources sources old ++ [replacement] := by
  have different : old ≠ replacement := fun same => differentRevision (congrArg (fun s : Source => s.revision) same)
  simp [withdrawSources, different]

theorem selected_preserves_qualified_key (ctx : SourceBoundContext) (query : Query) (evidence : Evidence)
    (selected : evidence ∈ EpistemicMeasurement.selected (projected ctx) query) :
    evidence.key = query.key :=
  selected_preserves_complete_key (projected ctx) query evidence selected

theorem verified_exact (episode : Episode) (report : Report) :
    verify episode report = true ↔ evaluate episode = .ok report := by
  cases result : evaluate episode <;> simp [verify, result]

theorem evaluated_binding (episode : Episode) (report : Report)
    (evaluated : evaluate episode = .ok report) : report.binding = episode := by
  unfold evaluate at evaluated
  cases result : replay episode with
  | error error =>
    rw [result] at evaluated
    change (Except.error error : Except Error Report) = .ok report at evaluated
    cases evaluated
  | ok steps =>
    rw [result] at evaluated
    change (Except.ok (Report.mk episode steps) : Except Error Report) = .ok report at evaluated
    cases Except.ok.inj evaluated
    rfl

theorem verified_episode_binding (episode : Episode) (report : Report)
    (checked : verify episode report = true) : report.binding = episode :=
  evaluated_binding episode report ((verified_exact episode report).mp checked)

theorem changed_episode_rejected (episode : Episode) (report : Report)
    (changed : report.binding ≠ episode) : verify episode report = false := by
  cases checked : verify episode report with
  | false => rfl
  | true => exact False.elim (changed (verified_episode_binding episode report checked))

end Nabt.EvidenceLifecycleV1
