import A116.QismAwamil
import A116.Hudud

/-!
# الترخيصُ الجبريُّ التدريجيّ للقسم، والوحدةُ بقيمتها (ADR ١٠٨)

أمرُ المالك: «يجب الترخيص الجبري التدريجي lean وبنا الوحدات بقيمة مثل slge».

**١. الدرجات.**
* القارئُ في الدرجة d علاماتُ الدرجات 0…d مجموعة (`daraja`).
* **قانونُ التدرّج:** مرشَّحو الدرجة ‎d+1‎ داخلَ مرشَّحي d (`daraja_tasfiya`). والمعيَّنُ في d يبقى بقسمه في ‎d+1‎ أو يصير
  «لا حكم» (`daraja_muayyan`). فلا درجةَ تنقض ما قبلها.
* **ولكلّ درجةٍ ضمانُ خطئها** بمجموع أخطاء علاماتها (`QismKhanat.khata_qari_le`).

**٢. تدقيقُ العلامة.**
* علامةٌ أدقّ من أخرى تُطلق حيث تُطلق الأخرى أو أقلّ، بالقيد نفسه.
* فخطؤها لا يزيد (`adaq_khata`).
* و**إبدالُها** بها لا يُنقص مرشَّحًا (`ibdal_cands`). ولا تقول هذه المبرهنةُ شيئًا عن خطأ القارئ.

**٣. تدقيقُ المفتاح.**
* كلُّ دالّةٍ في مفتاحٍ أخشن تتحقّق في المفتاح الأدقّ بإصابتها نفسها (`hits_comp`).
* فما يُقرأ بالذرّات يُقرأ بعدد الشهادة ولا ينقص.
* والشاهد «عَلَى/عَلَا» (`ala_alaa_rabh`): دالّةٌ في عدد الشهادة تصيب ما لا تصيبه دالّةٌ في الخانات.

**٤. الوحدةُ بقيمتها.** المعيَّنُ وحدةٌ `Hudud.Wahda`: جنسُها قسمُها وخاناتُها خاناتُ الكلمة، وعددُها
‎`Hudud.n` = 11·F + n(الجنس)‎. والقراءةُ تُخرج وحداتٍ أعدادُها متباينة (`wahdat_nodup`)، وتُحلّ الواحدةُ منها بعينها
(`wahda_radd`).
-/

namespace A116.QismDaraja

open A116 A116.QismKhanat

variable {α : Type}

/-! ## ١. الدرجات -/

def daraja (ds : List (List (Alama α))) (d : Nat) : List (Alama α) := (ds.take (d + 1)).flatten

theorem daraja_succ (ds : List (List (Alama α))) (d : Nat) :
    ∃ bs, daraja ds (d + 1) = daraja ds d ++ bs := by
  refine ⟨(ds.drop (d + 1)).take 1 |>.flatten, ?_⟩
  unfold daraja
  rw [show d + 1 + 1 = (d + 1) + 1 from rfl, List.take_add, List.flatten_append]

/-- **قانونُ التدرّج**: الدرجةُ التالية تقطع ولا تزيد. -/
theorem daraja_tasfiya (ds : List (List (Alama α))) (d : Nat) (x : α) (q : Qism)
    (h : q ∈ cands (daraja ds (d + 1)) x) : q ∈ cands (daraja ds d) x := by
  obtain ⟨bs, hb⟩ := daraja_succ ds d
  rw [hb] at h
  exact QismAwamil.cands_append_sub _ _ x q h

/-- **ولا تنقض**: المعيَّنُ يبقى بقسمه أو يصير «لا حكم». -/
theorem daraja_muayyan (ds : List (List (Alama α))) (d : Nat) (x : α) (q : Qism)
    (h : qiraa (daraja ds d) x = .muayyan q) :
    qiraa (daraja ds (d + 1)) x = .muayyan q ∨ qiraa (daraja ds (d + 1)) x = .laHukm := by
  obtain ⟨bs, hb⟩ := daraja_succ ds d
  rw [hb]
  exact QismAwamil.muayyan_baqi _ _ x q h

/-- وعلى درجاتٍ بعيدة: كلُّ درجةٍ بعد d تقطع ما قطعته d. -/
theorem daraja_tasfiya_k (ds : List (List (Alama α))) (d k : Nat) (x : α) (q : Qism)
    (h : q ∈ cands (daraja ds (d + k)) x) : q ∈ cands (daraja ds d) x := by
  induction k with
  | zero => simpa using h
  | succ k ih => exact ih (daraja_tasfiya ds (d + k) x q (by simpa [Nat.add_assoc] using h))

/-! ## ٢. تدقيقُ العلامة -/

/-- `b` أدقُّ من `a`: تُطلق حيث تُطلق `a` أو أقلّ، بالقيد نفسه. -/
def Adaq (b a : Alama α) : Prop := (∀ x, b.tutabiq x = true → a.tutabiq x = true) ∧ b.tubqi = a.tubqi

theorem adaq_khata (b a : Alama α) (h : Adaq b a) (p : α × Qism) (hk : khata b p = true) :
    khata a p = true := by
  simp only [khata, Bool.and_eq_true] at *
  exact ⟨h.1 _ hk.1, by rw [← h.2]; exact hk.2⟩

/-- **خطأُ الأدقّ لا يزيد** على أيّ مرجع. -/
theorem adaq_khata_count (b a : Alama α) (h : Adaq b a) (R : List (α × Qism)) :
    R.countP (khata b) ≤ R.countP (khata a) :=
  countP_mono R _ _ fun p _ hp => adaq_khata b a h p hp

