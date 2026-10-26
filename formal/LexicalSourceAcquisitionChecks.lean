import Nabt.LexicalSourceAcquisition

/-! Independent literal-record counterexamples for the acquisition contract.
These finite controls are not a source census or a contextual-sense benchmark. -/
open Nabt LexicalSourceAcquisition

namespace LexicalSourceAcquisitionChecks

def eye : String :=
  "(5:45:7:3)\tEayona\tN\tSTEM|POS:N|LEM:Eayon|ROOT:Eyn|F|ACC\r\n"
def knew : String :=
  "(2:60:15:1)\tEalima\tV\tSTEM|POS:V|PERF|LEM:Ealima|ROOT:Elm|3MS\r\n"
def duplicateLemma : String :=
  "(5:45:7:3)\tEayona\tN\tSTEM|POS:N|LEM:Eayon|LEM:Eayon\r\n"
def corpus : Corpus := ⟨"fixture", "declared-fixture-revision", ("header\r\n" ++ eye).toUTF8.data.toList⟩
def interval : Span := ⟨8, 65⟩

set_option maxRecDepth 10000
set_option maxHeartbeats 4000000

theorem lemma_extracted_from_literal_record :
    (parseRecord eye).map Record.lemma = some "Eayon" := by decide +kernel

theorem form_is_not_replaced_by_lemma :
    (parseRecord eye).map Record.form = some "Eayona" := by decide +kernel

theorem duplicate_identical_lemma_rejected : parseRecord duplicateLemma = none := by decide +kernel

theorem empty_lemma_rejected :
    parseRecord "(1:1:1:1)\tEayona\tN\tSTEM|POS:N|LEM:\r\n" = none := by decide +kernel

theorem unrelated_annotation_does_not_supply_lemma :
    parseRecord "(1:1:1:1)\tEayona\tN\tSTEM|POS:N|XLEM:Eayon\r\n" = none := by decide +kernel

theorem disagreeing_pos_rejected :
    parseRecord "(1:1:1:1)\tEayona\tN\tSTEM|POS:V|LEM:Eayon\r\n" = none := by decide +kernel

theorem duplicate_pos_rejected :
    parseRecord "(1:1:1:1)\tEayona\tN\tSTEM|POS:N|POS:N|LEM:Eayon\r\n" = none := by decide +kernel

theorem empty_form_rejected :
    parseRecord "(1:1:1:1)\t\tN\tSTEM|POS:N|LEM:Eayon\r\n" = none := by decide +kernel

theorem unknown_direct_pair_rejected :
    parseRecord "(1:1:1:1)\tEayo~na\tN\tSTEM|POS:N|LEM:Eayon\r\n" = none := by decide +kernel

theorem extra_tab_rejected :
    parseRecord "(1:1:1:1)\tEayona\tN\tSTEM|POS:N|LEM:Eayon\t\r\n" = none := by decide +kernel

theorem lf_only_is_not_silently_trimmed :
    parseRecord "(1:1:1:1)\tEayona\tN\tSTEM|POS:N|LEM:Eayon\n" = none := by decide +kernel

theorem extra_line_not_swallowed :
    parseRecord "(1:1:\n1:1)\tEayona\tN\tSTEM|POS:N|LEM:Eayon\r\n" = none := by decide +kernel

theorem global_row_acquired :
    (acquireRow corpus interval).map (fun row => (row.raw, row.record.lemma)) =
      some (eye, "Eayon") := by decide +kernel

theorem row_interior_offset_rejected : acquireRow corpus ⟨9, 65⟩ = none := by decide +kernel

theorem truncated_row_rejected : acquireRow corpus ⟨8, 64⟩ = none := by decide +kernel

theorem out_of_range_rejected : acquireRow corpus ⟨8, 66⟩ = none := by decide +kernel

theorem repeated_span_rejected : acquireRows corpus [interval, interval] = none := by decide +kernel

theorem bad_second_row_rejects_whole_batch :
    acquireRows corpus [interval, ⟨9, 65⟩] = none := by decide +kernel

def threeEyes : Corpus :=
  ⟨"fixture-three-rows", "declared-revision", (eye ++
    "(34:12:9:1)\tEayona\tN\tSTEM|POS:N|LEM:Eayon|ROOT:Eyn|F|ACC\r\n" ++
    "(102:7:3:1)\tEayona\tN\tSTEM|POS:N|LEM:Eayon|ROOT:Eyn|F|ACC\r\n").toUTF8.data.toList⟩

theorem three_homographic_occurrences_are_preserved :
    (acquireRows threeEyes [⟨0,57⟩, ⟨57,115⟩, ⟨115,173⟩]).map
      (fun rows => rows.map (fun row => row.record.location)) =
      some ["(5:45:7:3)", "(34:12:9:1)", "(102:7:3:1)"] := by decide +kernel

end LexicalSourceAcquisitionChecks
