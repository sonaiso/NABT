# Vendored from Alghanem 9d8fa03, gate/mabni_verbs.py. MIT; see vendor/alghanem-a116/LICENSE.
"""توليدُ الأفعال المبنيّة من كلّ جذرٍ ثلاثيٍّ في «مقاييس اللغة»، واسترجاعُها بعكس التوليد.

## الدعوى

لكلّ جذرٍ ثلاثيٍّ ‎ρ‎ في جدول المقاييس المودَع تُولِّد `verb_forms(ρ)` صورَ الماضي
المبنيّ للمعلوم والمجهول والأمرِ بإسنادها إلى الضمائر، في الأوزان العشرة (عدا
التاسع) حيث يصحّ القالب. والاسترجاعُ عكسُ التوليد حرفيًّا (‎μ(s) = {(ρ, w) :
ε(⊗(ρ, w)) = s}‎ في وثيقة البرهان): فهرسٌ من الصورة المطبَّعة إلى تحليلاتها، فما
يُسترجَع مولَّدٌ بالبناء، وما لا يُولَّد لا يُسترجَع.

## القواعد — كلُّها منقولةٌ من الصرف المشهور ومسمّاةٌ بأصنافها

* **الصحيح والمهموز**: قوالبُ `_SOUND_TEMPLATES`؛ والهمزةُ حرفٌ صحيح. والهمزتان
  الثانيةُ ساكنةٌ تُبدَل مدًّا من جنس حركة الأولى (‎ءَءْ ← ءَا: آمَنَ‎).
  وأمرُ «أخذ، أكل، أمر» محذوفُ الفاء (خُذْ، كُلْ، مُرْ).
* **المضاعف**: يُدغَم المثلان إن تحرّك الثاني، ويُفكّ إن سكن (‎مَدَّ، مَدَدْتُ‎)،
  ولأمره صورتا الإدغام والفكّ (‎مُدَّ، امْدُدْ‎).
* **الأجوف**: تُقلب العينُ ألفًا بعد فتح، وتُحذف لالتقاء الساكنين قبل ضمير
  الرفع المتحرّك، فيُضمّ الفاءُ في الواويّ ويُكسر في اليائيّ (وفي باب ‎فَعِلَ‎)
  (‎قَالَ، قُلْتُ، بِعْتُ، خِفْتُ؛ قِيلَ؛ قُلْ، قُولُوا‎)، ومزيدُه في الرابع والسابع
  والثامن والعاشر.
* **الناقص**: اللامُ ألفٌ أو ياءٌ مقصورةٌ بعد فتح في الماضي، وتُحذف مع واو
  الجماعة، وتثبت ساكنةً قبل الضمير المتحرّك (‎دَعَا، دَعَوْا، دَعَوْتُ؛ رَمَى؛
  رَضِيَ، رَضُوا؛ ادْعُ، ارْمِ، اخْشَ‎)، ومزيدُه بالياء (‎أَعْطَى، أَعْطَيْتُ‎).
* **المثال**: تُحذف واوُه في أمر باب ‎يَفْعِلُ‎ (‎عِدْ‎)، وتُقلب تاءً وتُدغَم في
  ‎افتعل‎ (‎اتَّقَى‎).

## الكتابة والتطبيع

الصورُ المولَّدة على اصطلاح المتن المودَع: حرفُ المدّ بلا علامة، والساكنُ بسكون،
والكراسيُّ همزةٌ مفردة. والتطبيعُ المعلن للمقابلة (`normalize`) يطبَّق على الطرفين:
NFC، والكراسيُّ ← ء (‎آ ← ءَا‎)، وحذفُ آخرِ علامةٍ (حركةُ الطرف تتغيّر بالحدّ).
فكرسيُّ الهمزة رسمٌ يُستعاد بالليف (`A116/Fiber.lean`) لا بالتوليد.

## ما لا يدّعيه

الأوزانُ مولَّدةٌ لكلّ جذرٍ ولا يُدّعى أنّ كلَّ وزنٍ مستعملٌ من كلّ جذر: التوليدُ
فوقَ المستعمل، والمستعملُ يُقاس بالمتن. وبابُ الماضي يُولَّد بحركاته الثلاث، فالبابُ
المسترجَعُ مرصودٌ من الشكل لا منقولٌ عن معجم. ولا اللفيفُ المقرون (‎طَوَى، رَوَى‎)
إلا بقواعد الناقص، ولا ‎حَيِيَ‎ ولا ‎رَأَى‎ في المضارع.
"""

from __future__ import annotations

import unicodedata
from typing import Final

__all__ = [
    "candidate_roots",
    "verb_forms",
    "normalize",
    "root_class",
]

A, I, U, S, SH = "َ", "ِ", "ُ", "ْ", "ّ"  # noqa: E741
MARKS: Final[frozenset[str]] = frozenset({A, I, U, S, SH, "ً", "ٌ", "ٍ"})
W, Y, H = "و", "ي", "ء"
WEAK: Final[frozenset[str]] = frozenset({W, Y})