/-- **الإبدالُ بالأدقّ لا يُنقص مرشَّحًا**: ما بقي مع `a` يبقى مع `b`. -/
theorem ibdal_cands (as bs : List (Alama α)) (b a : Alama α) (h : Adaq b a) (x : α) (q : Qism)
    (hq : q ∈ cands (as ++ a :: bs) x) : q ∈ cands (as ++ b :: bs) x := by
  rw [mem_cands] at *
  intro c hc ht
  simp only [List.mem_append, List.mem_cons] at hc
  rcases hc with hc | rfl | hc
  · exact hq c (by simp [hc]) ht
  · rw [h.2]; exact hq a (by simp) (h.1 x ht)
  · exact hq c (by simp [hc]) ht

/-! ## ٣. تدقيقُ المفتاح -/

def hitsR {κ : Type} (g : κ → Qism) (R : List (κ × Qism)) : Nat := R.countP (fun p => g p.1 == p.2)

/-- **كلُّ دالّةٍ في المفتاح الأخشن تتحقّق في الأدقّ بإصابتها**: `g ∘ f` على المفتاح الأدقّ. -/
theorem hits_comp {κ κ' : Type} (f : κ' → κ) (g : κ → Qism) (R : List (κ' × Qism)) :
    hitsR (g ∘ f) R = hitsR g (R.map fun p => (f p.1, p.2)) := by
  unfold hitsR
  rw [List.countP_map]
  rfl

theorem tadqiq_la_yanqus {κ κ' : Type} (f : κ' → κ) (R : List (κ' × Qism)) (g : κ → Qism) :
    ∃ g' : κ' → Qism, hitsR g' R = hitsR g (R.map fun p => (f p.1, p.2)) :=
  ⟨g ∘ f, hits_comp f g R⟩

/-- **شاهدُ الرِّبح**: «عَلَى» حرفٌ و«عَلَا» فعل، خاناتُهما واحدة ورتبتاهما 1 و0. لا دالّةَ في الخانات تصيبهما معًا، ودالّةٌ في
(الخانات، الرتبة) تصيبهما. -/
def alaRows : List ((List Cell × Nat) × Qism) := [((cell "عَلَاْ", 1), .harf), ((cell "عَلَاْ", 0), .fil)]

def ofRank : List Cell × Nat → Qism := fun p => if p.2 == 1 then .harf else .fil

theorem ala_alaa_rabh :
    hitsR ofRank alaRows = 2 ∧
    ∀ g : List Cell → Qism, hitsR g (alaRows.map fun p => (p.1.1, p.2)) ≤ 1 := by
  refine ⟨by decide +kernel, fun g => ?_⟩
  simp only [hitsR, alaRows, List.map, List.countP_cons, List.countP_nil]
  cases h : g (cell "عَلَاْ") <;> simp

/-! ## ٤. الوحدةُ بقيمتها -/

def jinsOf : Qism → Hudud.Jins
  | .ism => .ism
  | .fil => .fil
  | .harf => .harf

theorem jinsOf_inj : ∀ {q r : Qism}, jinsOf q = jinsOf r → q = r := by
  intro q r h; cases q <;> cases r <;> first | rfl | cases h

def wahda (q : Qism) (c : List Cell) : Hudud.Wahda := ⟨jinsOf q, c⟩

/-- وحداتُ القراءة: لكلّ مرشَّحٍ وحدة. -/
def wahdat (as : List (Alama α)) (x : α) (c : List Cell) : List Hudud.Wahda :=
  (cands as x).map (wahda · c)

/-- **عددُ الوحدة يُحلّ إليها بعينها**: قسمُها وخاناتُها. -/
theorem wahda_radd (q r : Qism) (c d : List Cell) (h : Hudud.n (wahda q c) = Hudud.n (wahda r d)) :
    q = r ∧ c = d := by
  have := Hudud.n_inj h
  simp only [wahda, Hudud.Wahda.mk.injEq] at this
  exact ⟨jinsOf_inj this.1, this.2⟩

/-- **أعدادُ وحدات القراءة متباينة**. -/
theorem wahdat_nodup (as : List (Alama α)) (x : α) (c : List Cell) :
    ((wahdat as x c).map Hudud.n).Nodup := by
  unfold wahdat
  rw [List.map_map]
  exact List.Pairwise.map _ (fun q r hqr heq => hqr (wahda_radd q r c c heq).1)
    (QismAwamil.cands_nodup as x)

/-- **المعيَّنُ وحدةٌ واحدة**. -/
theorem muayyan_wahda (as : List (Alama α)) (x : α) (c : List Cell) (q : Qism)
    (h : qiraa as x = .muayyan q) : wahdat as x c = [wahda q c] := by
  unfold qiraa at h
  unfold wahdat
  generalize cands as x = l at h
  match l, h with
  | [m], h => simp only [Iqtiran.mantuq, Iqtiran.Mantuq.muayyan.injEq] at h; simp [h]
  | [], h => simp [Iqtiran.mantuq] at h
  | _ :: _ :: _, h => simp [Iqtiran.mantuq] at h

/-! ## شاهد: درجتان على «يَكُنْ» بعد «لَمْ» -/

def dShahid : List (List (Alama (List Cell × Option (List Cell)))) := [[harfLafz], [badLam]]

theorem shahid_darajat :
    qiraa (daraja dShahid 0) (cell "يَكُنْ", some (cell "لَمْ")) = .muhtamal [.ism, .fil, .harf] ∧
    qiraa (daraja dShahid 1) (cell "يَكُنْ", some (cell "لَمْ")) = .muayyan .fil ∧
    wahdat (daraja dShahid 1) (cell "يَكُنْ", some (cell "لَمْ")) (cell "يَكُنْ") =
      [wahda .fil (cell "يَكُنْ")] := by
  decide +kernel

end A116.QismDaraja
