"""Independent, synthetic receipt attacks; never reads the v3 gold or packets."""
from copy import deepcopy
from hashlib import sha256
import json
import unittest

from tools import sourced_acquisition_v3_checks as checks


BINDING = dict(source_id="review:synthetic", revision="1", scope="synthetic-review",
               ending="wasl", onset="word_initial")


def span(text, start, end):
    return {"start": start, "end": end, "byte_start": len(text[:start].encode()),
            "byte_end": len(text[:end].encode()), "raw": text[start:end]}


def byte_span(text, start, end):
    raw = text[start:end].encode()
    return {"start_byte": len(text[:start].encode()), "end_byte": len(text[:end].encode()),
            "raw_text": text[start:end], "sha256": sha256(raw).hexdigest()}


def shape(cells, mode):
    # This is deliberately only structural evidence, not a generated or checked
    # machine certificate. The helper must never claim otherwise.
    return {"status": "SHAPE_LICENSED", "mode": mode, "certificate": {
        "cells": cells[:], "mode": mode, "alphabet_id": "nabt.a116.v1",
        "source_text": None, "source_sha256": None, "start_state": 0,
        "cell_length": len(cells), "certificate_type": "WORD_SHAPE"}}


def receipt(*, onset="word_initial", v3=True, scope=None, ending="wasl", person=False):
    binding = {**BINDING, "onset": onset, "scope": scope or BINDING["scope"], "ending": ending}
    text = "قُمْتُ" if person else "بَ ابَ"
    rows = [(0, 2, [73]), (2, 4, [83]), (4, 6, [17])] if person else [
        (0, 2, [0]), (2, 3, []), (3, 4, [112]), (4, 6, [0])]
    ranges = [(0, 6)] if person else [(0, 2), (3, 6)]
    pieces = [{**span(text, start, end), "cells": cells, "status": "BOUNDARY" if text[start:end] == " " else "LICENSED",
               "rule": "SYNTHETIC"} for start, end, cells in rows]
    words = [{**span(text, start, end), "status": "ACQUIRED",
              "cells": [cell for piece in pieces if start <= piece["start"] < end for cell in piece["cells"]]}
             for start, end in ranges]
    acquisition = {**binding, "text": text, "law_id": "nabt.sourced-acquisition.v3" if v3 else "nabt.aligned-acquisition.v2",
                   "alphabet_id": "nabt.a116.v1", "status": "ACQUIRED", "pieces": pieces, "words": words}
    result = {"status": "ACQUIRED", "verified": True, "onset": onset, "acquisition": acquisition,
              "shape_handoffs": [], "world_truth": "NOT_ESTABLISHED"}
    if v3:
        realized = deepcopy(pieces)
        if onset == "connected" and not person:
            realized[2].update(cells=[], rule="ARTICLE_WASL_ELISION")
        realized_words = [{**word, "cells": [cell for piece in realized
                            if word["start"] <= piece["start"] < word["end"] for cell in piece["cells"]]}
                          for word in words]
        offset = 0
        for piece in realized:
            piece.update(cell_start=offset if onset == "connected" else None,
                         cell_end=offset + len(piece["cells"]) if onset == "connected" else None)
            offset += len(piece["cells"])
        joins = [] if person else [{"left_word": 0, "right_word": 1, "elided": onset == "connected",
            "status": "JOINED" if onset == "connected" else "CITATION_BOUNDARY",
            "rule": "ARTICLE_WASL_ELISION" if onset == "connected" else "CITATION_BOUNDARY", "span": span(text, 2, 3)}]
        phrase = [cell for piece in realized for cell in piece["cells"]] if onset == "connected" else []
        result.update(shape_verified=True, phrase_shape=shape(phrase, ending) if onset == "connected" else None,
            realization={"mode": onset, "status": "REALIZED", "pieces": realized, "words": realized_words,
                         "joins": joins, "phrase_cells": phrase})
    if onset == "word_initial":
        result["shape_handoffs"] = [{"word_index": index,
            "span": {key: word[key] for key in ("start", "end", "byte_start", "byte_end")},
            **shape(word["cells"], ending if index == len(words) - 1 else "wasl")} for index, word in enumerate(words)]
    return result


