import A116.QismKhanat
import A116.Awamil

/-!
# سدُّ الفجوة: علاماتُ العوامل المائة والأوزان قيودًا (ADR ١٠٧)

يبني على `QismKhanat` (ADR ١٠٦). الفجوةُ بين ما تعيّنه علاماتُه (4.80٪) وسقفِ الخانات (99.24٪). وهنا ثلاثةُ أشياء:

1. **إضافةُ علامةٍ تقطع ولا تزيد** (`cands_append_sub`).
   * والمعيَّنُ يبقى معيَّنًا بقسمه، أو يصير «لا حكم» إن تعارضت علامتان (`muayyan_baqi`). ولا ينقلب قسمًا آخر.
   * و`khata_qari_le` يضمن الخطأَ مهما زادت العلامات.
2. **علامةُ ما بعد العامل** تُبقي قسمَ معموله `Awamil.target` بعينه (`next_tubqi`). فالقيدُ مأخوذٌ من الجدول المبرهَن، لا مكتوبٌ
   باليد. فما بعد حرف الجرّ اسم (`next_jarr`، و`Awamil.jarr_targets_ism`)، وما بعد الجازم فعل.
3. **الموافقة**: صفُّ العامل حروفٌ وحركاتٌ مكتوبةٌ أو حرّة، والكلمةُ توافقه إن تساوت الحروفُ ووافقت كلُّ حركةٍ مكتوبة
   (`muwafiq`). فـ«مِنْ» توافق «من» ولا توافق «مَن».

والشواهدُ على تعارضاتٍ يعرفها النحاة:
* «مِنْ أَنْ»: ما بعد الجارّ اسم، و«أنْ» حرف. والمرجعُ حرف، و«أنْ» وصلتُها في تأويل مصدر، فالقارئُ «لا حكم» ولا يخمّن
  (`min_an`).
* «أَعْلَمُ» مضارعًا للمتكلّم، و«أَعْلَمُ» اسمَ تفضيل: خاناتٌ واحدة (`afal_yashtabih`).
* «قَاتِلْ» أمرًا يوافق قالبَ فاعِل (`amr_faail_yashtabih`).

وأرقامُ المصحف في `docs/qism-khanat/result-2.json`، على تسجيلٍ مسبق (`PREREG-2.md`).
-/

namespace A116.QismAwamil

open A116 A116.QismKhanat

variable {α : Type}

/-- **إضافةُ العلامات تقطع ولا تزيد**. -/
theorem cands_append_sub (as bs : List (Alama α)) (x : α) (q : Qism)
    (h : q ∈ cands (as ++ bs) x) : q ∈ cands as x := by
  rw [mem_cands] at *
  exact fun a ha => h a (List.mem_append_left _ ha)

theorem cands_append_iff (as bs : List (Alama α)) (x : α) (q : Qism) :
    q ∈ cands (as ++ bs) x ↔ q ∈ cands as x ∧ q ∈ cands bs x := by
  simp only [mem_cands, List.mem_append]
  constructor
  · intro h; exact ⟨fun a ha => h a (Or.inl ha), fun a ha => h a (Or.inr ha)⟩
  · rintro ⟨h₁, h₂⟩ a (ha | ha)
    · exact h₁ a ha
    · exact h₂ a ha

theorem cands_nodup (as : List (Alama α)) (x : α) : (cands as x).Nodup :=
  (List.filter_sublist (l := kull)).nodup (by decide)

/-- **المعيَّنُ يبقى أو يصير «لا حكم»**: علامةٌ مضافةٌ لا تنقله إلى قسمٍ آخر ولا تجعله محتمَلًا. -/
theorem muayyan_baqi (as bs : List (Alama α)) (x : α) (q : Qism)
    (h : qiraa as x = .muayyan q) :
    qiraa (as ++ bs) x = .muayyan q ∨ qiraa (as ++ bs) x = .laHukm := by
  have hl : cands as x = [q] := by
    unfold qiraa at h
    generalize cands as x = l at h
    match l, h with
    | [m], h => simp only [Iqtiran.mantuq, Iqtiran.Mantuq.muayyan.injEq] at h; rw [h]
    | [], h => simp [Iqtiran.mantuq] at h
    | _ :: _ :: _, h => simp [Iqtiran.mantuq] at h
  have hs : ∀ r, r ∈ cands (as ++ bs) x → r = q := by
    intro r hr; have := cands_append_sub as bs x r hr; rw [hl] at this; simpa using this
  unfold qiraa
  generalize hm : cands (as ++ bs) x = m at hs
  match m, hs with
  | [], _ => exact Or.inr rfl
  | [r], hs => rw [hs r (by simp)]; exact Or.inl rfl
  | r :: s :: rest, hs =>
    have hn := cands_nodup (as ++ bs) x
    rw [hm] at hn
    have := List.nodup_cons.mp hn
    exact absurd (by rw [hs r (by simp), hs s (by simp)]; simp) this.1

/-! ## العواملُ المائة -/

def ofTarkib : Tarkib.Qism → Qism
  | .ism => .ism
  | .fil => .fil
  | .harf => .harf

/-- علامةُ ما بعد عاملٍ أثرُه `a`: تُطلق إذا وافق السابقُ صفَّه، وتُبقي قسمَ معموله من `Awamil.target`. -/
def next (a : Awamil.Athar) (yuwafiq : Option (List Cell) → Bool) : Alama (List Cell × Option (List Cell)) where
  tutabiq x := yuwafiq x.2 && (Awamil.target a).isSome
  tubqi := ((Awamil.target a).map ofTarkib).toList

