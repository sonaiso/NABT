import A116.SidqData
import A116.Istiqama

/-!
# الصدقُ عند السيرافيّ (ADR ٨٩، أمرُ المالك 2026-10-17)

السندُ شرحُ السيرافيّ المختوم على باب الاستقامة (Sham19Y0017726، الأسطرُ 1-based، مراسيه في `SidqData.marasi`):

* س5081–5082: «وإنّما خصّ "حملت الجبل" و"شربت ماء البحر" بالكذب، لأنّ ظاهرهما يدلّ على كذب قائلهما، قبل التصفّح
  والبحث». وس5064–5065: ويلحق بهما «صعدت السماء».
* س5084–5085: «وإلّا فكلُّ كلامٍ… كان مخبَرُه على خلاف ما يوجبه الظاهر فهو كذب، علم أو لم يعلم، كقول القائل: لقيت زيدًا
  اليوم… إذا لم يكن الأمرُ على ما قال، فهو مستقيمٌ كذب».
* س5103–5112: المحالُ الكذب كذبٌ، خلافًا للأخفش، و«الكذبُ إنّما هو الإخبار عن الشيء بخلاف ما هو به».
* س5122: «غير أنّه مثّل الأول بشيءٍ هو محالٌ كذبٌ أيضًا».
* س5125–5129: «فأمّا المحالُ الذي ليس بكذب، فاللفظُ الذي يستحيل في الأمر وفي الاستفهام… كقولك لمن تأمره: قم أمس…
  فالمحالُ على ضربين: كذبٌ وغيرُ كذب، والكذبُ على ضربين: محالٌ وغيرُ محال».
* س5091–5092: «كي قد جُعلت بمعنى أن أو بمعنى اللام… فحكمُ الفعل أن يليها دون الاسم».

## ما يُبنى

**الطبقة (أ): مصدرُ معرفة الكذب ثلاثة.**
* **اللفظ:** المحالُ في الخبر كذبٌ يُعرف من اللفظ وحدَه.
* **المعلوماتُ السابقة:** الكذبُ الظاهرُ «قبل التصفّح والبحث» يُعرف بصفٍّ ثلاثيٍّ من المودَع.
* **الواقع:** ما سوى ذلك لا يُعرف إلّا بشاهد واقع، «علم أو لم يعلم». فبلا شاهدٍ «لا حكم».
* ولا صدقَ ولا كذبَ إلّا في الخبر.

**النسبةُ ثلاثيّة.** جنسُ الفاعل، والفعل، وجنسُ المفعول. فالصفةُ المطلقة «الجبلُ لا يُحمل» تحكم بكذب «وَحُمِلَتِ
الْأَرْضُ وَالْجِبَالُ» (المصحف المختوم س5337) وفاعلُها غيرُ مذكور، والثلاثيّةُ لا تحكم عليها.

**الطبقة (ب): مرجعُ أحكامٍ منقول.** شواهدُ السيرافيّ الثلاثة للكذب الظاهر يُقاس عليها الحكم. وصفوفُ المسوّدة
(`musawwada`) لا يقرؤها الحكم إلّا بتوقيع المالك (`signed`).
-/

namespace A116.SidqSirafi

open A116.Istiqama

/-- نوعُ الكلام: خبرٌ أو أمرٌ أو استفهام. -/
inductive Naw | khabar | amr | istifham
  deriving DecidableEq, Repr

/-- مصدرُ معرفة الحكم. -/
inductive Masdar | lafz | malumat | waqi
  deriving DecidableEq, Repr

/-- النسبةُ الثلاثيّة. -/
structure Nisba3 where
  fail : String
  fil : String
  mafool : String
  ijab : Bool
  deriving DecidableEq, Repr

/-- الحكمُ ثلاثيّ، والصادقُ والكاذبُ يحملان مصدرهما. -/
inductive Hukm
  | sadiq (m : Masdar)
  | kadhib (m : Masdar)
  | laHukm
  deriving DecidableEq, Repr

/-- الشاهدُ من الصفوف: الفاعلُ والفعلُ والمفعولُ كالنسبة. -/
def yashhad (n : Nisba3) (r : Saff3) : Bool :=
  r.fail == n.fail && r.fil == n.fil && r.mafool == n.mafool

