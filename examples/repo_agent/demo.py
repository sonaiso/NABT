"""Exercise the real NABT management path without modifying the main checkout."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.repo_agent import manager, policy, repository, state


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--counterexample", action="store_true", help="inject a known codec fault into the private candidate and require rejection")
    args = parser.parse_args()
    base = repository.git(ROOT, "rev-parse", "HEAD").decode().strip()
    repository.clean(ROOT, base)
    directory = state.create_directory(ROOT, args.output_dir)
    relative = "docs/REPOSITORY_AGENT_DEMO_RESULT.md"
    task = {"schema": "nabt.repo-agent.task.v1", "id": "document-agent-demo", "base_commit": base,
            "goal": "Create a reviewable documentation candidate through the real existing gates.",
            "allowed_paths": [relative], "acceptance": ["Original checkout remains unchanged.", "Reuse ownership checks and independent fresh replay pass."]}
    proposal = {"schema": "nabt.repo-agent.proposal.v1", "base_commit": base,
                "rationale": "Demonstrate task isolation and engineering receipts without granting semantic authority.",
                "changes": [{"path": relative, "before_sha256": None,
                             "content": "# تجربة إدارة المستودع\n\nهذا مرشح توثيق محلي؛ نجاح فحوصه لا يثبت اكتمال العربية.\n"}]}
    if args.counterexample:
        relative = "src/nabt/codec.py"
        original = (ROOT / relative).read_bytes()
        source = original.decode("utf-8")
        policy.require(source.count("n = BASE * n + a + 1") == 1, "DEMO_STALE", "codec fault site changed")
        task.update(id="reject-codec-counterexample", goal="Reject an intentionally incorrect codec candidate using its existing owner tests.",
                    allowed_paths=[relative], acceptance=["The codec owner's checks reject the candidate; original checkout remains unchanged."])
        proposal.update(rationale="An independent negative control: alter the bijective digit offset in the isolated candidate.",
                        changes=[{"path": relative, "before_sha256": policy.digest(original),
                                  "content": source.replace("n = BASE * n + a + 1", "n = BASE * n + a + 2")}])
    state.write_json(directory / "task.json", task)
    state.write_json(directory / "proposal.json", proposal)
    before = repository.snapshot(ROOT)
    result = manager.run(task, proposal, output_dir=directory / "candidate")
    if args.counterexample:
        policy.require(result["status"] == "CHECKS_FAILED" and result["checks"][-1]["id"] == "owner-tests"
                       and result["checks"][-1]["status"] == "FAILED" and result["candidate_commit"] is None
                       and repository.snapshot(ROOT) == before,
                       "DEMO_FAILED", "known codec fault was not rejected by owner tests")
        summary = {"status": "COUNTEREXAMPLE_REJECTED", "base_commit": base, "rejected_by": "owner-tests",
                   "original_checkout_unchanged": True, "publication_performed": False}
        state.write_json(directory / "summary.json", summary)
        print(json.dumps(summary, indent=2))
        return
    policy.require(result["status"] == "READY_FOR_REVIEW", "DEMO_FAILED", "candidate checks did not pass")
    verification = manager.verify(directory / "candidate", task, proposal, output_dir=directory / "replay")
    policy.require(verification["valid"] and repository.snapshot(ROOT) == before,
                   "DEMO_FAILED", "fresh replay failed or original checkout changed")
    summary = {"status": "DEMO_PASSED", "base_commit": base, "candidate_tree": result["candidate_tree"],
               "checks": [c["id"] for c in result["checks"]], "fresh_replay": True,
               "original_checkout_unchanged": True, "publication_performed": False}
    state.write_json(directory / "summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