Form = tuple[str, str, str]  # (الصيغة، الوزن، الضمير)
Forms = dict[str, list[Form]]


def _put(out: Forms, word: str, analysis: Form) -> None:
    """صورةٌ واحدةٌ قد تكون لتحليلين (‎آمَنَ‎: أفعل وفاعل؛ ‎مُدُّوا‎: أمرٌ ومجهول)."""

    bucket = out.setdefault(word, [])
    if analysis not in bucket:
        bucket.append(analysis)


# --- الإسناد -----------------------------------------------------------------

VOWEL_PERSONS: Final[tuple[tuple[str, str, str], ...]] = (
    ("3MS", A, ""),
    ("3MD", A, "ا"),
    ("3MP", U, "وا"),
    ("3FS", A, "تْ"),
    ("3FD", A, "تَا"),
)
"""ضمائرُ الماضي التي تُبقي لامَ الفعل متحرّكة."""

CONSONANT_PERSONS: Final[tuple[tuple[str, str], ...]] = (
    ("3FP", "نَ"),
    ("2MS", "تَ"),
    ("2FS", "تِ"),
    ("2D", "تُمَا"),
    ("2MP", "تُمْ"),
    ("2FP", "تُنَّ"),
    ("1S", "تُ"),
    ("1P", "نَا"),
)
"""ضمائرُ الرفع المتحرّكة: تُسكَّن قبلها لامُ الفعل."""

BEFORE_OBJECT: Final[dict[str, str]] = {"وا": "و", "وْا": "وْ", "تُمْ": "تُمُو"}


def _nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def _idgham(text: str) -> str:
    """المثلان الأوّلُ ساكنٌ يُدغمان: ‎Xْ X ← Xّ‎."""

    out = unicodedata.normalize("NFD", text)
    changed = True
    while changed:
        changed = False
        for i in range(len(out) - 2):
            if out[i + 1] == S and out[i] == out[i + 2] and out[i] not in MARKS:
                out = out[: i + 1] + SH + out[i + 3 :]
                changed = True
                break
    return _nfc(out)


def _spell(text: str) -> str:
    """اصطلاحُ المتن: حرفُ المدّ بلا سكون، والهمزتان ‎ءَءْ ← ءَا‎، والمثلان يُدغمان."""

    text = _idgham(_nfc(text))
    text = unicodedata.normalize("NFD", text)
    for vowel, letter in ((A, "ا"), (U, W), (I, Y)):
        text = text.replace(H + vowel + H + S, H + vowel + letter)
    text = text.replace(U + W + S, U + W).replace(I + Y + S, I + Y)
    return _nfc(text)


def _attach(stem: str, last: str, suffix: str, before_object: bool) -> list[str]:
    """جذعٌ ينتهي بلام الفعل بلا حركة، ثمّ حركتُها، ثمّ اللاحقة (ومتغيّرُها قبل المفعول)."""

    variants = [suffix]
    if before_object and suffix in BEFORE_OBJECT:
        variants.append(BEFORE_OBJECT[suffix])
    return [_spell(stem + last + v) for v in variants]


# --- القوالب الصحيحة ---------------------------------------------------------

SOUND_TEMPLATES: Final[tuple[tuple[str, str, str], ...]] = (
    ("I-a", "PAST", f"1{A}2{A}3"),
    ("I-i", "PAST", f"1{A}2{I}3"),
    ("I-u", "PAST", f"1{A}2{U}3"),
    ("II", "PAST", f"1{A}2{SH}{A}3"),
    ("III", "PAST", f"1{A}ا2{A}3"),
    ("IV", "PAST", f"ء{A}1{S}2{A}3"),
    ("V", "PAST", f"ت{A}1{A}2{SH}{A}3"),
    ("VI", "PAST", f"ت{A}1{A}ا2{A}3"),
    ("VII", "PAST", f"ان{S}1{A}2{A}3"),
    ("VIII", "PAST", f"ا1{S}ت{A}2{A}3"),
    ("X", "PAST", f"اس{S}ت{A}1{S}2{A}3"),
    ("I", "PASSIVE", f"1{U}2{I}3"),
    ("II", "PASSIVE", f"1{U}2{SH}{I}3"),
    ("III", "PASSIVE", f"1{U}و2{I}3"),
    ("IV", "PASSIVE", f"ء{U}1{S}2{I}3"),
    ("V", "PASSIVE", f"ت{U}1{U}2{SH}{I}3"),
    ("VI", "PASSIVE", f"ت{U}1{U}و2{I}3"),
    ("VII", "PASSIVE", f"ان{S}1{U}2{I}3"),
    ("VIII", "PASSIVE", f"ا1{S}ت{U}2{I}3"),
    ("X", "PASSIVE", f"اس{S}ت{U}1{S}2{I}3"),
    ("I-a", "IMPERATIVE", f"ا1{S}2{A}3"),
    ("I-i", "IMPERATIVE", f"ا1{S}2{I}3"),
    ("I-u", "IMPERATIVE", f"ا1{S}2{U}3"),
    ("II", "IMPERATIVE", f"1{A}2{SH}{I}3"),
    ("III", "IMPERATIVE", f"1{A}ا2{I}3"),
    ("IV", "IMPERATIVE", f"ء{A}1{S}2{I}3"),
    ("V", "IMPERATIVE", f"ت{A}1{A}2{SH}{A}3"),
    ("VI", "IMPERATIVE", f"ت{A}1{A}ا2{A}3"),
    ("VII", "IMPERATIVE", f"ان{S}1{A}2{I}3"),
    ("VIII", "IMPERATIVE", f"ا1{S}ت{A}2{I}3"),
    ("X", "IMPERATIVE", f"اس{S}ت{A}1{S}2{I}3"),
)

