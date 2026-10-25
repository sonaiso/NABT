'use strict';
// Curated supplied-record projection. Reported proof statuses are unverified imports.
(() => {
  globalThis.NabtEvidenceSample = {
  "schema": "Tabaqat4Record:v1",
  "sample_note": "مقتطف عرض من سجل المستخدم المنسوخ في المحادثة؛ حُذفت مسارات الجهاز الشخصية وأوامرها. ليس أرشيف المصدر الأصلي، ولا نتيجة تشغيل جديد، ولا إعادة تحقق من Lean.",
  "timestamp_utc": "2026-10-24T12:07:12.532821+00:00",
  "input": {
    "nass_kama_wasal": "ذَهَبَ الْوَلَدُ",
    "nfc": "ذَهَبَ الْوَلَدُ",
    "nfc_eq_input": true,
    "sha256": "34c9ac0fff60bc73c9ed17b600b1c133d2f0c83d5b47427e921bb533853450e2",
    "codepoints": 16,
    "tahwil": []
  },
  "tokens": [
    {
      "idx": 0,
      "anchor": "W-34c9ac0f-000",
      "surface": "ذَهَبَ"
    },
    {
      "idx": 1,
      "anchor": "W-34c9ac0f-001",
      "surface": "الْوَلَدُ"
    }
  ],
  "dal": [
    {
      "surface": "ذَهَبَ",
      "khalaya": [
        92,
        4,
        104
      ],
      "wasl": false,
      "al": false,
      "tanwin": false,
      "transforms": [],
      "residuals": [],
      "cells_human": [
        "ذَ=92",
        "هَ=4",
        "بَ=104"
      ]
    },
    {
      "surface": "الْوَلَدُ",
      "khalaya": [
        55,
        112,
        52,
        69
      ],
      "wasl": true,
      "al": true,
      "tanwin": false,
      "transforms": [
        "AL_FLAG:همزة_الوصل_لا_تُرمَّز(Dal.Kalima.al=true,wasl=true)",
        "AL_QAMARIYYA:لام_ساكنة"
      ],
      "residuals": [],
      "cells_human": [
        "لْ=55",
        "وَ=112",
        "لَ=52",
        "دُ=69"
      ]
    }
  ],
  "maani": [
    {
      "ref": "Jisr/Utur.lean:327",
      "haqiqa": 10,
      "tim": true,
      "qism": "fiil",
      "wasf": "ذهب — عَرَضٌ فعليّ (tim=true) ، لازم بنيويًّا (إطار بلا خانة مفعول)",
      "mudaa": {
        "ism": "المخصص",
        "sha256": "936c68e0c2c62ddbfb881c573487c7b37650ef69117bca364c219b6d1bf8e76c",
        "mawdi": "PageV01P309–310",
        "masdar": "Shahid_Ahmad.lean ت1"
      },
      "ism": "dhahab",
      "shahid": "Jisr/Utur.lean:908 dhahaba"
    },
    {
      "ref": "Jisr/Utur.lean:326",
      "haqiqa": 20,
      "tim": false,
      "qism": "ism",
      "wasf": "ولد — ذاتٌ ، خاصّة 21 ، علاقة (1,30) ، قابليّات [10,11]",
      "mudaa": null,
      "ism": "walad",
      "shahid": "Jisr/Utur.lean:909 alWalad"
    }
  ],
  "plan": {
    "naw": "فعل ماضٍ + فاعل معرَّف بأل",
    "ud": "Jisr.Mulhaqat.darabaZayd",
    "shahid_mashru": "dhahabaAlWalad (Jisr/Utur.lean:914)",
    "isnad": {
      "mawdu": "walad",
      "mahmul": ".qabiliyya 10",
      "nisba": ".isnadiyya",
      "qaida": "ISNAD_RULE_FIIL_FAIL (موروثة من الشاهد): الفاعل موضوعٌ ، والفعل قابليّةٌ بحقيقته"
    }
  },
  "lean": {
    "pass1": {
      "rc": 0,
      "stdout": "Jisr.Utur.Hukm.murakhkhas\ntrue\n[92, 4, 104, 55, 112, 52, 69]\n[Aql.Isnad.Rutba.mahkum, Aql.Isnad.Rutba.hakim]\ntrue\nsome (Aql.Azmina.Zaman3.madi)\n{ amudi := 0, ufuqi := 0, tuli := 0 }\n",
      "stderr": ""
    },
    "pass2": {
      "rc": 0,
      "stdout": "'Tabaqat4.tabaqa1_kalimat' does not depend on any axioms\n'Tabaqat4.tabaqa2_maani' does not depend on any axioms\n'Tabaqat4.tabaqa3_hukm' depends on axioms: [propext]\n'Tabaqat4.tabaqa3_isnad' does not depend on any axioms\n'Tabaqat4.tabaqa4_ajza' depends on axioms: [propext]\n'Tabaqat4.tabaqa4_kalam' depends on axioms: [propext]\n'Tabaqat4.tabaqa4_zaman' does not depend on any axioms\n'Tabaqat4.tabaqa4_mawdi' does not depend on any axioms\n'Tabaqat4.tabaqa4_thabat' depends on axioms: [propext, Quot.sound]\n",
      "stderr": ""
    },
    "observed": {
      "hukm3": ".murakhkhas",
      "ibtida3": "true",
      "silsila": "[92, 4, 104, 55, 112, 52, 69]",
      "ajza": "[.mahkum, .hakim]",
      "yastaghni": "true",
      "zaman": "some .madi",
      "mawdi": "⟨0, 0, 0⟩"
    },
    "theorems": {
      "tabaqa1_kalimat": {
        "passed": true,
        "axioms": []
      },
      "tabaqa2_maani": {
        "passed": true,
        "axioms": []
      },
      "tabaqa3_hukm": {
        "passed": true,
        "axioms": [
          "propext"
        ]
      },
      "tabaqa3_isnad": {
        "passed": true,
        "axioms": []
      },
      "tabaqa4_ajza": {
        "passed": true,
        "axioms": [
          "propext"
        ]
      },
      "tabaqa4_kalam": {
        "passed": true,
        "axioms": [
          "propext"
        ]
      },
      "tabaqa4_zaman": {
        "passed": true,
        "axioms": []
      },
      "tabaqa4_mawdi": {
        "passed": true,
        "axioms": []
      },
      "tabaqa4_thabat": {
        "passed": true,
        "axioms": [
          "propext",
          "Quot.sound"
        ]
      }
    },
    "files": {
      "pass1": "4fe5fa06c4c156e7d2d073a85f60f38f84603c7a09867cc86e76218098a42203",
      "pass2": "c1d3cb620a9bc97880500cfeb4e591ac5aa7f7d72ad40f270f9aeed86b2ab53e"
    }
  },
  "stages": [
    {
      "stage": "S0_HAWIYYA",
      "started": true,
      "completed": true,
      "found": true,
      "produced": true,
      "accepted": true,
      "stored": true,
      "consumed_by_next": null,
      "reason": null,
      "residuals": []
    },
    {
      "stage": "S1_TAQTI",
      "started": true,
      "completed": true,
      "found": true,
      "produced": true,
      "accepted": true,
      "stored": true,
      "consumed_by_next": true,
      "reason": null,
      "residuals": []
    },
    {
      "stage": "S2_DAL",
      "started": true,
      "completed": true,
      "found": true,
      "produced": true,
      "accepted": true,
      "stored": true,
      "consumed_by_next": true,
      "reason": null,
      "residuals": [],
      "hawamil_source": "Dal/Makharij.lean:def hawamil (قُرئ وقت التشغيل ، 29 حاملًا)"
    },
    {
      "stage": "S3_HOKOM_TAQDIR",
      "started": false,
      "completed": null,
      "found": null,
      "produced": null,
      "accepted": null,
      "stored": null,
      "consumed_by_next": null,
      "reason": "NOT_REQUESTED (--hokom غير مطلوب)",
      "residuals": []
    },
    {
      "stage": "S4_MADLUL",
      "started": true,
      "completed": true,
      "found": true,
      "produced": true,
      "accepted": true,
      "stored": true,
      "consumed_by_next": true,
      "reason": null,
      "residuals": [
        "W-34c9ac0f-001:MADLUL_SOURCE_UNDECLARED_IN_MASHRU"
      ]
    },
    {
      "stage": "S5_MAAN_ITAR",
      "started": true,
      "completed": true,
      "found": true,
      "produced": true,
      "accepted": true,
      "stored": true,
      "consumed_by_next": true,
      "reason": null,
      "residuals": []
    },
    {
      "stage": "S6_AQL",
      "started": true,
      "completed": true,
      "found": true,
      "produced": true,
      "accepted": true,
      "stored": true,
      "consumed_by_next": true,
      "reason": "Mirsat ⟨0, ⟨0,0,0⟩⟩ و Arad .fiil 10 (-1) .saa none — افتراضات معلَنة (ت3/ت4/ت5 من الشاهد)",
      "residuals": [
        "MIRSAT_DEFAULT_ASSUMED",
        "ARAD_IZAHA_DEFAULT_ASSUMED",
        "LAZIM_BY_FRAME_NOT_BY_TEXT"
      ]
    },
    {
      "stage": "S7_BURHAN",
      "started": true,
      "completed": true,
      "found": true,
      "produced": true,
      "accepted": true,
      "stored": true,
      "consumed_by_next": null,
      "reason": null,
      "residuals": []
    }
  ],
  "claims": [
    {
      "tabaqa": 1,
      "ism": "dal_W-34c9ac0f-000",
      "qima": [
        92,
        4,
        104
      ],
      "tarjama": "«ذَهَبَ»: 3 خلية [ذَ=92, هَ=4, بَ=104]",
      "rutba": "مطابَق",
      "burhan": "ترميز بجدول Dal/Makharij.lean (n=4·حامل+حالة) ؛ يُبرهَن على مستوى الجملة في S7",
      "sabab_ghiyab": null
    },
    {
      "tabaqa": 1,
      "ism": "dal_W-34c9ac0f-001",
      "qima": [
        55,
        112,
        52,
        69
      ],
      "tarjama": "«الْوَلَدُ»: 4 خلية [لْ=55, وَ=112, لَ=52, دُ=69] ، بأل التعريف (همزة وصل)",
      "rutba": "مطابَق",
      "burhan": "ترميز بجدول Dal/Makharij.lean (n=4·حامل+حالة) ؛ يُبرهَن على مستوى الجملة في S7",
      "sabab_ghiyab": null
    },
    {
      "tabaqa": 2,
      "ism": "madlul_W-34c9ac0f-000",
      "qima": "dhahab",
      "tarjama": "«ذَهَبَ» ↔ مدلول Mashru `dhahab` (ذهب — عَرَضٌ فعليّ (tim=true) ، لازم بنيويًّا (إطار بلا خانة مفعول)) — Jisr/Utur.lean:327 ؛ مودَع: المخصص 936c68e0c2c6… PageV01P309–310",
      "rutba": "مطابَق",
      "burhan": "مطابقة اسمية بين السطح وتعريف Mashru ؛ حقوله تُبرهَن في S7",
      "sabab_ghiyab": null
    },
    {
      "tabaqa": 2,
      "ism": "madlul_W-34c9ac0f-001",
      "qima": "walad",
      "tarjama": "«الْوَلَدُ» ↔ مدلول Mashru `walad` (ولد — ذاتٌ ، خاصّة 21 ، علاقة (1,30) ، قابليّات [10,11]) — Jisr/Utur.lean:326 ؛ بلا مودَع معجمي معلَن",
      "rutba": "مطابَق",
      "burhan": "مطابقة اسمية بين السطح وتعريف Mashru ؛ حقوله تُبرهَن في S7",
      "sabab_ghiyab": null
    },
    {
      "tabaqa": 3,
      "ism": "naw_jumla",
      "qima": "فعل ماضٍ + فاعل معرَّف بأل",
      "tarjama": "نوع الجملة: فعل ماضٍ + فاعل معرَّف بأل ← إطار Jisr.Mulhaqat.darabaZayd (شاهد Mashru: dhahabaAlWalad (Jisr/Utur.lean:914))",
      "rutba": "مقيس",
      "burhan": "اختيار الإطار بشروط سطحية (قسم المدلول الأوّل ، أل/تنوين الثاني) — حكمه يُبرهَن في S7",
      "sabab_ghiyab": null
    },
    {
      "tabaqa": 1,
      "ism": "tabaqa1_kalimat",
      "qima": [
        [
          92,
          4,
          104
        ],
        [
          55,
          112,
          52,
          69
        ]
      ],
      "tarjama": "خلايا الكلمتَين كما بناها Mashru في الإطار الثلاثي (مطابقة البناء)",
      "rutba": "مبرهن على الشاهد",
      "burhan": "lean rc=0 ؛ axioms=[]",
      "sabab_ghiyab": null
    },
    {
      "tabaqa": 2,
      "ism": "tabaqa2_maani",
      "qima": [
        "dhahab",
        "walad"
      ],
      "tarjama": "المدلولان في الإطار ، و`dhahab.tim = true` (عَرَضٌ له زمان)",
      "rutba": "مبرهن على الشاهد",
      "burhan": "lean rc=0 ؛ axioms=[]",
      "sabab_ghiyab": null
    },
    {
      "tabaqa": 3,
      "ism": "tabaqa3_hukm",
      "qima": ".murakhkhas",
      "tarjama": "حكم الإطار الثلاثي hukm3 = مرخَّص (.murakhkhas) ؛ ibtida3=true ؛ سلسلة الوصل [92, 4, 104, 55, 112, 52, 69]",
      "rutba": "مبرهن على الشاهد",
      "burhan": "lean rc=0 ؛ axioms=['propext']",
      "sabab_ghiyab": null
    },
    {
      "tabaqa": 3,
      "ism": "tabaqa3_isnad",
      "qima": {
        "mawdu": "walad",
        "mahmul": ".qabiliyya 10",
        "nisba": ".isnadiyya",
        "qaida": "ISNAD_RULE_FIIL_FAIL (موروثة من الشاهد): الفاعل موضوعٌ ، والفعل قابليّةٌ بحقيقته"
      },
      "tarjama": "الإسناد الدلالي: walad موضوعٌ ، قابليّة 10 محمولٌ ، نسبة إسنادية",
      "rutba": "مبرهن على الشاهد",
      "burhan": "lean rc=0 ؛ axioms=[]",
      "sabab_ghiyab": null
    },
    {
      "tabaqa": 4,
      "ism": "tabaqa4_ajza",
      "qima": "[.mahkum, .hakim]",
      "tarjama": "أجزاء الجملة الصغرى بالرتبة: [.mahkum, .hakim] (محكوم ثمّ حاكم)",
      "rutba": "مبرهن على الشاهد",
      "burhan": "lean rc=0 ؛ axioms=['propext']",
      "sabab_ghiyab": null
    },
    {
      "tabaqa": 4,
      "ism": "tabaqa4_kalam",
      "qima": "true",
      "tarjama": "كلامٌ يُستغنى به بالسكوت: true",
      "rutba": "مبرهن على الشاهد",
      "burhan": "lean rc=0 ؛ axioms=['propext']",
      "sabab_ghiyab": null
    },
    {
      "tabaqa": 4,
      "ism": "tabaqa4_zaman",
      "qima": "some .madi",
      "tarjama": "زمن الحدث عند المرساة: some .madi (بإزاحة -1 ساعة معلَنة)",
      "rutba": "مبرهن على الشاهد",
      "burhan": "lean rc=0 ؛ axioms=[]",
      "sabab_ghiyab": null
    },
    {
      "tabaqa": 4,
      "ism": "tabaqa4_mawdi",
      "qima": "⟨0, 0, 0⟩",
      "tarjama": "موضع الجملة نسبةً إلى «هنا»: ⟨0, 0, 0⟩",
      "rutba": "مبرهن على الشاهد",
      "burhan": "lean rc=0 ؛ axioms=[]",
      "sabab_ghiyab": null
    },
    {
      "tabaqa": 4,
      "ism": "tabaqa4_thabat",
      "qima": true,
      "tarjama": "نقل المرساة والحدث معًا بساعة لا يغيّر الزمن (thabat_naql_arad)",
      "rutba": "مبرهن",
      "burhan": "lean rc=0 ؛ axioms=['propext', 'Quot.sound']",
      "sabab_ghiyab": null
    }
  ],
  "wasm_summary": {
    "مبرهن": 1,
    "مبرهن على الشاهد": 8,
    "مطابَق": 4,
    "مفحوص": 0,
    "مقيس": 1,
    "تقدير": 0,
    "رأي": 0,
    "بلا رتبة": 0
  },
  "tabaqat_state": {
    "1": "مبرهن على الشاهد",
    "2": "مبرهن على الشاهد",
    "3": "مبرهن على الشاهد",
    "4": "مبرهن على الشاهد"
  },
  "hukm3": ".murakhkhas",
  "la_yuddaa": [
    "لا صحّة لغوية خارجية: ما يمرّ هنا مرّ على بنى Mashru كما عرّفها د. صالح ، لا على العربية كلّها.",
    "المدلول لا يُولَّد: كلمة بلا مدلول معرَّف في Mashru تتوقّف عند الطبقة الثانية بالاسم NO_SEALED_MADLUL.",
    "أنواع الجمل المنفَّذة في هذه الأداة: [فعل ماضٍ + فاعل معرَّف بأل] و [فعل ماضٍ + فاعل منوَّن] فقط ؛ ما عداها OUT_OF_EXECUTED_PATH.",
    "المرساة (الآن=0 ، هنا=⟨0,0,0⟩) وإزاحة الحدث (−1 ساعة) موروثتان من Shahid_Ahmad.lean ت3/ت4 ، افتراضٌ معلَن قابل للتغيير بوسيطَي --an/--izaha.",
    "الإسناد الدلالي ⟨مدلول_الفاعل ، qabiliyya(حقيقة_الفعل) ، isnadiyya⟩ قاعدةٌ بنيوية موروثة من الشاهد ، ليست استنتاجًا من النصّ.",
    "رتبة «مبرهن على الشاهد» تعني: نظرية by decide مرّت على هذه الجملة بعينها في Lean ، بمسلّمات ⊆ {propext, Classical.choice, Quot.sound}. ليست «مبرهن» عامًّا."
  ],
  "identity": {
    "mashru_head": "df6bcc9eb9b536db3684cc8a2eb773c2c9f01136",
    "mashru_tree_clean": false,
    "mashru_status_porcelain": "?? audit.txt\n?? build.log\n?? by-hussein/\n?? jumla_kamila.json",
    "lean_toolchain": "leanprover/lean4:v4.34.1",
    "qamus_sha256": "e8662a21d29bfe8b0a1fe38d5b9a724bb6f43e60ef3d57770e721d8f8a5b6b20",
    "tool_files": {
      "README.md": "00f8605e4007470ebd1cf4d888c67e51a69917cefd440d73c6e12ef84468c1c2",
      "TAQRIR_TASLIM.md": "5660ce83eb9df91bbfae84348922ec397ce629e51588c8e4e74d101555dc947e",
      "_runs_samples/a/taqrir.json": "7c80bdec79ce67a9a12e8e8831f489adce4e36ed8b576a867be6f0be8c2d229f",
      "_runs_samples/a/taqrir.md": "77dbb464e8b92d3322c5c6960e32f296101453cc180f7156ba851b0307723ace",
      "_runs_samples/b/taqrir.json": "b48cae0c87c2d50f4c1da6af2f029ba1b040c906fadeb6b927e5cdc9b693189a",
      "_runs_samples/b/taqrir.md": "ccd354ab3c877df90968b04a61828fd64f4122bb54b1ef4b35e7a78dc47acd45",
      "_runs_samples/c/taqrir.json": "f9ead96b162ef318e22cf77b03dd25a0dc4f82cca9a7ea6207cc005d97e3e708",
      "_runs_samples/c/taqrir.md": "17a3d7efc2b5e99241a4c6da6628a78dbb274de5590bb9e2634eeece64bcf982",
      "_runs_samples/e/taqrir.json": "004b78e048c32207cc01317a75c8972650a3b976b1770b2302a0c401cd7fcb81",
      "_runs_samples/e/taqrir.md": "d426e555157e12876b62470336963d22fb6d7bf77e95a732d1db929b298f7adc",
      "_runs_samples/f/taqrir.json": "b07e7812be3909a4faaf54f01c95be338537bb0287cb5540c372ec077d9bced2",
      "_runs_samples/f/taqrir.md": "7ee9a3f8c8eacd1e473d80428e0e003d1c126ec9b232a7c769d7313746f3cee5",
      "hokom_adapter.example.py": "f2960748511e6b921874fb0a7cd2062904692f8b422a561de5398a3b77576f06",
      "run.py": "c77f8f185ab0d7e07b1d3f37030c428d4a5d6f0d93e3af1415745c904faa3f50",
      "t4/__init__.py": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "t4/core.py": "a397346591e5332da6430075074117b89f34996f318f8e5858ce1c3c6333574c",
      "t4/dal.py": "1c3a62d0977528ec841e2a8bed446adff01b26fde7c7a829dd2395f85f33fcfa",
      "t4/qamus.json": "e8662a21d29bfe8b0a1fe38d5b9a724bb6f43e60ef3d57770e721d8f8a5b6b20",
      "t4/report.py": "2593ad5e16f6c0482de6a6c91d68d4e41df3b6befeb2762624d0135210745178",
      "tests/test_tabaqat4.py": "27052856c95f7e639462e9c537de18b155e84a28aa3f63fb2685410fa4070510"
    }
  }
};
})();
