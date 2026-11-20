import A116.Ledger
import A116.RootGrade
import A116.Numbering
import A116.Tarkib
import A116.Amil

/-!
# حدودُ الوحدات: كلُّ وحدةٍ حدٌّ بعددٍ n (ADR ٨٥، أمرُ المالك «ثبّت حدَّ الجذر والوزن والاسم والفعل والكلمة
في التركيب والضمير والموصول والإشارة والنداء والاستفهام … وهو unit له n»)

**الحدّ** هنا: الوحدةُ جنسٌ من أحدَ عشرَ جنسًا مغلقًا (`Jins`) وخاناتٌ (`Wahda`)، وعددُها
‎n = 11 · F(الخانات) + n(الجنس)‎ على `Numbering.atomNumber` — تباينٌ على الوحدات كلِّها (`n_inj`): لا وحدتان
بعددٍ واحد، ولا تشترك وحدةٌ من جنسٍ في عددٍ مع وحدةٍ من جنسٍ آخر ولو اتّحدت الخانات (`jins_separates`:
الاسمُ والفعلُ والحرفُ على خاناتٍ واحدة ثلاثةُ أعداد). والعددُ يُحلّ (`unn`): الجنسُ باقي القسمة والخاناتُ
بالخارج (`unn_n`).

## الحدودُ بأجناسها

| الجنس | الخانات | سندُه |
|---|---|---|
| الجذر | أصولُه بلا حركة (`jidhr`) | `RootGrade` — الأصولُ 28، والحدُّ تباينٌ (`jidhr_inj`) |
| الوزن | صيغتُه المرجعيّة على ك ت ب (`wazn`) | `Ledger.formOf` — الإحدى والثلاثون بأعدادٍ متباينة (`wazn_nodup`) |
| الاسم / الفعل / الحرف | خاناتُ الكلمة بقسمها (`kalima`) | `Tarkib.Qism` — القسمُ معاملٌ يفصل الأعداد (`jins_separates`) |
| الكلمةُ في التركيب | خاناتُها وموضعُها (`nFi`) | `Numbering.pair` — الموضعُ والخاناتُ يُستردّان (`nFi_inj`) |
| الضميرُ المنفصل | شرحُ ابن عقيل س792–803 | المرفوعُ اثنا عشر والمنصوبُ اثنا عشر؛ المودَعُ ما له شكلٌ مختوم |
| الموصول | س1023، والكتاب س13928–13929 (من، أيّ) | `mawsul` |
| اسمُ الإشارة | س985–995 | `ishara` |
| حرفُ النداء | س6681–6685 | `nida` |
| الاستفهام | الكتاب س1083–1084، 9769، 13929، 14193 | `istifham` |

**الشكلُ من المختوم لا من اليد:** خاناتُ كلّ صورةٍ هي ما تطبعه البوّابة للكلمة بعينها في المصحف المختوم
(`tests/test_hudud.py` يُعيد كلَّ صورةٍ عبر `gate.enter` ويطابق الذرّات)؛ وما لا شكلَ مختومًا له من قوائم الشرح
(أَنْتِ، أَنْتُنَّ، إِيَّايَ…، اللَّذَانِ، اللَّتَانِ، ذِي، ذِهِ، تِي، تَا، أَيْ، آ، أَيَا، هَيَا، وَا، مَتَى، أَيَّانَ، أَنَّى)
**لا يُودَع** باسمه `FORM_WITHOUT_SEALED_VOWELS` — الغيابُ ليس امتناعًا.

**البناء** (س738 «وكلّ مضمرٍ له البنا يجب»، س741–744 «لفظُ ما جرّ كلفظ ما نصب»): المبنيُّ حدٌّ واحدٌ لا تغيّره
علامة: وضعُ أيّ حركةٍ على آخر مضمرٍ إمّا يعيده بعينه أو يُخرجه من القائمة (`damir_mabni`، وكذا الموصولُ
والإشارةُ والاستفهام)؛ أمّا المعربُ فله بكلّ علامةٍ عدد (`zayd_three_n`).

