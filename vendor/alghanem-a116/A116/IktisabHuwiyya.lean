import A116.Jadwal
import A116.Hadd

/-!
# اكتسابُ قوانين الهويّة بالحدّ الأدنى المكتمل — الوجودُ والابتداء (ADR ١٢٤)

**القيمة** هويّةُ الخانة: حاملٌ وحالة في موضعها (`Nizam.Huwiyya`). **والقانون** دالّةٌ عليها. وما يكتسبه المتعلّم
(`tools/gen_iktisab_huwiyya.py`) ليس برنامجًا على بتّات: يكتسب **أصغرَ مجموعة أوصافٍ تعيّن القانون**، وجدولَه عليها.

* **المجال** `dom`: البرجُ حرفًا × حالة (`Jadwal.jadwal` × `Jadwal.harakat`)، 116 خانةً هي الشبكة (`Jadwal.khanat_cells`).
* **الأوصاف** `Wasf`: الحالة، ومخرجُ سيبويه، ومخرجُ الجزريّ، وحيّزُ الخليل، والصفاتُ الأربعَ عشرة — حقولُ `Jadwal.Harf`
  بعينها. ولا وصفَ هو الحرفُ نفسُه.
* **التعيين** `yuayyin`: لا خانتين بأوصافٍ واحدة وقانونٍ مختلف — أي لا **مانع** بلغة `Fasl`. و`yuayyin_iff` يُثبت
  لكلّ قانونٍ ولكلّ أوصاف: التعيينُ ⟺ القانونُ دالّةٌ في المفتاح على المجال.
* **الحدّ الأدنى المكتمل** `adna`: الأوصافُ تعيّن، وحذفُ أيٍّ منها يُسقط التعيين (على نسق `Fasl.mukhtamal`).
* **القوانين الثلاثة على الخانة:**
  * الوجود: `Jadwal.licensableCell`.
  * الابتداء: صنفُ الخانة أوّلًا `cv`، أي `Hadd.kindOne none` و`Nizam.ternary.ibtida`.
  * المبتدأُ به: كلاهما.
  * وربطُها بـ`Nizam` و`TawrithSitta.qawanin_sitta` معلنٌ لا مبرهَن هنا (`NIZAM_LINK_DECLARED`): `Nizam.ternary.wujud` هو
    `true`، والوجودُ هنا `licensableCell`.
-/

set_option autoImplicit false

namespace A116.IktisabHuwiyya

open A116 A116.Jadwal

/-- الخانةُ في البرج: حرفُ الجدول وحالتُه. -/
abbrev Khana := Harf × Haraka

def dom : List Khana := jadwal.flatMap fun h => harakat.map (h, ·)

/-- الخانةُ خليّةً (`Ladder.atom`). -/
def cellOf (x : Khana) : Cell := Ladder.atom x.1.c x.2

/-- أوصافُ الهويّة. -/
inductive Wasf where
  | hala | makhraj | jazari | hayyiz
  | sifa (i : Nat)
  deriving DecidableEq, Repr

def wasfAll : List Wasf := [.hala, .makhraj, .jazari, .hayyiz] ++ (List.range 14).map .sifa

def halaN : Haraka → Nat
  | .fatha => 0 | .damma => 1 | .kasra => 2 | .sukun => 3

def qima : Wasf → Khana → Nat
  | .hala, x => halaN x.2
  | .makhraj, x => x.1.makhraj
  | .jazari, x => x.1.jazariMakhraj
  | .hayyiz, x => x.1.hayyiz
  | .sifa i, x => if x.1.sifat.getD i false then 1 else 0

def key (ws : List Wasf) (x : Khana) : List Nat := ws.map (qima · x)

/-- التعيين: لا مانع — خانتان بمفتاحٍ واحد قانونُهما واحد. -/
def yuayyin (ws : List Wasf) (law : Khana → Bool) (D : List Khana) : Bool :=
  D.all fun a => D.all fun b => key ws a != key ws b || law a == law b

/-- قيمةُ القانون على المفتاح: قيمةُ أوّل خانةٍ به. -/
def bilMiftah (ws : List Wasf) (law : Khana → Bool) (D : List Khana) (k : List Nat) : Bool :=
  match D.find? (key ws · == k) with
  | some a => law a
  | none => false

/-- **التعيينُ هو أنّ القانون دالّةٌ في المفتاح** على المجال، لكلّ قانونٍ ولكلّ أوصاف. -/
theorem yuayyin_iff (ws : List Wasf) (law : Khana → Bool) (D : List Khana) :
    yuayyin ws law D = true ↔ ∃ f : List Nat → Bool, ∀ x ∈ D, law x = f (key ws x) := by
  constructor
  · intro h
    refine ⟨bilMiftah ws law D, fun x hx => ?_⟩
    unfold bilMiftah
    have hf : (D.find? (key ws · == key ws x)).isSome := by
      rw [List.find?_isSome]; exact ⟨x, hx, by simp⟩
    obtain ⟨a, ha⟩ := Option.isSome_iff_exists.1 hf
    rw [ha]
    have haD := List.mem_of_find?_eq_some ha
    have hka : key ws a = key ws x := by simpa using List.find?_some ha
    have := List.all_eq_true.1 (List.all_eq_true.1 h x hx) a haD
    simp only [Bool.or_eq_true, bne_iff_ne, ne_eq, beq_iff_eq] at this
    rcases this with h1 | h1
    · exact absurd hka.symm h1
    · exact h1
  · rintro ⟨f, hf⟩
    simp only [yuayyin, List.all_eq_true, Bool.or_eq_true, bne_iff_ne, ne_eq, beq_iff_eq]
    intro a ha b hb
    by_cases hk : key ws a = key ws b
    · exact Or.inr (by rw [hf a ha, hf b hb, hk])
    · exact Or.inl hk

/-- الحدُّ الأدنى المكتمل: يعيّن، وحذفُ أيّ وصفٍ يُسقط التعيين. -/
def adna (ws : List Wasf) (law : Khana → Bool) (D : List Khana) : Bool :=
  yuayyin ws law D && (List.range ws.length).all fun i => !yuayyin (ws.eraseIdx i) law D

/-- **لا وصفَ يُحذف من الأدنى**: بعد حذف أيّ وصفٍ لا دالّةَ في المفتاح الباقي تساوي القانون. -/
theorem adna_la_hadhf {ws : List Wasf} {law : Khana → Bool} {D : List Khana}
    (h : adna ws law D = true) (i : Nat) (hi : i < ws.length) :
    ¬ ∃ f : List Nat → Bool, ∀ x ∈ D, law x = f (key (ws.eraseIdx i) x) := by
  rw [← yuayyin_iff]
  simp only [adna, Bool.and_eq_true, List.all_eq_true, List.mem_range] at h
  simpa using h.2 i hi

/-- المجموعاتُ بحجمٍ k بترتيب القائمة. -/
def ikhtiyar {α : Type} : List α → Nat → List (List α)
  | _, 0 => [[]]
  | [], _ + 1 => []
  | a :: t, k + 1 => (ikhtiyar t k).map (a :: ·) ++ ikhtiyar t (k + 1)

/-- الجدولُ المكتسَب: مفتاحٌ وقيمة. -/
def bahth (J : List (List Nat × Bool)) (k : List Nat) : Option Bool := (J.find? (·.1 == k)).map (·.2)

/-! ## القوانين -/

def wujud (x : Khana) : Bool := licensableCell (cellOf x)

def ibtida (x : Khana) : Bool := Hadd.kindOne none (cellOf x) == .cv

def mubtada (x : Khana) : Bool := wujud x && ibtida x

end A116.IktisabHuwiyya
