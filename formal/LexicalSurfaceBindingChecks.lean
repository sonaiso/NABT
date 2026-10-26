import Nabt.LexicalSurfaceBinding

/-! Independent boundary controls for the exact surface bridge. The retained
QAC 102:7:3:1 row is a spelling/annotation witness only. These controls do not
assert the intended sense of a new occurrence or completeness of Arabic. -/
open Nabt Nabt.LexicalSurfaceBinding

private def row : String :=
  "(102:7:3:1)\tEayona\tN\tSTEM|POS:N|LEM:Eayon|ROOT:Eyn|F|ACC\r\n"

private def witness : Witness :=
  ⟨"qac:102:7:3:1",
    ⟨⟨"qac-record:102:7:3:1",
      "4d453eb7a1f933aa0f82b175886cf203a14a656e654f655314f549187824c6d0", row⟩,
      "qac-FORM", "102:7:3:1", "Eayon", 12, 18, "Eayona"⟩,
    "عين", "linguistic"⟩

private def source (text : String) : Foundation.Source := ⟨"control", "v1", text⟩
private def frame (text : String) : LinguisticTruth.Frame :=
  ⟨⟨"control", "v1", text, 0, text.utf8ByteSize, "unspecified", "unspecified", "control"⟩,
    "عين", "linguistic"⟩

set_option maxRecDepth 10000
set_option maxHeartbeats 3000000

example : decodeForm "Eayona" = some [68, 111, 96] := by decide +kernel
example : renderArabic [68, 111, 96] = "عَيْنَ" := by decide +kernel
example : encodeForm [68, 111, 96] = "Eayona" := by decide +kernel
example : decodeForm "Eayon" = none := by decide +kernel
example : decodeForm "EayoNa" = none := by decide +kernel
example : decodeForm ">asada" = none := by decide +kernel
example : decodeForm "Eayo~na" = none := by decide +kernel
example : decodeForm "Eayona " = none := by decide +kernel
example : decodeForm "" = some [] := by decide +kernel

example : checkWitness (source "عَيْنَ") (frame "عَيْنَ") "عَيْنَ" [witness] witness = true := by
  decide +kernel
example : checkWitness (source "عِيْنَ") (frame "عِيْنَ") "عِيْنَ" [witness] witness = false := by
  decide +kernel
example : checkWitness (source "عَيْنُ") (frame "عَيْنُ") "عَيْنُ" [witness] witness = false := by
  decide +kernel
example : checkWitness (source "عين") (frame "عين") "عين" [witness] witness = false := by
  decide +kernel
example : checkWitness (source "عَ يْنَ") (frame "عَ يْنَ") "عَ يْنَ" [witness] witness = false := by
  decide +kernel
example : (Foundation.project (source "عَ يْنَ")).cells =
    (Foundation.project (source "عَيْنَ")).cells := by decide +kernel
example : checkWitness (source "عَيْنَ") (frame "عَيْنَ") "عَيْنَ" [] witness = false := by
  decide +kernel
example : checkWitness (source "عَيْنَ") {frame "عَيْنَ" with expression := "ذهب"}
    "عَيْنَ" [witness] witness = false := by decide +kernel
example : checkWitness (source "عَيْنَ") {frame "عَيْنَ" with convention := "other"}
    "عَيْنَ" [witness] witness = false := by decide +kernel
example : checkWitness (source "عَيْنَ") (frame "عَيْنَ") "عَيْنَ" [witness]
    {witness with binding := {witness.binding with startByte := 11}} = false := by
  decide +kernel
example : (witnesses (source "عَيْنَ") (frame "عَيْنَ") "عَيْنَ"
    [witness, {witness with id := "second-explicit-witness"}]).length = 2 := by
  decide +kernel
