/-
  Nizam/QawaidB.lean — رخصةُ صفّ الأسماء الستّة ووقفُه على الأعداد، مساويتان للمواصفة لكلّ موضع؛ والقراءةُ والحكمُ يستدعيانهما ويساويان المواصفة.

  قولُ المالك (2026-10-21، 20:35 بتوقيت عمّان): «انت يجب انت تعمل بمنطق رقمي وفق الطريقة العقلية ححل واستنتج وطبق»، بعد تحليلٍ لصقه
  (أُحيل إلى سطور رسالته بالحرف ر) مركزُه f̂(E(x)) = E(f(x)) («قانون حفظ العملية»، ر200–204)، وx ∈ Dom(f) ⟺ E(x) ∈ Dom(f̂) («قانون حفظ
  مجالها»، ر208–216) وغايتُه أن «يمنع أن يقبل التنفيذ البتّي انتقالًا ترفضه العملية الأصلية» (ر218)؛ ومتطلّباتُ الإثبات لقاعدةٍ R⁺ (ر458)
  وشواهدُ الإثبات P (ر444) بشرط (P ∧ R⁺) = R⁺ (ر466)، والناقصُ R⁺ ∖ P (ر594). وهنا التطبيقُ الأوّل على ما بُني في Mashru: رخصةُ
  `Jisr.QawaidSitta.rukhsa` ووقفُها `mawquf`. وتعيينُ P أصولَ الموضع لكلّ قانونٍ بحالته (لا قناعًا واحدًا عامًّا كما في التحليل) قرارُ البنّاء.

  الترميز (تعيينُ البنّاء):
  * **الكلمة** `ramz`: عددُ خلاياها `Dal.Adad.adad` إن كانت كلُّها أقلَّ من 116، وإلّا فلا رمز (`ramz_majal`: مجالُ الترميز).
  * **القانون** `ramzQanun`: (عددُ صورة نتيجته، حالتُها، قناعُ مقدّماته R⁺) — الصورة 1، الإضافة 2، طلبُ الحالة 4، الصحبة 8
    (`bitQadiyya`). فقوانينُ الجدول السبعةُ والعشرون أعدادٌ (`qawaninB_qiyam`).
  * **الموضع** `alamat`: الاسميّةُ البتُّ 0، والإضافةُ البتُّ 1، وكلُّ حالةٍ h يطلبها الموضعُ البتُّ h+2 (`alamat_bitat`).
  * **الأصولُ** `usulB` قناعُ P لقانونٍ حالتُه h: الصورةُ (مطابقتُها شرطٌ في `yuntijB`)، والإضافةُ، وطلبُ الحالة إن كان الموضعُ اسميًّا
    يطلبها؛ والصحبةُ لا تُقرأ من الدالّ فلا بتَّ لها في P أبدًا.
  * **الناقص** `naqsB` = R⁺ ∖ P بـ XOR: R⁺ ^^^ (R⁺ &&& P).

  المنفّذ: `rukhsaB` = قانونٌ ينتج الكلمةَ بحالةٍ يطلبها الموضع وناقصُه 0؛ و`mawqufB` = قانونٌ ينتجها، في R⁺ بتُّ ما لا يُقرأ، وناقصُه
  داخلَ ذلك البتّ. وكلاهما لا يستدعي `aslMawdi` ولا `Qaida.maqbulM`: أعدادٌ وأقنعة. والمبرهنتان المركزيّتان (لكلّ موضعٍ وكلّ كلمة، على
  هذا الجدول):
  * `rukhsaB_sawa`: rukhsaB (ramz خلاياها) (alamat …) = rukhsa …
  * `mawqufB_sawa`: mawqufB (ramz خلاياها) (alamat …) = mawquf …
  وهما حفظُ المجال بمعنى التحليل: المساواةُ تشمل الكلمةَ خارج المجال (رمزُها `none`)، فالمنفّذُ لا يقبل ما ترفضه المواصفة.
  و`qiraaB` (القراءةُ بالجدول) و`hukmB` (حكمُ الطبقة الثالثة) يستدعيان `rukhsaB` و`mawqufB` ويساويان `qiraaSitta` و`hukmSitta` لكلّ إطار
  (`qiraaB_sawa`، `hukmB_sawa`)؛ وما سواهما فيهما على المحتوى لا على الأعداد (انظر «لا يُدّعى»).
  ونواقصُ القوانين التي تنتج الكلمةَ بأسمائها (`asmaNaqs`): «ذُو» في موضع الإضافة ناقصُها الصحبةُ وحدها، و«أَبُو» بلا إضافةٍ ناقصُها
  الإضافة (`naqs_shawahid`). واختبارُ الحالة في `yuntijB` (كاختبارها في `yuntij`) زائدٌ في الرخصة والوقف — بتُّ طلب الحالة في R⁺ لا يُستوفى
  إلّا إن طلب الموضعُ حالةَ القانون؛ استنتاجٌ من التعريفات، شاهدُه أنّ P424 تُبقي `rukhsaB_sawa` و`mawqufB_sawa` (لا يفشل تحتها إلّا
  `naqs_shawahid`)، وبرهنه المراجعُ المستقلّ لـ`yuntij` خارج المستودع؛ وكلٌّ من الاختبارين (الحالةُ في `yuntijB`، وطلبُها في `usulB`/`aslMawdi`)
  زائدٌ ما بقي الآخر لا معًا —، ويحدّد ما يُسرد في `naqsMawdi`: «أَبَا» في موضع رفعٍ نواقصُ قانون الرفع وحده (`naqs_shawahid`، وبه
  تُقتل P424). وبتُّ الصورة لا يقع في الناقص أبدًا (`usulB` تضعه، ومطابقةُ الصورة شرطٌ في `yuntijB`)، فلا اسمَ له: كلمةٌ لا
  قانونَ ينتجها نواقصُها قائمةٌ فارغة، لا سببٌ مسمّى.

  والسلسلةُ المقبولة عند الفاحص بالمحتوى هي المقدّماتُ أصولًا (`maqbul_silsila`، لكلّ قاعدة)، فالمنفّذُ لا يتجاوز `Qaida.maqbulM`:
  يساويه على كلّ موضع.

  العدّ بالمعيار الموحَّد (`Nizam/Asas.lean`): 16 مبرهنة — 11 لكلّ (`fahsM_usul`، `maqbul_silsila`، `rukhsa_usul`، `ramz_sawa`،
  `qinaHalat_bit`، `qinaHalat_sifr`، `alamat_bitat`، `rukhsaB_sawa`، `mawqufB_sawa`، `qiraaB_sawa`، `hukmB_sawa`)، و2 تعريفيّة (`ramz_majal`،
  `qanun_bitat`)، و3 على الشاهد (`qawaninB_qiyam`، `mawadi_bitat`، `naqs_shawahid`). ومساعداتٌ خاصّةٌ غيرُ معدودة ولا مدقّقة بأسمائها في
  `Audit.lean` (كمساعدتَي `Jisr/Utur.lean` الخاصّتين؛ ومسلّماتُها داخلةٌ في تدقيق ما يستعملها)، مصنَّفةً بالمعيار: `qanun_fi` لكلّ (تستدعي
  `List.mem_flatMap`/`List.mem_map`)، و`majal_qawanin` على الشاهد (decide على الجدول: صورُ القوانين كلُّها في المجال)، و`naqs_7_15`
  و`waqf_7_15` لكلّ (قضيّتان عامّتان في ثلاثة بتّات، برهانُهما cases ثمّ decide — بسابقة `Nizam.Aqd.irabMurashshah_la_jazm`). فعمومُ `rukhsaB_sawa` و`mawqufB_sawa` في الموضع والكلمة على هذا الجدول،
  وصحّتُهما على جدولٍ آخر تحتاج `majal_qawanin` عليه. و`maqbul_silsila` مساواةٌ تُتمّ `QawaidSitta.silsila_maqbula` (الاتّجاهُ الواحد).
  وأعدادُ `qawaninB_qiyam` مخرجُ `#eval qawaninB` نُقل إليها، فـ decide تحرسها من التغيّر لا تشهد لها؛ والشاهدُ المستقلّ
  `tahaqquq/test_qawaid.py` §٤: يحسبها من الصور اليدوية بصيغة التحليل بحدّيها (لا بتعريف `Dal.Adad.adad`) ويطابقها.
  طفراتُها P416–P424 في `tahaqquq/tafrat.json` تُفشل `lake build`: P416–P421 وP423–P424 تطفّر السلوك، وP422 تطفّر التوقّع (عددُ قانونٍ في
  `qawaninB_qiyam`) ويقتلها الاختبارُ §٤ أيضًا.

  لا يُدّعى: أنّ الترميزَ وحده يحكم — الحكمُ من القوانين المرمَّزة، وهي من الجدول؛ ولا أنّ القراءةَ والحكمَ منفَّذان على الأعداد كلُّهما:
  في `qiraaB` المحمولاتُ `laIllaAkhir` و`laFathaJarr` و`laIrabBilHarf` والمرورُ `kullMawdi` على محتوى الكلمة والإطار، وفي `hukmB` حدُّ الطبقة
  `fiHadd` والابتداءُ والوصلُ والوقفُ والتركيبُ (`ibtida3`، `waslBase`، `waslMl`، `jisrMadlul`، `waslMadlul`، `waqf3`، `rakkib`) كما هي (وقانونُ الدالّ منفَّذٌ
  بالبتّات في `Nizam/Aqd.lean`، ولم يُوصل هنا)؛ ولا قناعَ نفيٍ N: قوانينُ الصفّ مقدّماتُها موجبةٌ كلُّها.
  بلا sorry ولا axiom ولا native_decide.
