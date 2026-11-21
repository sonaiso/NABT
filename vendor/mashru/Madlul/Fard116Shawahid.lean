/- مولَّد بـ `python3 -I shabaka/fard116.py --lean`؛ لا يُحرَّر يدويًّا. مبرهن على الشاهد: كلُّ مبرهنةٍ مرورٌ واحدٌ على جمهورٍ
   من `Madlul/Fard116Data.lean` بتعريفات `Madlul/Fard116.lean`؛ والأعدادُ أعدادُ `shabaka/out/fard116.json` بعينها. -/
import Madlul.Fard116

namespace Madlul.Fard116.Shawahid
open SLGE.Law Madlul.Fard116 Madlul.Fard116Data

/-- المخالِفُ لآلة الجذر في lisan3: 56 — ءدط، ءشج، ءطد، ءها، ءهب، ءهر، ءهق، ءهل، ءهن، بءه، ببم، بمم، بهء، تطا، جشا، جشب، جشر، جشش، جشع، جشم، جشن، حتد، حعل، دطر، ربم، شبم، شجا، شجب، شجج، شجح، شجذ، شجر، شجع، شجم، شجن، طتء، طدي، عبم، عتد، عطد، فجش، فشج، قتد، كتد، لبم، لتد، مبد، متد، مشج، نجش، نشج، نهء، هءن، وتد، وشج، وطد. -/
theorem mukhalif_lisan3 : lisan3.filter (fun c => !licN3 c) = [509, 299, 481, 57, 55, 44, 36, 42, 43, 21867, 22647, 22676, 21895, 15630, 7887, 7885, 7874, 7869, 7862, 7886, 7873, 3903, 3464, 14776, 13396, 9191, 8699, 8697, 8680, 8675, 8694, 8686, 8674, 8698, 8685, 13978, 13960, 3304, 3062, 3004, 21296, 21324, 6426, 7267, 11714, 11472, 23478, 23246, 23006, 12045, 12073, 11803, 855, 24087, 23847, 24029] := by decide +kernel

/-- المخالِفُ لآلة الجذر في maqayis3: 32 — ءهب، ءهر، ءهل، ءهن، بهء، جشء، جشب، جشر، جشع، جشم، حتد، رهء، شبم، شجب، شجذ، شجر، شجع، شجن، عبم، عتد، عطد، فشج، قتد، كتد، مشج، نجش، نشج، نهء، وءه، وتد، وشج، وطد. -/
theorem mukhalif_maqayis3 : maqayis3.filter (fun c => !licN3 c) = [55, 44, 42, 43, 21895, 7859, 7885, 7874, 7862, 7886, 3903, 12644, 9191, 8697, 8694, 8686, 8674, 8685, 3304, 3062, 3004, 21324, 6426, 7267, 23006, 12045, 12073, 11803, 23549, 24087, 23847, 24029] := by decide +kernel

/-- المخالِفُ لآلة الجذر في lisan4: 8 — شجعم، عفشج، عمبر، عنجش، عنشج، فنجش، مجشن، هءهء. -/
theorem mukhalif_lisan4 : lisan4.filter (fun c => !licK 4 c) = [251573, 94491, 96643, 85212, 85240, 621770, 666376, 24418] := by decide +kernel

/-- المخالِفُ لآلة الجذر في lisan5: 1 — عفنجش. -/
theorem mukhalif_lisan5 : lisan5.filter (fun c => !licK 5 c) = [2743613] := by decide +kernel

/-- ء–ه متجاورين في ثلاثيّ اللسان: 10. -/
theorem jiwar_0_1 : (lisan3.filter (fun c => jiwarN c 0 1)).length = 10 := by decide +kernel

/-- ع–ح متجاورين في ثلاثيّ اللسان: 1. -/
theorem jiwar_3_4 : (lisan3.filter (fun c => jiwarN c 3 4)).length = 1 := by decide +kernel

/-- غ–خ متجاورين في ثلاثيّ اللسان: 0. -/
theorem jiwar_5_6 : (lisan3.filter (fun c => jiwarN c 5 6)).length = 0 := by decide +kernel

