import GovernorProfile

/-! Small, explicit grammar over A116 words in continuous reading. Word
boundaries and the licensed lexical form ledger are inputs. The input never
supplies a sentence analysis, a chosen operator or a choice of witnesses. -/
namespace GovernorProfile.Surface
open Nabt
abbrev Word := List Atom
abbrev Words := List Word

inductive Frame where
  | inna | layta | laalla | hal | ya | laNahiya
  deriving DecidableEq, Repr

def frames : List Frame := [.inna, .layta, .laalla, .hal, .ya, .laNahiya]
theorem allFrames (f : Frame) : f ∈ frames := by cases f <;> decide

def headCells : Frame → Word
  | .inna => [114,99,96]       -- ءِ نْ نَ
  | .layta => [88,111,8]      -- لَ يْ تَ
  | .laalla => [88,68,91,88]  -- لَ عَ لْ لَ
  | .hal => [100,91]          -- هَ لْ
  | .ya => [108,3]            -- يَ اْ
  | .laNahiya => [88,3]       -- لَ اْ

def owner : Frame → Id
  | .inna => 0 | .layta => 4 | .laalla => 5 | .hal => 85 | .ya => 94 | .laNahiya => 60

theorem owner_alignment :
    frames.map (fun f => ((row (owner f)).label, (foldRow (owner f)).style)) =
    [("إنّ","الخبر"),("ليت","التمني"),("لعلّ","الترجي"),("هل","الاستفهام"),("يا","النداء"),("لا الناهية","الطلب")] := by decide

inductive FormKind where
  | nameAcc | nameNom | predicateNom | nameVocBuiltDamm | secondPersonJussive
  deriving DecidableEq, Repr

structure Form where
  kind : FormKind
  cells : Word
  witness : Nat
  deriving DecidableEq, Repr

/-- Role is explicit even when two positions have the same case ending. -/
inductive Slot where
  | particleName | particlePredicate | topic | predicate | addressee | prohibitedVerb
  deriving DecidableEq, Repr

def pattern : Frame → List (Slot × FormKind)
  | .inna | .layta | .laalla => [(.particleName,.nameAcc),(.particlePredicate,.predicateNom)]
  | .hal => [(.topic,.nameNom),(.predicate,.predicateNom)]
  | .ya => [(.addressee,.nameVocBuiltDamm)]
  | .laNahiya => [(.prohibitedVerb,.secondPersonJussive)]

abbrev Binding := Slot × Form
abbrev Reading := Frame × List Binding

inductive Aligned (lex : List Form) :
    List (Slot × FormKind) → Words → List Binding → Prop where
  | nil : Aligned lex [] [] []
  | cons (p : Slot × FormKind) (form : Form) (found : form ∈ lex)
      (kind : form.kind = p.2) (tail : Aligned lex ps ws bs) :
      Aligned lex (p :: ps) (form.cells :: ws) ((p.1,form) :: bs)

inductive Reference (lex : List Form) : Words → Reading → Prop where
  | clause (f : Frame) (tail : Aligned lex (pattern f) ws bs) :
      Reference lex (headCells f :: ws) (f,bs)

def scan (lex : List Form) : List (Slot × FormKind) → Words → List (List Binding)
  | [], [] => [[]]
  | p :: ps, w :: ws => (lex.filter fun form => decide (form.kind = p.2 ∧ form.cells = w)).flatMap
      fun form => (scan lex ps ws).map fun tail => (p.1,form) :: tail
  | _, _ => []

theorem scan_exact (lex : List Form) (ps : List (Slot × FormKind)) (ws : Words) (bs : List Binding) :
    bs ∈ scan lex ps ws ↔ Aligned lex ps ws bs := by
  induction ps generalizing ws bs with
  | nil =>
    cases ws with
    | nil =>
      constructor
      · intro h; have : bs = [] := by simpa [scan] using h
        subst bs; exact .nil
      · intro h; cases h; simp [scan]
    | cons w ws => constructor <;> intro h
                   · simp [scan] at h
                   · cases h
  | cons p ps ih =>
    cases ws with
    | nil => constructor <;> intro h
             · simp [scan] at h
             · cases h
    | cons w ws =>
      constructor
      · intro h
        obtain ⟨form, hf, tail, ht, rfl⟩ := by simpa [scan, List.mem_flatMap] using h
        obtain ⟨member,kind,rfl⟩ := hf
        exact .cons p form member kind ((ih _ _).mp ht)
      · intro h
        cases h with
        | cons _ form found kind tail =>
          simp only [scan, List.mem_flatMap, List.mem_filter, decide_eq_true_eq, List.mem_map]
          exact ⟨form,⟨found,kind,rfl⟩,_,(ih _ _).mpr tail,rfl⟩