IMPERATIVE_PERSONS: Final[tuple[tuple[str, str, str], ...]] = (
    ("2MS", S, ""),
    ("2FS", I, "ي"),
    ("2D", A, "ا"),
    ("2MP", U, "وا"),
    ("2FP", S, "نَ"),
)

IFTAAL_TA: Final[dict[str, str]] = {
    **dict.fromkeys("صضطظ", "ط"),
    **dict.fromkeys("دذز", "د"),
    **dict.fromkeys("وي", "ت"),
}
"""تاءُ ‎افتعل‎: طاءً بعد الإطباق، دالًا بعد د ذ ز، والفاءُ الواويّةُ تاءٌ تُدغَم (نقل)."""


def _fill(template: str, root: str) -> str:
    filled = "".join(root[int(ch) - 1] if ch in "123" else ch for ch in template)
    if template.startswith("ا1") and "ت" in template[:6]:
        c1 = root[0]
        if c1 in IFTAAL_TA:
            cut = filled.index("ت", 2)
            filled = filled[:cut] + IFTAAL_TA[c1] + filled[cut + 1 :]
            if c1 in WEAK:
                filled = filled[:1] + "ت" + filled[2:]
    return filled


def _sound(root: str, before_object: bool) -> Forms:
    out: Forms = {}
    for form, kind, template in SOUND_TEMPLATES:
        stem = _fill(template[:-1], root)
        stem3 = stem + root[2]
        if kind == "IMPERATIVE":
            for person, last, suffix in IMPERATIVE_PERSONS:
                for word in _attach(stem3, last, suffix, before_object):
                    _put(out, word, (kind, form, person))
            continue
        for person, last, suffix in VOWEL_PERSONS:
            for word in _attach(stem3, last, suffix, before_object):
                _put(out, word, (kind, form, person))
        for person, suffix in CONSONANT_PERSONS:
            for word in _attach(stem3, S, suffix, before_object):
                _put(out, word, (kind, form, person))
    return out


# --- المضاعف -------------------------------------------------------------------


def _merge_doubled(word: str, root: str, x: str | None = None) -> str:
    """‎X(ح١) X(ح٢) ← Xّ(ح٢)‎ إن تحرّك الثاني، وتنتقل الأولى إلى ما قبلها إن سكن؛ وتسقط ألفُ
    الوصل إن تحرّك ما بعدها (‎امْدُدُوا ← مُدُّوا‎)."""

    x = root[1] if x is None else x
    nfd = unicodedata.normalize("NFD", word)
    letters: list[list[str]] = []
    for ch in nfd:
        if ch in MARKS and letters:
            letters[-1].append(ch)
        else:
            letters.append([ch])
    for k in range(len(letters) - 1, 0, -1):
        first, second = letters[k - 1], letters[k]
        if first[0] != x or second[0] != x:
            continue
        v1 = [m for m in first[1:] if m in (A, I, U)]
        v2 = [m for m in second[1:] if m in (A, I, U)]
        if not v1 or not v2 or SH in first[1:] or SH in second[1:]:
            continue
        before = letters[k - 2] if k >= 2 else None
        if before is not None and before[1:] == [S]:
            letters[k - 2] = [before[0], v1[0]]
        merged = [x, SH, v2[0]]
        letters[k - 1 : k + 1] = [merged]
        if (
            letters[0] == ["ا"]
            and len(letters) > 1
            and any(m in (A, I, U) for m in letters[1][1:])
        ):
            letters = letters[1:]
        break
    return _nfc("".join("".join(c) for c in letters))


def _doubled(root: str, before_object: bool) -> Forms:
    out: Forms = {}
    for word, analyses in _sound(root, before_object).items():
        for analysis in analyses:
            _put(out, _merge_doubled(word, root), analysis)
            if analysis[0] == "IMPERATIVE" and analysis[2] == "2MS":
                _put(out, word, analysis)  # فكُّ الأمر: امْدُدْ
    c1, x = root[0], root[1]
    for v in (A, I, U):  # أمرُ المضاعف المُدغَم بحركة البناء (مُدَّ، فِرَّ)
        for last in (A, I):
            _put(out, _nfc(c1 + v + x + SH + last), ("IMPERATIVE", "I", "2MS"))
    return out