/-- ج–ش متجاورين في ثلاثيّ اللسان: 23. -/
theorem jiwar_9_10 : (lisan3.filter (fun c => jiwarN c 9 10)).length = 23 := by decide +kernel

/-- ط–د متجاورين في ثلاثيّ اللسان: 6. -/
theorem jiwar_16_17 : (lisan3.filter (fun c => jiwarN c 16 17)).length = 6 := by decide +kernel

/-- ط–ت متجاورين في ثلاثيّ اللسان: 2. -/
theorem jiwar_16_18 : (lisan3.filter (fun c => jiwarN c 16 18)).length = 2 := by decide +kernel

/-- د–ت متجاورين في ثلاثيّ اللسان: 7. -/
theorem jiwar_17_18 : (lisan3.filter (fun c => jiwarN c 17 18)).length = 7 := by decide +kernel

/-- ز–س متجاورين في ثلاثيّ اللسان: 0. -/
theorem jiwar_19_20 : (lisan3.filter (fun c => jiwarN c 19 20)).length = 0 := by decide +kernel

/-- ز–ص متجاورين في ثلاثيّ اللسان: 0. -/
theorem jiwar_19_21 : (lisan3.filter (fun c => jiwarN c 19 21)).length = 0 := by decide +kernel

/-- س–ص متجاورين في ثلاثيّ اللسان: 0. -/
theorem jiwar_20_21 : (lisan3.filter (fun c => jiwarN c 20 21)).length = 0 := by decide +kernel

/-- ظ–ذ متجاورين في ثلاثيّ اللسان: 0. -/
theorem jiwar_22_23 : (lisan3.filter (fun c => jiwarN c 22 23)).length = 0 := by decide +kernel

/-- ظ–ث متجاورين في ثلاثيّ اللسان: 0. -/
theorem jiwar_22_24 : (lisan3.filter (fun c => jiwarN c 22 24)).length = 0 := by decide +kernel

/-- ذ–ث متجاورين في ثلاثيّ اللسان: 0. -/
theorem jiwar_23_24 : (lisan3.filter (fun c => jiwarN c 23 24)).length = 0 := by decide +kernel

/-- ب–م متجاورين في ثلاثيّ اللسان: 7. -/
theorem jiwar_26_27 : (lisan3.filter (fun c => jiwarN c 26 27)).length = 7 := by decide +kernel

/-- ء–ع (خارج القانون) متجاورين في ثلاثيّ اللسان: 0. -/
theorem jiwar_0_3 : (lisan3.filter (fun c => jiwarN c 0 3)).length = 0 ∧ conflict 0 3 = false := by decide +kernel

/-- ع–غ (خارج القانون) متجاورين في ثلاثيّ اللسان: 0. -/
theorem jiwar_3_5 : (lisan3.filter (fun c => jiwarN c 3 5)).length = 0 ∧ conflict 3 5 = false := by decide +kernel

/-- ح–خ (خارج القانون) متجاورين في ثلاثيّ اللسان: 0. -/
theorem jiwar_4_6 : (lisan3.filter (fun c => jiwarN c 4 6)).length = 0 ∧ conflict 4 6 = false := by decide +kernel

/-- ق–ك (خارج القانون) متجاورين في ثلاثيّ اللسان: 0. -/
theorem jiwar_7_8 : (lisan3.filter (fun c => jiwarN c 7 8)).length = 0 ∧ conflict 7 8 = false := by decide +kernel

/-- س–ث (خارج القانون) متجاورين في ثلاثيّ اللسان: 0. -/
theorem jiwar_20_24 : (lisan3.filter (fun c => jiwarN c 20 24)).length = 0 ∧ conflict 20 24 = false := by decide +kernel

/-- ف–ب (خارج القانون) متجاورين في ثلاثيّ اللسان: 0. -/
theorem jiwar_25_26 : (lisan3.filter (fun c => jiwarN c 25 26)).length = 0 ∧ conflict 25 26 = false := by decide +kernel

