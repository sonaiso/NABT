"""Host-authorized local output. Pure gateway replay never enters this module."""
import argparse
from contextlib import closing
import json
from pathlib import Path
import sqlite3

from tools.evidence_lifecycle_v1 import strict_loads
from tools.grammar_catalog import gateway
from tools.grammar_catalog.ntp import request
from tools.grammar_catalog.operations import digest
from tools.lexical_training import report_draft


def checked(lesson):
    req = request("cognitive.lesson", {"lesson": lesson})
    receipt = gateway.run(req)
    verdict = gateway.accept_output(receipt, expected_request=req)
    if not verdict["valid"]:
        raise ValueError("Gateway did not verify the independent report request: " + verdict["status"])
    owner = receipt["execution"]["owner_result"]["owner_result"]
    if owner.get("schema") != report_draft.RESULT:
        raise ValueError("Unexpected lesson owner")
    return receipt, owner


def read_store(path, task_id):
    if not path.exists():
        return None, None
    with closing(sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True, timeout=15)) as db:
        db.execute("BEGIN")
        tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        # A concurrent first writer may not yet have committed the schema.
        if not tables:
            return None, None
        if not {"report_tasks", "report_skills"} <= tables:
            raise ValueError("Not an NTP report-draft store")
        row = db.execute("SELECT input_sha256, draft_body FROM report_tasks WHERE task_id=?", (task_id,)).fetchone()
        memory = db.execute("SELECT examples FROM report_skills WHERE policy=?", (report_draft.POLICY,)).fetchone()
        observation = None if row is None else {"input_sha256": row[0],
                                               "body_sha256": None if row[1] is None else digest(row[1])}
        return observation, None if memory is None else strict_loads(memory[0].encode(), maximum_bytes=4096)


def commit_task(path, owner):
    """Single durable commit for the decision, actual document and reusable lesson."""
    with closing(sqlite3.connect(path, timeout=15)) as db, db:
        db.execute("PRAGMA synchronous=FULL")
        db.execute("BEGIN IMMEDIATE")
        db.execute("CREATE TABLE IF NOT EXISTS report_tasks (task_id TEXT PRIMARY KEY, input_sha256 TEXT NOT NULL, draft_body TEXT)")
        db.execute("CREATE TABLE IF NOT EXISTS report_skills (policy TEXT PRIMARY KEY, examples TEXT NOT NULL)")
        db.execute("INSERT INTO report_tasks VALUES (?,?,?) ON CONFLICT(task_id) DO NOTHING",
                   (owner["task_id"], owner["input_sha256"], owner.get("draft_body")))
        db.execute("INSERT INTO report_skills VALUES (?,?) ON CONFLICT(policy) DO NOTHING",
                   (report_draft.POLICY, json.dumps(owner["learning"]["examples"])))


def run(lesson, path, *, apply):
    # Only host observations may enter the operational interface.
    if type(lesson) is not dict or set(lesson) != {"schema", "instruction", "reports", "task_id"} or lesson["schema"] != report_draft.SCHEMA:
        raise ValueError("Expected an original report task")
    report_draft.validated(lesson)
    observed, prior = read_store(path, lesson["task_id"])
    bound = dict(lesson, store_observation=observed)
    if prior is not None:
        bound["prior_examples"] = prior
    receipt, owner = checked(bound)
    if (not apply or owner["status"] not in ("DRAFT_PLANNED", "NO_DRAFT")
            or owner["draft_observation"] != "ABSENT_IN_SNAPSHOT"):
        return receipt
    commit_task(path, owner)
    # A crash here leaves the completed operation retrievable by its logical ID.
    observed, _ = read_store(path, lesson["task_id"])
    return checked(dict(bound, store_observation=observed))[0]


def cli(argv):
    parser = argparse.ArgumentParser(prog="python -m tools.ntp " + argv[0])
    parser.add_argument("--text", required=True, help="original Arabic instruction")
    parser.add_argument("--reports", type=Path, required=True, help="JSON list of immutable local report snapshots")
    parser.add_argument("--task-id", required=True, help="stable logical operation ID, reused after interruption")
    parser.add_argument("--store", type=Path, required=True, help="local SQLite draft store")
    args = parser.parse_args(argv[1:])
    if args.store.resolve() == args.reports.resolve():
        parser.error("Draft store and report sources must be distinct")
    try:
        with args.reports.open("rb") as source:
            reports = strict_loads(source.read(gateway.MAX_REQUEST + 1), maximum_bytes=gateway.MAX_REQUEST)
        lesson = {"schema": report_draft.SCHEMA, "instruction": args.text, "task_id": args.task_id, "reports": reports}
        receipt = run(lesson, args.store, apply=argv[0] == "draft")
    except (OSError, ValueError, sqlite3.Error) as error:
        parser.exit(2, str(error) + "\n")
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
    owner = receipt["execution"]["owner_result"]["owner_result"]
    if owner.get("draft_observation") in ("STORE_MISMATCH", "TASK_ID_CONFLICT"):
        return 4
    if owner["status"] not in ("COUNTED", "NO_DRAFT", "DRAFT_PLANNED"):
        return 3
    if owner["status"] == "DRAFT_PLANNED" and owner.get("draft_observation") != "MATCHED_SNAPSHOT":
        return 3
    return 0