# --- الأجوف --------------------------------------------------------------------

HOLLOW_FAMILIES: Final[tuple[tuple[str, str, str, str, str], ...]] = (
    # ‎(الوزن، قبل الفاء، حركةُ الفاء قبل الألف، ما بين الفاء والعين المحذوفة، حركةُ الفاء
    # حين تُحذف العين)‎؛ والعينُ المعتلّةُ موضعُها بعد الفاء.
    ("IV", f"ء{A}", A, "", A),
    ("VII", f"ان{S}", A, "", A),
    ("VIII", "ا", A, f"{S}ت", A),
    ("X", f"اس{S}ت{A}", A, "", A),
)


def _hollow(root: str, before_object: bool) -> Forms:
    c1, w, c3 = root[0], root[1], root[2]
    out: Forms = {}

    def add(words: list[str], analysis: Form) -> None:
        for word in words:
            _put(out, word, analysis)

    short = (U, I) if w == W else (I,)
    long_amr = {U: W, I: Y, A: "ا"}
    # الثلاثيّ: قَالَ قَالُوا … قُلْتُ / بِعْتُ / خِفْتُ
    for person, last, suffix in VOWEL_PERSONS:
        add(
            _attach(c1 + A + "ا" + c3, last, suffix, before_object),
            ("PAST", "I", person),
        )
        add(
            _attach(c1 + I + Y + c3, last, suffix, before_object),
            ("PASSIVE", "I", person),
        )
    for v in short:
        for person, suffix in CONSONANT_PERSONS:
            add(_attach(c1 + v + c3, S, suffix, before_object), ("PAST", "I", person))
    for person, suffix in CONSONANT_PERSONS:
        add(_attach(c1 + I + c3, S, suffix, before_object), ("PASSIVE", "I", person))
    for v in (U, I, A) if w == W else (I, A):
        for person, last, suffix in IMPERATIVE_PERSONS:
            if last == S:
                stem = c1 + v + c3
            else:
                stem = c1 + v + long_amr[v] + c3
            add(_attach(stem, last, suffix, before_object), ("IMPERATIVE", "I", person))
    # المزيد: أَقَامَ أَقَمْتُ أُقِيمَ أَقِمْ أَقِيمُوا …
    for form, head, _, mid, _ in HOLLOW_FAMILIES:
        if form == "VIII" and c1 in IFTAAL_TA and c1 not in WEAK:
            mid = S + IFTAAL_TA[c1]  # ازْدَادَ، اصْطَادَ
        base = head + c1 + mid
        for person, last, suffix in VOWEL_PERSONS:
            add(
                _attach(base + A + "ا" + c3, last, suffix, before_object),
                ("PAST", form, person),
            )
        for person, suffix in CONSONANT_PERSONS:
            add(
                _attach(base + A + c3, S, suffix, before_object), ("PAST", form, person)
            )
        passive_head = head.replace(A, U) if form in ("IV", "X") else head
        passive_mid = mid.replace(A, U)
        for person, last, suffix in VOWEL_PERSONS:
            add(
                _attach(
                    passive_head + c1 + passive_mid + I + Y + c3,
                    last,
                    suffix,
                    before_object,
                ),
                ("PASSIVE", form, person),
            )
        amr_v = I if form in ("IV", "X") else A
        for person, last, suffix in IMPERATIVE_PERSONS:
            if last == S:
                stem = base + amr_v + c3
            else:
                stem = base + amr_v + long_amr[amr_v] + c3
            add(
                _attach(stem, last, suffix, before_object), ("IMPERATIVE", form, person)
            )
    # II III V VI صحيحةُ العين
    for word, analyses in _sound(root, before_object).items():
        for analysis in analyses:
            if analysis[1] in ("II", "III", "V", "VI"):
                _put(out, word, analysis)
    return out


# --- الناقص --------------------------------------------------------------------

DEFECTIVE_STEMS: Final[tuple[tuple[str, str, str, str], ...]] = (
    # ‎(الوزن، الماضي حتى العين بحركتها، المجهول، الأمر)‎؛ واللامُ بعدها.
    ("II", f"1{A}2{SH}{A}", f"1{U}2{SH}{I}", f"1{A}2{SH}{I}"),
    ("III", f"1{A}ا2{A}", f"1{U}و2{I}", f"1{A}ا2{I}"),
    ("IV", f"ء{A}1{S}2{A}", f"ء{U}1{S}2{I}", f"ء{A}1{S}2{I}"),
    ("V", f"ت{A}1{A}2{SH}{A}", f"ت{U}1{U}2{SH}{I}", f"ت{A}1{A}2{SH}{A}"),
    ("VI", f"ت{A}1{A}ا2{A}", f"ت{U}1{U}و2{I}", f"ت{A}1{A}ا2{A}"),
    ("VII", f"ان{S}1{A}2{A}", f"ان{S}1{U}2{I}", f"ان{S}1{A}2{I}"),
    ("VIII", f"ا1{S}ت{A}2{A}", f"ا1{S}ت{U}2{I}", f"ا1{S}ت{A}2{I}"),
    ("X", f"اس{S}ت{A}1{S}2{A}", f"اس{S}ت{U}1{S}2{I}", f"اس{S}ت{A}1{S}2{I}"),
)


