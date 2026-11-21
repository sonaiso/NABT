import A116

/-!
مخرجاتٌ لمطابقة Lean بالبايثون في CI:

* بلا وسيط: جدولُ الانتقال كاملًا (‎3 × 116 = 348‎ سطرًا)
  `state,carrier_index,haraka_index,next_state` بأسماء `SyllableState`.
* `counts`: ‎U(n)‎ لـ‎n = 0 … 6‎، أي عددُ السلاسل التي يقبلها النموذج، كما حسبه
  Lean من التعريف الذي بُرهِن عليه التقابل (`A116.U`).
* `bridge-order`: ‎k,carrier,haraka‎ لـ‎k < 116‎ من `bridgeCell`، ليُطابَق بـ
  `canonical116.bridge.A116` خانةً خانة.
* `numbers`: ‎F‎ (`atomNumber`) لكلّ سلسلةٍ بطول ‎≤ 2‎ بترتيب الجسر (13,573 سطرًا).
* `pairs`: ‎P(u, r)‎ لـ‎u, r < 64‎.
* `hadd`: لكلّ سلسلةِ خاناتٍ بطول ‎1 … 4‎ من ستّة حواملَ (ء ا و ي ل ج) × أربع حالات
  (‎24 + 24² + 24³ + 24⁴ = 346,200‎ سطرًا): الذرّاتُ نصًّا، ثمّ `Hadd.kindOf` و`continueB` و
  `Hadd.strictB`، ليُطابَق بـ`gate.licence.kind_of` و`strict_licensed` سطرًا سطرًا.
* `hadd-join`: لكلّ زوجٍ (أولى بطول ‎1 … 3‎، ثانيةٌ بطول ‎1 … 2‎) من ثلاثة حواملَ (ا ل ج) × أربع
  حالات (‎1,884 × 156 = 293,904‎ سطرًا): الذرّاتُ، ثمّ `Hadd.strictB` على الموصول و`Hadd.strictJoinB`،
  ليُطابَق بـ`gate.licence.strict_joined` سطرًا سطرًا.
* `mantuq`: الجسرُ من المنطوق إلى المفهوم (`MantuqMafhum`، ADR ١١٢): `naw` على الصفات الستّ عشرة، و`mukhalafa`
  على ثمانية قيودٍ × الأغلب × المعطِّل، والرتبةُ بمساريها على مودَعاتٍ صغيرة بالطرق والأنواع كلّها، وتركيبُ الرتبة على مخرج
  الجسر بمعنيين (178 سطرًا)، ليُطابَق بـ`gate.mantuq`.
* `furu`: فروعُ السلسلة وحملُ الحرف ومرشَّحو التقشير ومفتاحُ الحرف (`SilsilaFuru`، ADR ١١٥) على الشاهد.
* `silsila`: السلسلةُ كلمةً كلمة (`Silsila`، ADR ١١٤): `khutwa` على كلمتين × ستّة أحكامٍ لما دون الطبقة × سبعة قرّاء
  (84 سطرًا)، و`silsila` على الشاهد (ستّة أسطر)، وقارئا الجنس والحمل (`SilsilaQurra`) على المعجم الشاهد (عشرةُ أسطر
  للجنس وسبعةٌ للحمل)، ليُطابَق بمرآة `tools/gen_silsila.py`.
* `syllables`: لكلّ سلسلةِ أنواعٍ بطول ‎1 … 11‎ (265,719 سلسلة) تقطيعُها بـ`Stages.parse`
  أو `none`، ثمّ `binOK` و`continueB` و`pauseB` من `Ternary`، ليُطابَق ذلك كلُّه
  بـ`mabni_stages.syllabify` و`ternary_licence` سلسلةً سلسلة.
-/

open A116

namespace SyllableTable

open Stages

def allK : Nat → List (List K)
  | 0 => [[]]
  | n + 1 => (allK n).flatMap fun p => [p ++ [.cv], p ++ [.v], p ++ [.c]]

def kName : K → String
  | .cv => "CV"
  | .v => "V"
  | .c => "C"

def leadName : Lead → List String
  | .none => []
  | .C => ["C|"]
  | .V => ["V|"]
  | .VC => ["VC|"]

def sylName : Syl → String
  | .CV => "CV"
  | .CVV => "CVV"
  | .CVC => "CVC"
  | .CVVC => "CVVC"
  | .CVCC => "CVCC"
  | .CVVCC => "CVVCC"

def render (k : List K) : String :=
  let key := "-".intercalate (k.map kName)
  let lic := s!"{Ternary.binOK k},{Ternary.continueB k},{Ternary.pauseB k}"
  match parse k with
  | some (l, ss) => s!"{key},{"-".intercalate (leadName l ++ ss.map sylName)},{lic}"
  | none => s!"{key},none,{lic}"

end SyllableTable

namespace HaddTable

open Stages

def mark : Haraka → Char
  | .fatha => '\u064E'
  | .damma => '\u064F'
  | .kasra => '\u0650'
  | .sukun => '\u0652'

def alphabet : List Cell :=
  ['ء', 'ا', 'و', 'ي', 'ل', 'ج'].flatMap fun ch => Haraka.all.map fun h => Ladder.atom ch h

def allW : Nat → List (List Cell)
  | 0 => [[]]
  | n + 1 => (allW n).flatMap fun w => alphabet.map fun c => w ++ [c]

def render (w : List Cell) : String :=
  let atoms := " ".intercalate (w.map fun c => String.ofList [Field112.carrierChar c.carrier, mark c.haraka])
  let k := Hadd.kindOf w
  s!"{atoms},{"-".intercalate (k.map SyllableTable.kName)},{Ternary.continueB k},{Hadd.strictB w},{Hadd.strictPauseB w}"

def joinAlphabet : List Cell :=
  ['ا', 'ل', 'ج'].flatMap fun ch => Haraka.all.map fun h => Ladder.atom ch h

def allJ : Nat → List (List Cell)
  | 0 => [[]]
  | n + 1 => (allJ n).flatMap fun w => joinAlphabet.map fun c => w ++ [c]

def atomsOf (w : List Cell) : String :=
  " ".intercalate (w.map fun c => String.ofList [Field112.carrierChar c.carrier, mark c.haraka])

def iltiqaAlphabet : List Cell :=
  ['ء', 'ا', 'و', 'ي', 'ن', 'ل'].flatMap fun ch => Haraka.all.map fun h => Ladder.atom ch h

def allI : Nat → List (List Cell)
  | 0 => [[]]
  | n + 1 => (allI n).flatMap fun w => iltiqaAlphabet.map fun c => w ++ [c]

def repairName : Option Iltiqa.Repair → String
  | none => "-"
  | some .farqAlifDropped => "FARQ_ALIF_DROPPED"
  | some .maddDropped => "MADD_DROPPED"
  | some .sakinKasra => "SAKIN_KASRA"

