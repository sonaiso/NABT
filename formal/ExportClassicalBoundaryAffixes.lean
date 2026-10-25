import Nabt.ClassicalBoundaryAffixes
import Lean
open Lean Nabt.ClassicalBoundaryAffixes
namespace BoundaryExport

def alphabet : Array String := #["ء","ا","ب","ت","ث","ج","ح","خ","د","ذ","ر","ز","س","ش","ص","ض","ط","ظ","ع","غ","ف","ق","ك","ل","م","ن","ه","و","ي","a","i","u","a:","i:","u:"]
def segments (ss : List Seg) : Json := toJson (ss.map fun s => alphabet[s]!)
def tagName : Tag → String
 | .deleteWeak => "delete_weak_final" | .retain => "retain_in_connection"
 | .dropBeforeWasl => "drop_light_nun_before_wasl" | .alif => "replace_light_nun_with_alif"
 | .restoreGlide => "restore_deleted_subject_glide" | .dropAfterRetained => "drop_light_nun_after_retained_glide"
 | .restoreIndicative => "restore_indicative_nun" | .yunusReplacement => "yunus_replacement_after_nonfatha"
 | .anaPause => "ana_pause_alif" | .anaFatha => "ana_connected_fatha" | .anaSukun => "ana_connected_sukun"
def evidenceName : Evidence → String
 | .conditional => "conditional_rule" | .khalil => "reported_khalil" | .yunus => "reported_yunus"
 | .analogyYunus => "source_analogical_yunus" | .majority => "reported_majority" | .minority => "reported_minority"
def alternativeJson (r : Alternative) : Json := Json.mkObj [
 ("segments",segments r.segments),("derivation",toJson (tagName r.tag)),("evidence_kind",toJson (evidenceName r.evidence))]
def radicalName : Radical → String | .waw => "و" | .ya => "ي" | .sound => "sound"
def personName : Person → String | .ms => "2ms" | .fs => "2fs" | .dual => "2dual" | .mp => "2mp" | .fp => "2fp"
def suffixName : Suffix → String | .none => "none" | .subject => "subject" | .object => "object" | .emphatic => "emphatic"
def endName : End → String | .wasl => "wasl" | .waqf => "waqf"
def followingName : Following → String | .none => "none" | .consonant => "consonant" | .hamzatWasl => "hamzat_wasl"
def profileName : Profile → String | .khalil => "khalil" | .yunus => "yunus" | .both => "both"
def nunName : NunKind → String | .light => "light" | .heavy => "heavy" | .feminine => "feminine"
def shapeName : Shape → String
 | .singularOpen => "singular_open" | .deletedYaCommand => "deleted_ya_command"
 | .deletedWawCommand => "deleted_waw_command" | .retainedYaCommand => "retained_ya_command"
 | .retainedWawCommand => "retained_waw_command" | .deletedYaIndicative => "deleted_ya_indicative"
 | .deletedWawIndicative => "deleted_waw_indicative" | .indicativeDual => "indicative_dual"
def analysisName : AnaAnalysis → String | .speaker => "speaker_pronoun" | .masdariyya => "masdariyya_particle" | .other => "other"
def anaProfileName : AnaProfile → String | .majority => "majority" | .minoritySukun => "minority_sukun" | .both => "both"

def weakFrames : List WeakFrame :=
 ([.waw,.ya,.sound] : List Radical).flatMap fun r =>
 ([.a,.i,.u] : List LongVowel).flatMap fun v =>
 ([.ms,.fs,.dual,.mp,.fp] : List Person).flatMap fun p =>
 ([.none,.subject,.object,.emphatic] : List Suffix).map fun s => ⟨[22],r,v,p,s⟩
def lightFrames : List LightFrame :=
 ([.singularOpen,.deletedYaCommand,.deletedWawCommand,.retainedYaCommand,
   .retainedWawCommand,.deletedYaIndicative,.deletedWawIndicative,.indicativeDual] : List Shape).flatMap fun s =>
 ([.khalil,.yunus,.both] : List Profile).flatMap fun p =>
 ([.light,.heavy,.feminine] : List NunKind).flatMap fun n =>
 ([.wasl,.waqf] : List End).flatMap fun e =>
 (([.none,.consonant,.hamzatWasl] : List Following).filter fun f => e == .wasl || f == .none).map fun f =>
 ⟨[22],s,p,n,e,f⟩
def anaFrames : List AnaFrame :=
 ([.speaker,.masdariyya,.other] : List AnaAnalysis).flatMap fun s =>
 ([.majority,.minoritySukun,.both] : List AnaProfile).flatMap fun p =>
 ([.wasl,.waqf] : List End).map fun e => ⟨s,p,e⟩

def weakJson (f : WeakFrame) : Json := Json.mkObj [
 ("rule_id",toJson "CMD-WEAK-DELETE"),
 ("frame",Json.mkObj [("segments",segments (f.stem ++ [longSegment f.vowel])),
  ("final_radical",toJson (radicalName f.radical)),("person",toJson (personName f.person)),
  ("suffix",toJson (suffixName f.suffix)),("start",toJson "ibtida"),("end",toJson "wasl")]),
 ("alternatives",toJson ((weakEnumerate f).map alternativeJson))]
def lightJson (f : LightFrame) : Json := Json.mkObj [
 ("rule_id",toJson "AFFIX-LIGHT-NUN-PAUSE"),
 ("frame",Json.mkObj [("segments",segments (f.stem ++ sourceTail f.shape)),
  ("shape",toJson (shapeName f.shape)),("profile",toJson (profileName f.profile)),
  ("nun_kind",toJson (nunName f.nunKind)),("end",toJson (endName f.ending)),
  ("following",toJson (followingName f.following)),("start",toJson "ibtida")]),
 ("alternatives",toJson ((lightEnumerate f).map alternativeJson))]
def anaJson (f : AnaFrame) : Json := Json.mkObj [
 ("rule_id",toJson "MUGHNI-ANA-BOUNDARY"),
 ("frame",Json.mkObj [("segments",segments [0,a,nun,aa]),("analysis",toJson (analysisName f.analysis)),
  ("profile",toJson (anaProfileName f.profile)),("end",toJson (endName f.ending)),("start",toJson "ibtida")]),
 ("alternatives",toJson ((anaEnumerate f).map alternativeJson))]
end BoundaryExport

def main : IO Unit := do
 let rows := BoundaryExport.weakFrames.map BoundaryExport.weakJson ++
             BoundaryExport.lightFrames.map BoundaryExport.lightJson ++
             BoundaryExport.anaFrames.map BoundaryExport.anaJson
 IO.println (Json.mkObj [("law_id",toJson lawId),("alphabet",toJson alphabetId),("rows",toJson rows)]).compress