def _past_defective(stem: str, l3: str, before_object: bool) -> list[tuple[str, str]]:
    """ماضٍ ناقصٌ عينُه مفتوحة: ‎دَعَا/رَمَى، دَعَوَا، دَعَوْا، دَعَتْ، دَعَتَا، دَعَوْتُ‎."""

    out: list[tuple[str, str]] = []
    final = "ا" if l3 == W else "ى"
    if _last_letter(stem) == Y:
        final = "ا"  # الياءُ لا تُتبَع بألفٍ مقصورة في الرسم: أَحْيَا، اسْتَحْيَا
    out.append(("3MS", _spell(stem + final)))
    if before_object and final == "ى":
        out.append(("3MS", _spell(stem + "ا")))  # ‎هَدَاهُ، رَآهُ‎: المقصورةُ ألفٌ قبل الضمير
    out.append(("3MD", _spell(stem + l3 + A + "ا")))
    for word in _attach(stem, "", "وْا", before_object):
        out.append(("3MP", word))
    out.append(("3FS", _spell(stem + "تْ")))
    out.append(("3FD", _spell(stem + "تَا")))
    for person, suffix in CONSONANT_PERSONS:
        for word in _attach(stem + l3, S, suffix, before_object):
            out.append((person, word))
    return out


def _past_defective_kasra(stem: str, before_object: bool) -> list[tuple[str, str]]:
    """ماضٍ ناقصٌ عينُه مكسورة (ولامُه ياء): ‎رَضِيَ، رَضِيَا، رَضُوا، رَضِيَتْ، رَضِيتُ‎."""

    out: list[tuple[str, str]] = []
    for person, last, suffix in VOWEL_PERSONS:
        if person == "3MP":
            for word in _attach(_revowel(stem, U), "", "وا", before_object):
                out.append((person, word))  # العينُ تُضمّ وتسقط الياء
            continue
        for word in _attach(stem + Y, last, suffix, before_object):
            out.append((person, word))
    for person, suffix in CONSONANT_PERSONS:
        for word in _attach(stem + Y, "", suffix, before_object):
            out.append((person, word))
    return out


def _last_letter(stem: str) -> str | None:
    for ch in reversed(unicodedata.normalize("NFD", stem)):
        if ch not in MARKS:
            return ch
    return None


def _last_vowel(stem: str) -> str | None:
    for ch in reversed(unicodedata.normalize("NFD", stem)):
        if ch in (A, I, U):
            return ch
        if ch not in MARKS:
            return None
    return None


def _revowel(stem: str, vowel: str) -> str:
    """يُبدِل حركةَ الحرف الأخير ويُبقي شدّتَه."""

    nfd = unicodedata.normalize("NFD", stem)
    k = len(nfd)
    while k and nfd[k - 1] in MARKS:
        k -= 1
    trailing = [m for m in nfd[k:] if m == SH]
    return _nfc(nfd[:k] + "".join(trailing) + vowel)


def _imperative_defective(
    stem: str, l3: str, before_object: bool
) -> list[tuple[str, str]]:
    """أمرُ الناقص بحسب حركة العين: ‎ادْعُ ادْعِي ادْعُوَا ادْعُوا ادْعُونَ / ارْمِ / اخْشَ اخْشَيْ‎."""

    vowel = _last_vowel(stem)
    out: list[tuple[str, str]] = [("2MS", _spell(stem))]
    if vowel == U:
        out += [
            ("2FS", _spell(_revowel(stem, I) + Y)),
            ("2D", _spell(stem + W + A + "ا")),
            ("2FP", _spell(stem + W + "نَ")),
        ]
        out += [("2MP", w) for w in _attach(stem, "", "وا", before_object)]
    elif vowel == I:
        out += [
            ("2FS", _spell(stem + Y)),
            ("2D", _spell(stem + Y + A + "ا")),
            ("2FP", _spell(stem + Y + "نَ")),
        ]
        out += [("2MP", w) for w in _attach(_revowel(stem, U), "", "وا", before_object)]
    else:
        out += [
            ("2FS", _spell(stem + Y + S)),
            ("2D", _spell(stem + Y + A + "ا")),
            ("2FP", _spell(stem + Y + S + "نَ")),
        ]
        out += [("2MP", w) for w in _attach(stem, "", "وْا", before_object)]
    return out