/-- التقاءُ الساكنين على الحدّ: الزوج، الوجه، الأولى بعد الإصلاح، الوصلُ قبلُ وبعدُ، والوقفُ بعدُ. -/
def renderIltiqa (l r : List Cell) : String :=
  let p := Iltiqa.repair l r
  s!"{atomsOf l}|{atomsOf r},{repairName p.2},{atomsOf p.1},{Hadd.strictJoinB l r},{Iltiqa.strictJoinRepairedB l r},{Iltiqa.strictJoinPauseRepairedB l r}"

def renderJoin (l r : List Cell) : String :=
  s!"{atomsOf l}|{atomsOf r},{Hadd.strictB (l ++ r)},{Hadd.strictJoinB l r},{Hadd.strictJoinPauseB l r}"

end HaddTable

namespace MizanTable

open A116.Mizan (hi ki)

/-- جدولُ الآلة كاملًا: الخانات، والأحوال، والانتقالُ وصلًا ووقفًا على المجال كلِّه. -/
def rows : List String :=
  (A116.cells.map fun c =>
      s!"cell,{String.ofList [Field112.carrierChar c.carrier, HaddTable.mark c.haraka]},{ki (HarfBridge.unproj c)}") ++
  (Harf.Hal.all.map fun s =>
      s!"state,{hi s},{Harf.qabilWasl s},{Harf.qabilWaqf s},{hi (Harf.hadd s)}") ++
  (Harf.Hal.all.flatMap fun s => Harf.Khana.all.map fun x =>
      s!"wasl,{hi s},{ki x},{hi (Harf.wasl s x)}") ++
  (Harf.Hal.all.flatMap fun s => Harf.Khana.all.map fun x =>
      s!"waqf,{hi s},{ki x},{hi (Harf.waqf s x)}")

def esc (c : Char) : String :=
  let h := String.ofList (Nat.toDigits 16 c.toNat)
  "'\\u" ++ String.ofList (List.replicate (4 - h.length) '0') ++ h ++ "'"

def harakaName : Haraka → String
  | .fatha => ".fatha" | .damma => ".damma" | .kasra => ".kasra" | .sukun => ".sukun"

def commas (l : List String) : List String := (l.dropLast.map (· ++ ",")) ++ l.getLast?.toList

def natRow (xs : List Nat) : String := "[" ++ ", ".intercalate (xs.map toString) ++ "]"

/-- الجدولُ نفسُه مصدرَ Lean: يولَّد هنا ثمّ تفحصه النواةُ في `A116.MizanKernel` فلا يُوثَق بهذا الطابع. -/
def leanFile : List String :=
  ["import A116.Cells", "",
   "/-! مولَّدٌ بـ`lake exe a116-table mizan-lean`؛ لا يُحرَّر باليد. النواةُ تفحصه في `A116.MizanKernel` (ADR ٤٤). -/",
   "", "set_option maxRecDepth 100000", "", "namespace A116.MizanData", "",
   "def cellT : List (Char × A116.Haraka × Nat) := ["] ++
  commas (A116.cells.map fun c =>
      s!"  ({esc (Field112.carrierChar c.carrier)}, {harakaName c.haraka}, {ki (HarfBridge.unproj c)})") ++
  ["]", "",
   "def stateT : List (Bool × Bool × Nat) := ["] ++
  ((Harf.Hal.all.map fun s =>
      s!"  ({Harf.qabilWasl s}, {Harf.qabilWaqf s}, {hi (Harf.hadd s)})") |> fun l =>
        commas l) ++
  ["]", "",
   "def waslT : List (List Nat) := ["] ++
  ((Harf.Hal.all.map fun s => "  " ++ natRow (Harf.Khana.all.map fun x => hi (Harf.wasl s x))) |> fun l =>
        commas l) ++
  ["]", "",
   "def waqfT : List (List Nat) := ["] ++
  ((Harf.Hal.all.map fun s => "  " ++ natRow (Harf.Khana.all.map fun x => hi (Harf.waqf s x))) |> fun l =>
        commas l) ++
  ["]", "", "end A116.MizanData"]

end MizanTable

