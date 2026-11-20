import Lean.Data.Json
import Archive.LexSamai
import Archive.MasdarLazim
import Archive.AjwafFuul
import Archive.Witnesses
import Archive.SamaiImperative

open Lean Ghanem

private def nounClass : LexSamai.RootType → String
  | .naqis => "ناقص" | .mahmuz => "مهموز" | .salim => "سالم"

private def impRoot : Samai.Root → String
  | .akhadha => "ءخذ" | .akala => "ءكل" | .adhina => "ءذن"
  | .ata => "ءتي" | .amara => "ءمر" | .awa => "ءوي"

private def imp (corpus : String) (c : Samai.Case) :=
  Json.arr #[toJson (impRoot c.root), toJson (if c.ctx == .ibtida then "ابتداء" else "وصل"),
    toJson corpus, toJson c.dropped]

def main : IO Unit := do
  IO.println (Json.mkObj [
    ("form_II", toJson (LexSamai.tafRows.map fun (s, t, m) =>
      [s, nounClass t, if m == LexSamai.MasdarII.tafil then "تفعيل" else "تفعلة"])),
    ("qamus", toJson (AjwafFuul.qamus.map fun (r, _, w) => [r,w])),
    ("lazim", Json.arr ((MasdarLazim.rows.map fun (r, lemma, _, shapes) =>
      Json.arr #[toJson r, toJson lemma, toJson shapes]).toArray)),
    ("trans", toJson (Witnesses.trans.map fun (r,v,t,_,w) => [r,v,t,w])),
    ("imperative", Json.arr ((Samai.quranTable.map (imp "QAC") ++ Samai.hadithTable.map (imp "Hadith")).toArray))
  ]).compress