def _defective(root: str, before_object: bool) -> Forms:
    c1, c2, l3 = root[0], root[1], root[2]
    out: Forms = {}

    def add(pairs: list[tuple[str, str]], kind: str, form: str) -> None:
        for person, word in pairs:
            _put(out, word, (kind, form, person))

    add(_past_defective(c1 + A + c2 + A, l3, before_object), "PAST", "I-a")
    add(_past_defective_kasra(c1 + A + c2 + I, before_object), "PAST", "I-i")
    add(_past_defective_kasra(c1 + U + c2 + I, before_object), "PASSIVE", "I")
    lead = "" if c1 == W else "ا" + c1 + S  # اللفيفُ المفروق: قِ، فِ (من يَفْعِلُ وحده)
    for v in (I,) if c1 == W else (U, I, A):
        add(_imperative_defective(lead + c2 + v, l3, before_object), "IMPERATIVE", "I")
    for form, past, passive, amr in DEFECTIVE_STEMS:
        root_y = root[:2] + Y
        add(_past_defective(_fill(past, root_y), Y, before_object), "PAST", form)
        add(
            _past_defective_kasra(_fill(passive, root_y), before_object),
            "PASSIVE",
            form,
        )
        add(
            _imperative_defective(_fill(amr, root_y), Y, before_object),
            "IMPERATIVE",
            form,
        )
    return out


# --- المثال والمهموز -------------------------------------------------------------


def _assimilated_imperative(root: str, before_object: bool) -> Forms:
    """أمرُ المثال الواويّ من ‎يَفْعِلُ‎: تسقط الفاء (‎عِدْ، عِدِي، عِدُوا‎)."""

    out: Forms = {}
    c2, c3 = root[1], root[2]
    for person, last, suffix in IMPERATIVE_PERSONS:
        for word in _attach(c2 + I + c3, last, suffix, before_object):
            _put(out, word, ("IMPERATIVE", "I", person))
    return out


HAMZA_FAA_DROPPED: Final[frozenset[str]] = frozenset({"ءخذ", "ءكل", "ءمر"})


def _hamza_faa_imperative(root: str, before_object: bool) -> Forms:
    """‎خُذْ، كُلْ، مُرْ‎: أمرٌ محذوفُ الفاء المهموزة (سماع)."""

    out: Forms = {}
    for person, last, suffix in IMPERATIVE_PERSONS:
        for word in _attach(root[1] + U + root[2], last, suffix, before_object):
            _put(out, word, ("IMPERATIVE", "I", person))
    return out


# --- التاسعُ والرباعيّ -------------------------------------------------------------

IX_TEMPLATES: Final[tuple[tuple[str, str], ...]] = (
    ("PAST", f"ا1{S}2{A}3{A}3"),
    ("IMPERATIVE", f"ا1{S}2{A}3{I}3"),
)
"""‎افْعَلَّ‎ (الألوان والعيوب: ابْيَضَّ، اسْوَدَّ): لامٌ مضعَّفةٌ تُدغَم إن تحرّكت الثانية."""


def _ninth(root: str, before_object: bool) -> Forms:
    out: Forms = {}
    for kind, template in IX_TEMPLATES:
        stem = _fill(template[:-1], root)
        persons = (
            IMPERATIVE_PERSONS
            if kind == "IMPERATIVE"
            else VOWEL_PERSONS + tuple((p, S, x) for p, x in CONSONANT_PERSONS)
        )
        for person, last, suffix in persons:
            for word in _attach(stem + root[2], last, suffix, before_object):
                _put(out, _merge_doubled(word, root, root[2]), (kind, "IX", person))
    return out


QUAD_TEMPLATES: Final[tuple[tuple[str, str, str], ...]] = (
    ("Q-I", "PAST", f"1{A}2{S}3{A}4"),
    ("Q-I", "PASSIVE", f"1{U}2{S}3{I}4"),
    ("Q-I", "IMPERATIVE", f"1{A}2{S}3{I}4"),
    ("Q-II", "PAST", f"ت{A}1{A}2{S}3{A}4"),
    ("Q-II", "IMPERATIVE", f"ت{A}1{A}2{S}3{A}4"),
    ("Q-IV", "PAST", f"ا1{S}2{A}3{A}4{A}4"),
)
"""الرباعيُّ المجرّد ‎فَعْلَلَ‎ ومزيدُه ‎تَفَعْلَلَ‎ و‎افْعَلَلَّ‎ (اطْمَأَنَّ). وجذورُ الرباعيّ
ليست في جدول المقاييس المودَع، فلا تدخل الفهرس؛ تُرشَّح من حروف السطح وحدها
(`candidate_roots`) وتُعَدّ «جذرًا غائبًا عن المعجم»."""


def _quadriliteral(root: str, before_object: bool) -> Forms:
    out: Forms = {}
    for form, kind, template in QUAD_TEMPLATES:
        filled = "".join(root[int(ch) - 1] if ch in "1234" else ch for ch in template)
        stem = filled[:-1]
        persons = (
            IMPERATIVE_PERSONS
            if kind == "IMPERATIVE"
            else VOWEL_PERSONS + tuple((p, S, x) for p, x in CONSONANT_PERSONS)
        )
        for person, last, suffix in persons:
            head = stem
            if form == "Q-IV" and last == S:  # اطْمَأْنَنْتُمْ: يُفكّ وتنتقل الحركة
                head = _nfc(f"ا{root[0]}{S}{root[1]}{A}{root[2]}{S}{root[3]}{A}")
            for word in _attach(head + root[3], last, suffix, before_object):
                if form == "Q-IV":
                    word = _merge_doubled(word, root, root[3])
                _put(out, word, (kind, form, person))
    return out