-/
import Dal.Adad
import Nizam.Aqd
import Jisr.QawaidSitta

namespace Nizam
namespace QawaidB

open Jisr.Utur Dal Jisr.QawaidJadwal Jisr.QawaidSitta

/-! ## ١. السلسلةُ المقبولة ⟺ المقدّماتُ أصول -/

theorem fahsM_usul (q : Qaida.Qaida Qadiyya) (A : Qadiyya → Bool) :
    ∀ (ms t : List Qadiyya) (rest : List (Qaida.KhatwaM Qadiyya)),
      Qaida.fahsM q A t (ms.map .asl ++ rest) = if ms.all A then Qaida.fahsM q A (t ++ ms) rest else none
  | [], t, rest => by simp
  | m :: ms, t, rest => by
    simp only [List.map_cons, List.cons_append, Qaida.fahsM, Qaida.tatbiqM, List.all_cons]
    by_cases hm : A m = true
    · simp only [hm, ite_true, Bool.true_and]
      rw [fahsM_usul q A ms (t ++ [m]) rest]
      simp
    · simp [hm]

/-- **السلسلةُ بالمحتوى مقبولةٌ ⟺ مقدّماتُ قانونها أصولٌ كلُّها**، لكلّ قانونٍ في القاعدة. -/
theorem maqbul_silsila (q : Qaida.Qaida Qadiyya) (A : Qadiyya → Bool) (r : Qaida.Qanun Qadiyya) (hr : r ∈ q.qawanin) :
    Qaida.maqbulM q A ⟨r.natija, silsila r⟩ = r.muqaddimat.all A := by
  unfold Qaida.maqbulM silsila
  rw [fahsM_usul q A r.muqaddimat [] [.qanun r]]
  cases h : r.muqaddimat.all A
  · simp
  · simp [Qaida.fahsM, Qaida.tatbiqM, hr]

