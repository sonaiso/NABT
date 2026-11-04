"""Plan, isolate, execute, observe and recheck a proposed repository change."""
from __future__ import annotations

import os
from pathlib import Path
import re
import signal
import subprocess
import time

from tools.entropy_framework.reuse import build_reuse_report

from . import SCHEMA
from . import policy, repository, state
from .policy import AgentError, canonical, digest, require

ROOT = Path(__file__).resolve().parents[2]
MAX_LOG_BYTES = 8 * 1024 * 1024


def identity():
    paths = sorted(Path(__file__).parent.glob("*.py"))
    paths += [ROOT / "tools/entropy_framework" / x for x in ("reuse.py", "reuse_run.py", "registry.py")]
    return {p.relative_to(ROOT).as_posix(): digest(p.read_bytes()) for p in paths}


def inspect(root=ROOT):
    root = Path(root).resolve()
    report = build_reuse_report(root)
    return {"head": repository.git(root, "rev-parse", "HEAD").decode().strip(),
            "tree": repository.git(root, "rev-parse", "HEAD^{tree}").decode().strip(),
            "instructions": {"path": "AGENTS.md", "sha256": digest((root / "AGENTS.md").read_bytes())},
            "catalogue": report["catalogue"], "population": report["population"],
            "families": report["families"], "open_bridge_debts": report["open_bridge_debts"],
            "semantic_authority": "NONE", "runtime_execution_performed": False}


def plan(task, proposal, *, root=ROOT):
    root = Path(root).resolve()
    policy.validate(task, proposal)
    repository.clean(root, task["base_commit"])
    repository.validate_before(root, proposal)
    inventory = inspect(root)
    paths = sorted(c["path"] for c in proposal["changes"])
    protected = {p for family in inventory["families"] for p in family["checker_paths"]}
    require(not (set(paths) & protected), "PROTECTED_PATH",
            "proposals cannot replace registered acceptance checkers: " + ", ".join(sorted(set(paths) & protected)))
    owners, selected = {}, []
    for relative in paths:
        owners[relative] = []
        for family in inventory["families"]:
            formal_paths = {"formal/" + module.replace(".", "/") + ".lean" for module in family["formal_modules"]}
            references = formal_paths | {p for key in ("runtime_paths", "checker_paths", "test_paths", "doc_paths") for p in family[key]}
            if relative in references:
                owners[relative].append(family["id"])
                if family not in selected:
                    selected.append(family)
    return {"schema": "nabt.repo-agent.plan.v1", "policy": policy.POLICY,
            "controller_inputs": identity(), "base_commit": inventory["head"], "base_tree": inventory["tree"],
            "task_sha256": digest(canonical(task)), "proposal_sha256": digest(canonical(proposal)),
            "instructions": inventory["instructions"], "catalogue": inventory["catalogue"],
            "paths": paths, "owners": owners, "unmapped_paths": [p for p in paths if not owners[p]],
            "owner_contracts": [{k: f[k] for k in ("id", "scope", "open_debts", "entrypoint_ids", "native_targets", "test_paths")} for f in selected],
            "checks": policy.checks(paths, selected, root=root),
            "acceptance_review": {"status": "NOT_AUTOMATICALLY_ASSESSED", "criteria": task["acceptance"]},
            "semantic_authority": "NONE", "publication_authority": "NONE"}


def environment(root):
    # This avoids passing API tokens by accident. It is not a security sandbox:
    # child Python code still has the permissions of the invoking OS user.
    result = {k: os.environ[k] for k in ("PATH", "SYSTEMROOT", "LANG", "LC_ALL", "TMPDIR", "TEMP", "TMP", "ELAN_HOME") if k in os.environ}
    result["PYTHONPATH"] = os.pathsep.join((str(root / "src"), str(root)))
    result["PYTHONDONTWRITEBYTECODE"] = "1"
    return result