def main (args : List String) : IO Unit := do
  match args with
  | ["counts"] =>
    for n in List.range 7 do
      IO.println s!"{n},{U n}"
  | ["bridge-order"] =>
    for k in List.range 116 do
      let c := Numbering.bridgeCell k
      IO.println s!"{k},{c.carrier.val},{c.haraka.index}"
  | ["numbers"] =>
    let ix := List.range 116
    IO.println s!",{Numbering.atomNumber []}"
    for i in ix do
      IO.println s!"{i},{Numbering.atomNumber [Numbering.bridgeCell i]}"
    for i in ix do
      for j in ix do
        IO.println
          s!"{i} {j},{Numbering.atomNumber [Numbering.bridgeCell i, Numbering.bridgeCell j]}"
  | ["syllables"] =>
    for n in List.range 11 do
      for k in SyllableTable.allK (n + 1) do
        IO.println (SyllableTable.render k)
  | ["hadd"] =>
    for n in List.range 4 do
      for w in HaddTable.allW (n + 1) do
        IO.println (HaddTable.render w)
  | ["mizan-lean"] =>
    for r in MizanTable.leanFile do IO.println r
  | ["masfufa-lean"] =>
    -- مصفوفتا انتقال الوصل والوقف ومتّجها القبول حرفيّةً (`TawafiqMasfufa`، STEP-0010)؛ النواةُ تفحص أنّها هي (`MW_eq`…).
    let lst : List Nat → String := fun r => "[" ++ String.intercalate ", " (r.map toString) ++ "]"
    IO.println "/-! مولَّدٌ بـ`lake exe a116-table masfufa-lean`؛ لا يُحرَّر باليد. النواةُ تفحص أنّه `TawafiqMasfufa.MW` و`MQ` و`aW` و`aQ` بعينها (`MW_eq`…). -/"
    IO.println ""
    IO.println "namespace A116.TawafiqMasfufaData"
    IO.println ""
    for (name, m) in [("wL", TawafiqMasfufa.MW), ("qL", TawafiqMasfufa.MQ)] do
      IO.println s!"def {name} : List (List Nat) := ["
      for (r, i) in m.zip (List.range m.length) do
        IO.println s!"  {lst r}{if i + 1 < m.length then "," else ""}"
      IO.println "]"
      IO.println ""
    IO.println s!"def aWL : List Nat := {lst TawafiqMasfufa.aW}"
    IO.println ""
    IO.println s!"def aQL : List Nat := {lst TawafiqMasfufa.aQ}"
    IO.println ""
    IO.println "end A116.TawafiqMasfufaData"
  | ["masfufa"] =>
    -- عددُ المرخَّص لكلّ طول (`TawafiqMasfufa`، STEP-0010): المصفوفتان صفًّا صفًّا ومتّجها القبول، والقيمُ 0–14 بالضرب
    -- (`wasl_list`، `waqf_list`)، ليعيدها `tests/test_tawafiq_masfufa.py` بضربٍ مستقلّ ويطابقها بالتكرار.
    let row : String → List Nat → String := fun t r => t ++ "," ++ String.intercalate "," (r.map toString)
    for r in TawafiqMasfufaData.wL do IO.println (row "W" r)
    for r in TawafiqMasfufaData.qL do IO.println (row "Q" r)
    IO.println (row "aW" TawafiqMasfufaData.aWL)
    IO.println (row "aQ" TawafiqMasfufaData.aQL)
    for n in List.range 15 do
      let w := (TawafiqMasfufa.iterL TawafiqMasfufaData.wL TawafiqMasfufaData.aWL n).head?.getD 0
      let q := (TawafiqMasfufa.iterL TawafiqMasfufaData.qL TawafiqMasfufaData.aQL n).head?.getD 0
      IO.println s!"val,{n},{w},{q}"
  | ["mizan"] =>
    for r in MizanTable.rows do IO.println r
  | ["hadd-join"] =>
    for m in List.range 3 do
      for l in HaddTable.allJ (m + 1) do
        for n in List.range 2 do
          for r in HaddTable.allJ (n + 1) do
            IO.println (HaddTable.renderJoin l r)
  | ["iltiqa"] =>
    for m in List.range 2 do
      for l in HaddTable.allI (m + 1) do
        for n in List.range 2 do
          for r in HaddTable.allI (n + 1) do
            IO.println (HaddTable.renderIltiqa l r)
  | ["licensable"] =>
    -- المرخَّصُ من الشبكة: 113 خانةً (الألفُ المتحرّكة الثلاثُ خارجَه) — ذرّةٌ في كلّ سطر.
    for c in Alif.licensable do
      IO.println (HaddTable.atomsOf [c])
  | ["roles"] =>
    -- الأدوارُ المرخَّصة (`NizamHadd.licensed_roles_n`، ADR ٢٥): الذرّة، الصنف، عددُ الخانة، عددُ الدور n.
    let nm : Stages.K → String
      | .cv => "cv" | .v => "v" | .c => "c"
    for c in Alif.licensable do
      for k in Exhaust.rolesOf c do
        IO.println s!"{HaddTable.atomsOf [c]},{nm k},{Numbering.bridgeIndex c},{NizamHadd.roleN (k, c)}"
  | ["hamza"] =>
    -- جدولُ الكرسيّ لكلّ سياق: pos,own,prev,prevLong,prevYa,nextWaw,seat
    for p in [Hamza.Pos.initial, .medial, .final] do
      for own in [Haraka.fatha, .damma, .kasra, .sukun] do
        for prev in [Haraka.fatha, .damma, .kasra, .sukun] do
          for pl in [false, true] do
            for py in [false, true] do
              for nw in [false, true] do
                let s := Hamza.seatOf ⟨p, own, prev, pl, py, nw⟩
                IO.println s!"{repr p},{repr own},{repr prev},{pl},{py},{nw},{repr s}"
  | ["degrees"] =>
    -- جداولُ الدرجات وصلًا (`Exhaust.table`): الدرجة d = 1 … 4، والعدد n، ومقاطعُ الصفّ — 255 سطرًا.
    for k in List.range 4 do
      for n in List.range (3 * 4 ^ k) do
        let ss := Exhaust.decodeW k n
        IO.println s!"{k + 1},{n},{"-".intercalate (ss.map SyllableTable.sylName)}"
  | ["wazn"] =>
    -- الأوزانُ الثلاثيّة على الخانات (`Wazn.thulathi`) ابتداءً وصلًا بحالة الأصل الأخير الصرفيّة: رقمُ القالب،
    -- ثمّ الذرّاتُ والأصولُ أرقامًا (1 2 3) بحالاتها، ثمّ المقاطعُ وصلًا ووقفًا على الجذر الصحيح ك ت ب.
    let mark : Haraka → String
      | .fatha => "َ" | .damma => "ُ" | .kasra => "ِ" | .sukun => "ْ"
    let nm : Stages.Syl → String
      | .CV => "CV" | .CVV => "CVV" | .CVC => "CVC" | .CVVC => "CVVC" | .CVCC => "CVCC"
      | .CVVCC => "CVVCC"
    let sy := fun (w : List Cell) =>
      match Wazn.syllables w with
      | some ss => "-".intercalate (ss.map nm)
      | none => "none"
    for (i, W) in (List.range Wazn.thulathi.length).zip Wazn.thulathi do
      let pre := if W.wasl then [s!"ء{mark (Wazn.waslH W Wazn.ktb)}"] else []
      let body := W.body.map fun
        | .lit c => s!"{Field112.carrierChar c.carrier}{mark c.haraka}"
        | .slot j h => s!"{j.val + 1}{mark h}"
      let last := s!"{W.last.val + 1}{mark (Wazn.lastH i)}"
      let cont := Wazn.realize W Wazn.ktb .start .continue (Wazn.lastH i)
      let paus := Wazn.realize W Wazn.ktb .start .pause (Wazn.lastH i)
      IO.println s!"{i},{" ".intercalate (pre ++ body ++ [last])},{sy cont},{sy paus}"
  | ["wazn-body"] =>
    -- جسمُ كلّ وزنٍ ثلاثيّ رموزًا (`Wazn.thulathi`): رقمُه، أله همزةُ وصل، رقمُ الأصل الأخير، ثمّ الرموز:
    -- خانةٌ زائدة حرفًا وحالةً، أو أصلٌ رقمًا (1 2 3) وحالة.
    let mark : Haraka → String
      | .fatha => "َ" | .damma => "ُ" | .kasra => "ِ" | .sukun => "ْ"
    for (i, W) in (List.range Wazn.thulathi.length).zip Wazn.thulathi do
      let toks := W.body.map fun
        | .lit c => s!"{Field112.carrierChar c.carrier}{mark c.haraka}"
        | .slot j h => s!"{j.val + 1}{mark h}"
      IO.println s!"{i},{W.wasl},{W.last.val + 1},{" ".intercalate toks}"
  | ["neutral"] =>
    -- التقييمُ بالمحايد (`Neutral.realizeN`) على الجذور المرجعيّة والأوزان كلِّها، ابتداءً وصلًا وابتداءً وقفًا.
    let mark : Haraka → String
      | .fatha => "َ" | .damma => "ُ" | .kasra => "ِ" | .sukun => "ْ"
    let atoms := fun (w : List Cell) =>
      " ".intercalate (w.map fun c => s!"{Field112.carrierChar c.carrier}{mark c.haraka}")
    let names := ["قول", "سير", "دعو", "رمي", "وعد", "ءمن", "سءل", "قرء", "مدد", "هوي", "حيي"]
    for (nm, r) in names.zip Neutral.refRoots do
      for (i, W) in (List.range Wazn.thulathi.length).zip Wazn.thulathi do
        let c := Neutral.realizeN W r .start .continue (Wazn.lastH i)
        let p := Neutral.realizeN W r .start .pause (Wazn.lastH i)
        IO.println s!"{nm},{i},{atoms c},{atoms p}"
  | ["tasrif"] =>
    -- التصريفُ على الخانات (`Tasrif`، ADR ٢٦) على جذورٍ شواهد: الجذر، الصيغة، الباب، حركةُ العين،
    -- حرفُ المضارعة، الإعراب، ثمّ الذرّات. الصيغُ: madi (الماضي 3MS)، mudari، amr، amr-pause، khudh.
    let mark : Haraka → String
      | .fatha => "َ" | .damma => "ُ" | .kasra => "ِ" | .sukun => "ْ"
    let hn : Haraka → String
      | .fatha => "a" | .damma => "u" | .kasra => "i" | .sukun => "0"
    let atoms := fun (w : List Cell) =>
      " ".intercalate (w.map fun c => s!"{Field112.carrierChar c.carrier}{mark c.haraka}")
    let roots := ["قوم", "قول", "نوم", "خوف", "كون", "وقي", "وعي", "وعد", "وصل", "ولد", "نمو", "دعو",
      "خشي", "رضي", "نهي", "هدي", "مشي", "ءخذ", "ءمر", "عطو", "مدد"]
    for nm in roots do
      match nm.toList with
      | [a, b, c] =>
        let r := Tasrif.r3 a b c
        let s := Tasrif.sifa r
        let row := fun (k bab v p m : String) (t : List (Wazn.CSym 3)) =>
          IO.println s!"{nm},{k},{bab},{v},{p},{m},{atoms (Wazn.fillC t r)}"
        for a' in Tasrif.harakat3 do
          row "madi" "I" (hn a') "-" "-" (Tasrif.madi s a' .fatha)
        for v in Tasrif.harakat3 do
          for p in Tasrif.prefixes do
            for m in Tasrif.moods do
              row "mudari" "I" (hn v) p.toString (hn m) (Tasrif.mudari s .mujarrad p v m)
          row "amr" "I" (hn v) "-" "-" (Tasrif.amr s .mujarrad v)
          row "amr-pause" "I" (hn v) "-" "-" (Tasrif.amrPause s .mujarrad v)
          row "khudh" "I" (hn v) "-" "-" (Tasrif.amrKhudh s v)
        for p in Tasrif.prefixes do
          for m in Tasrif.moods do
            row "mudari" "IV" "i" p.toString (hn m) (Tasrif.mudari s .afala p .kasra m)
        row "amr" "IV" "i" "-" "-" (Tasrif.amr s .afala .kasra)
      | _ => pure ()
  | ["rubai"] =>
    -- أوزانُ الرباعيّ (`Rubai`، ADR ٢٨) على جذورٍ شواهد: اسمُ الوزن، الجذر، الذرّاتُ ابتداءً وصلًا ووقفًا؛
    -- ثمّ عددُ شاهد الدلالة المختوم (`Rubai.maqayisCount`).
    let mark : Haraka → String
      | .fatha => "َ" | .damma => "ُ" | .kasra => "ِ" | .sukun => "ْ"
    let atoms := fun (w : List Cell) =>
      " ".intercalate (w.map fun c => s!"{Field112.carrierChar c.carrier}{mark c.haraka}")
    let roots := ["حصحص", "عسعس", "دمدم", "وسوس", "بعثر", "زحزح", "زلزل", "دحرج", "مضمض", "دهده", "طمءن",
      "شمءز", "قشعر"]
    for B in Rubai.abniya do
      for nm in roots do
        match nm.toList with
        | [a, b, c, d] =>
          let r := Rubai.r4 a b c d
          IO.println s!"{B.name},{nm},{atoms (Wazn.realize B.w r .start .continue B.h)},{atoms (Wazn.realize B.w r .start .pause B.h)}"
        | _ => pure ()
    IO.println s!"maqayis,{Rubai.maqayisCount}"
  | ["maqayis"] =>
    -- جذورُ «مقاييس اللغة» الثلاثيّة صفوفًا من جدول الدرجة (`Maqayis.roots`، ADR ٣٥): الأصولُ حروفًا بترتيب العدد n.
    for r in Maqayis.roots do
      IO.println (String.ofList (r.map fun d => Field112.carrierChar (RootGrade.toCarrier d)))
  | ["degrees-pause"] =>
    -- جداولُ الدرجات وقفًا (`ExhaustPause.pauseTable`، ADR ١٨): الدرجة d = 1 … 4، والعدد n، ومقاطعُ الصفّ — 510 سطرًا.
    for k in List.range 4 do
      for n in List.range (6 * 4 ^ k) do
        let ss := ExhaustPause.decodeP k n
        IO.println s!"{k + 1},{n},{"-".intercalate (ss.map SyllableTable.sylName)}"
  | ["ledger"] =>
    -- الأوزانُ في جداول درجاتها (`Ledger.waznRows`، ADR ١٩): رقمُ القالب، الدرجة، العدد n.
    for (i, d, n) in Ledger.waznRows do
      IO.println s!"{i},{d},{n}"
  | ["qufl"] =>
    -- قفلُ الدالّ (`Qufl.locked`، ADR ٦٢): لكلّ درجةٍ 1–4 ولكلّ وظيفةٍ قيامُ سندها؛ ثمّ شواهدُ القفل: الماضي فَعَلَ
    -- على جذور الصفات الستّ وصلًا ووقفًا، ودَحْرَجَ على فَعْلَلَ.
    let wn := fun (w : Exhaust.Wazifa) => match w with
      | .tarmiz => "tarmiz" | .imla => "imla" | .sawt => "sawt" | .ishtiqaq => "ishtiqaq"
      | .sarf => "sarf" | .nahw => "nahw" | .dalala => "dalala"
    for d in [1, 2, 3, 4] do
      for w in Exhaust.Wazifa.all do
        let reason := match Qufl.locked d w with | .muallaq r => r | _ => "-"
        IO.println s!"row,{d},{wn w},{(Qufl.locked d w).qaim},{reason}"
    for r in Qufl.shawahid do
      let f := Wazn.fillC (Tasrif.madi (Tasrif.sifa r) .fatha .fatha) r
      IO.println s!"madi,{HaddTable.atomsOf f},{Hadd.strictB f},{Hadd.strictPauseB (Pause.pause f)}"
    let q := Wazn.realize Rubai.faalala.w (Rubai.r4 'د' 'ح' 'ر' 'ج') .start .continue Rubai.faalala.h
    IO.println s!"rubai,{HaddTable.atomsOf q},{Hadd.strictB q},{Hadd.strictPauseB (Wazn.realize Rubai.faalala.w (Rubai.r4 'د' 'ح' 'ر' 'ج') .start .pause Rubai.faalala.h)}"
  | ["tawafiq"] =>
    -- توافيقُ الخانات (`Tawafiq`، ADR ٦٣): لكلّ طولٍ 1–3 كلُّ سلاسل الشبكة المرخَّصة (113^n)، والمرخَّصُ منها
    -- وصلًا ووقفًا، وما آخرُه ألفٌ مُغلِقة (`ALIF_CLOSER_NOT_REFUSED`).
    IO.println "n,total,wasl,waqf,alif_closers"
    for n in [1, 2, 3] do
      let s := Tawafiq.seqs n
      IO.println s!"{n},{s.length},{Tawafiq.wasl n},{Tawafiq.waqf n},{Tawafiq.alifClosers n}"
    -- الفضاءُ المولَّد (ADR ٦٩): أبنيةُ الاسم الثلاثيّ — الأعمى، والقانونُ وصلًا ووقفًا، والاثنا عشر، والمنقولُ عشرة.
    IO.println s!"g,ism3,{Tawafiq.shapes64.length},{(Tawafiq.shapes64.filter Hadd.strictB).length},{(Tawafiq.shapes64.filter Hadd.strictPauseB).length},{Tawafiq.lawIsm.length},{Tawafiq.naqlIsm.length}"
    for r in Tawafiq.naqlIsm do
      IO.println s!"naql,{HaddTable.atomsOf (Tawafiq.shape r.1 r.2.1 .sukun)},{r.2.2.1},{r.2.2.2}"
    -- الدرجاتُ الأعلى (ADR ٧٠): الفعلُ الثلاثيّ، والرباعيُّ المجرّد، والزوائد — الأعمى، والقانون، والمنقول.
    IO.println s!"g,fil3,{Tawafiq.ismPairs.length},{Tawafiq.lawFil.length},-,{Tawafiq.lawFil.length},{Tawafiq.naqlFil.length}"
    IO.println s!"g,rubai4,{Tawafiq.shapes48.length},{(Tawafiq.shapes48.filter Hadd.strictB).length},-,-,1"
    IO.println s!"g,zawaid,{Wazn.thulathi.length},{Wazn.thulathi.length},-,-,{Wazn.thulathi.length}"
  | ["amil"] =>
    -- العاملُ والمعمول (`Amil`، ADR ٧٠): لكلّ زوجٍ (صنف، حالة) له آخرٌ: الآخرُ، أصليٌّ أم حرفيّ، ونائبٌ عن أصله أم لا.
    let short := fun (s : String) => (s.splitOn ".").getLastD s
    let cn := fun (c : Qism.Cls) => short (repr c).pretty
    let en := fun (e : Qism.Ending) => short (repr e).pretty
    let irn := fun (i : Qism.Irab) => short (repr i).pretty
    IO.println "cls,irab,ending,asliyya,naib"
    for p in Qism.pairs do
      match Qism.ending p.1 p.2 with
      | some e => IO.println s!"{cn p.1},{irn p.2},{en e},{Amil.asliyya e},{Amil.naib p.1 p.2}"
      | none => pure ()
  | ["need"] =>
    -- قانونُ الحاجة المتبادلة (`Hajah.NeedLaw`) على كلّ سلسلةِ أدوارٍ بطول 1 … 8 (9,840 سطرًا): السلسلة، والقانون،
    -- وحالةُ الوراثة بعدها (ذيلُ المقطع المفتوح، أو none).
    let st := fun (s : Option (Option (List Stages.K))) => match s with
      | some (some t) => "[" ++ "-".intercalate (t.map SyllableTable.kName) ++ "]"
      | some none => "none"
      | none => "refused"
    for n in List.range 8 do
      for k in SyllableTable.allK (n + 1) do
        IO.println s!"{"-".intercalate (k.map SyllableTable.kName)},{decide (Hajah.NeedLaw k)},{st (Hajah.needState none k)}"
  | ["nizam"] =>
    -- نظامُ الجوار الثلاثيّ (`Nizam.ternary`، ADR ٢٣): لكلّ زوجٍ (قبل، بعد) من أصناف الذرّة إذنُه وصلًا ووقفًا.
    let nm : Stages.K → String
      | .cv => "cv" | .v => "v" | .c => "c"
    for a in [Stages.K.cv, .v, .c] do
      for b in [Stages.K.cv, .v, .c] do
        IO.println s!"{nm a},{nm b},{Nizam.waslK a b},{Nizam.waqfK a b}"
  | ["silsila"] =>
    -- السلسلةُ كلمةً كلمة (`Silsila`، ADR ١١٤)، ليُطابَق بمرآة `tools/gen_silsila.py` سطرًا سطرًا.
    let duns : List Silsila.Hal :=
      [.muayyan "d", .muhtamal ["d", "e"], .laHukm (.rafd "R"), .laHukm .dunaha, .laHukm .laQari,
       .laHukm .kharij]
    let qs : List (String × Option (String → Silsila.Hal → Silsila.Hal)) :=
      [("none", none), ("m", some fun _ _ => .muayyan "v"), ("p", some fun _ _ => .muhtamal ["v", "u"]),
       ("l", some fun _ _ => .laHukm (.rafd "Q")), ("k", some fun _ _ => .laHukm .kharij), ("echo", some fun _ d => d),
       ("word", some fun w _ => if w = "x" then .muayyan w else .laHukm (.rafd "R"))]
    for w in ["x", "y"] do for d in duns do for (qn, q) in qs do
      IO.println s!"khutwa,{w},{Silsila.ramz d},{qn},{Silsila.ramz (Silsila.khutwa w d ⟨qn, q⟩)}"
    let ws := ["كَتَبَ", "كتب"]
    let out := Silsila.silsila [Silsila.shahadaMithal, Silsila.qismMithal, Silsila.jinsMithal] ws
    for (w, hs) in ws.zip out do
      for (k, h) in (List.range hs.length).zip hs do
        IO.println s!"silsila,{w},{k},{Silsila.ramz h}"
    -- قارئا الجنس والحمل (`SilsilaQurra`) على المعجم الشاهد: الهيكلُ والجذورُ والأجناس، ثمّ الحملُ على مفاتيحَ وقيود.
    let nawR : Haqaiq.Naw → String
      | .lughawiyya => "lughawiyya" | .shariyya => "shariyya"
      | .urfiyya .amma => "urfiyya_amma" | .urfiyya .khassa => "urfiyya_khassa"
    let pr : List (String × String) → String := fun ps => String.intercalate "|" (ps.map fun p => s!"{p.1}:{p.2}")
    for w in ["ءَلْكَلْبُ", "ءَشْشَمْسُ", "لْكَلْبُ", "كَلْبُ", "عَيْنُ", "ءَلْعَيْنُ", "كَتَبَ", "ءَلْلَيْلُ", "ءَيْيَاْمِ", "شْشَمْسُ"] do
      let rs := SilsilaQurra.judhurOf SilsilaQurra.hyMithal (Itar.k w)
      IO.println s!"jins,{w},{QiraaMadlul.haykal (SilsilaQurra.tajrid (Itar.k w))},{String.intercalate "|" rs},{pr (SilsilaQurra.ajnasOf SilsilaQurra.ajMithal rs)}"
    let hs : List (String × String × List String) :=
      [("الصلاة", "صَ لَ اْ ت", ["صلو"]), ("الصلاة", "صَ لَ اْ ت", ["عين"]), ("الكلب", "كَ لْ ب", ["كلب"]),
       ("الدابة", "كَ لْ ب", ["كلب"]), ("الرفع", "عَ يْ ن", ["عين", "عون"]), ("عين", "عَ يْ ن", []),
       ("الكلب", "سَ مَ اْ ء", ["سمو"])]
    for (l, key, rs) in hs do
      let out := SilsilaQurra.hamlOf Haqaiq.naql SilsilaQurra.wadMithal l key rs
      IO.println s!"haml,{l},{key},{String.intercalate "|" rs},{String.intercalate "|" (out.map fun x => s!"{x.1}:{nawR x.2}")}"
  | ["furu"] =>
    -- فروعُ السلسلة وحملُ الحرف ومرشَّحو التقشير (`SilsilaFuru`، ADR ١١٥)، ليُطابَق بمرآة `tools/gen_silsila.py` سطرًا سطرًا.
    let str : List Cell → String := fun w => String.ofList ((Imla.render w).map Char.ofNat)
    let ws := ["بِسْمِ", "وَلَاْ", "وَبِلْغَيْبِ", "فَلِيَعْبُدُوْاْ", "كَمَثَلِ", "لِلْ", "بِهِ", "ءِلَاْ", "ءِلْلَاْ", "حَتْتَاْ",
      "مِنْ", "وَمَاْ", "لَكُمْ", "كَتَبَ"]
    for w in ws do
      IO.println s!"qashr,{w},{String.intercalate "|" ((SilsilaFuru.qashr (Itar.k w)).map str)}"
      IO.println s!"key,{w},{SilsilaFuru.harfKey (Itar.k w)}"
      let hit : List Cell → Bool := fun v => ["لا", "ما", "وما", "من", "لغيب", "يعبدوا"].contains (SilsilaFuru.harfKey v)
      IO.println s!"awwal,{w},{((SilsilaFuru.awwal hit (Itar.k w)).map str).getD "-"}"
    let mn : Iqtiran.Mantuq String → String
      | .muayyan m => s!"m:{m}" | .muhtamal ms => s!"p:{String.intercalate "|" ms}" | .laHukm => "l"
    let hk : Naql.Hukm → String
      | .minHaythuHiya => "hiya" | .maluma ss => s!"maluma:{ss.length}"
      | .mafhum r s ss => s!"mafhum:{match r with | .qati => "qati" | .zanni => "zanni"}:{s.qail}:{ss.length}"
    for k in ["من", "و", "رب", "ءلا"] do
      let (m, _, h) := SilsilaFuru.hamlHarf (fun _ => false) SilsilaFuru.maaniMithal k
      IO.println s!"harf,{k},{mn m},{hk h}"
    for keys in [["صَ لَ اْ ت"], ["صَ لَ اْ ت", "كَ لْ ب"], ["كَ لْ ب"]] do
      let out := SilsilaFuru.hamlWad Haqaiq.naql (fun _ => false) SilsilaFuru.shWad "الصلاة" keys
      IO.println s!"wad,{String.intercalate "|" keys},{String.intercalate "|" (out.map fun x => s!"{x.1}:{hk x.2.2}")}"
  | ["mantuq"] =>
    -- الجسرُ من المنطوق إلى المفهوم الأصوليّ (`MantuqMafhum`، ADR ١١٢)، ليُطابَق بـ`gate.mantuq` سطرًا سطرًا:
    -- `naw` على الصفات الستّ عشرة، و`mukhalafa` على ثمانية قيودٍ × الأغلب × المعطِّل، والرتبةُ بمساريها على مودَعاتٍ صغيرة.
    let b : Bool → String := fun x => if x then "1" else "0"
    let nn : MantuqMafhum.Naw → String
      | .iqtida => "iqtida" | .tanbih => "tanbih" | .ishara => "ishara"
      | .muwafaqa => "muwafaqa" | .mukhalafa => "mukhalafa"
    let mn : MantuqMafhum.Mani → String
      | .adadBilaSiyaq => "adadBilaSiyaq" | .ism => "ism" | .wasfGhayrMufhim => "wasfGhayrMufhim"
      | .innama => "innama" | .aghlab => "aghlab" | .muattil => "muattil"
    let hn : MantuqMafhum.Hukm → String
      | .yumal m => s!"yumal:{nn m.naw}" | .layumal x => s!"layumal:{mn x}"
    let bs := [false, true]
    for s1 in bs do for s2 in bs do for s3 in bs do for s4 in bs do
      IO.println s!"naw,{b s1}{b s2}{b s3}{b s4},{nn (MantuqMafhum.naw ⟨s1, s2, s3, s4⟩)}"
    let qs : List (String × MantuqMafhum.Qayd) :=
      [("sifa1", .sifa MantuqMafhum.saima), ("sifa0", .sifa Dalalat.sail), ("shart", .shart), ("ghaya", .ghaya),
       ("adad1", .adad true), ("adad0", .adad false), ("ism", .ism), ("innama", .innama)]
    for (qn, q) in qs do for a in bs do for u in bs do
      IO.println s!"mukhalafa,{qn},{b a}{b u},{hn (MantuqMafhum.mukhalafa q a u "م")}"
    let m1 : MantuqMafhum.MafhumUsul := ⟨.mukhalafa, "أ"⟩
    let m2 : MantuqMafhum.MafhumUsul := ⟨.mukhalafa, "ب"⟩
    let sh : Naql.Tariq → Naql.Mawda → Naql.Shahada := fun t w => ⟨"م", "م", t, w, 0⟩
    let tn : Naql.Tariq → String | .naql => "naql" | .hiss => "hiss" | .aql => "aql"
    let wn : Naql.Mawda → String
      | .waqiMakhtum => "waqiMakhtum" | .wad => "wad" | .malumat => "malumat" | .marjaMahjub => "marjaMahjub"
    let kinds : List Naql.Shahada :=
      [Naql.Tariq.naql, .hiss, .aql].flatMap fun t => [Naql.Mawda.waqiMakhtum, .wad, .malumat, .marjaMahjub].map (sh t)
    let one : Naql.Shahada → String := fun s => s!"{tn s.tariq}-{wn s.mawda}"
    let dn : MantuqMafhum.Mudaa → String := fun d =>
      if d.isEmpty then "none" else "|".intercalate (d.map fun (m, s) => s!"{if m = m1 then "m1" else "m2"}:{one s}")
    let ds : List MantuqMafhum.Mudaa :=
      [[]] ++ kinds.map (fun s => [(m1, s)]) ++ [[(m2, sh .hiss .waqiMakhtum)]] ++
      [[(m1, sh .naql .wad), (m1, sh .naql .marjaMahjub)], [(m1, sh .naql .wad), (m1, sh .naql .malumat)],
       [(m1, sh .hiss .waqiMakhtum), (m1, sh .hiss .wad)]]
    let hs : List (String × MantuqMafhum.Hukm) := [("yumal:m1", .yumal m1), ("layumal:ism", .layumal .ism)]
    let rn : Iqtiran.Martaba → String
      | .minHaythuHiya => "minHaythuHiya" | .maluma => "maluma" | .mafhum => "mafhum"
    let nh : Naql.Hukm → String
      | .minHaythuHiya => "minHaythuHiya"
      | .maluma ws => s!"maluma:{ws.length}"
      | .mafhum r _ ss => s!"mafhum:{match r with | .qati => "qati" | .zanni => "zanni"}:{ss.length + 1}"
    for d in ds do for (hnm, h) in hs do
      IO.println s!"martaba,{dn d},{hnm},{rn (MantuqMafhum.martabaWaqi d h)},{nh (MantuqMafhum.hukmNaql (Naql.jisrWad (fun _ => false)) d h)},{nh (MantuqMafhum.hukmNaql (Naql.jisrWad (fun _ => true)) d h)},{nh (MantuqMafhum.hukmNaql Naql.jisrWaqi d h)}"
    -- التركيب: رتبةُ ما يُخرجه الجسرُ نفسُه (`martabaWaqi d (mukhalafa q a u mana)`) بمعنيين، فالمفهومُ في الحكم لا مُدخَلٌ منفصل.
    for (qn, q) in qs do for (a, u) in [(false, false), (true, false)] do for mana in ["أ", "ب"] do
      for d in [[], [(m1, sh .hiss .waqiMakhtum)], [(m2, sh .hiss .waqiMakhtum)]] do
        IO.println s!"tarkib,{qn},{b a}{b u},{mana},{dn d},{rn (MantuqMafhum.martabaWaqi d (MantuqMafhum.mukhalafa q a u mana))}"
  | ["amr"] =>
    -- المضارعُ والأمر (`Mudari`، ADR ٢٤) على الجذور المرجعيّة × الأوزان التسعة × الأبواب: رقمُ الجذر، الوزن، الباب،
    -- المضارعُ رفعًا بالياء، والمجزومُ بالتاء، والأمر — ذرّاتٍ، وأأقام قانونُ الابتداء همزةَ وصل.
    let mark : Haraka → String
      | .fatha => "َ" | .damma => "ُ" | .kasra => "ِ" | .sukun => "ْ"
    let atoms := fun (w : List Cell) =>
      " ".intercalate (w.map fun c => s!"{Field112.carrierChar c.carrier}{mark c.haraka}")
    let fname : Mudari.Form → String
      | .I => "I" | .II => "II" | .III => "III" | .IV => "IV" | .V => "V" | .VI => "VI"
      | .VII => "VII" | .VIII => "VIII" | .X => "X"
    for (r, i) in Mudari.refRoots.zip (List.range Mudari.refRoots.length) do
      for f in Mudari.Form.all do
        for b in Mudari.babs r f do
          IO.println s!"{i},{fname f},{mark b},{atoms (Mudari.mudari r f b 'ي' .damma)},{atoms (Mudari.mudari r f b 'ت' .sukun)},{atoms (Mudari.amr r f b)},{Mudari.amrWasl r f b}"
  | ["qarar"] =>
    -- سلسلةُ القرار (`Qarar.judge1`، `Manhaj.judgeT`، ADR ٥٨) على كلّ سلسلةٍ حتى ثلاثِ دعاوى (33,296 سطرًا): لكلّ دعوى
    -- رقمُها i ووجودٌ وحسٌّ ومعارض، وأصولُها من السابق مع أصلٍ مفقود (9) أو بدونه؛ ثمّ الحكمان بالترتيب.
    let hn : Qarar.Hukm → String
      | .qati => "qati" | .zanni => "zanni" | .khata => "khata" | .saqit => "saqit"
      | .dawr => "dawr" | .laHukm => "laHukm"
    let b : Bool → String := fun x => if x then "1" else "0"
    let subsets : List Nat → List (List Nat) :=
      fun xs => xs.foldr (fun x acc => acc.map (x :: ·) ++ acc) [[]]
    let opts : Nat → List (List Nat) := fun n =>
      (subsets ((List.range n).map (· + 1))).flatMap fun us => [us, us ++ [9]]
    let bits : List (Bool × Bool × Bool) :=
      [false, true].flatMap fun w => [false, true].flatMap fun s => [false, true].map fun m => (w, s, m)
    let grow : List (List Qarar.Daawa) → Nat → List (List Qarar.Daawa) := fun chs n =>
      chs.flatMap fun ch => bits.flatMap fun (w, s, m) => (opts n).map fun us =>
        ch ++ [Qarar.d (n + 1) w s m us]
    let enc : Qarar.Daawa → String := fun c =>
      s!"{c.id}:{b c.wujud}{b c.mahsus}{b c.muarid}:{".".intercalate (c.usul.map toString)}"
    let mut chs : List (List Qarar.Daawa) := [[]]
    for n in List.range 3 do
      chs := grow chs n
      for ch in chs do
        let v1 := (Qarar.run ch).map fun x => hn x.2
        let vT := (Manhaj.ids (Manhaj.runD Manhaj.judgeT ch)).map fun x => hn x.2
        IO.println s!"{";".intercalate (ch.map enc)},{" ".intercalate v1},{" ".intercalate vT}"
  | ["huruf"] =>
    -- جدولُ المخارج والصفات (`Jadwal`، ADR ٧٣): البرجُ مخرجٌ ⊃ حرفٌ ⊃ حركة، 116 خانةً بترتيب المخارج الستّةَ عشر؛
    -- لكلّ خانة: مخرجُها عند سيبويه وابن جنّي (16)، والجزريّ (17، والألفُ في الجوف 0)، وحيزُها عند الخليل (11)،
    -- وصفاتُها الأربعَ عشرة، وترخيصُها، وجوازُ الابتداء بها، والوقفُ عليها.
    let hn := fun (h : Haraka) => match h with
      | .fatha => "fatha" | .damma => "damma" | .kasra => "kasra" | .sukun => "sukun"
    IO.println s!"k,harf,haraka,makhraj16,jazari17,khalil11,{",".intercalate ["hams", "shidda", "tawassut", "istila", "itbaq", "idhlaq", "safir", "qalqala", "lin", "inhiraf", "takrir", "tafashi", "istitala", "ghunna"]},licensable,ibtida,waqf"
    let mut k := 0
    for h in Jadwal.jadwal do
      for v in Jadwal.harakat do
        let x := Ladder.atom h.c v
        let lic := Jadwal.licensableCell x
        let bits := ",".intercalate (h.sifat.map fun b => if b then "1" else "0")
        IO.println s!"{k},{h.c},{hn v},{h.makhraj},{h.jazariMakhraj},{h.hayyiz},{bits},{lic},{lic && v != .sukun},{v == .sukun}"
        k := k + 1
  | ["marja"] =>
    -- مرجعُ المالك (`Marja`، ADR ١١٨): لكلّ خانةٍ من البرج (`Jadwal.khanat`) ولكلّ موضعٍ من التسعة ولادةٌ بعددها
    -- ‎n = 9·k + m‎، ودورُها (`Hadd.kindOne`) وحكمُها، وشرطُ المشروط واسمُ المرفوض؛ ودرجةُ ولادة الحرف في سُلَّم الباب.
    let hn := fun (h : Haraka) => match h with
      | .fatha => "fatha" | .damma => "damma" | .kasra => "kasra" | .sukun => "sukun"
    let kn := fun (k : Stages.K) => match k with | .cv => "cv" | .v => "v" | .c => "c"
    let mn := fun (m : Marja.Mawdi) => match m with
      | .ibtida => "ibtida" | .wasl p => s!"wasl:{hn p}" | .waqf p => s!"waqf:{hn p}"
    IO.println "n,k,harf,haraka,makhraj16,wilada,mawdi,dawr,hukm,qabl,shart"
    for b in Marja.wiladat do
      let x := b.1
      let c := Field112.carrierChar x.carrier
      let (h, q, s) := match Marja.hukm b.2 x with
        | .murakhkhas => ("murakhkhas", "", "")
        | .mashrut qs sh => ("mashrut", " ".intercalate (qs.map kn), sh)
        | .yuskan => ("yuskan", "", "")
        | .marfud ism => ("marfud", "", ism)
      IO.println s!"{Marja.nOf b},{Jadwal.khanat.idxOf x},{c},{hn x.haraka},{Makharij.makhrajOf c},{Marja.wilada c},{mn b.2},{kn (Marja.dawr b.2 x)},{h},{q},{s}"
  | ["marja-huruf"] =>
    -- الحروفُ في سُلَّم الباب (`Marja`، ADR ١١٨): المخرجُ وحجمُ ليفه، والجهرُ والصنفُ والإطباق، ودرجةُ الولادة، وقرناءُ
    -- الحرف في كلّ درجةٍ قبلها، وأقسامُ قانون الإدغام (`MakharijIdgham.qism`) والحرفُ أوّلًا.
    let b := fun (x : Bool) => if x then "1" else "0"
    IO.println "harf,makhraj16,lif,jahr,manner,itbaq,wilada,qurana0,qurana1,qurana2,mithl,mithl_mumtani,shahid_idgham,shahid_mumtani,maskut,mumtani,izhar"
    for c in Makharij.placed16 do
      let m := Makharij.makhrajOf c
      let qs := ",".intercalate ([0, 1, 2].map fun d => String.ofList (Marja.qurana d c))
      let ids := ",".intercalate ((Marja.idghamAdad c).map toString)
      IO.println s!"{c},{m},{(Marja.lif m).length},{b (Makharij.jahrOf c)},{Makharij.mannerOf c},{b (Makharij.itbaqOf c)},{Marja.wilada c},{qs},{ids}"
  | ["baqi"] =>
    -- المتبقّي (`Baqi`، ADR ١٢٢): كلُّ صيغةٍ بعمقٍ ≤ 2 على ⊤ و⊥ وذرّتين، مع كلّ أدلّةٍ ثلاثيّة على الذرّتين؛
    -- الحكمُ والمطلوبُ الأدنى، ليُطابَقا بتعدادٍ مستقلٍّ للاستكمالات في `tests/test_baqi.py`.
    let qs : Bawwabat.Q → String
      | some true => "P" | some false => "N" | none => "U"
    let rec sh : Baqi.Sigha → String
      | .thabit => "T" | .mumtani => "F" | .dharra a => s!"a{a}"
      | .wa p q => s!"({sh p}&{sh q})" | .aw p q => s!"({sh p}|{sh q})"
    let d0 : List Baqi.Sigha := [.thabit, .mumtani, .dharra 0, .dharra 1]
    let up (l : List Baqi.Sigha) : List Baqi.Sigha :=
      l.flatMap fun p => l.flatMap fun q => [.wa p q, .aw p q]
    let d1 := d0 ++ up d0
    let d2 := d0 ++ up d1
    let vs : List Bawwabat.Q := [none, some true, some false]
    IO.println "sigha,e0,e1,hukm,matlub"
    for f in d2 do for v0 in vs do for v1 in vs do
      let e : Nat → Bawwabat.Q := fun a => if a = 0 then v0 else if a = 1 then v1 else none
      let m := (Baqi.matlubAdna e f).map fun S =>
        if S.isEmpty then "{}" else String.intercalate "+" (S.map fun a => s!"a{a}")
      IO.println s!"{sh f},{qs v0},{qs v1},{qs (Baqi.qima e f)},{String.intercalate "/" m}"
  | ["marja-azwaj"] =>
    -- الأزواجُ الـ841 بقسمها في قانون الإدغام (`MakharijIdgham.qism`)، يقرؤها `tools/gen_marja.py` للشاهد (ADR ١١٨).
    let qn := fun (q : MakharijIdgham.Qism) => match q with
      | .mithl => "mithl" | .mithlMumtani => "mithl_mumtani" | .shahidIdgham => "shahid_idgham"
      | .shahidMumtani => "shahid_mumtani" | .maskut => "maskut" | .mumtani => "mumtani" | .izhar => "izhar"
    IO.println "a,b,qism"
    for (a, c) in MakharijIdgham.allPairs do
      IO.println s!"{a},{c},{qn (MakharijIdgham.qism a c)}"
  | ["utf8"] =>
    -- أبجديّةُ الرسم: الحروفُ ‎U+0621–U+064A‎، العلاماتُ ‎U+064B–U+0652‎، ألفُ الوصل ‎U+0671‎، والمسافة.
    for c in (List.range 0x2B).map (· + 0x621) ++ (List.range 8).map (· + 0x64B) ++ [0x671, 0x20] do
      IO.println s!"{c},{" ".intercalate ((Unicode.utf8Encode c).map toString)}"
  | ["pairs"] =>
    for u in List.range 64 do
      for r in List.range 64 do
        IO.println s!"{u},{r},{Numbering.pair u r}"
  | _ =>
    for q in State.all do
      for c in cells do
        IO.println s!"{q.pyName},{c.carrier.val},{c.haraka.index},{(step q c).pyName}"
