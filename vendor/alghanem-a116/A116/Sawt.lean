import A116.Hadd
import A116.Jadwal

/-!
# الصوت: الحركاتُ أبعاضُ حروف المدّ، والحرفُ مخرجٌ وصفات، والمدُّ بأحكامه (ADR ٨٤)

أمرُ المالك (2026-10-16): «ونعمل Lean الصوت … ضروريٌّ عملُ Lean».

## السند (منقولٌ بلفظه من النصوص المختومة في `corpora/kitab/`، يفحصها `tests/test_sawt.py`)

* ابنُ جنّي، «سرّ صناعة الإعراب» (JK001326، س232–234): «اعلم أنّ الحركاتِ أبعاضُ حروف المدّ واللين، وهي الألفُ
  والياءُ والواو … فالفتحةُ بعضُ الألف، والكسرةُ بعضُ الياء، والضمّةُ بعضُ الواو».
* س245–248: «متى أشبعتَ واحدةً منهنّ حدث بعدها الحرفُ الذي هي بعضُه … فتحةُ عين عُمَر … إن أشبعتها حدثت بعدها
  ألفٌ فقلت عامر … وضمّةُ عين عُمَر لو أشبعتها لأنشأتَ بعدها واوًا ساكنة … عومر».
* س239–240: «فإذا أوقعتَ بعدهنّ الهمزةَ أو الحرفَ المدغمَ ازددن طولًا وامتدادًا».
* الجزريّة (Shamela0012093، باب المدّ): «والمدُّ لازمٌ وواجبٌ أتى، وجائزٌ، وهو وقصرٌ ثبتا؛ فلازمٌ إن جاء بعد حرف
  مدٍّ ساكنُ حالين وبالطول يُمدّ؛ وواجبٌ إن جاء قبل همزةٍ متّصلًا إن جُمعا بكلمة؛ وجائزٌ إذا أتى منفصلًا أو عرض
  السكونُ وقفًا».

## ما يُبرهَن (لكلّ كلمة)

١. **الحركةُ بعضُ حرف المدّ** (`baad`): لكلّ حركةٍ غير السكون حرفُ مدٍّ واحد هي بعضُه، وهو ما يجعله `Hadd.maddVowel`
   مدًّا لها؛ و**الصوتُ يوافق الترخيص** (`madd_iff_v`): الخانةُ تُدمج بما قبلها صائتًا طويلًا ⟺ صنفُها `v`.
٢. **الصوتُ بلا ضياع** (`sawt_radd`): الكلمةُ صوامتُ وصوائتُ قصيرةٌ وطويلة، وتُردّ إلى خاناتها بأعيانها؛ والإشباعُ
   يُحدث حرفَ المدّ (`ishba_umar`: عُمَر ← عُومَر، `ishba_amir`: عَمِر ← عَامِر).
٣. **الحرفُ مخرجٌ وأربعُ صفات** (`key4_inj`): الحواملُ التسعة والعشرون تتعيّن بمخرجها والهمسِ والشدّةِ والتوسّطِ
   والاستعلاء (`Jadwal.fasl_four`)، فالصوتُ بالسمات (`sawtF`) بلا ضياعٍ أيضًا (`sawtF_radd`).
٤. **أحكامُ المدّ على الأصناف** (`hukm`): لازمٌ (يليه ساكنٌ في الكلمة)، متّصلٌ (يليه همزةٌ في الكلمة)، طبيعيّ،
   وطرفٌ يُحكم بما بعد الكلمة (منفصل/عارض)؛ و`lazim_mudgham`: في كلّ كلمةٍ مرخَّصةٍ بقيد الحدّ ليست مدَّ فرقٍ،
   ساكنُ اللازم أوّلُ مثلين — «أو الحرفَ المدغم» عند ابن جنّي؛ و`lazim_akhir`: لا لازمَ في آخر الكلمة وصلًا
   (قَالْتُ)، فالساكنُ «حالين» داخلَها.

ما لا يُبرهَن: مقاديرُ المدّ بالحركات (لا نصَّ مختومًا بعددها: `MADD_MIQDAR_NOT_IN_SEALED_TEXT`)، والغنّةُ
والإخفاءُ والقلب (`NUN_SAKINA_RULES_NOT_WRITTEN`)، وأنّ هذا صوتُ العربيّة — Lean يُبرهن المرويَّ لا اللغة.
-/