def audit(entry, report, *, text="بَ ابَ", **kwargs):
    return checks.audit_report(entry, report, text=text, **{**BINDING, **kwargs})


def natural(text="عين جارية", selected=True):
    start, end = text.index("عين"), text.index("عين") + 3
    occurrence_span = byte_span(text, start, end)
    frame = {"expression": "العين", "convention": "linguistic", "occurrence": {
        "source": BINDING["source_id"], "revision": "1", "raw": text,
        "start_byte": occurrence_span["start_byte"], "end_byte": occurrence_span["end_byte"],
        "referent": "unresolved", "time": "unspecified", "context": BINDING["scope"]}}
    candidate = {"intended_sense": "ayn_spring", "designation": {"id": "synthetic"}, "relation": None}
    row = {"sense_id": "ayn_spring", "candidate": candidate, "support_status": "SUPPORTED_PREMISES",
           "native_use_kind": "literal_origin"}
    selection = ["ayn_spring"] if selected else []
    occurrence = {"expression": "العين", "span": occurrence_span, "candidates": [row],
        "selected_sense_ids": selection, "native_checked": True,
        "native_request": {"frame": frame, "proposed": [candidate], "known": [
            {"scope": BINDING["scope"], "positive": True, "value": {"kind": "used", "frame": frame, "sense": "ayn_spring"}}]},
        "native_result": {"status": "CHECKED", "law_id": "nabt.linguistic-truth.v1",
            "authority": "CONDITIONAL_SUPPLIED_LEDGER", "complete_proposal": True,
            "all_arabic_senses_enumerated": False, "world_truth_asserted": False,
            "rows": [{"candidate": candidate, "kind": "literal_origin", "verdict": "SUPPORTED_PREMISES"}]}}
    if selected:
        occurrence["cue_span"] = byte_span(text, 0, len(text))
    return {"status": "COMPLETE" if selected else "UNKNOWN", "binding": BINDING.copy(),
        "source": {"source_id": BINDING["source_id"], "revision": "1", "raw_text": text,
                   "sha256": sha256(text.encode()).hexdigest(), "bytes": len(text.encode())},
        "occurrences": [occurrence], "candidate_sense_ids": ["ayn_spring"], "selected_sense_ids": selection,
        "native_checked": True, "semantic_scope_complete": selected, "chain_complete": False,
        "acquisition": {"status": "DEFER", "verified": False, "shape_verified": False},
        "world_truth_established": False, "author_intention_established": False}


def person():
    acquired = receipt(person=True)
    text = acquired["acquisition"]["text"]
    token = {**span(text, 0, 6), "lexeme": "QUMTU"}
    projection = {"word_index": 0, "source_word": token, "source_suffix": span(text, 4, 6),
                  "person": 1, "source_vowel": "ُ", "referent": None}
    native = {**BINDING, "text": text, "task": "person", "law_id": "nabt.acquired-syntax.v3",
        "status": "LICENSED_PERSON", "reading_id": "QUMTU", "tokens": [token],
        "source_pieces": [span(text, 0, 2), span(text, 2, 4), span(text, 4, 6)],
        "person": projection, "nominal": None}
    return {"status": "LICENSED_PERSON", "verified": True, "chain_complete": True,
        "binding": BINDING.copy(), "task": "person", "source_sha256": sha256(text.encode()).hexdigest(),
        "acquisition": acquired, "syntax": {"verified": True, "native_result": native, "status": "LICENSED_PERSON"},
        "gates": {key: True for key in checks.PERSON_GATES}, "person": projection, "nominal": None}


