/-
  Madlul/NTP/Silsila.lean — التواترُ بشجرة النقل: لا يُعدّ شاهدان مستقلَّين إلّا إذا لم يلتقيا في سلسلتيهما.

  الطلب (قولُ المالك 2026-11-17، 00:15 بتوقيت عمّان): «هل يُعدّ التواتر بشجرة النقل؟ وإن وافقت، فأوّل عمل هو جدول مصادر المعاجم
  بسلاسلها … موافق انت مفوض ومعك اذن بالدمج والدفع». والتصميمُ قرارُ البنّاء.

  الفجوةُ: `NTP.adad` (`Madlul/NTP/Muallij.lean`) يعدّ أرقامَ المصادر المتمايزة في السجلّ، فكتابان ينقل أحدُهما عن الآخر، أو ينقلان عن أصلٍ واحد،
  يُعدّان شاهدين. وهنا شجرةُ نقلٍ `Shajara`: لكلّ كتابٍ مصادرُه كما سمّاها صاحبُه في خطبته (`some l`)، أو «لم تُقرأ» (`none`).

  الحكمُ على الاستقلال ثلاثيّ (`istiqlal`):
  * **غيرُ مستقلّ** إن التقت سلسلتاهما في كتاب (ومنه الكتابُ نفسُه: `nafsuhu_ghayr`، `mushtarak_ghayr`).
  * **لا حكم** إن لم تلتقيا في المقروء وفي إحداهما كتابٌ لم تُقرأ مصادرُه، أو نفد الوقود: الغيابُ ليس استقلالًا (`maftuh_la_yustaqill`).
  * **مستقلّ** إن أُغلقت السلسلتان كلتاهما بالقراءة ولم تلتقيا (`mustaqill_iff`).

  العدّ `adadS`: أكبرُ عددٍ من الشهود كلُّ اثنين منهم مستقلّان بالحكم الثالث (`akbar`، بحثٌ تامّ بوقودٍ هو طولُ القائمة). مبرهنٌ لكلّ شجرة:
  أنّه منها (`akbar_minha`)، وأنّ كلَّ اثنين فيه مستقلّان (`akbar_mustaqill`)، وأنّ شهودًا يلتقون كلُّهم في كتابٍ واحد لا يزيدون على واحد
  (`jidd_wahid`)، وأنّه لا يزيد على عدّ السجلّ `NTP.adad` (`adadS_le_adad`): فالقبولُ بالشجرة أضيقُ من القبول بالسجلّ (`yuqbalS_yuqbal`).

  حدود: شجرةُ الكتب لا الرواة. وكتابٌ ليس له مصادرُ مقروءة يُغلق بـ`some []` حين يقرّر قارئُه أنّه سماعٌ لا نقل، وهذا قرارٌ في الجدول لا هنا.
  بلا sorry ولا axiom ولا native_decide.
-/
import Madlul.NTP.Muallij

set_option autoImplicit false

namespace NTP
namespace Silsila

/-- شجرةُ النقل: مصادرُ كلّ كتابٍ كما سمّاها صاحبُه، أو `none` إن لم تُقرأ. -/
abbrev Shajara := Nat → Option (List Nat)

/-- أسلافُ الكتاب (وأوّلُهم هو) بوقودٍ يحدّ العمق. -/
def aslaf (m : Shajara) : Nat → Nat → List Nat
  | 0, n => [n]
  | k + 1, n => n :: (match m n with
      | some l => l.flatMap (aslaf m k)
      | none => [])

/-- في السلسلة كتابٌ لم تُقرأ مصادرُه، أو نفد الوقود. -/
def maftuh (m : Shajara) : Nat → Nat → Bool
  | 0, _ => true
  | k + 1, n => match m n with
      | some l => l.any (maftuh m k)
      | none => true

inductive Istiqlal | mustaqill | ghayr | laHukm
deriving DecidableEq, Repr

def iltaqaya (m : Shajara) (k a b : Nat) : Bool := (aslaf m k a).any (fun x => (aslaf m k b).contains x)

def istiqlal (m : Shajara) (k a b : Nat) : Istiqlal :=
  if iltaqaya m k a b then .ghayr
  else if maftuh m k a || maftuh m k b then .laHukm
  else .mustaqill