ILHAQ_SHAPES: Final[tuple[tuple[str, str, int], ...]] = (
    ("QL", "1234", 19135),  # فَعْلَلَ: «ألحقوا الزيادة من موضع اللام» — جَلْبَبَ، شَمْلَلَ (س19136)
    ("QW", "1و23", 19137),  # فَوْعَلَ: «فوعلت نحو حوقلت حوقلة»
    ("QY", "1ي23", 19137),  # فَيْعَلَ: «فيعلت نحو بيطرت بيطرة وهينمت هينمة» (س19138)
    ("QV", "12و3", 19138),  # فَعْوَلَ: «فعولت نحو جهورة وهرولة هرولة»
)
"""الملحَقُ بالرباعيّ من الثلاثيّ الصحيح على باب الكتاب (JK006989 المختوم في SLGE، س19135–19138): زيادةٌ
تُجري الثلاثيَّ مجرى دَحْرَجَ — لامٌ مكرَّرة، أو واوٌ/ياءٌ ثانيةً، أو واوٌ ثالثةً. الشكلُ: مواضعُ الجذر ‎1 2 3‎
وحرفُ الزيادة بعينه؛ والرابعُ في ‎QL‎ هو الثالثُ مكرَّرًا (‎4 = 3‎). الصورُ على ‎Q-I‎ (ماضٍ ومبنيٌّ
للمجهول وأمر) و‎Q-II‎ (تَفَعْلَلَ: «تجلبب ويتجلبب أجريته مجرى تدحرج»، س21110؛ «يتحوقل»، س19099) — لا
‎Q-IV‎. سماعيٌّ معجمًا قياسيٌّ شكلًا؛ لذلك لا يدخل الفهرسَ المعكوس (`verb_index`) المقيسَ على المرجع،
ويُطلب بـ `derive(root, ilhaq=True)` ويُفحص ردًّا (`test_ilhaq.py`) لا قياسًا."""


def ilhaq_forms(root: str, before_object: bool = False) -> Forms:
    """الملحَقُ بالرباعيّ من جذرٍ ثلاثيٍّ صحيح: الصورةُ ← ‎(الصيغة، الوزن ‎QL/QW/QY/QV‎-I/II، الضمير)‎."""

    root = _seat_free(root)
    out: Forms = {}
    if len(root) != 3 or root_class(root) != "SOUND":
        return out
    for shape, pattern, _ in ILHAQ_SHAPES:
        quad = "".join(root[int(ch) - 1] if ch in "123" else ch for ch in pattern)
        if shape == "QL":
            quad = root + root[2]
        for word, analyses in _quadriliteral(quad, before_object).items():
            for kind, form, person in analyses:
                if form in ("Q-I", "Q-II"):
                    _put(out, word, (kind, f"{shape}-{form[2:]}", person))
    return out


_ASSIMILATING_TA: Final[frozenset[str]] = frozenset("تثدذزسشصضطظ")


def _orthographic_variants(out: Forms, root: str) -> None:
    """صورٌ رسميّةٌ ثابتةٌ بالسماع، تُضاف إلى ما وُلِّد ولا تحلّ محلّه:

    * بعد همزة الاستفهام تسقط ألفُ الوصل (‎أَفْتَرَى، أَسْتَكْبَرْتَ، أَطَّلَعَ‎)؛
    * تاءُ ‎تَفَعَّلَ، تَفَاعَلَ‎ تُدغَم في فاءٍ تقاربها وتُجتلب همزةُ وصل (‎ادَّارَكَ، اطَّهَّرُوا‎)؛
    * المضاعفُ المكسورُ العين تُحذف عينُه قبل الضمير المتحرّك (‎ظَلْتَ، ظَلْتُمْ‎).
    """

    for word, analyses in list(out.items()):
        nfd = unicodedata.normalize("NFD", word)
        if len(nfd) > 3 and nfd[0] == "ا" and nfd[1] not in MARKS and nfd[2] in (S, SH):
            for analysis in analyses:
                _put(out, word[1:], analysis)
        c1 = root[0]
        if c1 in _ASSIMILATING_TA and nfd.startswith("ت" + A + c1):
            for analysis in analyses:
                if analysis[1] in ("V", "VI") and analysis[0] in ("PAST", "IMPERATIVE"):
                    _put(out, _nfc("ا" + c1 + SH + nfd[3:]), analysis)
    if len(root) == 3 and root[1] == root[2] and root[1] not in WEAK:
        for person, suffix in CONSONANT_PERSONS:
            _put(
                out, _spell(root[0] + A + root[1] + S + suffix), ("PAST", "I-i", person)
            )


# --- الجامع --------------------------------------------------------------------