/-- ق–ج (خارج القانون) متجاورين في ثلاثيّ اللسان: 1. -/
theorem jiwar_7_9 : (lisan3.filter (fun c => jiwarN c 7 9)).length = 1 ∧ conflict 7 9 = false := by decide +kernel

/-- ه–ح (خارج القانون) متجاورين في ثلاثيّ اللسان: 1. -/
theorem jiwar_1_4 : (lisan3.filter (fun c => jiwarN c 1 4)).length = 1 ∧ conflict 1 4 = false := by decide +kernel

/-- ه–خ (خارج القانون) متجاورين في ثلاثيّ اللسان: 1. -/
theorem jiwar_1_6 : (lisan3.filter (fun c => jiwarN c 1 6)).length = 1 ∧ conflict 1 6 = false := by decide +kernel

/-- ك–ج (خارج القانون) متجاورين في ثلاثيّ اللسان: 2. -/
theorem jiwar_8_9 : (lisan3.filter (fun c => jiwarN c 8 9)).length = 2 ∧ conflict 8 9 = false := by decide +kernel

/-- ف–م (خارج القانون) متجاورين في ثلاثيّ اللسان: 5. -/
theorem jiwar_25_27 : (lisan3.filter (fun c => jiwarN c 25 27)).length = 5 ∧ conflict 25 27 = false := by decide +kernel

/-- ك–ط (خارج القانون) متجاورين في ثلاثيّ اللسان: 2. -/
theorem jiwar_8_16 : (lisan3.filter (fun c => jiwarN c 8 16)).length = 2 ∧ conflict 8 16 = false := by decide +kernel

/-- ج–ط (خارج القانون) متجاورين في ثلاثيّ اللسان: 3. -/
theorem jiwar_9_16 : (lisan3.filter (fun c => jiwarN c 9 16)).length = 3 ∧ conflict 9 16 = false := by decide +kernel

/-- ل–ر (خارج القانون) متجاورين في ثلاثيّ اللسان: 11. -/
theorem jiwar_13_15 : (lisan3.filter (fun c => jiwarN c 13 15)).length = 11 ∧ conflict 13 15 = false := by decide +kernel

/-- خ–ك (خارج القانون) متجاورين في ثلاثيّ اللسان: 4. -/
theorem jiwar_6_8 : (lisan3.filter (fun c => jiwarN c 6 8)).length = 4 ∧ conflict 6 8 = false := by decide +kernel

/-- الموضعان 1 و2 متماثلان في ثلاثيّ اللسان: 30. -/
theorem tamathul_12 : (lisan3.filter (fun c => mithlN c 0 1)).length = 30 := by decide +kernel

/-- الموضعان 2 و3 متماثلان في ثلاثيّ اللسان: 501. -/
theorem tamathul_23 : (lisan3.filter (fun c => mithlN c 1 2)).length = 501 := by decide +kernel

/-- الموضعان 1 و3 متماثلان في ثلاثيّ اللسان: 79. -/
theorem tamathul_13 : (lisan3.filter (fun c => mithlN c 0 2)).length = 79 := by decide +kernel

/-- الخليل (lisan س143025): «قال الخليل: العين والحاء لا يأتلفان في كلمة واحدة أصلية» — ع وح معًا: 1 ثلاثيًّا و1 رباعيًّا. -/
theorem qayd_3_4 : (lisan3.filter (fun c => maanN3 c 3 4)).length = 1 ∧ (lisan4.filter (fun c => maanK 4 c 3 4)).length = 1 := by decide +kernel

/-- الخليل (lisan س42494): «وبعد الحاء الهاء ولم يأتلفا في كلمة واحدة أصلية الحروف» — ح وه معًا: 2 ثلاثيًّا و1 رباعيًّا. -/
theorem qayd_4_1 : (lisan3.filter (fun c => maanN3 c 4 1)).length = 2 ∧ (lisan4.filter (fun c => maanK 4 c 4 1)).length = 1 := by decide +kernel

/-- الأزهري (lisan س107377): «قال الأزهري: لا تأتلف الصاد مع» — ص وس معًا: 0 ثلاثيًّا و0 رباعيًّا. -/
theorem qayd_21_20 : (lisan3.filter (fun c => maanN3 c 21 20)).length = 0 ∧ (lisan4.filter (fun c => maanK 4 c 21 20)).length = 0 := by decide +kernel