theorem nafsuhu_aslaf (m : Shajara) (k n : Nat) : n ∈ aslaf m k n := by
  cases k <;> simp [aslaf]

theorem mushtarak_iltaqaya (m : Shajara) (k a b c : Nat) (ha : c ∈ aslaf m k a) (hb : c ∈ aslaf m k b) :
    iltaqaya m k a b = true := by
  unfold iltaqaya
  rw [List.any_eq_true]
  exact ⟨c, ha, by simpa using hb⟩

/-- **ما التقت سلسلتاهما في كتابٍ غيرُ مستقلّين.** -/
theorem mushtarak_ghayr (m : Shajara) (k a b c : Nat) (ha : c ∈ aslaf m k a) (hb : c ∈ aslaf m k b) :
    istiqlal m k a b = .ghayr := by
  simp [istiqlal, mushtarak_iltaqaya m k a b c ha hb]

/-- **الكتابُ ليس مستقلًّا عن نفسه:** فشاهدان من كتابٍ واحد شاهدٌ واحد. -/
theorem nafsuhu_ghayr (m : Shajara) (k a : Nat) : istiqlal m k a a = .ghayr :=
  mushtarak_ghayr m k a a a (nafsuhu_aslaf m k a) (nafsuhu_aslaf m k a)

/-- **الغيابُ ليس استقلالًا:** ما في سلسلته كتابٌ لم تُقرأ مصادرُه لا يُحكم باستقلاله. -/
theorem maftuh_la_yustaqill (m : Shajara) (k a b : Nat) (h : maftuh m k a = true ∨ maftuh m k b = true) :
    istiqlal m k a b ≠ .mustaqill := by
  unfold istiqlal
  split
  · simp
  · rcases h with h | h <;> simp [h]

/-- **المستقلّان:** سلسلتان مغلقتان بالقراءة لا تلتقيان. -/
theorem mustaqill_iff (m : Shajara) (k a b : Nat) :
    istiqlal m k a b = .mustaqill ↔
      iltaqaya m k a b = false ∧ maftuh m k a = false ∧ maftuh m k b = false := by
  unfold istiqlal
  cases h1 : iltaqaya m k a b <;> cases h2 : maftuh m k a <;> cases h3 : maftuh m k b <;> simp

/-! ## العدّ: أكبرُ جماعةٍ مستقلّةٍ مثنى مثنى -/

def akbar (m : Shajara) (k : Nat) : Nat → List Nat → List Nat
  | 0, _ => []
  | _ + 1, [] => []
  | f + 1, x :: xs =>
    let a := akbar m k f xs
    let b := x :: akbar m k f (xs.filter (fun y => istiqlal m k x y == .mustaqill))
    if a.length ≤ b.length then b else a

def adadS (m : Shajara) (k : Nat) (ws : List Nat) : Nat := (akbar m k ws.length ws).length

/-- ما في الجماعة من الشهود. -/
theorem akbar_minha (m : Shajara) (k : Nat) : ∀ (f : Nat) (l : List Nat), ∀ y ∈ akbar m k f l, y ∈ l
  | 0, _, y, h => by simp [akbar] at h
  | _ + 1, [], y, h => by simp [akbar] at h
  | f + 1, x :: xs, y, h => by
    simp only [akbar] at h
    split at h
    · rcases List.mem_cons.1 h with e | e
      · exact e ▸ List.mem_cons_self
      · exact List.mem_cons_of_mem _ (List.mem_filter.1 (akbar_minha m k f _ y e)).1
    · exact List.mem_cons_of_mem _ (akbar_minha m k f xs y h)

/-- **كلُّ اثنين في الجماعة مستقلّان** (بترتيبهما في القائمة). -/
theorem akbar_mustaqill (m : Shajara) (k : Nat) :
    ∀ (f : Nat) (l : List Nat), (akbar m k f l).Pairwise (fun a b => istiqlal m k a b = .mustaqill)
  | 0, _ => by simp [akbar]
  | _ + 1, [] => by simp [akbar]
  | f + 1, x :: xs => by
    simp only [akbar]
    split
    · refine List.pairwise_cons.2 ⟨fun y hy => ?_, akbar_mustaqill m k f _⟩
      have := akbar_minha m k f _ y hy
      simpa using (List.mem_filter.1 this).2
    · exact akbar_mustaqill m k f xs