/-- الرخصةُ: قانونٌ ينتج الكلمةَ ومقدّماتُه أصولٌ في الموضع. -/
theorem rukhsa_usul (n : Bool) (hs : List Nat) (w : Kalima) (m : Bool) :
    rukhsa n hs w m = qawanin.any (fun r => yuntij hs w r && r.muqaddimat.all (aslMawdi n hs w m)) := by
  unfold rukhsa
  apply Bool.eq_iff_iff.mpr
  simp only [List.any_eq_true, Bool.and_eq_true]
  constructor
  · rintro ⟨r, hr, hy, hm⟩
    exact ⟨r, hr, hy, by rwa [maqbul_silsila qSitta _ r hr] at hm⟩
  · rintro ⟨r, hr, hy, hm⟩
    exact ⟨r, hr, hy, by rwa [maqbul_silsila qSitta _ r hr]⟩

/-! ## ٢. الترميز -/

/-- **رمزُ الكلمة**: عددُ خلاياها إن كانت كلُّها في المجال، وإلّا فلا رمز. -/
def ramz (c : List Nat) : Option Nat := if c.all (· < 116) then some (Adad.adad c) else none

/-- **مجالُ الترميز:** للكلمة رمزٌ ⟺ خلاياها كلُّها أقلُّ من 116. -/
theorem ramz_majal (c : List Nat) : (ramz c).isSome = c.all (· < 116) := by
  unfold ramz
  split <;> simp_all

