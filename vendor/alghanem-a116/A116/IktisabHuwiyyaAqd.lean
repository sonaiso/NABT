import A116.IktisabHuwiyyaData

/-!
# ما اكتسبه المتعلّم من قوانين الهويّة، مبرهَنًا على المجال كلِّه (ADR ١٢٤)

لكلّ قانون (الوجود، الابتداء، المبتدأ به) أربعُ مبرهناتٍ على البرج كلِّه (116 خانة) بـ`decide +kernel`:

* **التعيين** (`*_yuayyin`): الأوصافُ المكتسَبة تعيّن القانون؛ فهو دالّةٌ فيها (`yuayyin_iff`).
* **الحدّ الأدنى المكتمل** (`*_adna`): حذفُ أيّ وصفٍ يُسقط التعيين (`adna_la_hadhf`).
* **الجدول** (`*_jadwal`): الجدولُ المكتسَب على المفتاح يعطي القانونَ في كلّ خانة.
* **لا أصغرَ ولا غيرَه بحجمه** (`*_wahid`): ما دون حجمه من مجموعات الأوصاف لا يعيّن، وما بحجمه يعيّن هو وحدَه — إلّا
  الابتداء، فكلُّ زوجٍ فيه الحالةُ يعيّنه (`ibtida_azwaj`).

فإن تغيّر ما يكتسبه المتعلّم وخالف القانونَ أو الحدَّ الأدنى سقط البناء.
-/

set_option autoImplicit false
set_option maxRecDepth 100000

namespace A116.IktisabHuwiyyaAqd

open A116.IktisabHuwiyya A116.IktisabHuwiyyaData

theorem wujud_yuayyin : yuayyin wujudW wujud dom = true := by decide +kernel
theorem wujud_adna : adna wujudW wujud dom = true := by decide +kernel
theorem wujud_jadwal : dom.all (fun x => bahth wujudJ (key wujudW x) == some (wujud x)) = true := by
  decide +kernel
/-- **الوجودُ لا يعيّنه وصفٌ واحد، ويعيّنه بزوجٍ واحدٍ فقط: الحالةُ ومخرجُ الجزريّ.** -/
theorem wujud_wahid :
    yuayyin [] wujud dom = false ∧ (ikhtiyar wasfAll 1).all (fun ws => !yuayyin ws wujud dom) = true ∧
      (ikhtiyar wasfAll 2).filter (yuayyin · wujud dom) = [wujudW] := by
  decide +kernel

theorem ibtida_yuayyin : yuayyin ibtidaW ibtida dom = true := by decide +kernel
theorem ibtida_adna : adna ibtidaW ibtida dom = true := by decide +kernel
theorem ibtida_jadwal : dom.all (fun x => bahth ibtidaJ (key ibtidaW x) == some (ibtida x)) = true := by
  decide +kernel
/-- **الابتداءُ يعيّنه وصفٌ واحدٌ هو الحالة**، فلا أثرَ للحامل فيه. -/
theorem ibtida_wahid :
    yuayyin [] ibtida dom = false ∧ (ikhtiyar wasfAll 1).filter (yuayyin · ibtida dom) = [ibtidaW] := by
  decide +kernel

/-- **وكلُّ زوجٍ فيه الحالةُ يعيّن الابتداء، وما ليس فيه لا يعيّنه.** -/
theorem ibtida_azwaj :
    (ikhtiyar wasfAll 2).all (fun ws => yuayyin ws ibtida dom == ws.contains .hala) = true := by
  decide +kernel

theorem mubtada_yuayyin : yuayyin mubtadaW mubtada dom = true := by decide +kernel
theorem mubtada_adna : adna mubtadaW mubtada dom = true := by decide +kernel
theorem mubtada_jadwal :
    dom.all (fun x => bahth mubtadaJ (key mubtadaW x) == some (mubtada x)) = true := by
  decide +kernel
theorem mubtada_wahid :
    yuayyin [] mubtada dom = false ∧ (ikhtiyar wasfAll 1).all (fun ws => !yuayyin ws mubtada dom) = true ∧
      (ikhtiyar wasfAll 2).filter (yuayyin · mubtada dom) = [mubtadaW] := by
  decide +kernel

/-- **مخرجُ سيبويه مع الحالة لا يعيّن الوجود**: الألفُ والهمزةُ مفتوحتين بمفتاحٍ واحد وقانونين. -/
theorem sibawayh_la_yakfi :
    yuayyin [.hala, .makhraj] wujud dom = false ∧
      (dom.filter fun x => x.1.c == 'ا' && x.2 == .fatha).all (fun a =>
        (dom.filter fun x => x.1.c == 'ء' && x.2 == .fatha).all fun b =>
          key [.hala, .makhraj] a == key [.hala, .makhraj] b && wujud a != wujud b) = true ∧
      (dom.filter fun x => x.1.c == 'ا' && x.2 == .fatha).length = 1 ∧
      (dom.filter fun x => x.1.c == 'ء' && x.2 == .fatha).length = 1 := by
  decide +kernel

/-- **ويعيّنه بحيّز الخليل ثالثًا.** -/
theorem sibawayh_khalil : yuayyin [.hala, .makhraj, .hayyiz] wujud dom = true := by decide +kernel

/-- القوانينُ دالّاتٌ في أوصافها المكتسَبة. -/
theorem dalla :
    (∃ f : List Nat → Bool, ∀ x ∈ dom, wujud x = f (key wujudW x)) ∧
      (∃ f : List Nat → Bool, ∀ x ∈ dom, ibtida x = f (key ibtidaW x)) ∧
      (∃ f : List Nat → Bool, ∀ x ∈ dom, mubtada x = f (key mubtadaW x)) :=
  ⟨(yuayyin_iff _ _ _).1 wujud_yuayyin, (yuayyin_iff _ _ _).1 ibtida_yuayyin,
    (yuayyin_iff _ _ _).1 mubtada_yuayyin⟩

/-- **والمتعلّمُ لم يغيّر القوانين:** المبتدأُ به 84 خانةً كما في `Jadwal.ibtida_wasl_waqf_counts`، والابتداءُ هو الحركة. -/
theorem mutabaqa :
    (dom.filter mubtada).length = 84 ∧ dom.all (fun x => ibtida x == (x.2 != .sukun)) = true := by
  decide +kernel

end A116.IktisabHuwiyyaAqd
