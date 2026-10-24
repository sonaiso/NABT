import Nabt.ClassicalLanguageEvidence
import Lean

/-!
49 deterministic rows: eight ending functions, four inverse surface readings,
all 6 × 2 × 3 inna/operator-form-ma cases, and one Jurjani count partition.
This export covers the finite
laws, not the authenticity of source snapshots or their interpreted readings.
-/

open Lean Nabt.ClassicalLanguageEvidence

def main : IO Unit := do
  for course in courses do
    IO.println (Json.mkObj [
      ("law_id", toJson endingLawId), ("kind", toJson "course"),
      ("course", toJson course.label), ("surface", toJson course.surface.label),
      ("regime", toJson course.regime.label)]).compress
  for surface in surfaces do
    IO.println (Json.mkObj [
      ("law_id", toJson endingLawId), ("kind", toJson "surface"),
      ("surface", toJson surface.label),
      ("courses", toJson ((coursesForSurface surface).map Course.label))]).compress
  for operator in innaOperators do
    for form in innaForms do
      for ma in maStatuses do
        IO.println (Json.mkObj [
          ("law_id", toJson innaLawId), ("kind", toJson "inna"),
          ("operator", toJson operator.label), ("form", toJson form.label),
          ("ma", toJson ma.label),
          ("options", toJson ((innaOptions operator form ma).map InnaEffect.label))]).compress
  IO.println (Json.mkObj [
    ("law_id", toJson awamilPartitionLawId), ("kind", toJson "awamil_partition"),
    ("samai", toJson jurjaniPartition.samai), ("qiyasi", toJson jurjaniPartition.qiyasi),
    ("manawi", toJson jurjaniPartition.manawi), ("total", toJson jurjaniPartition.total)]).compress