/-- حكمُ المعلومات السابقة وحدَها. -/
def bilMalumat (rows : List Saff3) (n : Nisba3) : Option Bool :=
  (rows.find? (yashhad n)).map (fun r => r.ijab == n.ijab)

/-- الحكم: لا حكمَ في غير الخبر؛ والمحالُ في الخبر كذبٌ من اللفظ؛ ثمّ المعلوماتُ السابقة؛ ثمّ الواقع. -/
def hukm (rows : List Saff3) (naw : Naw) (k : List Juz) (n : Option Nisba3) (waqi : Option Bool) : Hukm :=
  if naw != .khabar then .laHukm
  else if muhalB k then .kadhib .lafz
  else match n.bind (bilMalumat rows) with
    | some true => .sadiq .malumat
    | some false => .kadhib .malumat
    | none => match waqi with
      | some true => .sadiq .waqi
      | some false => .kadhib .waqi
      | none => .laHukm

/-- لا صدقَ ولا كذبَ في غير الخبر («موضعٌ لا يقع فيه الكذب»). -/
theorem khabar_faqat (rows : List Saff3) (naw : Naw) (k : List Juz) (n : Option Nisba3) (w : Option Bool)
    (h : naw ≠ .khabar) : hukm rows naw k n w = .laHukm := by
  cases naw <;> simp_all [hukm]

/-- المحالُ في الخبر كذبٌ من اللفظ، بلا معلومةٍ ولا واقع (السيرافيّ خلافًا للأخفش). -/
theorem muhal_khabar_kadhib (rows : List Saff3) (k : List Juz) (n : Option Nisba3) (w : Option Bool)
    (h : muhalB k = true) : hukm rows .khabar k n w = .kadhib .lafz := by
  simp [hukm, h]

/-- «قم أمس» محالٌ لا كذب: الأمرُ مستقبلٌ، فمع «أمس» محال، ولا حكمَ عليه. -/
theorem qum_ams :
    muhalB [.fil .mustaqbal, .zarf .ams] = true ∧
    hukm [] .amr [.fil .mustaqbal, .zarf .ams] none none = .laHukm := by decide

/-- شاهدُ المحال عند سيبويه «أتيتك غدا وسآتيك أمس» محالٌ كذبٌ أيضًا (س5122). -/
theorem sibawayh_muhal_kadhib :
    hukm [] .khabar (juz Istiqama.muhal) none none = .kadhib .lafz := by decide

/-- الكذبُ بالمعلومات لا يكون إلّا بصفٍّ شاهدٍ إيجابُه خلافُ إيجاب النسبة. -/
theorem kadhib_malumat_bi_shahid (rows : List Saff3) (k : List Juz) (n : Nisba3) (w : Option Bool)
    (h : hukm rows .khabar k (some n) w = .kadhib .malumat) :
    ∃ r ∈ rows, yashhad n r = true ∧ (r.ijab == n.ijab) = false := by
  unfold hukm at h
  simp only [bne_self_eq_false, Bool.false_eq_true, ↓reduceIte, Option.bind_some] at h
  split at h
  · cases h
  · split at h
    · cases h
    · rename_i hb
      unfold bilMalumat at hb
      cases hf : rows.find? (yashhad n) with
      | none => simp [hf] at hb
      | some r =>
        simp [hf] at hb
        exact ⟨r, List.mem_of_find?_eq_some hf, List.find?_some hf, by simp [hb]⟩
    · split at h <;> cases h

/-- الكذبُ بالواقع لا يكون إلّا بشاهد واقعٍ ينفي. -/
theorem kadhib_waqi_bi_shahid (rows : List Saff3) (k : List Juz) (n : Option Nisba3) (w : Option Bool)
    (h : hukm rows .khabar k n w = .kadhib .waqi) : w = some false := by
  unfold hukm at h
  simp only [bne_self_eq_false, Bool.false_eq_true, ↓reduceIte] at h
  split at h
  · cases h
  · split at h
    · cases h
    · cases h
    · split at h
      · cases h
      · rfl
      · cases h

