import A116.Tasrif
import A116.Rubai
import Nabt.NominalPatterns
import Nabt.InflectionEvidence

namespace VerbMorphology
open A116 A116.Wazn A116.Tasrif A116.Hadd

/-- Admission uses the observed cells after reconstruction. An arbitrary score has no premise here. -/
theorem checkedPast (r : Root 3) (hr : NoAlif r) (a : Haraka) (ha : a ∈ harakat3)
    (seen : List Cell) (matchCells : fillC (madi (sifa r) a .fatha) r = seen) :
    strictB seen = true := matchCells ▸ (madi_exhausted r hr a ha).1

theorem checkedImperfect (r : Root 3) (hr : NoAlif r) (b : Bab) (hb : b ∈ babs)
    (v : Haraka) (hv : v ∈ harakat3) (p : Char) (hp : p ∈ prefixes)
    (m : Haraka) (hm : m ∈ moods) (seen : List Cell)
    (h : fillC (mudari (sifa r) b p v m) r = seen) : strictB seen = true :=
  h ▸ (mudari_exhausted r hr b hb v hv p hp m hm).1

theorem checkedImperative (r : Root 3) (hr : NoAlif r) (b : Bab) (hb : b ∈ babs)
    (v : Haraka) (hv : v ∈ harakat3) (seen : List Cell)
    (h : fillC (amr (sifa r) b v) r = seen) : strictB seen = true :=
  h ▸ (amr_exhausted r hr b hb v hv).1

theorem checkedQuad (r : Root 4) (hr : NoAlif r) (b : Rubai.Bina) (hb : b ∈ Rubai.abniya)
    (seen : List Cell) (h : realize b.w r .start .continue b.h = seen) : strictB seen = true :=
  h ▸ (Rubai.rubai_licensed r hr b hb).1

/-- A filled masdar preserves the supplied root. Lexical usage needs an independent witness. -/
theorem checkedNominal (p : Nabt.Derivation.CatalogPattern) (hp : p ∈ Nabt.NominalPatterns.patterns)
    (r : Nabt.Derivation.Root p.arity) (seen : List Char) (h : Nabt.Derivation.fill p.tokens r = seen) :
    Nabt.Derivation.recover p.tokens seen = some r :=
  h ▸ Nabt.NominalPatterns.pattern_recovery p hp r
/-- Deleting the inflectional nun cannot by itself settle the government of the plural. -/
example : Nabt.InflectionEvidence.realize .fKhamsaW .nasb =
    Nabt.InflectionEvidence.realize .fKhamsaW .jazm :=
  Nabt.InflectionEvidence.five_verbs_deletion_keeps_case_ambiguity.1
end VerbMorphology