/-- **مطابقةُ الرمز مطابقةُ الخلايا**، لصورةٍ في المجال. -/
theorem ramz_sawa (c c' : List Nat) (hc : c.all (· < 116) = true) : (ramz c' == some (Adad.adad c)) = (c' == c) := by
  unfold ramz
  split
  · rename_i h'
    apply Bool.eq_iff_iff.mpr
    simp only [beq_iff_eq, Option.some.injEq]
    constructor
    · intro h
      exact Adad.adad_inj c' c (by simpa using h') (by simpa using hc) h
    · intro h; rw [h]
  · rename_i h'
    have hne : c' ≠ c := by intro e; rw [e] at h'; exact h' hc
    simp [hne]

/-- بتُّ المقدّمة: الصورة 1، الإضافة 2، طلبُ الحالة 4، الصحبة 8؛ والنتيجةُ ليست مقدّمةً في الجدول (16 لا يكون أصلًا). -/
def bitQadiyya : Qadiyya → Nat
  | .sura _ => 1 | .mudaf _ => 2 | .matlub _ _ => 4 | .sahib _ => 8 | .murab _ _ => 16

/-- قناعُ ما لا يُقرأ من الدالّ: بتُّ الصحبة. -/
def qinaLaYuqra : Nat := 8

/-- قناعُ المتطلّبات R⁺. -/
def talab (ms : List Qadiyya) : Nat := ms.foldl (fun t p => t ||| bitQadiyya p) 0

/-- القانونُ عددًا: عددُ صورة نتيجته، وحالتُها، وقناعُ مقدّماته. -/
structure QanunB where
  ramz : Nat
  hala : Nat
  talab : Nat
deriving DecidableEq, Repr

def ramzQanun (r : Qaida.Qanun Qadiyya) : QanunB :=
  match r.natija with
  | .murab h c => ⟨Adad.adad c, h, talab r.muqaddimat⟩
  | _ => ⟨0, 0, 16⟩

def qawaninB : List QanunB := qawanin.map ramzQanun

/-- **القوانينُ أعدادًا** (على الجدول): سبعةٌ وعشرون؛ R⁺ = 7 (الصورة والإضافة وطلبُ الحالة) و15 لـ«ذو» (والصحبة). -/
theorem qawaninB_qiyam : qawaninB =
    [⟨25868, 1, 7⟩, ⟨25648, 0, 7⟩, ⟨25916, 2, 7⟩, ⟨25648, 1, 7⟩, ⟨25648, 0, 7⟩, ⟨25648, 2, 7⟩,
     ⟨16588, 1, 7⟩, ⟨16368, 0, 7⟩, ⟨16636, 2, 7⟩, ⟨16368, 1, 7⟩, ⟨16368, 0, 7⟩, ⟨16368, 2, 7⟩,
     ⟨241628, 1, 7⟩, ⟨241408, 0, 7⟩, ⟨241676, 2, 7⟩, ⟨241408, 1, 7⟩, ⟨241408, 0, 7⟩, ⟨241408, 2, 7⟩,
     ⟨74124, 1, 7⟩, ⟨73904, 0, 7⟩, ⟨74172, 2, 7⟩,
     ⟨11948, 1, 7⟩, ⟨11728, 0, 7⟩, ⟨11996, 2, 7⟩,
     ⟨11020, 1, 15⟩, ⟨10800, 0, 15⟩, ⟨11068, 2, 15⟩] := by decide

