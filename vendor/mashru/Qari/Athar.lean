import Nizam.Athar
/-!
# أداةُ الأثر (`athar`)
تطبع لكلّ جملةٍ أثرَ عُقَدها في المنطوق والمفهوم (`Nizam/Athar.lean`): صفوفَ كلّ كلمةٍ في جدول العوامل وأقسامَها، وحكمَ الجملة قبل المعجم
وبعده، والإطاراتِ بعد المعجم بمقدّمات كلماتها في أدوارها، وقوّةَ الجملة ودعواها بمقدّمتيها، والمنطوقَ (دورُ كلّ كلمةٍ ونسبتُه)، وقيدَ الجملة، وعقدةَ
المفهوم بمقدّماتها، ومفاهيمَ الجسر. ويفحصها `tahaqquq/test_athar.py`. تنفيذيٌّ مستقلٌّ عن القارئ فلا تتغيّر بصمتُه.

المدخل: سطرٌ لكلّ جملة «مفتاح⇥جملة مشكولة» (الفاصلُ بين الكلمات U+0020). وبالخيار `--sufuf` يطبع لكلّ سطرٍ «مفتاح⇥كلمة» صفوفَها وحدها.
المخرج (حقولٌ مفصولةٌ بـ⇥):
- `مفتاح SUFUF صفوف` — بالخيار `--sufuf`؛ والصفوفُ مفصولةٌ بفاصلة (`sufufKalima` على خلايا القارئ).
- `مفتاح ADAT رقم كلمة صفوف أقسام` — الأقسامُ لكلّ صفٍّ (`qism`)، أو «-» لصفٍّ بلا قسم.
- `مفتاح JUMLA حكم_قبل_المعجم حكم_بعده`.
- `مفتاح ITAR رقم أدوار حكم_بعد_المعجم`، ثمّ `مفتاح MUQ itar رقم نوع حال اسم سند` لمقدّمات الكلمات في أدوارها.
- `مفتاح QUWWA قوّة صفوف_الصدر` و`مفتاح DAWA حكم`، ثمّ `مفتاح MUQ dawa نوع حال اسم سند` لمقدّمتيها (الحكمُ المسنَد، والقوّة).
- `مفتاح MANTUQ رقم كلمة دور نسبة`.
- `مفتاح QAYD قيد رقم_الكلمة` أو `مفتاح QAYD -`.
- `مفتاح MAFHUM حكم مخرج عدد_مفاهيم_الجسر`، ثمّ `مفتاح MUQ mafhum نوع حال اسم سند`.
-/
open Nizam.Shahada Nizam.Silsila Nizam.Athar

def natijaIsmA : Natija → String
  | .ghayrMarbut => "غير_مربوط"
  | .madkhalFasid x => "مدخل_فاسد: " ++ x
  | .mumtani x => "ممتنع: " ++ x
  | .laTantabiq x => "لا_تنطبق: " ++ x
  | .muallaq l => "معلق: " ++ " | ".intercalate l
  | .murakhkhas => "مرخص"

def nawIsmA : Naw → String
  | .madkhal => "مدخل" | .shart => "شرط" | .mani => "مانع"

def halIsmA : Hal → String
  | .mashhud => "مشهود" | .manfi => "منفي" | .ghayrMafhus => "لم_يفحص"

def nisbaIsm : Option Jisr.Nisab.Nisba → String
  | some .isnadiyya => "إسنادية" | some .taqyidiyya => "تقييدية" | some .idafiyya => "إضافية" | none => "-"

def qismatIsm (r : Nat) : String :=
  match qism r with
  | some ks => "+".intercalate (ks.map qismIsm)
  | none => "-"

def muqA (k uqda : String) (ms : List Muqaddima) : IO Unit :=
  for m in ms do IO.println s!"{k}\tMUQ\t{uqda}\t{nawIsmA m.naw}\t{halIsmA m.halFiil}\t{m.ism}\t{m.sanad}"

def athar (k s : String) : IO Unit := do
  let t := s.toList
  for kw in kalimatM t do
    let rs := sufufKalima (khalaya kw.w)
    IO.println s!"{k}\tADAT\t{kw.i + 1}\t{String.ofList kw.w}\t{",".intercalate (rs.map toString)}\t{",".intercalate (rs.map qismatIsm)}"
  IO.println s!"{k}\tJUMLA\t{natijaIsmA (hukm (jumla t))}\t{natijaIsmA (hukm (jumlaM t))}"
  let us := utur t
  for (x, j) in us.zip (List.range us.length) do
    IO.println s!"{k}\tITAR\t{j + 1}\t{adwarIsm x.1}\t{natijaIsmA (hukm (uqdaItarM t x))}"
    muqA k s!"itar {j + 1}" (adawatItar t x.1)
  IO.println s!"{k}\tQUWWA\t{quwwaIsm (quwwaJumla t)}\t{",".intercalate ((sadr t).map toString)}"
  IO.println s!"{k}\tDAWA\t{natijaIsmA (hukm (uqdaDawa t))}"
  muqA k "dawa" [isnadMuq t, shartQuwwa t]
  for (m, j) in (mantuq t).zip (List.range (mantuq t).length) do
    IO.println s!"{k}\tMANTUQ\t{j + 1}\t{m.1}\t{dawrIsm m.2.1}\t{nisbaIsm m.2.2}"
  match qaydJumla t with
  | some p => IO.println s!"{k}\tQAYD\t{qaydIsm p.1}\t{p.2.i + 1}"
  | none => IO.println s!"{k}\tQAYD\t-"
  let n := uqdaMafhum t wadaKhali
  IO.println s!"{k}\tMAFHUM\t{natijaIsmA (hukm n)}\t{n.makhraj}\t{(mafahim t wadaKhali).length}"
  muqA k "mafhum" (muqMafhum t wadaKhali)

def main (args : List String) : IO UInt32 := do
  match args with
  | ["--sufuf", path] =>
    for line in ← IO.FS.lines path do
      match line.splitOn "\t" with
      | [k, w] => IO.println s!"{k}\tSUFUF\t{",".intercalate ((sufufKalima (khalaya w.toList)).map toString)}"
      | _ => IO.println s!"{line}\tKHALAL\tسطرٌ ليس «مفتاح⇥كلمة»"
    return 0
  | [path] =>
    for line in ← IO.FS.lines path do
      match line.splitOn "\t" with
      | [k, s] => athar k s
      | _ => IO.println s!"{line}\tKHALAL\tسطرٌ ليس «مفتاح⇥جملة»"
    return 0
  | _ => IO.eprintln "الاستعمال: athar [--sufuf] <ملفّ: مفتاح⇥جملة>"; return 2