def recognize (lex : List Form) : Words → List Reading
  | [] => []
  | h :: ws => (frames.filter fun f => decide (headCells f = h)).flatMap
      fun f => (scan lex (pattern f) ws).map fun bs => (f,bs)

theorem recognize_iff_reference (lex : List Form) (s : Words) (a : Reading) :
    a ∈ recognize lex s ↔ Reference lex s a := by
  constructor
  · intro h
    cases s with
    | nil => simp [recognize] at h
    | cons word ws =>
      obtain ⟨f,hf,bs,hb,rfl⟩ := by simpa [recognize, List.mem_flatMap] using h
      obtain ⟨_,rfl⟩ := hf
      exact .clause f ((scan_exact ..).mp hb)
  · intro h
    cases h with
    | clause f tail =>
      simp only [recognize, List.mem_flatMap, List.mem_filter, decide_eq_true_eq, List.mem_map]
      exact ⟨f,⟨allFrames f,rfl⟩,_,(scan_exact ..).mpr tail,rfl⟩

/-- The vocative owner represents the *visible* damma by its raf code.
The lexical kind still says "built on damm", and its syntactic position is nasb.
Interrogative hal contributes no governor-case equations for the inner clause. -/
def toOwner : Slot × FormKind → Option Governors.Equation
  | (.particleName,.nameAcc) => some (.primary,.nasb)
  | (.particlePredicate,.predicateNom) => some (.complement,.raf)
  | (.prohibitedVerb,.secondPersonJussive) => some (.imperfect,.jazm)
  | (.addressee,.nameVocBuiltDamm) => some (.vocative,.raf)
  | _ => none

theorem aligned_kinds {lex ps ws bs} (h : Aligned lex ps ws bs) :
    bs.map (fun b => (b.1,b.2.kind)) = ps := by
  induction h with
  | nil => rfl
  | cons p form _ kind _ ih => simp [kind, ih]

theorem pattern_is_owner_alternative (f : Frame) :
    (pattern f).filterMap toOwner ∈ (foldRow (owner f)).equations ∧
    (foldRow (owner f)).links = [] := by cases f <;> decide

theorem recognized_roles_project_to_owner {lex s a} (h : a ∈ recognize lex s) :
    (a.2.map (fun b => (b.1,b.2.kind))).filterMap toOwner ∈
      (foldRow (owner a.1)).equations := by
  cases (recognize_iff_reference ..).mp h with
  | clause f tail => simpa only [aligned_kinds tail] using (pattern_is_owner_alternative f).1

/- زَيْدًا / زَيْدٌ / زَيْدُ / حَاضِرٌ / تَكْتُبْ. Wasl encodes tanwin
as short vowel + silent nun. The vocative uses a built ending. -/
def demoLex : List Form :=
  [⟨.nameAcc,[40,111,28,99],1⟩, ⟨.nameNom,[40,111,29,99],2⟩,
   ⟨.nameVocBuiltDamm,[40,111,29],3⟩, ⟨.predicateNom,[20,3,58,37,99],4⟩,
   ⟨.secondPersonJussive,[8,87,9,7],5⟩]

def examples : List Words :=
  [[[114,99,96],[40,111,28,99],[20,3,58,37,99]],
   [[88,111,8],[40,111,28,99],[20,3,58,37,99]],
   [[88,68,91,88],[40,111,28,99],[20,3,58,37,99]],
   [[100,91],[40,111,29,99],[20,3,58,37,99]],
   [[108,3],[40,111,29]], [[88,3],[8,87,9,7]]]

theorem examples_checked : examples.map (fun s => (recognize demoLex s).map Prod.fst) =
    [[.inna],[.layta],[.laalla],[.hal],[.ya],[.laNahiya]] := by decide

theorem changed_witness :
  recognize demoLex [[114,99,96],[40,111,29,99],[20,3,58,37,99]] = [] ∧
  recognize demoLex [[108,3],[40,111,29,99]] = [] ∧
  recognize demoLex [[88,3],[8,87,9,5]] = [] ∧
  (recognize (⟨.predicateNom,[20,3,58,37,99],44⟩ :: demoLex)
    [[114,99,96],[40,111,28,99],[20,3,58,37,99]]).length = 2 := by decide

end GovernorProfile.Surface

#print axioms GovernorProfile.expand_exact
#print axioms GovernorProfile.derivation_exact
#print axioms GovernorProfile.Surface.recognize_iff_reference
