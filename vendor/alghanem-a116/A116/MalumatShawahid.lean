import A116.MalumatData

/-!
# المعلوماتُ السابقة على المودَع (ADR ٨٧)

مبرهناتٌ على صفوف `MalumatData.rows` كما ملأها الوكيل من النصوص المختومة.
-/

namespace A116.Malumat

/-- مرتبةُ كلّ صفٍّ كما ملأها الوكيل هي مرتبةُ نوعه بالقانون. -/
theorem martaba_mutabiqa : rows.all (fun r => r.martaba == martaba r.naw) = true := by decide

/-- الخاصّةُ ليست شيئًا ثانيًا: لا محمولَ خاصّةٍ موضوعٌ لصفّ. -/
theorem khassa_laysat_shay :
    rows.all (fun r => r.naw != .khassa || rows.all (fun s => s.mawdu != r.mahmul)) = true := by
  decide

/-- خاصّيّةُ الربط تفصل الإنسانَ من الحيوان («التفكير» س20). -/
theorem rabt_yafsil :
    rows.any (fun r => r.mawdu == "دماغ الإنسان" && r.mahmul == "ربط المعلومات" && r.ijab) = true ∧
    rows.any (fun r => r.mawdu == "دماغ الحيوان" && r.mahmul == "ربط المعلومات" && !r.ijab) = true := by
  decide

/-- قابليّةُ الانعكاس في المرآة لا في الدماغ («التفكير» س14). -/
theorem inikas_yafsil :
    rows.any (fun r => r.mawdu == "المرآة" && r.naw == .qabiliyya && r.ijab) = true ∧
    rows.any (fun r => r.mawdu == "الدماغ" && r.naw == .qabiliyya && !r.ijab) = true := by
  decide

/-- التمييزُ الغريزيُّ واقعٌ في المودَع، ولا مرتبةَ له. -/
theorem tamyiz_bila_martaba :
    rows.any (fun r => r.naw == .tamyiz) = true ∧
    rows.all (fun r => r.naw != .tamyiz || r.martaba == none) = true := by
  decide

/-- القطعيُّ في المودَع صفُّ الوجود من «التفكير» س28 وحدَه. -/
theorem qati_wahid :
    rows.all (fun r => r.martaba != some .qati || (r.naw == .wujud && r.nass == "tafkir" && r.satr == 28))
      = true := by
  decide

/-- مرساتا الزمان والمكان من المقام: الآن، وهنا، وهناك. -/
theorem marasi_maqam :
    rows.all (fun r => (r.naw != .marsaZaman && r.naw != .marsaMakan) ||
      r.mawdu == "الآن" || r.mawdu == "هنا" || r.mawdu == "هناك") = true := by
  decide

/-- الإطاران الهجريُّ والميلاديُّ مستعملان في الجزء الأوّل اصطلاحين. -/
theorem itarayn_mustamalan :
    rows.any (fun r => r.naw == .istilah && r.mahmul == "الهجري" && r.nass == "j1") = true ∧
    rows.any (fun r => r.naw == .istilah && r.mahmul == "الميلادي" && r.nass == "j1") = true := by
  decide

end A116.Malumat