ما ليس هنا — باسمه: `HADD_LISTS_ARE_QURAN_ATTESTED` (القوائمُ ما له شكلٌ في المصحف من قوائم الشرح، لا كلُّ
ما في الشرح)؛ `MUTTASIL_NOT_LISTED` (الضمائرُ المتّصلة خاناتٌ في كلماتٍ لا وحداتٌ هنا)؛ `ISHARA_BARE_FORMS_UNSEALED`
(ذِي ذِهِ تِي تَا بلا شكلٍ مختوم، والمودَعُ ما جاء بـ«ها» أو الكاف).
-/

namespace A116.Hudud

open A116 A116.Ladder A116.Hadd A116.Numbering A116.RootGrade

/-! ## ١. الجنسُ والوحدةُ وعددُها -/

inductive Jins where
  | jidhr | wazn | ism | fil | harf | kalimaFiTarkib | damir | mawsul | ishara | nida | istifham
  deriving DecidableEq, Repr

def ajnas : List Jins :=
  [.jidhr, .wazn, .ism, .fil, .harf, .kalimaFiTarkib, .damir, .mawsul, .ishara, .nida, .istifham]

def jinsN : Jins → Nat
  | .jidhr => 0 | .wazn => 1 | .ism => 2 | .fil => 3 | .harf => 4 | .kalimaFiTarkib => 5
  | .damir => 6 | .mawsul => 7 | .ishara => 8 | .nida => 9 | .istifham => 10

def ofN : Nat → Jins
  | 0 => .jidhr | 1 => .wazn | 2 => .ism | 3 => .fil | 4 => .harf | 5 => .kalimaFiTarkib
  | 6 => .damir | 7 => .mawsul | 8 => .ishara | 9 => .nida | _ => .istifham

theorem jinsN_lt (j : Jins) : jinsN j < 11 := by cases j <;> decide

theorem ofN_jinsN (j : Jins) : ofN (jinsN j) = j := by cases j <;> rfl

theorem ajnas_length : ajnas.length = 11 := by rfl

/-- الوحدة: جنسٌ وخانات. -/
structure Wahda where
  jins : Jins
  cells : List Cell
  deriving DecidableEq, Repr

/-- عددُ الوحدة. -/
def n (u : Wahda) : Nat := 11 * atomNumber u.cells + jinsN u.jins

/-- حلُّ العدد: الجنسُ باقيه والخاناتُ خارجُه (على شمول `atomNumber`؛ وجوديٌّ فغيرُ محسوب). -/
noncomputable def unn (k : Nat) : Wahda :=
  ⟨ofN (k % 11), (atomNumber_surjective (k / 11)).choose⟩

theorem n_mod (u : Wahda) : n u % 11 = jinsN u.jins := by
  unfold n; have := jinsN_lt u.jins; omega

theorem n_div (u : Wahda) : n u / 11 = atomNumber u.cells := by
  unfold n; have := jinsN_lt u.jins; omega