/-- «لقيت زيدًا اليوم» بلا صفٍّ ولا شاهد واقع «لا حكم»: «علم أو لم يعلم». -/
theorem laqitu_zaydan (rows : List Saff3) :
    hukm rows .khabar [.fil .madi, .ism, .ism] (some ⟨"الإنسان", "لقي", "زيد", true⟩) none =
      (match bilMalumat rows ⟨"الإنسان", "لقي", "زيد", true⟩ with
       | some true => .sadiq .malumat
       | some false => .kadhib .malumat
       | none => .laHukm) := by
  simp only [hukm, bne_self_eq_false, Bool.false_eq_true, ↓reduceIte, Option.bind_some]
  have : muhalB [.fil .madi, .ism, .ism] = false := by decide
  rw [this]
  rfl

/-- وعلى المسوّدة نفسِها «لقيت زيدًا اليوم» «لا حكم»: لا صفَّ له ولا شاهدَ واقع. -/
theorem laqitu_zaydan_la_hukm :
    hukm musawwada .khabar [.fil .madi, .ism, .ism] (some ⟨"الإنسان", "لقي", "زيد", true⟩) none =
      .laHukm := by decide

/-! ## النسبةُ ثلاثيّة -/

/-- الصفةُ المطلقة: تُطابق الفعلَ والمفعولَ وتنسى الفاعل. -/
def bilMalumatMutlaq (rows : List Saff3) (n : Nisba3) : Option Bool :=
  (rows.find? (fun r => r.fil == n.fil && r.mafool == n.mafool)).map (fun r => r.ijab == n.ijab)

/-- «وَحُمِلَتِ الْأَرْضُ وَالْجِبَالُ» وفاعلُها غيرُ مذكور. -/
def hamlAlJibal : Nisba3 := ⟨"", "حمل", "الجبل", true⟩

/-- الصفةُ المطلقة تحكم بكذب خبر المصحف، والثلاثيّةُ لا تحكم عليه. -/
theorem thulathi_la_yahkum :
    bilMalumatMutlaq musawwada hamlAlJibal = some false ∧
    bilMalumat musawwada hamlAlJibal = none := by decide

/-! ## الطبقة (ب): شواهدُ السيرافيّ مرجعًا -/

/-- شواهدُ الكذب الظاهر: الفاعلُ المتكلّمُ إنسانٌ بالمقام (`MUTAKALLIM_INSAN_DECLARED`). -/
def shawahid : List (Nat × List Juz × Nisba3) :=
  [(5064, [.fil .madi, .ism], ⟨"الإنسان", "حمل", "الجبل", true⟩),
   (5064, [.fil .madi, .ism, .ism], ⟨"الإنسان", "شرب", "ماء البحر", true⟩),
   (5065, [.fil .madi, .ism], ⟨"الإنسان", "صعد", "السماء", true⟩)]

/-- كم شاهدًا يحكم عليه بالكذب من المعلومات، على صفوفٍ معطاة. -/
def mahkum (rows : List Saff3) : Nat :=
  shawahid.countP (fun (_, k, n) => hukm rows .khabar k (some n) none == .kadhib .malumat)

/-- القياسُ على مرجع السيرافيّ: صفرٌ قبل التوقيع، وثلاثةٌ بعده. -/
theorem qiyas : mahkum rows3 = if signed then 3 else 0 := by decide

/-- والمسوّدةُ تحكم على الشواهد الثلاثة كلِّها بالكذب من المعلومات. -/
theorem musawwada_tahkum : mahkum musawwada = 3 := by decide

/-- والحكمُ بلا صفوفٍ لا يحكم على شيءٍ منها: الغيابُ «لا حكم». -/
theorem bila_sufuf : mahkum [] = 0 := by decide

/-- وصفوفُ المسوّدة كلُّها بشواهد السيرافيّ في مراسيه. -/
theorem sufuf_bi_marasi :
    musawwada.all (fun r => marasi.any (fun (n, _) => n == r.shahid)) = true := by decide

/-- القسمةُ الرباعيّة (س5129): المحالُ كذبٌ وغيرُ كذب، والكذبُ محالٌ وغيرُ محال. -/
theorem qisma_rubaiyya :
    hukm musawwada .khabar (juz Istiqama.muhalKadhib) none none = .kadhib .lafz ∧
    hukm musawwada .amr [.fil .mustaqbal, .zarf .ams] none none = .laHukm ∧
    hukm musawwada .khabar [.fil .madi, .ism] (some ⟨"الإنسان", "حمل", "الجبل", true⟩) none =
      .kadhib .malumat ∧
    hukm musawwada .khabar (juz Istiqama.hasan) none none = .laHukm := by decide

end A116.SidqSirafi