/-- الجماعةُ بلا تكرار (الكتابُ غيرُ مستقلٍّ عن نفسه). -/
theorem akbar_nodup (m : Shajara) (k f : Nat) (l : List Nat) : (akbar m k f l).Nodup := by
  have hp := akbar_mustaqill m k f l
  unfold List.Nodup
  refine List.Pairwise.imp (fun {a b} h e => ?_) hp
  subst e
  rw [nafsuhu_ghayr] at h
  cases h

/-- **شهودٌ يلتقون كلُّهم في كتابٍ واحد لا يزيدون على واحد.** -/
theorem jidd_wahid (m : Shajara) (k c : Nat) (ws : List Nat) (h : ∀ w ∈ ws, c ∈ aslaf m k w) :
    adadS m k ws ≤ 1 := by
  unfold adadS
  have hp := akbar_mustaqill m k ws.length ws
  have hs := akbar_minha m k ws.length ws
  generalize akbar m k ws.length ws = r at hp hs
  match r, hp, hs with
  | [], _, _ => simp
  | [_], _, _ => simp
  | x :: y :: _, hp, hs =>
    have hxy := (List.pairwise_cons.1 hp).1 y (by simp)
    rw [mushtarak_ghayr m k x y c (h x (hs x (by simp))) (h y (hs y (by simp)))] at hxy
    cases hxy

theorem mem_mutamayyiz : ∀ (l : List Nat) (x : Nat), x ∈ mutamayyiz l ↔ x ∈ l
  | [], _ => by simp [mutamayyiz]
  | y :: ys, x => by
    have ih := mem_mutamayyiz ys x
    unfold mutamayyiz
    split
    · rename_i hy
      rw [ih]; constructor
      · exact List.mem_cons_of_mem _
      · intro hx; rcases List.mem_cons.1 hx with e | e
        · exact e ▸ (mem_mutamayyiz ys y).1 hy
        · exact e
    · simp [ih]

/-- **العدُّ بالشجرة لا يزيد على العدّ بالسجلّ** (`NTP.adad`). -/
theorem adadS_le_adad (m : Shajara) (k : Nat) (sh : List Shahid) :
    adadS m k (sh.map (·.masdar)) ≤ adad sh := by
  unfold adadS adad
  apply List.Nodup.length_le_of_subset (akbar_nodup m k _ _)
  intro y hy
  exact (mem_mutamayyiz _ y).2 (akbar_minha m k _ _ y hy)

/-- القبولُ بالتواتر على الشجرة. -/
def yuqbalS (K : Nat) (m : Shajara) (k : Nat) (sh : List Shahid) : Bool :=
  decide (K ≤ adadS m k (sh.map (·.masdar))) && decide (0 < adadS m k (sh.map (·.masdar)))

/-- **القبولُ بالشجرة أضيقُ:** ما قُبل بها قُبل بالسجلّ. -/
theorem yuqbalS_yuqbal (K : Nat) (m : Shajara) (k : Nat) (sh : List Shahid) (h : yuqbalS K m k sh = true) :
    yuqbal K sh = true := by
  have hle := adadS_le_adad m k sh
  simp only [yuqbalS, yuqbal, Bool.and_eq_true, decide_eq_true_eq] at h ⊢
  omega

/-- **ما التقى شهودُه كلُّهم في كتابٍ لا يُقبل** متى كانت العتبة اثنين فأكثر. -/
theorem jidd_wahid_la_yuqbal (K : Nat) (hK : 2 ≤ K) (m : Shajara) (k c : Nat) (sh : List Shahid)
    (h : ∀ s ∈ sh, c ∈ aslaf m k s.masdar) : yuqbalS K m k sh = false := by
  have := jidd_wahid m k c (sh.map (·.masdar)) (by
    intro w hw
    obtain ⟨s, hs, rfl⟩ := List.mem_map.1 hw
    exact h s hs)
  simp only [yuqbalS]
  have : ¬ K ≤ adadS m k (sh.map (·.masdar)) := by omega
  simp [this]

end Silsila
end NTP