def root_class(root: str) -> str:
    """صنفُ الجذر من حروفه: الناقصُ أوّلًا، ثمّ الأجوف، ثمّ المضاعف، وإلا الصحيح."""

    if root[2] in WEAK:
        return "DEFECTIVE"
    if root[1] in WEAK:
        return "HOLLOW"
    if root[1] == root[2]:
        return "DOUBLED"
    return "SOUND"


def verb_forms(root: str, before_object: bool = False) -> Forms:
    """كلُّ فعلٍ مبنيٍّ مولَّدٍ للجذر: الصورةُ بالاصطلاح ← ‎(الصيغة، الوزن، الضمير)‎."""

    root = _seat_free(root)
    if len(root) == 4:
        quad = _quadriliteral(root, before_object)
        _orthographic_variants(quad, root)
        return quad
    kind = root_class(root)
    if kind == "DEFECTIVE":
        out = _defective(root, before_object)
    elif kind == "HOLLOW":
        out = _hollow(root, before_object)
    elif kind == "DOUBLED":
        out = _doubled(root, before_object)
    else:
        out = _sound(root, before_object)
    extra: list[Forms] = []
    if root[0] == W and kind != "DEFECTIVE":
        extra.append(_assimilated_imperative(root, before_object))
    if root in HAMZA_FAA_DROPPED:
        extra.append(_hamza_faa_imperative(root, before_object))
    if root == "ءخذ":
        extra.append(_sound("تخذ", before_object))  # اتَّخَذَ: إبدالُ الهمزة تاءً (سماع)
    if kind in ("SOUND", "DOUBLED", "HOLLOW"):
        extra.append(_ninth(root, before_object))  # ابْيَضَّ، اسْوَدَّ: العينُ صحيحةٌ فيه
    if kind == "HOLLOW":
        extra.append(
            {
                w: [a for a in an if a[1] == "X"]
                for w, an in _sound(root, before_object).items()
            }
        )  # ‎اسْتَحْوَذَ‎: العاشرُ الأجوفُ مصحَّحًا (سماع)
    for more in extra:
        for word, analyses in more.items():
            for analysis in analyses:
                _put(out, word, analysis)
    for word, analyses in list(out.items()):
        if word.startswith("ا" + H + S):  # ‎فَأْتُوا‎: ألفُ الوصل تسقط بعد السابقة
            for analysis in analyses:
                _put(out, word[1:], analysis)
    _orthographic_variants(out, root)
    return {w: a for w, a in out.items() if a}


_SEATS: Final[dict[str, str]] = {"أ": H, "إ": H, "ؤ": H, "ئ": H, "ء": H}


def _seat_free(text: str) -> str:
    text = _nfc(text).replace("آ", H + A + "ا")
    return "".join(_SEATS.get(ch, ch) for ch in text)


def normalize(form: str) -> str:
    """التطبيعُ المعلن للطرفين: NFC، والكراسيُّ همزة، وآخرُ السكون والكسر والضمّ يُحذف.

    الآخرُ الساكنُ يُحرَّك بالكسر أو الضمّ لالتقاء الساكنين (‎قَالَتِ، تُمُ، ادْعُ‎)،
    فهذه الثلاثُ صنفٌ واحدٌ عند الحدّ. أمّا الفتحُ فلا يُجتلب لذلك في الفعل، فيبقى
    مميِّزًا: ‎قَالَ‎ (ماضٍ) غيرُ ‎قَالِ‎ (أمرٌ من «قالى»).
    """

    form = _seat_free(_nfc(form))
    form = _nfc(form).replace(I + Y + S, I + Y).replace(U + W + S, U + W)
    while form and form[-1] in (I, U, S):
        form = form[:-1]
    if len(form) >= 3 and form[-1] == "ا" and form[-2] in (U, S) and form[-3] == W:
        form = form[:-2] + "ا"  # ‎دَعَوْا / دَعَوُا‎: حركةُ واو الجماعة قبل همزة الوصل
    return form


def candidate_roots(surface: str) -> tuple[str, ...]:
    """جذورٌ مرشَّحةٌ من حروف السطح وحدها (لا من معجم): ثلاثيّاتٌ مرتّبة، ومعها
    زوجٌ تُدرَج فيه واوٌ أو ياءٌ (الأجوف والناقص والمثال) أو يُكرَّر ثانيه (المضاعف)."""

    letters = [ch for ch in _seat_free(normalize(surface)) if ch not in MARKS]
    if letters and letters[0] == "ا":
        letters = letters[1:]
    letters = [ch for ch in letters if ch not in ("ا", "ى")]
    found: list[str] = []

    def add(root: str) -> None:
        if root not in found:
            found.append(root)

    n = len(letters)
    for i in range(n):
        for j in range(i + 1, n):
            x, y = letters[i], letters[j]
            for weak in (W, Y):
                add(x + weak + y)
                add(x + y + weak)
                add(weak + x + y)
            add(x + y + y)
            for k in range(j + 1, n):
                add(x + y + letters[k])
                for m in range(k + 1, n):
                    add(x + y + letters[k] + letters[m])
    return tuple(found)