namespace A116.Sawt

open A116 A116.Stages A116.Ladder A116.Hadd

/-! ## ١. الحركةُ بعضُ حرف المدّ -/

/-- حرفُ المدّ الذي الحركةُ بعضُه. -/
def maddOf : Haraka → Option (Fin carrierCount)
  | .fatha => some (carrierOf 'ا')
  | .damma => some (carrierOf 'و')
  | .kasra => some (carrierOf 'ي')
  | .sukun => none

/-- **الحركةُ بعضُ حرف المدّ**: حرفُ مدّها هو ما يجعله `maddVowel` مدًّا لها، ولا غيرُه. -/
theorem baad : ∀ (h : Haraka) (k : Fin carrierCount), maddOf h = some k ↔ maddVowel k = some h := by
  intro h k; cases h <;> revert k <;> decide

/-! ## ٢. الصوت -/

/-- مقطعُ الصوت: صامتٌ، أو صائتٌ بحركته وطوله. -/
inductive Seg where
  | samit (k : Fin carrierCount)
  | saait (q : Haraka) (tawil : Bool)
  deriving DecidableEq, Repr

def emit (c : Cell) : List Seg :=
  .samit c.carrier :: (if c.haraka = .sukun then [] else [.saait c.haraka false])

/-- الإدماج: متحرّكٌ يليه حرفُ مدّ حركته ساكنًا = صامتٌ وصائتٌ طويل. -/
def madmuj (c d : Cell) : Bool :=
  c.haraka != .sukun && d.haraka == .sukun && maddVowel d.carrier == some c.haraka

def sawt : List Cell → List Seg
  | [] => []
  | [c] => emit c
  | c :: d :: t =>
    if madmuj c d then .samit c.carrier :: .saait c.haraka true :: sawt t
    else emit c ++ sawt (d :: t)

def maddCell (q : Haraka) : Cell := ⟨(maddOf q).getD (carrierOf 'ا'), .sukun⟩

def un : List Seg → List Cell
  | [] => []
  | .samit k :: .saait q true :: t => ⟨k, q⟩ :: maddCell q :: un t
  | .samit k :: .saait q false :: t => ⟨k, q⟩ :: un t
  | .samit k :: .samit k' :: t => ⟨k, .sukun⟩ :: un (.samit k' :: t)
  | [.samit k] => [⟨k, .sukun⟩]
  | .saait _ _ :: t => un t

/-- **الصوتُ يوافق الترخيص**: الإدماجُ ⟺ صنفُ الخانة الثانية `v` بعد حركة الأولى. -/
theorem madd_iff_v_all :
    Haraka.all.all (fun h => cells.all fun d =>
      (madmuj ⟨⟨0, by decide⟩, h⟩ d) == (kindOne (some h) d == .v)) = true := by decide

theorem madd_iff_v (c d : Cell) : madmuj c d = true ↔ kindOne (some c.haraka) d = .v := by
  have h1 := List.all_eq_true.1 madd_iff_v_all c.haraka (Haraka.mem_all _)
  have h2 := List.all_eq_true.1 h1 d (mem_cells d)
  have : madmuj c d = madmuj ⟨⟨0, by decide⟩, c.haraka⟩ d := rfl
  rw [this]
  revert h2
  cases madmuj ⟨⟨0, by decide⟩, c.haraka⟩ d <;> cases kindOne (some c.haraka) d <;> simp

theorem madd_cell_all :
    Haraka.all.all (fun h => cells.all fun d =>
      !(madmuj ⟨⟨0, by decide⟩, h⟩ d) || d == maddCell h) = true := by decide

theorem madd_cell (c d : Cell) (h : madmuj c d = true) : d = maddCell c.haraka := by
  have h1 := List.all_eq_true.1 madd_cell_all c.haraka (Haraka.mem_all _)
  have h2 := List.all_eq_true.1 h1 d (mem_cells d)
  have : madmuj c d = madmuj ⟨⟨0, by decide⟩, c.haraka⟩ d := rfl
  rw [this] at h
  simp only [h, Bool.not_true, Bool.false_or, beq_iff_eq] at h2
  exact h2

/-- الصوتُ يبدأ بصامتٍ أو يكون فارغًا. -/
def headSamit : List Seg → Bool
  | [] => true
  | .samit _ :: _ => true
  | _ => false

