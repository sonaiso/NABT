import A116.MalumatData
import A116.Istiqama

/-!
# الصدقُ يقرأ المعلوماتِ السابقة (ADR ٨٨، أمرُ المالك 2026-10-17)

طبقةُ الحكم فوق الاستقامة (المادّة ١٠). موضوعُها النسبة: موضوعٌ ومحمولٌ وإيجاب (المادّة ١٣). ومصدرُها مودَعُ
«المعلومات السابقة» (`MalumatData.rows`، ADR ٨٧). حكمُها ثلاثيّ:
* **صادقٌ** بشاهد: صفٌّ في المودَع موضوعُه ومحمولُه كالنسبة وإيجابُه كإيجابها.
* **كاذبٌ** بشاهد: الصفُّ نفسُه بإيجابٍ مخالف.
* **لا حكم**: لا صفَّ في المودَع. والغيابُ لا يُعدّ كذبًا، فلا عالَمَ مغلقًا (المادّة ١٦).

ولا يُحكم بصفٍّ لا مرتبةَ له: فالتمييزُ الغريزيُّ «ليس فكرًا ولا إدراكًا» («التفكير» س18)، فلا يكون شاهدًا.
ومرتبةُ الحكم مرتبةُ شاهده: الوجودُ قطعيّ، وما سواه ظنّيّ («التفكير» س28).
-/

namespace A116.Sidq

open A116.Malumat

/-- النسبةُ المحكومُ عليها. -/
structure Nisba where
  mawdu : String
  mahmul : String
  ijab : Bool
  deriving DecidableEq, Repr

/-- الحكمُ ثلاثيّ، والصادقُ والكاذبُ يحملان شاهدهما. -/
inductive Hukm
  | sadiq (shahid : Saff)
  | kadhib (shahid : Saff)
  | laHukm
  deriving DecidableEq, Repr

/-- الشاهدُ صفٌّ ذو مرتبة، موضوعُه ومحمولُه كالنسبة. -/
def yashhad (n : Nisba) (r : Saff) : Bool :=
  r.mawdu == n.mawdu && r.mahmul == n.mahmul && r.martaba.isSome

def shahidOf (n : Nisba) : Option Saff := rows.find? (yashhad n)

def hukm (n : Nisba) : Hukm :=
  match shahidOf n with
  | some r => if r.ijab == n.ijab then .sadiq r else .kadhib r
  | none => .laHukm

/-- لا صادقَ ولا كاذبَ بلا شاهدٍ ذي مرتبةٍ من المودَع. -/
theorem la_hukm_bila_shahid (n : Nisba) (r : Saff)
    (h : hukm n = .sadiq r ∨ hukm n = .kadhib r) :
    r ∈ rows ∧ r.martaba.isSome = true ∧ r.mawdu = n.mawdu ∧ r.mahmul = n.mahmul := by
  unfold hukm at h
  split at h
  · rename_i s hs
    have hr : s = r := by
      split at h <;> rcases h with h | h <;> cases h <;> rfl
    subst hr
    have hm := List.mem_of_find?_eq_some hs
    have hy := List.find?_some hs
    simp [yashhad] at hy
    exact ⟨hm, hy.2, hy.1.1, hy.1.2⟩
  · rcases h with h | h <;> cases h

/-- الغيابُ ليس كذبًا: ما لا شاهدَ له «لا حكم». -/
theorem ghiyab_laysa_kadhib (n : Nisba) (h : shahidOf n = none) : hukm n = .laHukm := by
  simp [hukm, h]

/-- الإيجابُ والسلبُ على شاهدٍ واحد متقابلان. -/
theorem taqabul (n : Nisba) (r : Saff) (h : hukm n = .sadiq r) :
    hukm { n with ijab := !n.ijab } = .kadhib r := by
  unfold hukm at h ⊢
  have e : shahidOf { n with ijab := !n.ijab } = shahidOf n := rfl
  rw [e]
  split at h
  · rename_i s _
    split at h
    · rename_i hij
      cases h
      simp at hij
      simp [hij]
    · cases h
  · cases h

/-! ## على المودَع -/

/-- «الجبلُ يُحمل» لا حكمَ له: المودَعُ لا صفَّ فيه. فكذبُه عند سيبويه نقلٌ، لا محسوبٌ هنا (`MALUMAT_SPARSE`). -/
theorem jabal_la_hukm : hukm ⟨"الجبل", "يُحمل", true⟩ = .laHukm := by decide

/-- التمييزُ الغريزيُّ لا يكون شاهدًا: «التفاحةُ تؤكل» لا حكمَ لها مع أنّها في المودَع. -/
theorem tamyiz_la_yuhkam :
    rows.any (fun r => r.mawdu == "التفاحة") = true ∧
    hukm ⟨"التفاحة", "تؤكل", true⟩ = .laHukm := by decide

/-- شواهدُ الصدق والكذب من «التفكير». -/
theorem shawahid_sidq :
    (match hukm ⟨"المرآة", "الانعكاس", true⟩ with | .sadiq _ => true | _ => false) = true ∧
    (match hukm ⟨"الدماغ", "الانعكاس", true⟩ with | .kadhib _ => true | _ => false) = true ∧
    (match hukm ⟨"دماغ الإنسان", "ربط المعلومات", true⟩ with | .sadiq _ => true | _ => false) = true ∧
    (match hukm ⟨"دماغ الحيوان", "ربط المعلومات", true⟩ with | .kadhib _ => true | _ => false) = true ∧
    (match hukm ⟨"الشمس", "الضوء", true⟩ with | .sadiq _ => true | _ => false) = true := by
  decide

/-- مرتبةُ الحكم مرتبةُ شاهده: وجودُ الواقع قطعيّ، والانعكاسُ في المرآة ظنّيّ. -/
theorem martaba_shahid :
    (match hukm ⟨"الواقع", "موجود", true⟩ with | .sadiq r => r.martaba | _ => none) = some .qati ∧
    (match hukm ⟨"المرآة", "الانعكاس", true⟩ with | .sadiq r => r.martaba | _ => none) = some .zanni := by
  decide

/-! ## الصدقُ فوق الاستقامة -/

def kadhibB : Hukm → Bool
  | .kadhib _ => true
  | _ => false

/-- القسمُ بالحكم: الاستقامةُ من اللفظ والكذبُ من المودَع. -/
def sinfBiSidq (k : List Istiqama.Juz) (n : Nisba) : Istiqama.Sinf :=
  Istiqama.sinf k (kadhibB (hukm n))

/-- الحكمُ لا يُسقط الاستقامة: الإحالةُ هي إحالةُ اللفظ أيًّا كان الحكم. -/
theorem hukm_la_yusqit (k : List Istiqama.Juz) (n : Nisba) :
    (sinfBiSidq k n = .muhal ∨ sinfBiSidq k n = .muhalKadhib) ↔ Istiqama.muhalB k = true :=
  Istiqama.kadhib_la_yughayyir k _

/-- وما لا حكمَ عليه لا يصير كذبًا: شاهدُ الكذب عند سيبويه مستقيمٌ حسنٌ بلا شاهدٍ مودَع. -/
theorem jabal_mustaqim :
    sinfBiSidq (Istiqama.juz Istiqama.kadhib) ⟨"الجبل", "يُحمل", true⟩ = .mustaqimHasan := by decide

end A116.Sidq