def conditional():
    text = "بَ ابَ"
    scope = json.dumps({"scope": BINDING["scope"], "time": "unspecified"}, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    source = {"source_id": BINDING["source_id"], "revision": "1", "raw_text": text,
              "bytes": len(text.encode()), "sha256": sha256(text.encode()).hexdigest()}
    licensed = {"verified": True, "native_checked": True, "closures_checked": True, "all_readings_complete": True,
        "status": "UNKNOWN", "aggregate": {"positive": False, "negative": False}, "source": source,
        "query": {key: source[key] for key in ("raw_text", "bytes", "sha256")},
        "binding": {"source_id": BINDING["source_id"], "revision": "1", "scope": BINDING["scope"],
                    "time": "unspecified", "native_scope": scope},
        "proposal": {"law_id": "nabt.licensed-inference.v1", "source": {
            "identity": BINDING["source_id"], "revision": "1", "scope": scope, "text": text}, "query_text": text}}
    licensed["native_result"] = {"law_id": "nabt.licensed-inference.v1", "verified": True,
        "source_text": text, "query_text": text, "source_id": BINDING["source_id"], "revision": "1", "source_scope": scope,
        "status": licensed["status"], "aggregate": licensed["aggregate"]}
    return {"status": "UNKNOWN", "verified": True, "chain_complete": True,
        "binding": {"source_id": BINDING["source_id"], "revision": "1", "scope": BINDING["scope"],
            "time": "unspecified", "native_scope": scope, "onset": "word_initial", "source_ending": "wasl", "query_ending": "waqf"},
        "source_acquisition": receipt(v3=False, scope=scope), "query_acquisition": receipt(v3=False, scope=scope, ending="waqf"),
        "licensed_inference": licensed, "gates": {key: True for key in checks.PR34_GATES},
        "answer": {"status": licensed["status"], "aggregate": licensed["aggregate"]}}


class IndependentSourceAndChainReview(unittest.TestCase):
    def assert_safe(self, result):
        self.assertTrue(result["source_safe"], result)
        self.assertTrue(result["chain_safe"], result)
        self.assertTrue(result["claim_safe"], result)

    def test_citation_and_retained_empty_elision_are_structurally_safe(self):
        for onset in ("word_initial", "connected"):
            self.assert_safe(audit("connected", receipt(onset=onset), onset=onset))

    def test_source_piece_cannot_cross_a_word_boundary_even_if_text_restores(self):
        report = receipt()
        p = report["acquisition"]["pieces"]
        p[:3] = [{**span("بَ ابَ", 0, 4), "cells": [0, 112]}]
        result = audit("connected", report)
        self.assertTrue(result["source_checks"][0]["restoration"])
        self.assertFalse(result["source_checks"][0]["word_members"])
        self.assertFalse(result["source_safe"])

    def test_realization_cannot_hide_source_mutation_or_elided_piece_deletion(self):
        for mutate in (lambda r: r["pieces"].pop(2),
                       lambda r: r["pieces"][2].update(raw=""),
                       lambda r: r["words"][1].update(start=2),
                       lambda r: r["joins"][0].update(left_word=False)):
            report = receipt(onset="connected")
            mutate(report["realization"])
            self.assertFalse(audit("connected", report, onset="connected")["source_safe"])

    def test_realization_membership_is_checked_separately_from_citation(self):
        report = receipt(onset="connected")
        p = report["realization"]["pieces"]
        p[:3] = [{**span("بَ ابَ", 0, 4), "cells": [0], "cell_start": 0, "cell_end": 1}]
        result = audit("connected", report, onset="connected")
        self.assertTrue(all(result["source_checks"][0].values()))
        self.assertFalse(result["realization_checks"][0]["geometry"])

    def test_phrase_intervals_and_shape_cells_are_not_authorized_by_flags(self):
        mutations = (lambda r: r["realization"]["pieces"][2].update(cell_end=True),
                     lambda r: r["realization"].update(phrase_cells=[0, 0, 0]),
                     lambda r: r["phrase_shape"]["certificate"].update(cells=[0, 1]),
                     lambda r: r["realization"]["pieces"][2].update(cells=[112]))
        for mutate in mutations:
            report = receipt(onset="connected"); mutate(report)
            self.assertFalse(audit("connected", report, onset="connected")["chain_safe"])

    def test_typed_coordinates_cells_flags_and_exact_request_binding(self):
        mutations = (lambda r: r["acquisition"]["pieces"][0].update(start=False),
                     lambda r: r["acquisition"]["pieces"][0].update(cells=[False]),
                     lambda r: r["acquisition"].update(revision="other"),
                     lambda r: r.update(shape_verified=1),
                     lambda r: r["shape_handoffs"][0].update(word_index=False))
        for mutate in mutations:
            report = receipt(); mutate(report)
            self.assertFalse(audit("connected", report)["chain_safe"])

    def test_semantic_completion_does_not_require_complete_sound_acquisition(self):
        report = natural()
        self.assert_safe(audit("natural", report, text="عين جارية"))
        report["chain_complete"] = True
        self.assertFalse(audit("natural", report, text="عين جارية")["chain_safe"])

    def test_natural_native_occurrence_and_premise_bindings_are_exact(self):
        mutations = (lambda r: r["occurrences"][0]["native_request"]["frame"]["occurrence"].update(raw="عين باصرة"),
                     lambda r: r["occurrences"][0]["native_request"]["known"][0].update(scope="foreign"),
                     lambda r: r["occurrences"][0]["candidates"][0].update(sense_id="different"),
                     lambda r: r["occurrences"][0]["native_result"]["rows"][0].update(verdict="UNKNOWN_PREMISE"),
                     lambda r: r["occurrences"][0].pop("cue_span"))
        for mutate in mutations:
            report = natural(); mutate(report)
            self.assertFalse(audit("natural", report, text="عين جارية")["claim_safe"])

    def test_unknown_quoted_and_unicode_separated_retrieval_stays_safe(self):
        for text in ("'عين'", "`عين`", "«عين»", "قال\u00a0عين"):
            self.assert_safe(audit("natural", natural(text, selected=False), text=text))

    def test_person_native_projection_and_suffix_are_source_bound(self):
        self.assert_safe(audit("person_nominal", person(), text="قُمْتُ", task="person"))
        mutations = (lambda r: r["syntax"]["native_result"].update(text="قُمْتَ"),
                     lambda r: r["person"].update(word_index=False),
                     lambda r: r["person"].update(source_suffix=span("قُمْتُ", 2, 4)),
                     lambda r: r.update(chain_complete=False),
                     lambda r: r.update(gates={"anything": True}),
                     lambda r: r["acquisition"].update(verified=False))
        for mutate in mutations:
            report = person(); mutate(report)
            self.assertFalse(audit("person_nominal", report, text="قُمْتُ", task="person")["chain_safe"])

    def test_pr34_exact_gate_set_and_native_binding_even_for_unknown_answer(self):
        kwargs = dict(query="بَ ابَ", query_ending="waqf")
        self.assert_safe(audit("conditional_pr34", conditional(), **kwargs))
        mutations = (lambda r: r.update(gates={"anything": True}),
                     lambda r: r["gates"].update(extra=True),
                     lambda r: r["gates"].update(source_shapes=1),
                     lambda r: r["query_acquisition"].update(verified=False),
                     lambda r: r["licensed_inference"]["native_result"].update(query_text="foreign"),
                     lambda r: r["licensed_inference"]["proposal"]["source"].update(scope="foreign"))
        for mutate in mutations:
            report = conditional(); mutate(report)
            self.assertFalse(audit("conditional_pr34", report, **kwargs)["chain_safe"])

    def test_bounded_non_json_and_cyclic_reports_fail_closed(self):
        report = receipt(); report["cycle"] = report
        self.assertFalse(audit("connected", report)["claim_safe"])
        report = receipt(); report["tuple"] = (1, 2)
        self.assertFalse(audit("connected", report)["claim_safe"])


if __name__ == "__main__":
    unittest.main()