theorem sawt_head : ∀ w, headSamit (sawt w) = true
  | [] => rfl
  | [c] => by unfold sawt emit; rfl
  | c :: d :: t => by
    unfold sawt
    split
    · rfl
    · unfold emit; rfl

theorem un_emit (c : Cell) (r : List Seg) (hr : headSamit r = true) : un (emit c ++ r) = c :: un r := by
  unfold emit
  cases hc : c.haraka with
  | sukun =>
    simp only [List.cons_append]
    cases r with
    | nil => cases c; simp_all [un]
    | cons s r' =>
      cases s with
      | samit k' => cases c; simp_all [un]
      | saait q b => simp [headSamit] at hr
  | fatha => cases c; simp_all [un]
  | damma => cases c; simp_all [un]
  | kasra => cases c; simp_all [un]

/-- **الصوتُ بلا ضياع**: الكلمةُ تُردّ من صوتها بأعيانها. -/
theorem sawt_radd : ∀ w, un (sawt w) = w
  | [] => rfl
  | [c] => by
    have := un_emit c [] rfl
    simp only [List.append_nil] at this
    simpa [sawt, un] using this
  | c :: d :: t => by
    unfold sawt
    split
    · rename_i hm
      have hd := madd_cell c d hm
      have hc : c.haraka ≠ .sukun := by
        intro h; simp [madmuj, h] at hm
      have ih := sawt_radd t
      cases hh : c.haraka with
      | sukun => exact absurd hh hc
      | _ => cases c; simp_all [un]
    · rw [un_emit c _ (sawt_head _), sawt_radd (d :: t)]

/-- **الإشباعُ يُحدث حرفَ المدّ**: ضمّةُ عين «عُمَر» مشبعةً «عُومَر»، وفتحتُها «عَامَر». -/
def ayn : Fin carrierCount := carrierOf 'ع'
def mim : Fin carrierCount := carrierOf 'م'
def ra : Fin carrierCount := carrierOf 'ر'

theorem ishba_umar :
    un [.samit ayn, .saait .damma true, .samit mim, .saait .fatha false, .samit ra] =
      [⟨ayn, .damma⟩, ⟨carrierOf 'و', .sukun⟩, ⟨mim, .fatha⟩, ⟨ra, .sukun⟩] := by decide

theorem ishba_amir :
    sawt [⟨ayn, .fatha⟩, ⟨carrierOf 'ا', .sukun⟩, ⟨mim, .kasra⟩, ⟨ra, .sukun⟩] =
      [.samit ayn, .saait .fatha true, .samit mim, .saait .kasra false, .samit ra] := by decide

/-! ## ٣. الحرفُ مخرجٌ وأربعُ صفات -/

def charOf (k : Fin carrierCount) : Char := Field112.carrierChar k

def key4 (k : Fin carrierCount) : Nat × List Bool :=
  Jadwal.key [.hams, .shidda, .tawassut, .istila] (charOf k)

/-- **الحواملُ تتعيّن بمخرجها وأربع صفات.** -/
theorem key4_inj : ∀ a b : Fin carrierCount, key4 a = key4 b → a = b := by decide

inductive SegF where
  | samit (sima : Nat × List Bool)
  | saait (q : Haraka) (tawil : Bool)
  deriving DecidableEq, Repr

def toF : Seg → SegF
  | .samit k => .samit (key4 k)
  | .saait q b => .saait q b

def fromKey (s : Nat × List Bool) : Fin carrierCount :=
  ((List.finRange carrierCount).find? (key4 · == s)).getD ⟨0, by decide⟩

theorem fromKey_key4 : ∀ k, fromKey (key4 k) = k := by decide

def ofF : SegF → Seg
  | .samit s => .samit (fromKey s)
  | .saait q b => .saait q b

def sawtF (w : List Cell) : List SegF := (sawt w).map toF

