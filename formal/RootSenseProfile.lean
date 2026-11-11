import Nabt.LexicalCatalog
import ProbeJson

/-! Occurrence alignments for a bounded teaching profile. The original lexical
catalogue, evidence, and three indication decisions remain with their owners.
ASCII digits in a surface template denote independent ordered root slots.
Other characters are exact orthography; unmarked input is matched by the
existing source-reading compatibility check, preserving all alternatives. -/
namespace RootSenseProfile
open Lean ProbeJson Nabt.LexicalDenotation Nabt.LexicalCatalog

private def packetHash := "6384f62328932e134b119ba7fa6f473754e015efbe3bc983b8d371ac4e9ff2cb"

private def man : Sense :=
  ⟨"root-profile:man", "رجل", ⟨"root_profile", "v1", packetHash, 0, 70,
    "درس تعريفي محصور: الرجل إنسان ذكر بالغ."⟩, ["إنسان", "ذكر", "بالغ"]⟩

private def key : Sense :=
  ⟨"root-profile:key", "فتح", ⟨"root_profile", "v1", packetHash, 71, 160,
    "درس تعريفي محصور: المفتاح آلة لفتح القفل الملائم."⟩, ["آلة", "لفتح القفل الملائم"]⟩

private def scorpion : Sense :=
  ⟨"root-profile:scorpion", "عقرب", ⟨"root_profile", "v1", packetHash, 161, 261,
    "قراءة حيوانية تعليمية للعقرب: من العنكبيات، ذو سم يلسع."⟩, ["من العنكبيات", "ذو سم", "يلسع"]⟩

private def clock_hand : Sense :=
  ⟨"root-profile:clock_hand", "عقرب", ⟨"root_profile", "v1", packetHash, 262, 327,
    "قراءة عقرب الساعة: مؤشر لبيان الوقت."⟩, ["مؤشر", "لبيان الوقت"]⟩

private def roll : Sense :=
  ⟨"root-profile:roll", "دحرج", ⟨"root_profile", "v1", packetHash, 328, 408,
    "قراءة حسية للدحرجة: تحريك جسم بطريق التدحرج."⟩, ["تحريك جسم", "بطريق التدحرج"]⟩

private def roller : Sense :=
  ⟨"root-profile:roller", "دحرج", ⟨"root_profile", "v1", packetHash, 409, 480,
    "قراءة مُدَحْرِج: صاحب الفعل في الدحرجة."⟩, ["صاحب الفعل", "في الدحرجة"]⟩

private def rolled : Sense :=
  ⟨"root-profile:rolled", "دحرج", ⟨"root_profile", "v1", packetHash, 481, 544,
    "قراءة مُدَحْرَج: المتأثر بالدحرجة."⟩, ["المتأثر", "بالدحرجة"]⟩

private def hasten : Sense :=
  ⟨"root-profile:hasten", "سرع", ⟨"root_profile", "v1", packetHash, 545, 628,
    "الماضي أَسْرَعَ، من مادة سرع، ومصدره الإسراع."⟩, ["الإسراع"]⟩

private def heavy_run : Sense :=
  ⟨"root-profile:heavy_run", "جربز", ⟨"root_profile", "v1", packetHash, 629, 675,
    "جربز الفرس عدا عدوا ثقيلا"⟩, ["عدو", "بكيفية ثقيلة"]⟩

private structure Form where
  sense : Sense
  template : String
  category : String
  genus : String
  property : String
  event : String
  role : String
  capability : String := ""