def execute(check, root, directory):
    stdout_path, stderr_path = directory / (check["id"] + ".stdout"), directory / (check["id"] + ".stderr")
    status, returncode, process = "UNAVAILABLE", None, None
    started = time.monotonic()
    try:
        with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
            try:
                process = subprocess.Popen(check["argv"], cwd=root / check["cwd"], env=environment(root),
                                           stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr,
                                           start_new_session=True)
            except OSError as error:
                stderr.write((type(error).__name__ + ": command unavailable\n").encode())
            if process is not None:
                status = "RUNNING"
                while process.poll() is None:
                    if time.monotonic() - started > check["timeout"]:
                        status = "TIMEOUT"
                        break
                    if stdout_path.stat().st_size + stderr_path.stat().st_size > MAX_LOG_BYTES:
                        status = "RESOURCE_LIMIT"
                        break
                    time.sleep(0.02)
                if status == "RUNNING":
                    status = "PASSED" if process.returncode == 0 else "FAILED"
    finally:
        # Kill the process group even if its leader exited while leaving children.
        if process is not None:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            returncode = process.wait()
    if stdout_path.stat().st_size + stderr_path.stat().st_size > MAX_LOG_BYTES:
        status = "RESOURCE_LIMIT"
    logs = {}
    for name, path in (("stdout", stdout_path), ("stderr", stderr_path)):
        # Retain a bounded prefix on overflow; never call it a complete log.
        truncated = path.stat().st_size > MAX_LOG_BYTES
        if truncated:
            with path.open("r+b") as handle:
                handle.truncate(MAX_LOG_BYTES)
        logs[name] = {"sha256": digest(path.read_bytes()), "bytes": path.stat().st_size, "truncated": truncated}
    return {"id": check["id"], "argv": check["argv"], "cwd": check["cwd"], "timeout": check["timeout"],
            "status": status, "returncode": returncode, "logs": logs}


def run(task, proposal, *, root=ROOT, output_dir):
    root = Path(root).resolve()
    planned = plan(task, proposal, root=root)
    directory = state.create_directory(root, output_dir)
    candidate = directory / "worktree"
    report = {"schema": SCHEMA, "plan": planned, "checks": [], "candidate_tree": None, "candidate_snapshot": None,
              "candidate_commit": None, "candidate_ref": None, "worktree": str(candidate),
              "semantic_authority": "NONE", "publication_authority": "NONE"}
    journal = state.Journal(directory, report)
    state.write_json(directory / "task.json", task)
    state.write_json(directory / "proposal.json", proposal)
    state.write_json(directory / "plan.json", planned)
    journal.event("PLANNED")
    try:
        repository.worktree(root, candidate, task["base_commit"])
        journal.event("ISOLATED")
        expected = repository.apply(candidate, proposal)
        report["candidate_tree"] = expected["index_tree"]
        report["candidate_snapshot"] = expected
        patch = repository.git(candidate, "diff", "--cached", "--binary", "--no-ext-diff", "--no-textconv")
        require(len(patch) <= 2 * policy.MAX_INPUT, "RESOURCE_LIMIT", "exported patch exceeds replay budget")
        (directory / "candidate.patch").write_bytes(patch)
        report["patch_sha256"] = digest(patch)
        journal.event("APPLIED", candidate_tree=report["candidate_tree"])
        for check in planned["checks"]:
            journal.event("CHECKING", check=check["id"])
            result = execute(check, candidate, directory)
            report["checks"].append(result)
            require(repository.snapshot(candidate) == expected, "TREE_DRIFT", "candidate changed during checks")
            require(identity() == planned["controller_inputs"], "TREE_DRIFT", "controller changed during checks")
            journal.event("CHECKED", check=check["id"], outcome=result["status"])
            if result["status"] != "PASSED":
                journal.event("CHECKS_FAILED", failed_check=check["id"])
                return report
        repository.clean(root, task["base_commit"])
        commit = repository.candidate_commit(candidate, expected["index_tree"], task["base_commit"], task["id"])
        ref = "refs/nabt-agent/" + task["id"] + "/" + digest(str(directory).encode())[:16]
        repository.git(root, "update-ref", ref, commit, "0" * 40)
        report.update(candidate_commit=commit, candidate_ref=ref)
        journal.event("READY_FOR_REVIEW", candidate_commit=commit)
    except KeyboardInterrupt:
        journal.event("INTERRUPTED")
    except (AgentError, OSError) as error:
        report["error"] = {"code": getattr(error, "code", "IO_ERROR"), "message": str(error)}
        journal.event("BLOCKED")
    return report