/-- **الصوتُ بالسمات بلا ضياع.** -/
theorem sawtF_radd (w : List Cell) : un ((sawtF w).map ofF) = w := by
  have : ∀ s : Seg, ofF (toF s) = s := by
    intro s; cases s <;> simp [toF, ofF, fromKey_key4]
  simp only [sawtF, List.map_map, Function.comp_def, this, List.map_id', sawt_radd]

/-! ## ٤. أحكامُ المدّ (الجزريّة) -/

inductive Madd where
  | tabii | lazim | muttasil | taraf
  deriving DecidableEq, Repr

/-- حكمُ كلّ مدٍّ في الكلمة من الخانة التي تليه: ساكنٌ ← لازم، همزةٌ ← متّصل، غيرُهما ← طبيعيّ، ولا شيء ← طرف. -/
def hukm : List (K × Cell) → List Madd
  | [] => []
  | (.v, _) :: rest =>
    (match rest with
      | [] => Madd.taraf
      | (k, x) :: _ => if x.carrier = hamza then .muttasil else if k = .c then .lazim else .tabii)
      :: hukm rest
  | _ :: rest => hukm rest

/-- **ساكنُ اللازم مدغم**: في كلمةٍ مرخَّصةٍ بقيد الحدّ ليست مدَّ فرق، مدٌّ يليه ساكنٌ فالساكنُ أوّلُ مثلين —
«أو الحرفَ المدغم» (ابن جنّي)، «ساكنُ حالين» (الجزريّ). -/
theorem lazim_mudgham {w : List Cell} (h : strictB w = true) (hf : isFarq w = false)
    {p q : List (K × Cell)} {a x y : Cell} {k : K}
    (hz : (kindOf w).zip w = p ++ (.v, a) :: (.c, x) :: (k, y) :: q) : x.carrier = y.carrier :=
  strict_cvvc_is_geminate h hf hz

/-- **لا لازمَ في آخر الكلمة وصلًا**: مدٌّ وساكنٌ أخيران لا يُرخَّصان (قَالْتُ)، فالسكونُ في الطرف عارضٌ للوقف. -/
theorem lazim_akhir (p : List (K × Cell)) (a x : Cell) :
    geminateB (p ++ [(.v, a), (.c, x)]) = false := geminateB_vc_final p a x

/-- الشواهد: «حَاجَّ» لازم، و«جَاءَ» متّصل، و«قَالَ» طبيعيّ. -/
def jaa : List Cell := [atom 'ج' .fatha, atom 'ا' .sukun, atom 'ء' .fatha]
def qala : List Cell := [atom 'ق' .fatha, atom 'ا' .sukun, atom 'ل' .fatha]

theorem shawahid_madd :
    hukm ((kindOf hajjaCells).zip hajjaCells) = [.lazim] ∧
    hukm ((kindOf jaa).zip jaa) = [.muttasil] ∧
    hukm ((kindOf qala).zip qala) = [.tabii] := by decide +kernel

/-- **الطولُ رتبة**: الطبيعيُّ أقصر، ويزداد قبل الهمزة والمدغم (ابن جنّي)؛ ولا عددَ للحركات هنا. -/
def tul : Madd → Nat
  | .tabii => 1
  | _ => 2

theorem ziyada : tul .tabii < tul .muttasil ∧ tul .tabii < tul .lazim := by decide

/-! ## المراسي (أسطرٌ يُعدّ أوّلُها 1) -/

def marasi : List (String × Nat × String) :=
  [ ("0392IbnJinniMawsili.SirrSinacatIcrab.JK001326-ara1", 232, "اعلم أن الحركات أبعاض حروف المد واللين"),
    ("0392IbnJinniMawsili.SirrSinacatIcrab.JK001326-ara1", 234, "بعض الألف والكسرة بعض الياء والضمة بعض الواو"),
    ("0392IbnJinniMawsili.SirrSinacatIcrab.JK001326-ara1", 239, "فإذا أوقعت بعدهن الهمزة أو الحرف المدغم ازددن طولا"),
    ("0392IbnJinniMawsili.SirrSinacatIcrab.JK001326-ara1", 245, "ويدلك على أن الحركات أبعاض لهذه الحروف أنك متى أشبعت"),
    ("0833IbnJazari.ManzumaJazariyya.Shamela0012093-ara1", 138, "والمد لازم وواجب أتى"),
    ("0833IbnJazari.ManzumaJazariyya.Shamela0012093-ara1", 139, "فلازم إن جاء بعد حرف مد"),
    ("0833IbnJazari.ManzumaJazariyya.Shamela0012093-ara1", 141, "وواجب إن جاء قبل همزة"),
    ("0833IbnJazari.ManzumaJazariyya.Shamela0012093-ara1", 142, "وجائز إذا أتى منفصلا") ]

end A116.Sawt