/-- الأزهري (lisan س112127): «قال الأزهري: لا تأتلف الصاد مع السين ولا مع» — ص وز معًا: 0 ثلاثيًّا و0 رباعيًّا. -/
theorem qayd_21_19 : (lisan3.filter (fun c => maanN3 c 21 19)).length = 0 ∧ (lisan4.filter (fun c => maanK 4 c 21 19)).length = 0 := by decide +kernel

/-- الجوهري (lisan س174513): «قال الجوهري: الجيم والقاف لا يجتمعان في كلمة واحدة من كلام العرب» — ج وق معًا: 10 ثلاثيًّا و21 رباعيًّا. -/
theorem qayd_9_7 : (lisan3.filter (fun c => maanN3 c 9 7)).length = 10 ∧ (lisan4.filter (fun c => maanK 4 c 9 7)).length = 21 := by decide +kernel

/-- الجوهري (lisan س126042): «الإجاص دخيل لأن الجيم والصاد لا يجتمعان» — ص وج معًا: 14 ثلاثيًّا و6 رباعيًّا. -/
theorem qayd_21_9 : (lisan3.filter (fun c => maanN3 c 21 9)).length = 14 ∧ (lisan4.filter (fun c => maanK 4 c 21 9)).length = 6 := by decide +kernel

/-- الجوهري (lisan س254417): «وكلاهما معرب لأن الطاء والجيم لا يجتمعان في أصل» — ط وج معًا: 12 ثلاثيًّا و10 رباعيًّا. -/
theorem qayd_16_9 : (lisan3.filter (fun c => maanN3 c 16 9)).length = 12 ∧ (lisan4.filter (fun c => maanK 4 c 16 9)).length = 10 := by decide +kernel

/-- — (lisan س300224): «لأن الهمزة والغين لا يجتمعان في بناء كلمة واحدة» — ء وغ معًا: 3 ثلاثيًّا و1 رباعيًّا. -/
theorem qayd_0_5 : (lisan3.filter (fun c => maanN3 c 0 5)).length = 3 ∧ (lisan4.filter (fun c => maanK 4 c 0 5)).length = 1 := by decide +kernel

/-- ابن فارس (maqayis س11825): «اعلم أن الخاء لا يكاد يأتلف مع العين إلا بدخيل» — خ وع معًا: 22 ثلاثيًّا و34 رباعيًّا. -/
theorem qayd_6_3 : (lisan3.filter (fun c => maanN3 c 6 3)).length = 22 ∧ (lisan4.filter (fun c => maanK 4 c 6 3)).length = 34 := by decide +kernel

/-- شمر (lisan س193447): «لأن الصاد والطاء لا يكاد يجتمعان في محض كلامهم» — ص وط معًا: 9 ثلاثيًّا و10 رباعيًّا. -/
theorem qayd_21_16 : (lisan3.filter (fun c => maanN3 c 21 16)).length = 9 ∧ (lisan4.filter (fun c => maanK 4 c 21 16)).length = 10 := by decide +kernel

/-- الرباعيُّ من الثلاثيّ: ثلاثيٌّ مشهودٌ بإسقاطِ حامل (G1). -/
theorem tawlid4_G1 : (lisan4.filter (G1 4 bits3)).length = 2491 := by decide +kernel

/-- وثلاثيّان مختلفان (G2). -/
theorem tawlid4_G2 : (lisan4.filter (G2 4 bits3)).length = 2406 := by decide +kernel

/-- وثنائيٌّ مكرَّر abab (Gr). -/
theorem tawlid4_Gr : (lisan4.filter Gr).length = 48 := by decide +kernel

/-- الخماسيُّ من الرباعيّ: G1 وG2. -/
theorem tawlid5 : (lisan5.filter (G1 5 bits4)).length = 58 ∧ (lisan5.filter (G2 5 bits4)).length = 37 := by decide +kernel

end Madlul.Fard116.Shawahid