def verify(previous_dir, task, proposal, *, root=ROOT, output_dir):
    """Fresh execution, not acceptance of historical success flags."""
    previous_dir = Path(previous_dir)
    old = policy.load(previous_dir / "state.json")
    expected_plan = plan(task, proposal, root=root)
    record_fields = {"schema", "plan", "checks", "candidate_tree", "candidate_snapshot", "candidate_commit",
                     "candidate_ref", "worktree", "semantic_authority", "publication_authority", "event_tail", "status", "patch_sha256"}
    require(type(old) is dict and set(old) == record_fields and old.get("schema") == SCHEMA
            and old.get("semantic_authority") == "NONE" and old.get("publication_authority") == "NONE"
            and canonical(old.get("plan")) == canonical(expected_plan),
            "REPLAY_MISMATCH", "record does not match independent task, proposal and current policy")
    require(policy.load(previous_dir / "task.json") == task
            and policy.load(previous_dir / "proposal.json") == proposal
            and policy.load(previous_dir / "plan.json") == expected_plan,
            "REPLAY_MISMATCH", "retained inputs or plan changed")
    events = state.validate_journal(previous_dir, old.get("event_tail"))
    require(old.get("status") == "READY_FOR_REVIEW" and type(old.get("checks")) is list
            and all(type(row) is dict for row in old["checks"])
            and len(old["checks"]) == len(expected_plan["checks"]),
            "REPLAY_MISMATCH", "prior record has no completed candidate")
    commit = old.get("candidate_commit")
    require(type(commit) is str and re.fullmatch(r"[0-9a-f]{40}", commit),
            "REPLAY_MISMATCH", "candidate commit identity missing")
    expected_ref = "refs/nabt-agent/" + task["id"] + "/" + digest(str(previous_dir.absolute()).encode())[:16]
    require(old.get("candidate_ref") == expected_ref
            and repository.git(root, "rev-parse", "--verify", expected_ref).decode().strip() == commit,
            "REPLAY_MISMATCH", "candidate reference changed")
    require(repository.git(root, "rev-parse", commit + "^{tree}").decode().strip() == old.get("candidate_tree")
            and repository.git(root, "rev-parse", commit + "^@").decode().splitlines() == [task["base_commit"]],
            "REPLAY_MISMATCH", "candidate ancestry or tree changed")
    patch_file = previous_dir / "candidate.patch"
    expected_patch = repository.git(root, "diff", task["base_commit"], commit, "--binary", "--no-ext-diff", "--no-textconv")
    require(patch_file.is_file() and patch_file.stat().st_size <= 2 * policy.MAX_INPUT
            and patch_file.read_bytes() == expected_patch and old.get("patch_sha256") == digest(expected_patch),
            "REPLAY_MISMATCH", "exported patch differs from candidate")
    prior_worktree = previous_dir.absolute() / "worktree"
    require(old.get("worktree") == str(prior_worktree)
            and repository.snapshot(prior_worktree) == old.get("candidate_snapshot"),
            "REPLAY_MISMATCH", "previously checked worktree changed")
    expected_events = [("PLANNED", {}), ("ISOLATED", {}), ("APPLIED", {"candidate_tree": old["candidate_tree"]})]
    for check in expected_plan["checks"]:
        expected_events += [("CHECKING", {"check": check["id"]}), ("CHECKED", {"check": check["id"], "outcome": "PASSED"})]
    expected_events.append(("READY_FOR_REVIEW", {"candidate_commit": commit}))
    require([(e["kind"], e["data"]) for e in events] == expected_events,
            "REPLAY_MISMATCH", "event transitions differ from completed plan")
    for expected, result in zip(expected_plan["checks"], old["checks"]):
        require(set(result) == set(expected) | {"status", "returncode", "logs"}
                and all(result.get(k) == v for k, v in expected.items())
                and result.get("status") == "PASSED" and type(result.get("returncode")) is int
                and result["returncode"] == 0 and type(result.get("logs")) is dict
                and set(result["logs"]) == {"stdout", "stderr"},
                "REPLAY_MISMATCH", "recorded checks differ from required plan")
        for stream in ("stdout", "stderr"):
            path = previous_dir / (expected["id"] + "." + stream)
            require(path.is_file() and path.stat().st_size <= MAX_LOG_BYTES,
                    "REPLAY_MISMATCH", "recorded log missing or oversized")
            raw = path.read_bytes()
            require(canonical(result["logs"].get(stream)) == canonical({"sha256": digest(raw), "bytes": len(raw), "truncated": False}),
                    "REPLAY_MISMATCH", "recorded log changed")
    fresh = run(task, proposal, root=root, output_dir=output_dir)
    valid = (fresh["status"] == "READY_FOR_REVIEW" and fresh["candidate_tree"] == old.get("candidate_tree")
             and fresh["candidate_snapshot"] == old.get("candidate_snapshot"))
    # Commit time/author and elapsed time are not semantic observations.
    result = {"schema": "nabt.repo-agent.verification.v1", "valid": valid,
              "status": "FRESH_CHECKS_PASSED" if valid else "REPLAY_MISMATCH",
              "candidate_tree": fresh["candidate_tree"], "fresh_state": str(Path(output_dir) / "state.json"),
              "historical_authenticity": "NOT_ESTABLISHED", "publication_authority": "NONE"}
    state.write_json(Path(output_dir) / "verification.json", result)
    return result