/-- علاماتُ الموضع: الاسميّةُ البتُّ 0، والإضافةُ البتُّ 1، والحالةُ h البتُّ h+2. -/
def qinaHalat (hs : List Nat) : Nat := hs.foldl (fun a h => a ||| 1 <<< (h + 2)) 0

def alamat (nom : Bool) (hs : List Nat) (mudaf : Bool) : Nat :=
  qinaHalat hs ||| (if mudaf then 2 else 0) ||| (if nom then 1 else 0)

theorem qinaHalat_bit (k : Nat) : ∀ (hs : List Nat) (a : Nat),
    (hs.foldl (fun a h => a ||| 1 <<< (h + 2)) a).testBit (k + 2) = (a.testBit (k + 2) || hs.contains k)
  | [], a => by simp
  | h :: hs, a => by
    rw [List.foldl_cons, qinaHalat_bit k hs, Nat.testBit_or]
    have hb : (1 <<< (h + 2)).testBit (k + 2) = (k == h) := by
      apply Bool.eq_iff_iff.mpr
      rw [Aqd.bit_wahid, beq_iff_eq]; omega
    rw [hb, List.contains_cons, Bool.or_assoc]

theorem qinaHalat_sifr : ∀ (hs : List Nat) (a : Nat) (i : Nat), i < 2 →
    (hs.foldl (fun a h => a ||| 1 <<< (h + 2)) a).testBit i = a.testBit i
  | [], a, i, _ => rfl
  | h :: hs, a, i, hi => by
    rw [List.foldl_cons, qinaHalat_sifr hs _ i hi, Nat.testBit_or]
    have : (1 <<< (h + 2)).testBit i = false := by
      cases hb : (1 <<< (h + 2)).testBit i
      · rfl
      · rw [Aqd.bit_wahid] at hb; omega
    rw [this, Bool.or_false]

/-- **بتّاتُ الموضع تحمل ما يُقرأ منه**: الاسميّة، والإضافة، وكلَّ حالةٍ يطلبها. -/
theorem alamat_bitat (nom : Bool) (hs : List Nat) (mudaf : Bool) :
    (alamat nom hs mudaf).testBit 0 = nom ∧ (alamat nom hs mudaf).testBit 1 = mudaf ∧
    ∀ h, (alamat nom hs mudaf).testBit (h + 2) = hs.contains h := by
  unfold alamat qinaHalat
  refine ⟨?_, ?_, ?_⟩
  · rw [Nat.testBit_or, Nat.testBit_or, qinaHalat_sifr hs 0 0 (by decide)]
    cases mudaf <;> cases nom <;> decide
  · rw [Nat.testBit_or, Nat.testBit_or, qinaHalat_sifr hs 0 1 (by decide)]
    cases mudaf <;> cases nom <;> decide
  · intro h
    rw [Nat.testBit_or, Nat.testBit_or, qinaHalat_bit h hs 0]
    have h4 : 4 ≤ 2 ^ (h + 2) := by
      rw [Nat.pow_succ, Nat.pow_succ]; have := Nat.two_pow_pos h; omega
    have h1 : (if mudaf = true then 2 else 0 : Nat).testBit (h + 2) = false := by
      apply Nat.testBit_lt_two_pow; cases mudaf <;> simp <;> omega
    have h2 : (if nom = true then 1 else 0 : Nat).testBit (h + 2) = false := by
      apply Nat.testBit_lt_two_pow; cases nom <;> simp <;> omega
    rw [h1, h2]; simp

/-! ## ٣. المنفّذ -/

/-- قناعُ الأصول P لقانونٍ حالتُه h في موضعٍ علاماتُه a: الصورة، والإضافة، وطلبُ الحالة إن كان اسميًّا يطلبها. -/
def usulB (a h : Nat) : Nat :=
  1 ||| (if a.testBit 1 then 2 else 0) ||| (if a.testBit 0 && a.testBit (h + 2) then 4 else 0)

