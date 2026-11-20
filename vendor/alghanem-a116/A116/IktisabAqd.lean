import A116.IktisabData

/-!
# عقودُ ما اكتسبه المتعلّم (ADR ١٢٣)

البرامجُ في `A116.IktisabData` يولّدها `tools/gen_iktisab.py` من حلقة الأمثلة المضادّة؛ وهنا تُقاس على
مواصفات `Iktisab` (المأخوذة من `TawrithBit`) **لكلّ عرض** عبر `min_jadwal`. فإن خالف المكتسَبُ مواصفتَه سقط
البناء؛ وإن تغيّر وبقي صحيحًا فذلك انجرافٌ يكشفه `gen_iktisab.py --check` لا هذا الملفّ.

* `naqis_aqd`: الإجراءُ المكتسَب أوّلًا يحسب ‎R \ P‎ في كلّ موضعٍ لكلّ عرض.
* `naqisB`: عقدُه على البتّات، وهو كلُّ ما يُحتاج منه بعد ذلك.
* `batt_qima_bil_min_naqis`: **التراكم في البرهان** — البرنامجُ المركّب بنداء `naqis` يُبرهن من `naqisB`
  و`subst_eval` دون فتح جسم `naqis`؛ ويساوي قيمةَ `fastQ` لكلّ بتّات (بلا شرط صلاح).
* `batt_qima_bila_aqd`: ما وجده المتعلّم بلا مكتبة يصحّ **على الصالح وحده**، وخارجه يخالف `fastQ`
  (`bila_kharij_salih`).
-/

set_option autoImplicit false

namespace A116.IktisabAqd

open A116.Iktisab A116.IktisabData A116.TawrithBit

theorem naqis_jadwal : jadwal 2 (fun _ => true) specNaqis naqis = true := by decide

/-- **عقدُ `naqis` لكلّ عرض:** البتُّ j من الناتج = البتُّ j من R وليس البتُّ j من P. -/
theorem naqis_aqd (r p j : Nat) :
    (evalN [r, p] naqis).testBit j = (r.testBit j && !p.testBit j) := by
  have := min_jadwal naqis_jadwal [r, p] rfl j rfl
  simpa [specNaqis, bitAt] using this

/-- عقدُ `naqis` على البتّات. -/
theorem naqisB (a b : Bool) : evalB [a, b] naqis = (a && !b) := by
  cases a <;> cases b <;> decide

/-- **التراكم في البرهان:** النداءُ يُحسب من عقد المكتسَب وحده. -/
theorem batt_qima_bil_min_naqis (env : List Bool) :
    evalB env batt_qima_bil_maktaba =
      (env.getD 1 false || (env.getD 3 false && !env.getD 0 false)) := by
  simp only [batt_qima_bil_maktaba, evalB, subst_eval, List.map, naqisB]

/-- وهو قيمةُ `fastQ` بعينها لكلّ بتّات. -/
theorem batt_qima_bil_fastQ (k₁ v₁ k₂ v₂ : Bool) :
    evalB [k₁, v₁, k₂, v₂] batt_qima_bil_maktaba = (fastQ (k₁, v₁) (k₂, v₂)).2 := by
  rw [batt_qima_bil_min_naqis]
  cases k₁ <;> cases v₁ <;> cases k₂ <;> cases v₂ <;> rfl

theorem batt_qima_bil_jadwal : jadwal 4 salihPairs specBattQima batt_qima_bil_maktaba = true := by
  decide

theorem batt_qima_bila_jadwal : jadwal 4 salihPairs specBattQima batt_qima_bila_maktaba = true := by
  decide

/-- **عقدُ البتّ لكلّ عرض، بالمكتبة:** على كلّ موضعٍ صالح. -/
theorem batt_qima_bil_aqd (k₁ v₁ k₂ v₂ j : Nat)
    (hv : salihPairs (bitAt [k₁, v₁, k₂, v₂] j) = true) :
    (evalN [k₁, v₁, k₂, v₂] batt_qima_bil_maktaba).testBit j =
      specBattQima (bitAt [k₁, v₁, k₂, v₂] j) :=
  min_jadwal batt_qima_bil_jadwal _ rfl j hv

/-- **وبلا المكتبة:** البرنامجُ الآخر يستوفي العقدَ نفسَه على الصالح. -/
theorem batt_qima_bila_aqd (k₁ v₁ k₂ v₂ j : Nat)
    (hv : salihPairs (bitAt [k₁, v₁, k₂, v₂] j) = true) :
    (evalN [k₁, v₁, k₂, v₂] batt_qima_bila_maktaba).testBit j =
      specBattQima (bitAt [k₁, v₁, k₂, v₂] j) :=
  min_jadwal batt_qima_bila_jadwal _ rfl j hv

/-- **وخارج الصالح يفترقان:** على زوجٍ ثانٍ غير صالح (غيرُ معلومٍ وقيمتُه صادقة) يخالف `fastQ`. -/
theorem bila_kharij_salih :
    evalB [false, false, false, true] batt_qima_bila_maktaba ≠
      (fastQ (false, false) (false, true)).2 := by
  decide

theorem batt_maalum_jadwal :
    jadwal 4 salihPairs specBattMaalum batt_maalum_bila_maktaba = true ∧
      jadwal 4 salihPairs specBattMaalum batt_maalum_bil_maktaba = true := by
  decide

theorem taarud_jadwal :
    jadwal 4 salihPairs specTaarud taarud_bila_maktaba = true ∧
      jadwal 4 salihPairs specTaarud taarud_bil_maktaba = true := by
  decide

/-- **عقدُ التعارض لكلّ عرض:** قناعُ `conflictQ` في كلّ موضعٍ صالح. -/
theorem taarud_aqd (k₁ v₁ k₂ v₂ j : Nat)
    (hv : salihPairs (bitAt [k₁, v₁, k₂, v₂] j) = true) :
    (evalN [k₁, v₁, k₂, v₂] taarud_bila_maktaba).testBit j =
      specTaarud (bitAt [k₁, v₁, k₂, v₂] j) :=
  min_jadwal taarud_jadwal.1 _ rfl j hv

/-- **عقدُ التعارض لكلّ عرض، بالمكتبة.** -/
theorem taarud_bil_aqd (k₁ v₁ k₂ v₂ j : Nat)
    (hv : salihPairs (bitAt [k₁, v₁, k₂, v₂] j) = true) :
    (evalN [k₁, v₁, k₂, v₂] taarud_bil_maktaba).testBit j =
      specTaarud (bitAt [k₁, v₁, k₂, v₂] j) :=
  min_jadwal taarud_jadwal.2 _ rfl j hv

/-- **عقدُ معلوم البتّ لكلّ عرض، بلا المكتبة وبها.** -/
theorem batt_maalum_aqd (k₁ v₁ k₂ v₂ j : Nat)
    (hv : salihPairs (bitAt [k₁, v₁, k₂, v₂] j) = true) :
    (evalN [k₁, v₁, k₂, v₂] batt_maalum_bila_maktaba).testBit j =
        specBattMaalum (bitAt [k₁, v₁, k₂, v₂] j) ∧
      (evalN [k₁, v₁, k₂, v₂] batt_maalum_bil_maktaba).testBit j =
        specBattMaalum (bitAt [k₁, v₁, k₂, v₂] j) :=
  ⟨min_jadwal batt_maalum_jadwal.1 _ rfl j hv, min_jadwal batt_maalum_jadwal.2 _ rfl j hv⟩

end A116.IktisabAqd
