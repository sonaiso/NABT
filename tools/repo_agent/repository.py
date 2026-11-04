"""Git identities and private worktrees; never mutate the operator's checkout."""
from __future__ import annotations

import os
from pathlib import Path
import subprocess

from .policy import AgentError, canonical, digest, require


def git(root, *args, data=None):
    env = {k: os.environ[k] for k in ("PATH", "SYSTEMROOT", "LANG", "LC_ALL", "TMPDIR", "TEMP", "TMP") if k in os.environ}
    try:
        result = subprocess.run(["git", "-c", "core.hooksPath=/dev/null", *args], cwd=root,
                                input=data, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                timeout=60, check=False, env=env)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise AgentError("EXECUTION_UNAVAILABLE", "Git operation unavailable") from error
    require(result.returncode == 0, "GIT_FAILED", result.stderr.decode("utf-8", "replace")[-2000:])
    return result.stdout


def clean(root, base):
    require(git(root, "rev-parse", "--show-toplevel").decode().strip() == str(root),
            "INVALID_INPUT", "root must be the worktree toplevel")
    require(git(root, "rev-parse", "HEAD").decode().strip() == base,
            "STALE_BASE", "task base differs from current HEAD")
    require(not git(root, "status", "--porcelain", "--untracked-files=all").strip(),
            "DIRTY_CHECKOUT", "commit or isolate existing changes before starting a task")


def safe_file(root, relative):
    current = root
    for part in Path(relative).parts:
        current = current / part
        require(not current.is_symlink(), "PROTECTED_PATH", "symlink is not a managed file")
    require(current.resolve().is_relative_to(root), "PROTECTED_PATH", "file escapes root")
    return current


def validate_before(root, proposal):
    for change in proposal["changes"]:
        file = safe_file(root, change["path"])
        index = git(root, "ls-files", "--stage", "--", change["path"]).decode()
        if change["before_sha256"] is None:
            require(not index and not file.exists(), "STALE_INPUT", "new file already exists: " + change["path"])
        else:
            require(index.startswith("100644 ") and file.is_file(),
                    "PROTECTED_PATH", "only ordinary tracked text files can be replaced")
            raw = file.read_bytes()
            require(digest(raw) == change["before_sha256"], "STALE_INPUT", "source bytes changed: " + change["path"])
            try:
                raw.decode("utf-8", "strict")
            except UnicodeError as error:
                raise AgentError("INVALID_INPUT", "binary original is not supported") from error
            require(change["content"] is None or raw != change["content"].encode("utf-8"),
                    "INVALID_INPUT", "proposal contains a no-op change")


def snapshot(root):
    """Content/mode identity also detects changes that were not staged."""
    files = git(root, "ls-files", "-z").decode("utf-8").split("\0")
    values = []
    for relative in sorted(filter(None, files)):
        file = root / relative
        if file.is_symlink():
            values.append([relative, "link", os.readlink(file)])
        elif file.is_file():
            values.append([relative, file.stat().st_mode & 0o777, digest(file.read_bytes())])
        else:
            values.append([relative, "missing"])
    others = git(root, "ls-files", "--others", "--exclude-standard", "-z").decode("utf-8").split("\0")
    return {"head": git(root, "rev-parse", "HEAD").decode().strip(),
            "index_tree": git(root, "write-tree").decode().strip(),
            "tracked_sha256": digest(canonical(values)), "untracked": sorted(filter(None, others))}


def worktree(root, destination, base):
    git(root, "worktree", "add", "--detach", str(destination), base)


def apply(root, proposal):
    validate_before(root, proposal)
    for change in proposal["changes"]:
        file = safe_file(root, change["path"])
        if change["content"] is None:
            file.unlink()
        else:
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_bytes(change["content"].encode("utf-8"))
            file.chmod(0o644)
    git(root, "add", "--", *(c["path"] for c in proposal["changes"]))
    actual = set(filter(None, git(root, "diff", "--cached", "--name-only", "-z").decode().split("\0")))
    require(actual == {c["path"] for c in proposal["changes"]}, "TREE_DRIFT", "staged scope differs from proposal")
    return snapshot(root)


def candidate_commit(root, tree, base, task_id):
    return git(root, "-c", "user.name=NABT Repository Agent", "-c", "user.email=agent@localhost",
               "commit-tree", tree, "-p", base,
               data=("Candidate for " + task_id + "\n").encode()).decode().strip()