/-- **الناقص** R⁺ ∖ P. -/
def naqsB (a : Nat) (q : QanunB) : Nat := q.talab ^^^ (q.talab &&& usulB a q.hala)

/-- القانونُ ينتج الكلمةَ (رمزُها رمزُ صورته) بحالةٍ يطلبها الموضع. -/
def yuntijB (k : Option Nat) (a : Nat) (q : QanunB) : Bool := k == some q.ramz && a.testBit (q.hala + 2)

/-- **الرخصةُ على الأعداد:** قانونٌ ينتج الكلمةَ وناقصُه صفر. -/
def rukhsaB (k : Option Nat) (a : Nat) : Bool := qawaninB.any fun q => yuntijB k a q && naqsB a q == 0

/-- **الوقفُ على الأعداد:** قانونٌ ينتج الكلمة، في R⁺ ما لا يُقرأ، وناقصُه داخله. -/
def mawqufB (k : Option Nat) (a : Nat) : Bool :=
  qawaninB.any fun q => yuntijB k a q && q.talab &&& qinaLaYuqra != 0 && (naqsB a q ||| qinaLaYuqra) == qinaLaYuqra

/-- أسماءُ بتّات الناقص (وبتُّ الصورة لا يقع فيه: مطابقتُها شرطٌ في `yuntijB`). -/
def asmaNaqs (x : Nat) : List String :=
  (if x.testBit 1 then ["الإضافة"] else []) ++
  (if x.testBit 2 then ["طلب الحالة"] else []) ++ (if x.testBit 3 then ["الصحبة"] else [])

/-- نواقصُ القوانين التي تنتج الكلمةَ في الموضع: سببُ ما لم يُرخَّص. -/
def naqsMawdi (k : Option Nat) (a : Nat) : List Nat := (qawaninB.filter (yuntijB k a)).map (naqsB a)

/-! ## ٤. حفظُ العمليّة -/

/-- قانونُ الجدول بمكوّناته: المقدّماتُ ثلاثٌ أو أربعٌ بالصحبة، والصورةُ في المجال. -/
theorem qanun_bitat (s : Saff) (v : Wajh) (h : Nat) :
    ramzQanun (qanun s v h) = ⟨Adad.adad (suraBi s v h), h, if s.sahib then 15 else 7⟩ := by
  cases hs : s.sahib <;> simp [ramzQanun, qanun, talab, bitQadiyya, hs]

private theorem majal_qawanin : ∀ s ∈ sitta, ∀ v ∈ wujuh s, ∀ h ∈ halat, (suraBi s v h).all (· < 116) = true := by decide

private theorem naqs_7_15 (m n x : Bool) :
    ((if x then 15 else 7) ^^^ ((if x then 15 else 7) &&&
      (1 ||| (if m then 2 else 0) ||| (if n then 4 else 0))) == (0 : Nat)) = (m && n && !x) := by
  cases m <;> cases n <;> cases x <;> decide

private theorem waqf_7_15 (m n x : Bool) :
    ((if x then 15 else 7) &&& qinaLaYuqra != (0 : Nat) &&
      (((if x then 15 else 7) ^^^ ((if x then 15 else 7) &&&
        (1 ||| (if m then 2 else 0) ||| (if n then 4 else 0)))) ||| qinaLaYuqra) == qinaLaYuqra) = (x && m && n) := by
  cases m <;> cases n <;> cases x <;> decide

private theorem qanun_fi (r : Qaida.Qanun Qadiyya) (hr : r ∈ qawanin) :
    ∃ s ∈ sitta, ∃ v ∈ wujuh s, ∃ h ∈ halat, r = qanun s v h := by
  simp only [qawanin, List.mem_flatMap, List.mem_map] at hr
  obtain ⟨s, hs, v, hv, h, hh, rfl⟩ := hr
  exact ⟨s, hs, v, hv, h, hh, rfl⟩

