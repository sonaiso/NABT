"""Small independent oracle, using letter identities and phase descriptions.

This is a second implementation of the declared source law, not a claim that
the law covers attested Arabic. It deliberately does not import runtime code
or the exported transition table. Source: Mashru/SLGE/Law.lean at df6bcc9.
"""

from collections import defaultdict

CANONICAL = tuple("ابتثجحخدذرزسشصضطظعغفقكلمنهويء")
GROUPS = ("ءها", "عح", "غخ", "ق", "ك", "جشي", "ض", "ل", "ن", "ر", "طدت", "زسص", "ظذث", "ف", "بمو")
SLGE = tuple("".join(GROUPS))
PLACE = {letter: place for place, group in enumerate(GROUPS) for letter in group}
WEAK = frozenset("اوي")
MADD = ("ا", "و", "ي")
DEAD = 96


def cell(letter, state):
    return 4 * CANONICAL.index(letter) + state


def forbidden_adjacency(left, right):
    return left != right and left not in WEAK and right not in WEAK and PLACE[left] == PLACE[right]


def transition(q, a):
    letter, vowel = CANONICAL[a // 4], a % 4
    radix = SLGE.index(letter)
    weight = int(not (q in (1, 2, 3) and vowel == 3 and letter == MADD[q - 1]))
    if q == DEAD or (letter == "ا" and (vowel != 3 or q != 1)):
        return DEAD, weight
    if vowel != 3:
        # A moving consonant opens a new CV unless the previous coda constrains it.
        if q in (0, 1, 2, 3, 4, 37):
            return 1 + vowel, weight
        if 6 <= q <= 34:
            return (1 + vowel if letter == SLGE[q - 6] else DEAD), weight
        if 38 <= q <= 66:
            return (1 + vowel if letter == SLGE[q - 38] else DEAD), weight
        if 67 <= q <= 95:
            return (DEAD if forbidden_adjacency(SLGE[q - 67], letter) else 1 + vowel), weight
        return DEAD, weight
    # Silent letters become madd, a coda, or a terminal double coda.
    if q in (1, 2, 3):
        return (4 if letter == MADD[q - 1] else 67 + radix), weight
    if q == 4:
        return 6 + radix, weight
    if 67 <= q <= 95:
        return 35, weight
    if 6 <= q <= 34:
        return 36, weight
    return DEAD, weight


def final(q, mode):
    return q in range(1, 35 if mode == "wasl" else 37) or q in range(67, 96)


def potential(q):
    if q == 0:
        return 0
    if q in (1, 2, 3, 35) or 67 <= q <= 95:
        return 2
    if 4 <= q <= 34 or q == 36:
        return 1
    return 0


def run(cells, mode="waqf", start=0):
    q, weight = start, 0
    for a in cells:
        q, added = transition(q, a)
        weight += added
    return final(q, mode), q, weight


def forward_count(weight, mode, start=0):
    """Forward dynamic program by exact length, distinct from recursive suffix C."""
    frontier = {(start, 0): 1}
    result = 0
    for _length in range(3 * weight + potential(start) + 1):
        result += sum(multiplicity for (q, w), multiplicity in frontier.items()
                      if w == weight and final(q, mode))
        following = defaultdict(int)
        for (q, w), multiplicity in frontier.items():
            for a in range(116):
                target, added = transition(q, a)
                if target != DEAD and w + added <= weight:
                    following[target, w + added] += multiplicity
        frontier = following
    return result


def grade_one_words():
    """Independent structural enumeration: CV and matching CVV, 28*3 each."""
    words = []
    for consonant in CANONICAL:
        if consonant == "ا":
            continue
        for vowel in range(3):
            head = cell(consonant, vowel)
            words.extend(((head,), (head, cell(MADD[vowel], 3))))
    return sorted(words)


def polynomial_number(cells):
    """Closed positional sum, not a copy of the runtime folding encoder."""
    return sum((a + 1) * 116 ** (len(cells) - i - 1) for i, a in enumerate(cells))
