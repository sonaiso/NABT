import Nabt.ClassicalGemination
import Lean

open Lean Nabt.ClassicalGemination

def vowelLabel : Vowel → String
  | .s => "s" | .a => "a" | .i => "i" | .u => "u"

def ruleLabel : Rule → String
  | .voweled => "GEM-VOWELED-FINAL" | .jussive => "GEM-JUSSIVE-VARIANTS"
  | .feminine => "GEM-FEMININE-SUFFIX" | .exclamation => "GEM-EXCLAMATION"

def contextLabel : Context → String
  | .ordinary => "ordinary" | .command => "command" | .jussive => "jussive"
  | .feminine => "feminine" | .exclamation => "exclamation" | .hallumma => "hallumma"

def dialectLabel : Dialect → String
  | .hijaz => "hijaz" | .tamim => "tamim" | .kabGhani => "kab_ghani"
  | .bakr => "bakr" | .attestedUnion => "attested_union"

def actionLabel : Action → String
  | .split => "split" | .contractKeep => "contract_keep" | .contractA => "contract_a"
  | .contractI => "contract_i" | .contractU => "contract_u"
  | .bakrUnvocalized => "bakr_contraction_unvocalized" | .retainHallumma => "retain_hallumma"

def connectionLabel : Connection → String
  | .withinWord => "within_word" | .wordBoundaryWasl => "word_boundary_wasl"
  | .wordBoundaryWaqf => "word_boundary_waqf"

def vowels : List Vowel := [.s, .a, .i, .u]

def cellJson (c : Cell) : Json := toJson [c.letter, vowelLabel c.vowel]

def main : IO Unit := do
  let morphology := [Rule.voweled, .jussive, .feminine, .exclamation].flatMap fun r =>
    [Context.ordinary, .command, .jussive, .feminine, .exclamation, .hallumma].flatMap fun c =>
    [Dialect.hijaz, .tamim, .kabGhani, .bakr, .attestedUnion].flatMap fun d =>
    vowels.flatMap fun preceding => vowels.map fun last =>
      Json.mkObj [("rule_id", toJson (ruleLabel r)), ("context", toJson (contextLabel c)),
        ("dialect", toJson (dialectLabel d)), ("preceding", toJson (vowelLabel preceding)),
        ("last", toJson (vowelLabel last)),
        ("actions", toJson ((enumerate r c d preceding last).map actionLabel))]
  let assimilation := ["ن", "م"].flatMap fun l => vowels.flatMap fun v =>
    ["ب", "ي", "د"].flatMap fun r =>
    [Connection.withinWord, .wordBoundaryWasl, .wordBoundaryWaqf].map fun c =>
      Json.mkObj [("left", toJson l), ("vowel", toJson (vowelLabel v)), ("right", toJson r),
        ("connection", toJson (connectionLabel c)),
        ("actions", toJson (if (nunToMim ⟨l, v⟩ ⟨r, .a⟩ c).isSome
          then ["nun_to_mim_before_ba"] else []))]
  let prefixes : List (List Cell) := [
    [⟨"ر", .s⟩], [⟨"ٱ", .u⟩, ⟨"ر", .s⟩], [⟨"ر", .a⟩],
    [⟨"ٱ", .i⟩, ⟨"ط", .s⟩, ⟨"م", .a⟩, ⟨"ء", .s⟩],
    [⟨"م", .a⟩, ⟨"ا", .s⟩], [⟨"أ", .a⟩, ⟨"م", .s⟩]]
  let projections := prefixes.flatMap fun leftCells =>
    [Vowel.a, .i, .u].flatMap fun first => vowels.flatMap fun last =>
    [Action.split, .contractKeep, .contractA, .contractI, .contractU,
      .bakrUnvocalized, .retainHallumma].map fun action =>
      let p : Payload := ⟨leftCells, ⟨"د", first⟩, ⟨"د", last⟩, [⟨"ن", .a⟩]⟩
      Json.mkObj [("prefix", toJson (leftCells.map cellJson)), ("first", toJson (vowelLabel first)),
        ("last", toJson (vowelLabel last)), ("action", toJson (actionLabel action)),
        ("cells", toJson ((project p action).map (List.map cellJson)))]
  IO.println (Json.mkObj [("law_id", toJson lawId), ("morphology", toJson morphology),
    ("assimilation", toJson assimilation), ("projections", toJson projections)]).compress