/-- **التباين**: وحدتان بعددٍ واحدٍ هما واحدة. -/
theorem n_inj {u v : Wahda} (h : n u = n v) : u = v := by
  have hj : jinsN u.jins = jinsN v.jins := by rw [← n_mod, ← n_mod, h]
  have hc : atomNumber u.cells = atomNumber v.cells := by rw [← n_div, ← n_div, h]
  have hj' : u.jins = v.jins := by rw [← ofN_jinsN u.jins, hj, ofN_jinsN]
  cases u; cases v
  simp only at hj' hc
  rw [hj', atomNumber_injective hc]

/-- **الحلّ**: العددُ يُردّ إلى وحدته. -/
theorem unn_n (u : Wahda) : unn (n u) = u := by
  have hc := atomNumber_injective ((atomNumber_surjective (n u / 11)).choose_spec.trans (n_div u))
  show Wahda.mk (ofN (n u % 11)) _ = u
  rw [n_mod, ofN_jinsN, hc]

/-- **الجنسُ يفصل**: خاناتٌ واحدة بجنسين عددان. -/
theorem jins_separates (w : List Cell) {j k : Jins} (h : j ≠ k) : n ⟨j, w⟩ ≠ n ⟨k, w⟩ := by
  intro he; exact h (congrArg Wahda.jins (n_inj he))

/-- **الخاناتُ تفصل**: جنسٌ واحد بخانتين مختلفتين عددان. -/
theorem cells_separate (j : Jins) {w v : List Cell} (h : w ≠ v) : n ⟨j, w⟩ ≠ n ⟨j, v⟩ := by
  intro he; exact h (congrArg Wahda.cells (n_inj he))

/-- لا تكرارَ في الأعداد حيث لا تكرارَ في الوحدات. -/
theorem nodup_map_n {L : List Wahda} (h : L.Nodup) : (L.map n).Nodup :=
  List.Pairwise.map n (fun _ _ hne he => hne (n_inj he)) h

/-- الاسمُ والفعلُ والحرفُ على خاناتٍ واحدة ثلاثةُ أعداد. -/
theorem ism_fil_harf_three (w : List Cell) :
    n ⟨.ism, w⟩ ≠ n ⟨.fil, w⟩ ∧ n ⟨.fil, w⟩ ≠ n ⟨.harf, w⟩ ∧ n ⟨.ism, w⟩ ≠ n ⟨.harf, w⟩ :=
  ⟨jins_separates w (by decide), jins_separates w (by decide), jins_separates w (by decide)⟩

/-! ## ٢. حدُّ الجذر: أصولُه بلا حركة -/

def rootCells (r : List (Fin 28)) : List Cell := r.map fun d => ⟨toCarrier d, .sukun⟩

def jidhr (r : List (Fin 28)) : Wahda := ⟨.jidhr, rootCells r⟩

theorem rootCells_inj {r s : List (Fin 28)} (h : rootCells r = rootCells s) : r = s := by
  induction r generalizing s with
  | nil => cases s with
    | nil => rfl
    | cons _ _ => simp [rootCells] at h
  | cons a r ih => cases s with
    | nil => simp [rootCells] at h
    | cons b s =>
      simp only [rootCells, List.map_cons, List.cons.injEq, Cell.mk.injEq, and_true] at h
      rw [toCarrier_injective h.1, ih (s := s) (by simpa [rootCells] using h.2)]

/-- جذران بعددٍ واحدٍ جذرٌ واحد، بأيّ طول. -/
theorem jidhr_inj {r s : List (Fin 28)} (h : n (jidhr r) = n (jidhr s)) : r = s :=
  rootCells_inj (congrArg Wahda.cells (n_inj h))

/-- عددُ الجذر عددٌ لا تحمله أيُّ كلمة: لا ألفَ في الأصول ولا حركة. -/
theorem jidhr_cells_sukun (r : List (Fin 28)) : (rootCells r).all (·.haraka == .sukun) = true := by
  induction r with
  | nil => rfl
  | cons _ _ ih => simp [rootCells] at ih ⊢

/-! ## ٣. حدُّ الوزن: صيغتُه المرجعيّة على ك ت ب -/

def wazn (p : Nat × Wazn.WaznC 3) : Wahda := ⟨.wazn, Ledger.formOf p .continue⟩

/-- صيغُ الأوزان الإحدى والثلاثين متباينةُ الخانات. -/
theorem wazn_forms_nodup : (Ledger.indexed.map wazn).Nodup := by decide +kernel

/-- فالأوزانُ الإحدى والثلاثون بأعدادٍ متباينة. -/
theorem wazn_nodup : (Ledger.indexed.map fun p => n (wazn p)).Nodup := by
  have := nodup_map_n wazn_forms_nodup
  simpa [List.map_map, Function.comp_def] using this

theorem wazn_count : Ledger.indexed.length = 31 := by decide +kernel

/-! ## ٤. حدُّ الكلمة بقسمها، وحدُّها في التركيب -/

def ofQism : Tarkib.Qism → Jins
  | .ism => .ism | .fil => .fil | .harf => .harf

theorem ofQism_inj {p q : Tarkib.Qism} (h : ofQism p = ofQism q) : p = q := by
  cases p <;> cases q <;> first | rfl | (exact absurd h (by decide))

/-- كلُّ اسمٍ وفعلٍ وحرفٍ حدٌّ بعدده. -/
def kalima (k : Tarkib.Kalima) : Wahda := ⟨ofQism k.qism, k.cells⟩

theorem kalima_inj {k l : Tarkib.Kalima} (h : n (kalima k) = n (kalima l)) : k = l := by
  have := n_inj h
  simp only [kalima, Wahda.mk.injEq] at this
  cases k; cases l
  simp only at this
  rw [ofQism_inj this.1, this.2]

/-- خاناتُ الكلمة الموضع i في التركيب. -/
def cellsAt (t : Tarkib.Tarkib) (i : Nat) : List Cell := ((t[i]?).map Tarkib.Kalima.cells).getD []

/-- الكلمةُ في التركيب: موضعُها وخاناتُها معًا بعددٍ واحد (`Numbering.pair`)، وجنسُها الخامس. -/
def nFi (t : Tarkib.Tarkib) (i : Nat) : Nat := 11 * pair i (atomNumber (cellsAt t i)) + jinsN .kalimaFiTarkib

/-- الموضعُ والخاناتُ يُستردّان من العدد: كلمتان في موضعين بعددٍ واحدٍ موضعٌ واحدٌ وخاناتٌ واحدة. -/
theorem nFi_inj {t s : Tarkib.Tarkib} {i j : Nat} (h : nFi t i = nFi s j) :
    i = j ∧ cellsAt t i = cellsAt s j := by
  unfold nFi at h
  simp only [jinsN] at h
  have hp := pair_injective (by omega : pair i (atomNumber (cellsAt t i)) = pair j (atomNumber (cellsAt s j)))
  exact ⟨hp.1, atomNumber_injective hp.2⟩

/-- عددُ الكلمة في التركيب من جنس الخامس: باقيه 5، فلا يلتبس بعدد وحدةٍ من جنسٍ آخر. -/
theorem nFi_mod (t : Tarkib.Tarkib) (i : Nat) : nFi t i % 11 = 5 := by
  unfold nFi; simp only [jinsN]; omega

/-! ## ٥. المبنيّات بشكلها المختوم -/

/-- المرفوعُ المنفصل (س792–797)؛ أَنْتِ وأَنْتُنَّ بلا شكلٍ مختوم. -/
def damirRaf : List (List Cell) :=
  [[atom 'ء' .fatha, atom 'ن' .fatha, atom 'ا' .sukun],                                   -- أَنَا
   [atom 'ن' .fatha, atom 'ح' .sukun, atom 'ن' .damma],                                   -- نَحْنُ
   [atom 'ء' .fatha, atom 'ن' .sukun, atom 'ت' .fatha],                                   -- أَنتَ
   [atom 'ء' .fatha, atom 'ن' .sukun, atom 'ت' .damma, atom 'م' .fatha, atom 'ا' .sukun], -- أَنتُمَا
   [atom 'ء' .fatha, atom 'ن' .sukun, atom 'ت' .damma, atom 'م' .sukun],                  -- أَنتُمْ
   [atom 'ه' .damma, atom 'و' .fatha],                                                    -- هُوَ
   [atom 'ه' .kasra, atom 'ي' .fatha],                                                    -- هِيَ
   [atom 'ه' .damma, atom 'م' .fatha, atom 'ا' .sukun],                                   -- هُمَا
   [atom 'ه' .damma, atom 'م' .sukun],                                                    -- هُمْ
   [atom 'ه' .damma, atom 'ن' .sukun, atom 'ن' .fatha]]                                   -- هُنَّ

/-- المنصوبُ المنفصل (س799–803)؛ المودَعُ أربعةٌ بشكلٍ مختوم. -/
def damirNasb : List (List Cell) :=
  [[atom 'ء' .kasra, atom 'ي' .sukun, atom 'ي' .fatha, atom 'ا' .sukun, atom 'ن' .fatha, atom 'ا' .sukun], -- إِيَّانَا
   [atom 'ء' .kasra, atom 'ي' .sukun, atom 'ي' .fatha, atom 'ا' .sukun, atom 'ك' .fatha],                  -- إِيَّاكَ
   [atom 'ء' .kasra, atom 'ي' .sukun, atom 'ي' .fatha, atom 'ا' .sukun, atom 'ك' .damma, atom 'م' .sukun], -- إِيَّاكُمْ
   [atom 'ء' .kasra, atom 'ي' .sukun, atom 'ي' .fatha, atom 'ا' .sukun, atom 'ه' .damma]]                  -- إِيَّاهُ

/-- الموصولُ (س1023؛ من وأيّ: الكتاب س13928–13929؛ ذا بمنزلة الذي س13929). -/
def mawsul : List (List Cell) :=
  [[atom 'ء' .fatha, atom 'ل' .sukun, atom 'ل' .fatha, atom 'ذ' .kasra, atom 'ي' .sukun],                   -- الَّذِي
   [atom 'ء' .fatha, atom 'ل' .sukun, atom 'ل' .fatha, atom 'ت' .kasra, atom 'ي' .sukun],                   -- الَّتِي
   [atom 'ء' .fatha, atom 'ل' .sukun, atom 'ل' .fatha, atom 'ذ' .kasra, atom 'ي' .sukun, atom 'ن' .fatha],  -- الَّذِينَ
   [atom 'ء' .fatha, atom 'ل' .sukun, atom 'ل' .fatha, atom 'ا' .sukun, atom 'ت' .kasra, atom 'ي' .sukun],  -- اللَّاتِي
   [atom 'ء' .fatha, atom 'ل' .sukun, atom 'ل' .fatha, atom 'ا' .sukun, atom 'ء' .kasra, atom 'ي' .sukun],  -- اللَّائِي
   [atom 'م' .fatha, atom 'ن' .sukun],                                                                      -- مَنْ
   [atom 'م' .fatha, atom 'ا' .sukun],                                                                      -- مَا
   [atom 'ء' .fatha, atom 'ي' .sukun, atom 'ي' .damma],                                                     -- أَيُّ
   [atom 'ذ' .fatha, atom 'ا' .sukun]]                                                                      -- ذَا

/-- اسمُ الإشارة (س985–995): المجرّدُ ذا، وما جاء بـ«ها» التنبيه أو بالكاف بشكلٍ مختوم. -/
def ishara : List (List Cell) :=
  [[atom 'ذ' .fatha, atom 'ا' .sukun],                                                                      -- ذَا
   [atom 'ه' .fatha, atom 'ذ' .fatha, atom 'ا' .sukun],                                                     -- هَذَا
   [atom 'ه' .fatha, atom 'ذ' .kasra, atom 'ه' .kasra],                                                     -- هَذِهِ
   [atom 'ه' .fatha, atom 'ذ' .fatha, atom 'ا' .sukun, atom 'ن' .kasra],                                    -- هَذَانِ
   [atom 'ه' .fatha, atom 'ا' .sukun, atom 'ت' .fatha, atom 'ي' .sukun, atom 'ن' .kasra],                   -- هَاتَيْنِ
   [atom 'ه' .fatha, atom 'ء' .damma, atom 'ل' .fatha, atom 'ا' .sukun, atom 'ء' .kasra],                   -- هَؤُلَاءِ
   [atom 'ء' .damma, atom 'ل' .fatha, atom 'ء' .kasra, atom 'ك' .fatha],                                    -- أُولَئِكَ
   [atom 'ذ' .fatha, atom 'ل' .kasra, atom 'ك' .fatha],                                                     -- ذَلِكَ
   [atom 'ت' .kasra, atom 'ل' .sukun, atom 'ك' .fatha]]                                                     -- تِلْكَ

/-- حرفُ النداء (س6681–6685: يا، أي، آ، هيا، الهمزة، وا)؛ المودَعُ «يَا» وحدَها بشكلٍ مختوم. -/
def nida : List (List Cell) :=
  [[atom 'ي' .fatha, atom 'ا' .sukun]]                                                    -- يَا

/-- الاستفهام (الكتاب س9769: هل كيف من؛ س13929: من أيّ؛ س14193: كم ماذا؛ س1084: أين). -/
def istifham : List (List Cell) :=
  [[atom 'ه' .fatha, atom 'ل' .sukun],                                                    -- هَلْ
   [atom 'ك' .fatha, atom 'ي' .sukun, atom 'ف' .fatha],                                   -- كَيْفَ
   [atom 'م' .fatha, atom 'ن' .sukun],                                                    -- مَنْ
   [atom 'ء' .fatha, atom 'ي' .sukun, atom 'ي' .damma],                                   -- أَيُّ
   [atom 'ك' .fatha, atom 'م' .sukun],                                                    -- كَمْ
   [atom 'م' .fatha, atom 'ا' .sukun, atom 'ذ' .fatha, atom 'ا' .sukun],                  -- مَاذَا
   [atom 'ء' .fatha, atom 'ي' .sukun, atom 'ن' .fatha]]                                   -- أَيْنَ

def mabniyyat : List (Jins × List (List Cell)) :=
  [(.damir, damirRaf ++ damirNasb), (.mawsul, mawsul), (.ishara, ishara), (.nida, nida), (.istifham, istifham)]

/-- وحداتُ المبنيّات بأعدادها. -/
def mabniWahdat : List Wahda := mabniyyat.flatMap fun p => p.2.map fun w => ⟨p.1, w⟩

theorem counts : damirRaf.length = 10 ∧ damirNasb.length = 4 ∧ mawsul.length = 9 ∧ ishara.length = 9 ∧
    nida.length = 1 ∧ istifham.length = 7 := by decide

theorem mabni_count : mabniWahdat.length = 40 := by decide

/-- كلُّ صورةٍ مرخَّصةٌ ابتداءً ووقفًا بقيد الحدّ. -/
theorem mabni_licensed :
    mabniWahdat.all (fun u => strictB u.cells && strictPauseB u.cells) = true := by decide +kernel

theorem mabni_wahdat_nodup : mabniWahdat.Nodup := by decide +kernel

/-- الأعدادُ الأربعون متباينة. -/
theorem mabni_nodup : (mabniWahdat.map n).Nodup := nodup_map_n mabni_wahdat_nodup

/-- «مَنْ» و«أَيُّ» و«ذَا» موصولًا واستفهامًا وإشارةً خاناتٌ واحدة وأعدادٌ مختلفة: الجنسُ حدٌّ لا الخانات. -/
theorem man_two_n :
    mawsul[5]! = istifham[2]! ∧ n ⟨.mawsul, mawsul[5]!⟩ ≠ n ⟨.istifham, istifham[2]!⟩ ∧
    mawsul[8]! = ishara[0]! ∧ n ⟨.mawsul, mawsul[8]!⟩ ≠ n ⟨.ishara, ishara[0]!⟩ :=
  ⟨by decide, jins_separates _ (by decide), by decide, jins_separates _ (by decide)⟩

/-! ## ٦. البناءُ والإعراب على الحدّ -/

/-- وضعُ علامةٍ على آخر المبنيّ إمّا يعيده بعينه أو يُخرجه من قائمته: لا علامةَ تنقل مبنيًّا إلى مبنيٍّ آخر
(س738 «وكلّ مضمرٍ له البنا يجب»). -/
def thabit (L : List (List Cell)) : Bool :=
  L.all fun w => Haraka.all.all fun h => Amil.applyMark w h == w || !(L.contains (Amil.applyMark w h))

theorem damir_mabni : thabit damirRaf = true ∧ thabit damirNasb = true := by decide +kernel
theorem mawsul_mabni : thabit mawsul = true := by decide +kernel
theorem ishara_mabni : thabit ishara = true := by decide +kernel
theorem istifham_mabni : thabit istifham = true := by decide +kernel

/-- المعربُ بكلّ علامةٍ عدد: زَيْدُ / زَيْدَ / زَيْدِ ثلاثةُ أعدادٍ لحدٍّ واحدٍ من جنسه. -/
def zayd : List Cell := [atom 'ز' .fatha, atom 'ي' .sukun, atom 'د' .damma]

theorem zayd_three_n :
    n ⟨.ism, Amil.applyMark zayd .damma⟩ ≠ n ⟨.ism, Amil.applyMark zayd .fatha⟩ ∧
    n ⟨.ism, Amil.applyMark zayd .fatha⟩ ≠ n ⟨.ism, Amil.applyMark zayd .kasra⟩ ∧
    n ⟨.ism, Amil.applyMark zayd .damma⟩ ≠ n ⟨.ism, Amil.applyMark zayd .kasra⟩ :=
  ⟨cells_separate _ (by decide), cells_separate _ (by decide), cells_separate _ (by decide)⟩

/-- الوقفُ يمحو الفرق: الأعدادُ الثلاثةُ وقفًا عددٌ واحد (`Amil.pause_erases_asliyya` على الحدّ). -/
theorem zayd_pause_one_n :
    n ⟨.ism, Amil.applyMark (Amil.applyMark zayd .damma) .sukun⟩ =
      n ⟨.ism, Amil.applyMark (Amil.applyMark zayd .fatha) .sukun⟩ :=
  congrArg (fun w => n ⟨.ism, w⟩) (by decide)

end A116.Hudud