/-- **قيدُ ما بعد العامل هو `Awamil.target` بعينه**. -/
theorem next_tubqi (a : Awamil.Athar) (y : Option (List Cell) → Bool) (q : Tarkib.Qism)
    (h : Awamil.target a = some q) : (next a y).tubqi = [ofTarkib q] := by
  simp [next, h]

theorem next_jarr (y : Option (List Cell) → Bool) : (next .jarr y).tubqi = [.ism] :=
  next_tubqi .jarr y .ism rfl

theorem next_jazm (y : Option (List Cell) → Bool) : (next .jazmFil y).tubqi = [.fil] :=
  next_tubqi .jazmFil y .fil rfl

/-- العطفُ والمهمَلُ لا قسمَ لمعمولهما: العلامةُ لا تُطلق. -/
theorem next_tabi_la (y : Option (List Cell) → Bool) (x : List Cell × Option (List Cell)) :
    (next .tabi y).tutabiq x = false := by
  simp [next, Awamil.target]

/-- صفُّ العامل: لكلّ حرفٍ حاملُه وحالاتُه المسموحة (`none` حرّة). -/
abbrev Saff := List (Fin carrierCount × Option (List Haraka))

def muwafiq : Saff → List Cell → Bool
  | [], [] => true
  | (c, h) :: s, w :: ws => w.carrier == c && (h.all fun hs => hs.contains w.haraka) && muwafiq s ws
  | _, _ => false

def ch (c : Char) : Fin carrierCount := Ladder.carrierOf c

/-- «من» بلا حركة، و«مَن» بالفتح. -/
def saffMin : Saff := [(ch 'م', none), (ch 'ن', none)]
def saffMan : Saff := [(ch 'م', some [.fatha]), (ch 'ن', none)]
/-- «أنْ»: الهمزةُ أوّلًا بفتحٍ أو ضمّ (`HAMZA_SEAT_VOWEL_DECLARED`)، والنونُ ساكنة. -/
def saffAn : Saff := [(ch 'ء', some [.fatha, .damma]), (ch 'ن', some [.sukun])]

theorem muwafiq_shawahid :
    muwafiq saffMin (cell "مِنْ") = true ∧ muwafiq saffMin (cell "مَنْ") = true ∧
    muwafiq saffMan (cell "مِنْ") = false ∧ muwafiq saffMan (cell "مَنْ") = true ∧
    muwafiq saffAn (cell "ءَنْ") = true ∧ muwafiq saffAn (cell "ءِنْ") = false := by
  decide +kernel

/-- علامةُ العامل نفسِه: «أنْ» حرف. -/
def ownAn : Alama (List Cell × Option (List Cell)) where
  tutabiq x := muwafiq saffAn x.1
  tubqi := [.harf]

def nextJarr : Alama (List Cell × Option (List Cell)) :=
  next .jarr (fun p => p.any (muwafiq [(ch 'م', some [.kasra]), (ch 'ن', none)]))

/-- **«مِنْ أَنْ» «لا حكم»**: ما بعد الجارّ اسم و«أنْ» حرف، والمصدرُ المؤوَّل لا تراه الخانات. فالقارئُ لا يخمّن. -/
theorem min_an : qiraa [nextJarr, ownAn] (cell "ءَنْ", some (cell "مِنْ")) = .laHukm := by
  decide +kernel

theorem ba_dar : qiraa [nextJarr] (cell "دَاْرِ", some (cell "مِنْ")) = .muayyan .ism := by
  decide +kernel

/-! ## الأوزان -/

/-- قالبُ المضارع الأوّل من `amr.csv` («يَصْبَرُ» بأصولٍ متغيّرة) وحرفُ المتكلّم: ءَ، R1 ساكن، R2 مفتوح، R3 حرّ. -/
def mudariAfal (w : List Cell) : Bool :=
  match w with
  | [p, r1, r2, _] => p == ⟨ch 'ء', .fatha⟩ && r1.haraka == .sukun && r2.haraka == .fatha
  | _ => false

/-- اسمُ التفضيل «أَفْعَلُ» (أَحْسَنُ، أَكْبَرُ) على القالب نفسِه. -/
theorem afal_yashtabih :
    mudariAfal (cell "ءَعْلَمُ") = true ∧ mudariAfal (cell "ءَحْسَنُ") = true ∧
    mudariAfal (cell "ءَكْبَرُ") = true := by
  decide +kernel

/-- قالبُ فاعِل: R1 مفتوح، ثمّ ألف، ثمّ R2 مكسور، ثمّ R3 حرّ. -/
def faail (w : List Cell) : Bool :=
  match w with
  | [r1, a, r2, _] => r1.haraka == .fatha && a == ⟨ch 'ا', .sukun⟩ && r2.haraka == .kasra
  | _ => false

/-- أمرُ فاعَلَ («قَاتِلْ»، «جَاهِدِ») يوافق قالبَ فاعِل. -/
theorem amr_faail_yashtabih :
    faail (cell "قَاْتِلْ") = true ∧ faail (cell "جَاْهِدِ") = true ∧ faail (cell "كَاْتِبُ") = true := by
  decide +kernel

end A116.QismAwamil
