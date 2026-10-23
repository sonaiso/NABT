
import hashlib, importlib.metadata as md, json, os, pathlib, sys
import nabt
import nabt.person_evidence, nabt.discourse, nabt.discourse_reader
import nabt.discourse_context, nabt.discourse_adverbs, nabt.discourse_laws
import nabt.construction_reader, nabt.construction_complements, nabt.construction_nominals
import nabt.construction_sources, nabt.construction_laws
distribution = md.distribution("nabt-machine")
root = pathlib.Path(nabt.__file__).parent
files = []
for path in sorted(root.rglob("*")):
    if path.is_file() and "__pycache__" not in path.parts:
        raw = path.read_bytes()
        files.append({"path": "nabt/" + str(path.relative_to(root)), "bytes": len(raw),
                      "sha256": hashlib.sha256(raw).hexdigest()})
metadata_path = next(p for p in distribution.files if str(p).endswith(".dist-info/METADATA"))
metadata = distribution.locate_file(metadata_path).read_bytes()
print(json.dumps({"distribution_version": distribution.version, "module_version": nabt.__version__,
    "module_origin": nabt.__file__, "python": sys.executable, "prefix": sys.prefix,
    "sys_path": sys.path, "pythonpath_present": "PYTHONPATH" in os.environ,
    "pythonhome_present": "PYTHONHOME" in os.environ, "files": files,
    "metadata_sha256": hashlib.sha256(metadata).hexdigest(),
    "readme_sha256": hashlib.sha256(metadata.partition(b"\n\n")[2]).hexdigest(),
    "requires_python": distribution.metadata["Requires-Python"],
    "requires_dist": distribution.requires or [],
    "entry_points": [{"name": e.name, "group": e.group, "value": e.value}
                     for e in distribution.entry_points],
    "nabt_module_origins": {name: module.__file__ for name, module in sorted(sys.modules.items())
                            if name.startswith("nabt") and getattr(module, "__file__", None)}}, indent=2))
