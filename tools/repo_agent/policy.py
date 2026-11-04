"""Code-owned task boundaries and check selection, independent of proposals."""
from __future__ import annotations

import hashlib
import json
from pathlib import PurePosixPath
import re
import sys

from tools.entropy_framework.reuse_run import entry_command

MAX_FILES = 24
MAX_TEXT = 262144
MAX_INPUT = 1048576
POLICY = "nabt.repo-agent.policy.v1"


class AgentError(ValueError):
    def __init__(self, code, message):
        self.code = code
        super().__init__(message)


def require(value, code, message):
    if not value:
        raise AgentError(code, message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def text(value, label, maximum=8192, *, allow_empty=False):
    require(type(value) is str and (allow_empty or bool(value.strip())) and "\x00" not in value,
            "INVALID_INPUT", label + " must be nonempty scalar text")
    try:
        size = len(value.encode("utf-8", "strict"))
    except UnicodeError as error:
        raise AgentError("INVALID_INPUT", label + " contains invalid Unicode") from error
    require(size <= maximum, "RESOURCE_LIMIT", label + " exceeds its byte budget")
    return value


def fields(value, names, label):
    require(type(value) is dict and set(value) == set(names),
            "INVALID_INPUT", label + " has missing or unexpected fields")


def path(value):
    text(value, "path", 512)
    p = PurePosixPath(value)
    require(not p.is_absolute() and p.as_posix() == value
            and all(x not in (".", "..", ".git", ".gitattributes", ".gitmodules") for x in p.parts)
            and not any(c in value for c in "\\\n\r\t") and not value.startswith("-"),
            "INVALID_INPUT", "noncanonical repository path")
    return value


def load(pathname):
    from tools.entropy_framework.registry import load_json
    require(pathname.is_file() and pathname.stat().st_size <= MAX_INPUT,
            "RESOURCE_LIMIT", "input missing or exceeds byte budget")
    try:
        return load_json(pathname)
    except ValueError as error:
        raise AgentError("INVALID_INPUT", str(error)) from error


def validate(task, proposal):
    fields(task, ("schema", "id", "base_commit", "goal", "allowed_paths", "acceptance"), "task")
    fields(proposal, ("schema", "base_commit", "rationale", "changes"), "proposal")
    require(task["schema"] == "nabt.repo-agent.task.v1"
            and proposal["schema"] == "nabt.repo-agent.proposal.v1", "INVALID_INPUT", "unsupported schema")
    require(type(task["id"]) is str and re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", task["id"]),
            "INVALID_INPUT", "task id must be a short ASCII identifier")
    require(type(task["base_commit"]) is str and re.fullmatch(r"[0-9a-f]{40}", task["base_commit"])
            and proposal["base_commit"] == task["base_commit"], "INVALID_INPUT", "exact base commit required")
    text(task["goal"], "goal")
    text(proposal["rationale"], "rationale")
    require(type(task["acceptance"]) is list and 1 <= len(task["acceptance"]) <= 16,
            "INVALID_INPUT", "acceptance needs 1..16 review criteria")
    for item in task["acceptance"]:
        text(item, "acceptance criterion")
    allowed = task["allowed_paths"]
    require(type(allowed) is list and 1 <= len(allowed) <= MAX_FILES,
            "INVALID_INPUT", "allowed_paths needs a bounded exact path list")
    for item in allowed:
        path(item)
    require(len(set(allowed)) == len(allowed), "INVALID_INPUT", "duplicate allowed path")
    changes = proposal["changes"]
    require(type(changes) is list and 1 <= len(changes) <= MAX_FILES,
            "INVALID_INPUT", "changes needs 1..24 replacements")
    seen = set()
    for change in changes:
        fields(change, ("path", "before_sha256", "content"), "change")
        relative = path(change["path"])
        require(relative in allowed and relative not in seen,
                "OUT_OF_SCOPE", "change is duplicated or outside exact task scope: " + relative)
        seen.add(relative)
        before = change["before_sha256"]
        require(before is None or (type(before) is str and re.fullmatch(r"[0-9a-f]{64}", before)),
                "INVALID_INPUT", "before_sha256 must identify the original bytes or absence")
        content = change["content"]
        require(content is None or type(content) is str, "INVALID_INPUT", "content must be text or deletion")
        if content is not None:
            # Empty files are allowed; arbitrary control NUL and surrogates are not.
            text(content, "replacement", MAX_TEXT, allow_empty=True)
        require(before is not None or content is not None, "INVALID_INPUT", "cannot delete an absent file")
        require(relative.startswith(("docs/", "src/nabt/", "tools/", "tests/", "examples/", "formal/Nabt/")),
                "PROTECTED_PATH", "path requires the external review workflow: " + relative)
        protected = relative.startswith(("tools/repo_agent/", "tools/entropy_framework/", "tools/check_",
                                          "src/nabt/data/")) or relative in ("tools/proof_catalog.py",)
        protected |= relative.endswith(".mk")
        protected |= relative.startswith("tests/") and before is not None
        require(not protected, "PROTECTED_PATH", "automatic changes cannot replace acceptance inputs: " + relative)
        if relative.startswith("tests/"):
            require(bool(re.fullmatch(r"tests/test_[A-Za-z0-9_]+\.py", relative)),
                    "PROTECTED_PATH", "only new discoverable test modules are supported")
    require(not any(a != b and b.startswith(a + "/") for a in seen for b in seen),
            "INVALID_INPUT", "file paths cannot be ancestors of other changes")
    require(len(canonical(task)) <= MAX_INPUT and len(canonical(proposal)) <= MAX_INPUT,
            "RESOURCE_LIMIT", "request exceeds total byte budget")


def checks(paths, families, *, root):
    """The caller can add proposal text, never remove these required gates."""
    python = sys.executable
    result = [{"id": "diff", "argv": ["git", "diff", "--cached", "--check"], "cwd": ".", "timeout": 30},
              {"id": "reuse", "argv": [python, "-B", "-m", "tools.entropy_framework", "reuse", "--summary"],
               "cwd": ".", "timeout": 120}]
    code = [p for p in paths if not (p.startswith("docs/") and p.endswith((".md", ".txt")))]
    if not code:
        return result
    targets = sorted({t for f in families for t in f["native_targets"]})
    if targets:
        result.append({"id": "native-build", "argv": ["lake", "build", *targets], "cwd": "formal", "timeout": 1200})
    # The installed recipe owns the prerequisite chain and native-required flags.
    # A single family's native target is not a complete adapter integration.
    productive_chain = {"aligned-acquisition", "sourced-acquisition", "productive-clause",
                        "evidence-lifecycle", "meaning-preservation", "licensed-inference", "linguistic-truth"}
    if any(f.get("id") in productive_chain for f in families):
        result.append({"id": "productive-native-integration",
                       "argv": ["make", "-f", "tools/meaning_preservation_v1.mk", "meaning-preservation-conformance", "PYTHON=" + python],
                       "cwd": ".", "timeout": 1800})
    owner_tests = sorted({p[:-3].replace("/", ".") for f in families for p in f["test_paths"]
                          if re.fullmatch(r"tests/test_[A-Za-z0-9_]+\.py", p)})
    if owner_tests:
        result.append({"id": "owner-tests", "argv": [python, "-B", "-m", "unittest", *owner_tests, "-v"],
                       "cwd": ".", "timeout": 1200})
    result.extend([
        {"id": "runtime", "argv": [python, "-B", "-m", "unittest", "discover", "-s", "tests", "-v"], "cwd": ".", "timeout": 1200},
        {"id": "integrity", "argv": [python, "-B", "tools/check_integrity.py"], "cwd": ".", "timeout": 120},
        {"id": "learned-conformance", "argv": entry_command("learned-conformance", ["--check"], root=root), "cwd": ".", "timeout": 120},
    ])
    owned = {p for f in families for k in ("runtime_paths", "checker_paths", "test_paths") for p in f[k]}
    if any(p.startswith(("formal/", "src/nabt/")) or p not in owned for p in code):
        result.extend({"id": name, "argv": ["make", name, "PYTHON=" + python], "cwd": ".", "timeout": 1200}
                      for name in ("formal", "conformance", "axioms"))
    return result
