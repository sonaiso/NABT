"""Source admission, withdrawals and independent replay of the NTP batch."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from tools.grammar_catalog import dictionary_reading, gateway, ntp
from tools.lexical_training import dictionary_deposit as deposit, teaching


ROOT = Path(__file__).resolve().parents[1]


def request(*queries, withdrawn=()):
    entries = [{"source": source, "term": term} for source, term in queries]
    return {"schema": deposit.SCHEMA, "queries": entries, "withdraw_sources": list(withdrawn)}


class DictionaryDepositTests(unittest.TestCase):
    def test_installed_batch_checks_every_quote_against_the_retained_source(self):
        data = json.loads((ROOT / "examples/io_gateway/ntl_dictionary_deposit.json").read_text())
        task = data["payload"]["input"]["lesson"]
        result = teaching.run_lesson(task)
        self.assertEqual(len(task["queries"]), result["total_queries"])
        self.assertEqual(result["counts"], {"SOURCE_ATTESTED": 45, "NOT_INDEXED": 4})
        sources = {key: (ROOT / s["path"]).read_bytes() for key, s in result["sources"].items()}
        for key, raw in sources.items():
            self.assertEqual(sha256(raw).hexdigest(), result["sources"][key]["sha256"])
        for i, row in enumerate(result["rows"]):
            self.assertEqual(row["position"], i)
            self.assertEqual(task["queries"][i], {k: row[k] for k in ("source","term")})
            for evidence in row["evidence"]:
                raw = sources[row["source"]]
                if row["source"] == "mukhtar":
                    citation = evidence["citation"]
                    start, end = citation["gloss_span"]
                    self.assertEqual(raw[start:end].decode(),citation["quotation"])
                    self.assertEqual(citation["source_sha256"],result["sources"]["mukhtar"]["sha256"])
                else:
                    block = raw[evidence["start_byte"]:evidence["end_byte"]]
                    self.assertEqual(block.decode(), evidence["raw_block"])
                    self.assertEqual(sha256(block).hexdigest(), evidence["block_sha256"])
        self.assertFalse(result["world_truth_established"])
        self.assertFalse(result["intended_sense_established"])

    def test_alternatives_isolation_withdrawal_and_partial_failure(self):
        task = request(("mukhtar","عين"), ("maqayis","كتب"), ("mukhtar","ناقص_في_الفهرس"))
        first = deposit.run(task)
        self.assertEqual({a["sense_id"] for a in first["rows"][0]["evidence"]},
                         {"mukhtar:eye","mukhtar:spring","mukhtar:spy"})
        first["rows"][0]["evidence"][0]["citation"]["gloss_span"][0] = -1
        self.assertGreater(deposit.run(task)["rows"][0]["evidence"][0]["citation"]["gloss_span"][0],0)
        withdrawn = deposit.run(dict(task, withdraw_sources=["maqayis"]))
        self.assertEqual(withdrawn["counts"],{"SOURCE_ATTESTED":1,"SOURCE_WITHDRAWN":1,"NOT_INDEXED":1})
        self.assertFalse(withdrawn["rows"][1]["evidence"])
        with TemporaryDirectory() as directory:
            path = Path(directory)/"wrong.txt"
            with patch.object(dictionary_reading, "SOURCE", path):
                self.assertEqual(deposit.run(task)["counts"], {"SOURCE_UNAVAILABLE":2,"SOURCE_ATTESTED":1})
                path.write_bytes(b"changed source")
                result = deposit.run(task)
        self.assertEqual(result["counts"], {"SOURCE_VERIFICATION_FAILED":2,"SOURCE_ATTESTED":1})
        self.assertEqual(result["rows"][1], first["rows"][1])

    def test_caller_cannot_supply_an_authority_or_hit(self):
        task = request(("mukhtar","قلم"), ("maqayis","كتب"))
        task["queries"][0]["license"] = "WORLD_TRUE"
        self.assertEqual(teaching.run_lesson(task)["counts"], {"INVALID_QUERY":1,"SOURCE_ATTESTED":1})
        self.assertEqual(teaching.run_lesson(dict(task, authority="SIGNED"))["status"],"INVALID_INPUT")
        self.assertEqual(teaching.run_lesson(dict(task, withdraw_sources=["mukhtar","mukhtar"]))["status"],"INVALID_INPUT")
        self.assertEqual(teaching.run_lesson(dict(task, queries=task["queries"]*33))["status"],"RESOURCE_LIMIT")

    def test_external_receipt_requires_original_request_and_untampered_quotes(self):
        lesson = request(("mukhtar","عين"), ("maqayis","كتب"))
        req = ntp.request("cognitive.lesson", {"lesson":lesson})
        receipt = gateway.run(req)
        self.assertTrue(gateway.accept_output(receipt,expected_request=req)["valid"])
        ntp_result = receipt["execution"]["owner_result"]
        self.assertEqual(ntp_result["recursive_observations"],[])
        self.assertEqual(ntp_result["owner_result"]["counts"],{"SOURCE_ATTESTED":2})
        self.assertEqual(ntp_result["observation_coverage"],"NO_REQUEST_TEXT_SOURCE")
        changed = deepcopy(req)
        changed["payload"]["input"]["lesson"]["withdraw_sources"] = ["mukhtar"]
        self.assertFalse(gateway.accept_output(receipt,expected_request=changed)["valid"])
        ntp_result["owner_result"]["rows"][0]["evidence"][0]["citation"]["quotation"] = "قول مدسوس"
        self.assertFalse(gateway.accept_output(receipt,expected_request=req)["valid"])