private def forms : List Form := [
  ⟨man, "1َ2ُ3", "جامد", "إنسان", "الذكورة والبلوغ", "", "", ""⟩,
  ⟨key, "مِ1ْ2َا3", "اسم آلة", "أداة", "وظيفة فتح القفل الملائم", "فتح", "آلة", "key_lock"⟩,
  ⟨scorpion, "1َ2ْ3َ4", "جامد", "عنكبيات", "اللسع", "", "", ""⟩,
  ⟨clock_hand, "1َ2ْ3َ4", "اسم في استعمال الساعة", "مؤشر", "بيان الوقت", "", "", ""⟩,
  ⟨roll, "1َ2ْ3َ4َة", "مصدر", "حدث حركي", "كيفية الحركة", "دحرجة", "إطار الحدث", ""⟩,
  ⟨roller, "مُ1َ2ْ3ِ4", "اسم فاعل", "حامل دور", "إسناد التحريك", "دحرجة", "فاعل", ""⟩,
  ⟨rolled, "مُ1َ2ْ3َ4", "اسم مفعول", "حامل دور", "تعلق الدحرجة بالجسم", "دحرجة", "متأثر", "roll_patient"⟩,
  ⟨hasten, "أَ1ْ2َ3َ", "فعل", "حدث حركي", "السرعة", "إسراع", "إسناد الفعل", ""⟩,
  ⟨heavy_run, "1َ2ْ3َ4َ", "فعل", "عدو", "كيفية ثقيلة للعدو", "عدو", "صاحب العدو", ""⟩,
  ⟨sense11, "العَمَى", "مصدر", "حال", "ذهاب البصر", "عمى", "حامل الحال", ""⟩] ++
  (forRoot "قلم").map (fun s => ⟨s, "1َ2َ3", "اسم", "", "", "", "", ""⟩)

private def realize (f : Form) : String :=
  String.ofList (f.template.toList.map fun c =>
    if '1' ≤ c && c ≤ '4' then
      (f.sense.root.toList[c.toNat - '1'.toNat]?).getD c
    else c)

def assess (target : List String) (encodeSense : Sense → Json) : Json :=
  Json.mkObj [("schema", toJson "nabt.root-sense.profile.v1"), ("target", toJson target),
    ("rows", Json.arr (forms.map (fun f => Json.mkObj [
      ("sense", encodeSense f.sense), ("template", toJson f.template),
      ("surface", toJson (realize f)), ("category", toJson f.category),
      ("genus", toJson f.genus), ("property", toJson f.property), ("event", toJson f.event),
      ("role", toJson f.role), ("capability", toJson f.capability),
      ("indications", toJson (([Indication.matching, .inclusion, .entailment].filter
        (fun k => check necessities f.sense k target)).map Indication.label))])).toArray)]

/-- Conditional interpretation of one locally reconstructed dictionary clause.
Only the two explicit degree terms are decomposed here; the occurrence does
not assert the event, a universal capability, or an actual lexical use. -/
def gloss (value : Json) (target : List String) : ProbeJson.ProbeM Json := do
  let text ← str (← field value "text")
  let first ← nat (← field value "start")
  let last ← nat (← field value "end")
  if text.utf8ByteSize > 8192 || first >= last || last > text.utf8ByteSize then
    return ← invalid "invalid gloss byte span"
  let some phrase := String.fromUTF8? (text.toUTF8.extract first last)
    | return ← invalid "invalid gloss byte boundaries"
  let words := ((phrase.replace "\t" " ").splitOn " ").filter (!·.isEmpty)
  let [head, actor, verb, action, manner] := words
    | return ← invalid "expected five dictionary terms"
  let deferred := Json.mkObj [("status", toJson "OUTSIDE_GLOSS_PROFILE")]
  if !(actor.startsWith "ال") || !(["عدا", "عَدَا"].contains verb) ||
      !(["عدوا", "عَدْوًا", "عَدْواً"].contains action) then return deferred
  let quality := if ["ثقيلا", "ثَقِيلًا", "ثَقِيلاً"].contains manner then "بكيفية ثقيلة"
    else if ["سريعا", "سَرِيعًا", "سَرِيعاً"].contains manner then "بكيفية سريعة" else ""
  if quality.isEmpty then return deferred
  let s : Sense := ⟨head, "", ⟨"input", "1", "", first, last, phrase⟩, ["عدو", quality]⟩
  return Json.mkObj [("status", toJson "CONDITIONAL_GLOSS"), ("head", toJson head),
    ("participant", toJson actor), ("quotation", toJson phrase),
    ("components", toJson s.components), ("target", toJson target),
    ("indications", toJson (([Indication.matching, .inclusion, .entailment].filter
      (fun k => check [] s k target)).map Indication.label))]

end RootSenseProfile