/-- **حفظُ العمليّة — الرخصة:** لكلّ موضعٍ وكلّ كلمة، الرخصةُ على رموزهما هي الرخصةُ بالمحتوى. -/
theorem rukhsaB_sawa (n : Bool) (hs : List Nat) (w : Kalima) (m : Bool) :
    rukhsaB (ramz w.khalaya) (alamat n hs m) = rukhsa n hs w m := by
  rw [rukhsa_usul]
  unfold rukhsaB qawaninB
  rw [List.any_map]
  apply Bool.eq_iff_iff.mpr
  simp only [List.any_eq_true, Function.comp]
  obtain ⟨b0, b1, bh⟩ := alamat_bitat n hs m
  have key : ∀ r ∈ qawanin, (yuntijB (ramz w.khalaya) (alamat n hs m) (ramzQanun r) &&
      naqsB (alamat n hs m) (ramzQanun r) == 0) = (yuntij hs w r && r.muqaddimat.all (aslMawdi n hs w m)) := by
    intro r hr
    obtain ⟨s, hs', v, hv, h, hh, rfl⟩ := qanun_fi r hr
    rw [qanun_bitat]
    unfold yuntijB naqsB usulB
    simp only
    rw [ramz_sawa _ _ (majal_qawanin s hs' v hv h hh), b0, b1, bh, naqs_7_15]
    unfold yuntij qanun
    by_cases hc : suraBi s v h = w.khalaya
    · cases hsa : s.sahib <;> simp_all [aslMawdi]
    · have e1 : (w.khalaya == suraBi s v h) = false := Bool.eq_false_iff.mpr (fun e => hc (beq_iff_eq.mp e).symm)
      have e2 : (suraBi s v h == w.khalaya) = false := Bool.eq_false_iff.mpr (fun e => hc (beq_iff_eq.mp e))
      cases hsa : s.sahib <;> simp [aslMawdi, e1, e2]
  constructor
  · rintro ⟨r, hr, e⟩; exact ⟨r, hr, by rw [← key r hr]; exact e⟩
  · rintro ⟨r, hr, e⟩; exact ⟨r, hr, by rw [key r hr]; exact e⟩

/-- **حفظُ العمليّة — الوقف:** لكلّ موضعٍ وكلّ كلمة. -/
theorem mawqufB_sawa (n : Bool) (hs : List Nat) (w : Kalima) (m : Bool) :
    mawqufB (ramz w.khalaya) (alamat n hs m) = mawquf n hs w m := by
  unfold mawqufB mawquf qawaninB
  rw [List.any_map]
  apply Bool.eq_iff_iff.mpr
  simp only [List.any_eq_true, Function.comp]
  obtain ⟨b0, b1, bh⟩ := alamat_bitat n hs m
  have key : ∀ r ∈ qawanin, (yuntijB (ramz w.khalaya) (alamat n hs m) (ramzQanun r) &&
      (ramzQanun r).talab &&& qinaLaYuqra != 0 &&
      (naqsB (alamat n hs m) (ramzQanun r) ||| qinaLaYuqra) == qinaLaYuqra) =
      (yuntij hs w r && r.muqaddimat.any laYuqra &&
        r.muqaddimat.all (fun x => laYuqra x || aslMawdi n hs w m x)) := by
    intro r hr
    obtain ⟨s, hs', v, hv, h, hh, rfl⟩ := qanun_fi r hr
    rw [qanun_bitat]
    unfold yuntijB naqsB usulB
    simp only
    rw [ramz_sawa _ _ (majal_qawanin s hs' v hv h hh), b0, b1, bh, Bool.and_assoc, waqf_7_15]
    unfold yuntij qanun
    by_cases hc : suraBi s v h = w.khalaya
    · cases hsa : s.sahib <;> simp_all [aslMawdi, laYuqra]
    · have e1 : (w.khalaya == suraBi s v h) = false := Bool.eq_false_iff.mpr (fun e => hc (beq_iff_eq.mp e).symm)
      have e2 : (suraBi s v h == w.khalaya) = false := Bool.eq_false_iff.mpr (fun e => hc (beq_iff_eq.mp e))
      cases hsa : s.sahib <;> simp [aslMawdi, laYuqra, e1, e2]
  constructor
  · rintro ⟨r, hr, e⟩; exact ⟨r, hr, by rw [← key r hr]; exact e⟩
  · rintro ⟨r, hr, e⟩; exact ⟨r, hr, by rw [key r hr]; exact e⟩

/-- القراءةُ بالجدول منفَّذةً على الأعداد: `qiraaSitta` بعينها والرخصةُ والوقفُ من الرموز. -/
def qiraaB (u : Itar3) : Jisr.Utur.Hukm :=
  if kullMawdi u (fun n hs w m => laIllaAkhir n hs w m || rukhsaB (ramz w.khalaya) (alamat n hs m)) &&
     kullMawdi u laFathaJarr &&
     kullMawdi u (fun n hs w m => laIrabBilHarf n hs w m || rukhsaB (ramz w.khalaya) (alamat n hs m)) then .murakhkhas
  else if kullMawdi u (fun n hs w m => laIrabBilHarf n hs w m || rukhsaB (ramz w.khalaya) (alamat n hs m) ||
      mawqufB (ramz w.khalaya) (alamat n hs m)) then .laHukm
  else .mumtani

/-- **القراءةُ على الأعداد هي القراءةُ بالمحتوى** لكلّ إطار. -/
theorem qiraaB_sawa (u : Itar3) : qiraaB u = qiraaSitta u := by
  unfold qiraaB qiraaSitta
  simp only [rukhsaB_sawa, mawqufB_sawa]

/-- حكمُ الطبقة الثالثة بصفّ الأسماء الستّة والقراءةُ فيه على الأعداد. -/
def hukmB (u : Itar3) : Jisr.Utur.Hukm :=
  if fiHadd u then
    damm (ofBool (ibtida3 u))
      (damm (damm (hukmTarkib (rakkib u.kalimat))
        (damm (ofBool (waslBase u && waslMl u && jisrMadlul u)) (damm (qiraaB u) (waslMadlul u.isnad))))
        (ofBool (waqf3 u)))
  else .laHukm

/-- **وحكمُها حكمُ `hukmSitta`** لكلّ إطار. -/
theorem hukmB_sawa (u : Itar3) : hukmB u = hukmSitta u := by
  unfold hukmB hukmSitta
  rw [qiraaB_sawa]

/-! ## ٥. على الشاهد -/

/-- **المواضعُ الثمانيةَ عشرَ** (`mawadiShawahid`) على الأعداد: الرخصةُ والوقفُ من الرموز كما في الجدول — حسابٌ مستقلٌّ عن `rukhsaB_sawa`. -/
theorem mawadi_bitat : mawadiShawahid.all (fun (_, w, h, m, r, q) =>
    rukhsaB (ramz w.khalaya) (alamat true [h] m) == r && mawqufB (ramz w.khalaya) (alamat true [h] m) == q) = true := by
  decide

/-- **أسبابُ ما لم يُرخَّص بأسمائها:** «ذُو» مرفوعًا في موضع الإضافة ناقصُها الصحبة؛ و«أَبُو» مرفوعًا بلا إضافةٍ ناقصُها الإضافة؛ و«أَبُو»
مرفوعًا مضافًا لا ناقصَ له؛ و«أَبَا» (صورةُ أربعة قوانين: نصبُ التمام والقصرُ بأحواله الثلاث) في موضع رفعٍ بلا إضافةٍ تُسرد نواقصُ قانونِ
حالته وحده (قصرُ الرفع: الإضافة) — فاختبارُ الحالة في `yuntijB` يحدّد ما يُسرد. -/
theorem naqs_shawahid :
    (naqsMawdi (ramz dhuK.khalaya) (alamat true [1] true)).map asmaNaqs = [["الصحبة"]] ∧
    (naqsMawdi (ramz abuK.khalaya) (alamat true [1] false)).map asmaNaqs = [["الإضافة"]] ∧
    naqsMawdi (ramz abuK.khalaya) (alamat true [1] true) = [0] ∧
    (naqsMawdi (ramz abaK.khalaya) (alamat true [1] false)).map asmaNaqs = [["الإضافة"]] := by
  decide

end QawaidB
end Nizam
