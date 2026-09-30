# run_exp229_fixed_nodes.py
"""EXP229 fixed-node physical-link producer. Code supplied; runtime checks pending.

Take-175 frozen Horaz-selected per-movie CSV graphs. Node IDs / time / XYZ stay
exact; only links are replaced, using the existing EXP002 physical Hungarian
linker (classical.link_frames(frames, max_link_um=8.0, allow_divisions=False))
at the official voxel scale (1.625, 0.40625, 0.40625) um per (z, y, x).

Gates enforced here:
  * config / helper / classical / reference CSV / receipt SHA256 verified before
    the file is parsed, imported or trusted;
  * helper + classical imported only after their SHA256 passes;
  * classical pins (mutable length-3 SCALE, link_frames(max_link_um,
    allow_divisions)) checked before execution, and SCALE is set to the official
    value before every link_frames call;
  * output directory created only after the full config and all 175 input pairs
    validate; an existing output directory is a hard failure (no resume);
  * one movie at a time: helper.node_lock / helper.write_csv are called with a
    single-dataset dict, never a combined 175-movie graph;
  * complete.json written only after all 175 per-movie gates pass.

Out of scope by construction: detection, pruning, gap filling, threshold tuning,
alternative candidates, training, labels, scoring, scheduling, submission, image
arrays, checkpoints. helper.main() and classical.main() are never called, and no
source-44-only restriction is imposed (both genotype directions are expected).
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import inspect
import json
import math
import os
import sys
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11
    tomllib = None

EXPERIMENT = "EXP229"
CODE_VERSION = "exp229-fixed-nodes-v1"
COMPLETE_STATUS = "PASS_ALL_175_PREDICTIONS_BEFORE_LABELS"
COLUMNS = ["id", "dataset", "row_type", "node_id", "t", "z", "y", "x",
           "source_id", "target_id"]
SCALE_ZYX_UM = (1.625, 0.40625, 0.40625)
MAX_LINK_UM = 8.0
ALLOW_DIVISIONS = False
ARM = "selected50_20"
MODE = "heldout"
FOLDS = {"44b6": 0, "6bba": 1}
PREFIX_COUNTS = {"44b6": 59, "6bba": 116}
N_MOVIES = 175
BOUND_EPS = 1e-9
SENTINELS = {"", "-1", "-1.0"}

class Exp229Error(RuntimeError):
    """Any EXP229 contract violation (fail loud, never continue)."""

class ConfigError(Exp229Error):
    """Config missing, malformed or out of contract."""

# --- audit guard: reject any path containing '.geff' (installed at import, not removable) ---
_GUARD_EVENTS = {"open", "os.mkdir", "os.rename", "os.remove", "os.rmdir", "os.link",
                 "os.symlink", "os.listdir", "os.scandir", "os.stat", "os.chdir",
                 "shutil.copyfile", "shutil.move", "shutil.rmtree"}

def _audit_guard(event, args):
    if event not in _GUARD_EVENTS:
        return
    for arg in args:
        if isinstance(arg, (str, bytes, os.PathLike)) and ".geff" in str(arg).lower():
            raise PermissionError("EXP229 audit guard: '.geff' path access denied: %r" % (arg,))

def install_audit_guard():
    """Idempotent; there is deliberately no uninstall."""
    if not getattr(install_audit_guard, "_installed", False):
        sys.addaudithook(_audit_guard)
        install_audit_guard._installed = True

def reject_geff_path(path):
    if ".geff" in str(path).lower():
        raise PermissionError("EXP229 audit guard: '.geff' path access denied: %r" % (str(path),))

install_audit_guard()

# --- SHA256 gates ---
def sha256_file(path, chunk=1 << 20):
    reject_geff_path(path)
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(chunk), b""):
            digest.update(block)
    return digest.hexdigest()

def _is_sha256(value):
    return isinstance(value, str) and len(value.strip()) == 64 and all(
        char in "0123456789abcdefABCDEF" for char in value.strip())

def verify_sha256(path, expected):
    path = Path(path)
    expected = str(expected).strip().lower()
    if not _is_sha256(expected):
        raise Exp229Error("%s: expected sha256 is not 64 hex chars: %r" % (path, expected))
    observed = sha256_file(path)
    if observed != expected:
        raise Exp229Error("%s: sha256 mismatch (got %s, want %s)" % (path, observed, expected))
    return observed

# --- config ---
def _split_top(text, separators):
    parts, depth, quote, current = [], 0, None, []
    for char in text:
        if quote is not None:
            current.append(char)
            if char == quote:
                quote = None
            continue
        if char in "'\"":
            quote = char
        elif char in "[{":
            depth += 1
        elif char in "]}":
            depth -= 1
        elif char in separators and depth == 0:
            parts.append("".join(current))
            current = []
            continue
        current.append(char)
    parts.append("".join(current))
    return [part.strip() for part in parts if part.strip()]

def _coerce_value(text):
    text = text.strip().rstrip(",").strip()
    if text.startswith("[") and text.endswith("]"):
        inner = text[1:-1].strip()
        return [_coerce_value(part) for part in _split_top(inner, ",")] if inner else []
    if text.startswith("{") and text.endswith("}"):
        payload = {}
        for part in _split_top(text[1:-1], ","):
            key, sep, value = part.partition("=")
            if not sep:
                key, sep, value = part.partition(":")
            if not sep:
                raise ConfigError("malformed inline object entry: %r" % part)
            payload[key.strip().strip("'\"")] = _coerce_value(value)
        return payload
    lowered = text.lower()
    if lowered in ("true", "false"):
        return lowered == "true"
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "'\"":
        return text[1:-1]
    for caster in (int, float):
        try:
            return caster(text)
        except ValueError:
            pass
    raise ConfigError("cannot parse config value: %r" % text)

def _parse_config_text(text):
    if text.lstrip().startswith("{"):
        return json.loads(text)
    if tomllib is not None:
        try:
            return tomllib.loads(text)
        except Exception:
            pass
    config = {}
    for statement in _split_top(text, ";\n"):
        key, sep, value = statement.partition("=")
        if not sep:
            raise ConfigError("config statement without '=': %r" % statement)
        config[key.strip()] = _coerce_value(value)
    return config

def parse_config(path, config_sha256):
    path = Path(path)
    verify_sha256(path, config_sha256)
    data = _parse_config_text(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ConfigError("config root must be a mapping")
    return data

def validate_config(config):
    if config.get("experiment") != EXPERIMENT:
        raise ConfigError("experiment %r != %r" % (config.get("experiment"), EXPERIMENT))
    for key in ("output_dir", "classical_path", "classical_sha256", "helper_path", "helper_sha256"):
        value = config.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ConfigError("config.%s must be a non-empty string" % key)
    for key in ("classical_sha256", "helper_sha256"):
        if not _is_sha256(config[key]):
            raise ConfigError("config.%s is not a sha256 hex digest" % key)
    scale = config.get("scale_zyx_um")
    if not isinstance(scale, list) or len(scale) != 3:
        raise ConfigError("scale_zyx_um must be [1.625, .40625, .40625]")
    try:
        scale_tuple = tuple(float(value) for value in scale)
    except (TypeError, ValueError):
        raise ConfigError("scale_zyx_um must contain numbers")
    if scale_tuple != SCALE_ZYX_UM:
        raise ConfigError("scale_zyx_um %r != official %r" % (scale_tuple, SCALE_ZYX_UM))
    rows = config.get("rows")
    if not isinstance(rows, list) or len(rows) != N_MOVIES:
        raise ConfigError("rows must be a list of exactly %d objects" % N_MOVIES)
    seen, counts = set(), {}
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ConfigError("rows[%d] must be an object" % index)
        dataset = row.get("dataset")
        if not isinstance(dataset, str) or not dataset:
            raise ConfigError("rows[%d].dataset must be a non-empty string" % index)
        if dataset in seen:
            raise ConfigError("duplicate dataset %r" % dataset)
        seen.add(dataset)
        prefix = next((name for name in PREFIX_COUNTS if dataset.startswith(name + "_")), None)
        if prefix is None:
            raise ConfigError("rows[%d].dataset %r has unknown prefix" % (index, dataset))
        counts[prefix] = counts.get(prefix, 0) + 1
        shape = row.get("shape")
        if not isinstance(shape, list) or len(shape) != 4 or any(
                isinstance(value, bool) or not isinstance(value, int) or value <= 0 for value in shape):
            raise ConfigError("rows[%d].shape must be [T,Z,Y,X] positive ints" % index)
        for key in ("reference_csv", "reference_sha256", "receipt_path", "receipt_sha256"):
            if not isinstance(row.get(key), str) or not row[key].strip():
                raise ConfigError("rows[%d].%s must be a non-empty string" % (index, key))
        for key in ("reference_sha256", "receipt_sha256"):
            if not _is_sha256(row[key]):
                raise ConfigError("rows[%d].%s is not a sha256 hex digest" % (index, key))
    if counts != PREFIX_COUNTS:
        raise ConfigError("dataset prefix counts %r != %r" % (counts, PREFIX_COUNTS))
    return rows

def resolve_path(base_dir, value):
    path = Path(value)
    return path if path.is_absolute() else Path(base_dir) / path

# --- receipts: only gate-verified selected-arm inputs ---
def verify_receipt(receipt_path, dataset, fold, csv_sha256):
    receipt_path = Path(receipt_path)
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if not isinstance(receipt, dict):
        raise Exp229Error("%s: receipt root must be an object" % receipt_path)
    contract = receipt.get("contract")
    if not isinstance(contract, dict):
        raise Exp229Error("%s: missing contract object" % receipt_path)
    observed_fold = contract.get("fold")
    if isinstance(observed_fold, str) and observed_fold.strip().isdigit():
        observed_fold = int(observed_fold.strip())
    for key, wanted in (("dataset", dataset), ("arm", ARM), ("fold", fold), ("mode", MODE)):
        observed = observed_fold if key == "fold" else contract.get(key)
        if observed != wanted:
            raise Exp229Error("%s: contract.%s=%r != %r" % (receipt_path, key, observed, wanted))
    receipt_sha = receipt.get("csv_sha256")
    if not _is_sha256(receipt_sha) or receipt_sha.strip().lower() != csv_sha256.strip().lower():
        raise Exp229Error("%s: receipt csv_sha256 does not match reference_sha256" % receipt_path)
    return receipt

# --- CSV parse / graph validation ---
def _shape_tuple(shape):
    if not isinstance(shape, (list, tuple)) or len(shape) != 4:
        raise Exp229Error("shape must be [T,Z,Y,X]")
    values = []
    for value in shape:
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise Exp229Error("shape values must be positive ints: %r" % (shape,))
        values.append(value)
    return tuple(values)

def _parse_number(raw, label):
    text = "" if raw is None else str(raw).strip()
    if not text:
        raise Exp229Error("%s: missing numeric value" % label)
    try:
        value = float(text)
    except ValueError:
        raise Exp229Error("%s: not numeric: %r" % (label, raw))
    if not math.isfinite(value):
        raise Exp229Error("%s: non-finite value %r" % (label, raw))
    return value

def _parse_integral(raw, label, minimum=None):
    value = _parse_number(raw, label)
    if not value.is_integer():
        raise Exp229Error("%s: not integral: %r" % (label, raw))
    integer = int(value)
    if minimum is not None and integer < minimum:
        raise Exp229Error("%s: %d < %d" % (label, integer, minimum))
    return integer

def _is_sentinel(raw):
    return ("" if raw is None else str(raw)).strip() in SENTINELS

def _row_kind(row, where):
    source_real = not _is_sentinel(row["source_id"])
    target_real = not _is_sentinel(row["target_id"])
    if source_real and target_real:
        return "edge"
    if not source_real and not target_real:
        return "node"
    raise Exp229Error("%s: exactly one of source_id/target_id populated" % where)

def parse_csv(path, dataset, shape):
    """Parse one frozen movie CSV. Returns {'nodes': int_id->(t,z,y,x), 'edges': [(src,dst)]}."""
    path = Path(path)
    reject_geff_path(path)
    total_t, dim_z, dim_y, dim_x = _shape_tuple(shape)
    limits = (dim_z, dim_y, dim_x)
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        header = list(reader.fieldnames or [])
        if header != COLUMNS:
            raise Exp229Error("%s: header %r != %r" % (path, header, COLUMNS))
        rows = list(reader)
    nodes, edges = {}, []
    edge_pairs, seen_row_ids, node_types, edge_types = set(), set(), set(), set()
    for offset, row in enumerate(rows):
        where = "%s row %d" % (path.name, offset + 2)
        missing = [column for column in COLUMNS if column not in row]
        if missing:
            raise Exp229Error("%s: missing columns %s" % (where, missing))
        row_id = str(row["id"]).strip()
        if not row_id:
            raise Exp229Error("%s: empty id" % where)
        if row_id in seen_row_ids:
            raise Exp229Error("%s: duplicate row id %r" % (where, row_id))
        seen_row_ids.add(row_id)
        _parse_integral(row_id, "%s id" % where, minimum=0)
        if str(row["dataset"]).strip() != dataset:
            raise Exp229Error("%s: dataset %r != %r" % (where, row["dataset"], dataset))
        row_type = str(row["row_type"]).strip()
        if not row_type:
            raise Exp229Error("%s: empty row_type" % where)
        kind = _row_kind(row, where)
        if row_type != kind:
            raise Exp229Error("row_type disagrees with payload: " + where)
        node_id_token = str(row["node_id"]).strip()
        if kind == "node":
            if _is_sentinel(node_id_token):
                raise Exp229Error("%s: node row without node_id" % where)
            node_id = _parse_integral(node_id_token, "%s node_id" % where, minimum=0)
            if node_id_token != str(node_id):
                raise Exp229Error("%s: node_id %r is not a canonical integer token"
                                  % (where, node_id_token))
            if node_id in nodes:
                raise Exp229Error("%s: duplicate node_id %r" % (where, node_id))
            time = _parse_integral(row["t"], "%s t" % where, minimum=0)
            if time >= total_t:
                raise Exp229Error("%s: t=%d outside [0,%d]" % (where, time, total_t - 1))
            coords = tuple(_parse_number(row[axis], "%s %s" % (where, axis))
                           for axis in ("z", "y", "x"))
            for axis, value, limit in zip(("z", "y", "x"), coords, limits):
                if value < 0 or value >= limit:
                    raise Exp229Error("%s: %s=%r outside [0,%d)" % (where, axis, value, limit))
            nodes[node_id] = (time,) + coords
            node_types.add(row_type)
        else:
            if not _is_sentinel(node_id_token):
                raise Exp229Error("%s: edge row node_id %r must be -1" % (where, node_id_token))
            for column in ("t", "z", "y", "x"):
                if not _is_sentinel(row[column]):
                    raise Exp229Error("%s: edge row %s %r must be -1" % (where, column, row[column]))
            source = _parse_integral(row["source_id"], "%s source_id" % where, minimum=0)
            target = _parse_integral(row["target_id"], "%s target_id" % where, minimum=0)
            if (source, target) in edge_pairs:
                raise Exp229Error("%s: duplicate edge %d->%d" % (where, source, target))
            edge_pairs.add((source, target))
            edges.append((source, target))
            edge_types.add(row_type)
    if len(node_types) > 1 or len(edge_types) > 1:
        raise Exp229Error("%s: inconsistent row_type tokens %r / %r" % (path, node_types, edge_types))
    if node_types and node_types == edge_types:
        raise Exp229Error("%s: node and edge rows share row_type %r" % (path, node_types))
    if not nodes:
        raise Exp229Error("%s: no node rows" % path)
    return {"nodes": nodes, "edges": edges}

def _graph_parts(graph):
    if graph is None:
        raise Exp229Error("graph is None")
    nodes = getattr(graph, "nodes", None)
    edges = getattr(graph, "edges", None)
    if nodes is None and isinstance(graph, dict):
        nodes = graph.get("nodes")
        edges = graph.get("edges")
    if nodes is None or edges is None:
        raise Exp229Error("graph must expose 'nodes' and 'edges'")
    return nodes, edges

def _public_graph(graph):
    return {"nodes": graph["nodes"], "edges": graph["edges"]}

def validate_graph(graph, shape, candidate=False, label="graph"):
    """Canonicalize + validate structure. Returns {'nodes','edges','counts'}."""
    raw_nodes, raw_edges = _graph_parts(graph)
    total_t, dim_z, dim_y, dim_x = _shape_tuple(shape)
    limits = (dim_z, dim_y, dim_x)
    nodes = {}
    for node_id, value in raw_nodes.items():
        key = int(node_id)
        if key in nodes:
            raise Exp229Error("%s: duplicate node id %r" % (label, key))
        if len(value) != 4:
            raise Exp229Error("%s: node %r must be (t,z,y,x)" % (label, key))
        time_value = float(value[0])
        if not time_value.is_integer():
            raise Exp229Error("%s: node %r t=%r not integral" % (label, key, value[0]))
        time = int(time_value)
        if time < 0 or time >= total_t:
            raise Exp229Error("%s: node %r t=%d outside [0,%d]" % (label, key, time, total_t - 1))
        coords = (float(value[1]), float(value[2]), float(value[3]))
        for axis, coord, limit in zip(("z", "y", "x"), coords, limits):
            if not math.isfinite(coord):
                raise Exp229Error("%s: node %r %s non-finite" % (label, key, axis))
            if coord < 0 or coord >= limit:
                raise Exp229Error("%s: node %r %s=%r outside [0,%d)" % (label, key, axis, coord, limit))
        nodes[key] = (time,) + coords
    seen_edges, indegree, outdegree = set(), {}, {}
    edges = []
    for raw_edge in raw_edges:
        if len(raw_edge) != 2:
            raise Exp229Error("%s: edge must be (source,target): %r" % (label, raw_edge))
        source, target = int(raw_edge[0]), int(raw_edge[1])
        if source not in nodes or target not in nodes:
            raise Exp229Error("%s: edge endpoint missing: %d->%d" % (label, source, target))
        if nodes[target][0] != nodes[source][0] + 1:
            raise Exp229Error("%s: edge %d->%d not consecutive in time (%d->%d)"
                              % (label, source, target, nodes[source][0], nodes[target][0]))
        if (source, target) in seen_edges:
            raise Exp229Error("%s: duplicate edge %d->%d" % (label, source, target))
        seen_edges.add((source, target))
        indegree[target] = indegree.get(target, 0) + 1
        outdegree[source] = outdegree.get(source, 0) + 1
        if indegree[target] > 1:
            raise Exp229Error("%s: indegree>1 at node %d" % (label, target))
        limit = 1 if candidate else 2
        if outdegree[source] > limit:
            raise Exp229Error("%s: outdegree>%d at node %d" % (label, limit, source))
        edges.append((source, target))
    counts = {
        "nodes": len(nodes),
        "edges": len(edges),
        "isolated": sum(1 for node in nodes if node not in indegree and node not in outdegree),
        "roots": sum(1 for node in nodes if node not in indegree),
        "leaves": sum(1 for node in nodes if node not in outdegree),
        "frames_used": len({value[0] for value in nodes.values()}),
        "total_t": total_t,
    }
    return {"nodes": nodes, "edges": edges, "counts": counts}

# --- helper / classical loading and classical pins ---
HELPER_CALLABLES = ("load_classical", "to_frames", "tg_to_graph", "remap_graph",
                    "node_lock", "write_csv")

def _import_from_path(path, name):
    path = Path(path)
    reject_geff_path(path)
    unique = "%s_%d" % (name, id(path))
    spec = importlib.util.spec_from_file_location(unique, path)
    if spec is None or spec.loader is None:
        raise Exp229Error("cannot import module from %s" % path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[unique] = module
    spec.loader.exec_module(module)
    return module

def load_helper(helper_path, helper_sha256):
    """SHA256 first, only then import; never calls helper.main()."""
    helper_path = Path(helper_path)
    verify_sha256(helper_path, helper_sha256)  # before import
    module = _import_from_path(helper_path, "exp229_helper")
    missing = [name for name in HELPER_CALLABLES if not callable(getattr(module, name, None))]
    if missing:
        raise Exp229Error("helper %s missing callables: %s" % (helper_path, missing))
    return module

def _classical_scale_values(classical):
    scale_object = getattr(classical, "SCALE", None)
    if scale_object is None:
        raise Exp229Error("classical module exposes no SCALE array")
    try:
        if len(scale_object) != 3:
            raise Exp229Error("classical.SCALE length %r != 3" % (len(scale_object),))
        values = tuple(float(scale_object[index]) for index in range(3))
    except Exp229Error:
        raise
    except Exception as error:
        raise Exp229Error("classical.SCALE is not a length-3 sequence: %r" % (error,))
    if not all(math.isfinite(value) and value > 0 for value in values):
        raise Exp229Error("classical.SCALE values must be finite positive: %r" % (values,))
    return values

def check_classical_pins(classical):
    """Pins checked before execution: mutable 3-scale + link_frames signature."""
    _classical_scale_values(classical)
    link_frames = getattr(classical, "link_frames", None)
    if not callable(link_frames):
        raise Exp229Error("classical module exposes no callable link_frames")
    parameters = inspect.signature(link_frames).parameters
    for required in ("max_link_um", "allow_divisions"):
        if required not in parameters:
            raise Exp229Error("classical.link_frames has no %r parameter" % required)
    positional = [parameter for parameter in parameters.values()
                  if parameter.kind in (parameter.POSITIONAL_ONLY, parameter.POSITIONAL_OR_KEYWORD)]
    if not positional and not any(parameter.kind == parameter.VAR_POSITIONAL
                                  for parameter in parameters.values()):
        raise Exp229Error("classical.link_frames accepts no positional frames argument")
    return True

def apply_classical_scale(classical, scale):
    scale_object = getattr(classical, "SCALE", None)
    if scale_object is None:
        raise Exp229Error("classical module exposes no SCALE array")
    wanted = tuple(float(value) for value in scale)
    try:
        scale_object[:] = wanted
    except Exception as error:
        raise Exp229Error("classical.SCALE is not assignable in place: %r" % (error,))
    observed = _classical_scale_values(classical)
    if observed != wanted:
        raise Exp229Error("classical.SCALE readback %r != %r" % (observed, wanted))
    return observed

def load_classical_module(helper, classical_path, classical_sha256):
    classical_path = Path(classical_path)
    verify_sha256(classical_path, classical_sha256)  # independent gate before use
    module = helper.load_classical(str(classical_path), classical_sha256)
    if module is None:
        raise Exp229Error("helper.load_classical returned None")
    check_classical_pins(module)
    return module

# --- transform: to_frames -> link_frames -> tg_to_graph -> remap_graph(inverse) ---
def transform_graph(graph, shape, classical, helper, scale=SCALE_ZYX_UM):
    """Replace links only; node IDs / t / XYZ are required to come back exact."""
    nodes, _edges = _graph_parts(graph)
    if not nodes:
        raise Exp229Error("cannot transform a graph with no nodes")
    total_t = _shape_tuple(shape)[0]
    frames, old_to_new = helper.to_frames(nodes, total_t)
    if frames is None or old_to_new is None:
        raise Exp229Error("helper.to_frames returned %r, %r" % (frames, old_to_new))
    try:
        frame_count = len(frames)
    except TypeError:
        raise Exp229Error("helper.to_frames frames are not sized")
    if frame_count != total_t:
        raise Exp229Error("helper.to_frames returned %d frames != T=%d" % (frame_count, total_t))
    apply_classical_scale(classical, scale)
    classical_graph = classical.link_frames(frames, max_link_um=MAX_LINK_UM,
                                           allow_divisions=ALLOW_DIVISIONS)
    raw = helper.tg_to_graph(classical_graph)
    mapping = dict(old_to_new)
    if not mapping:
        raise Exp229Error("helper.to_frames returned an empty old_to_new mapping")
    inverse = {int(new): int(old) for old, new in mapping.items()}
    try:
        remapped = helper.remap_graph(raw["nodes"], raw["edges"], inverse)
    except Exp229Error:
        raise
    except Exception as error:
        raise Exp229Error("helper.remap_graph failed: %r" % (error,))
    candidate_nodes, candidate_edges = _graph_parts(remapped)
    candidate = validate_graph({"nodes": candidate_nodes, "edges": candidate_edges},
                               shape, candidate=True, label="candidate")
    reference_nodes = validate_graph(graph, shape, candidate=False, label="reference")["nodes"]
    if candidate["nodes"] != reference_nodes:
        differing = sorted(set(candidate["nodes"]) ^ set(reference_nodes))[:5]
        raise Exp229Error("candidate node dictionary changed; differing ids=%r" % differing)
    return _public_graph(candidate)

# --- per-movie pipeline (streaming) ---
def process_movie(row, base_dir, output_dir, helper, classical):
    dataset = row["dataset"]
    prefix = dataset[:4]
    if prefix not in FOLDS:
        raise Exp229Error("dataset %r has unknown prefix" % dataset)
    fold = FOLDS[prefix]
    shape = list(row["shape"])
    reference_csv = resolve_path(base_dir, row["reference_csv"])
    receipt_path = resolve_path(base_dir, row["receipt_path"])
    verify_sha256(reference_csv, row["reference_sha256"])
    verify_sha256(receipt_path, row["receipt_sha256"])
    verify_receipt(receipt_path, dataset, fold, row["reference_sha256"])
    reference = validate_graph(parse_csv(reference_csv, dataset, shape), shape,
                               candidate=False, label="reference")
    reference_lock = helper.node_lock([dataset], {dataset: _public_graph(reference)})
    candidate = transform_graph(_public_graph(reference), shape, classical, helper, SCALE_ZYX_UM)
    candidate = validate_graph(candidate, shape, candidate=True, label="candidate")
    if candidate["nodes"] != reference["nodes"]:
        raise Exp229Error("%s: candidate node dictionary != reference" % dataset)
    candidate_lock = helper.node_lock([dataset], {dataset: _public_graph(candidate)})
    if str(candidate_lock) != str(reference_lock):
        raise Exp229Error("%s: node_lock mismatch %r != %r" % (dataset, candidate_lock, reference_lock))
    output_csv = Path(output_dir) / ("physical__%s.csv" % dataset)
    if output_csv.exists():
        raise Exp229Error("refusing to overwrite existing output %s" % output_csv)
    helper.write_csv(str(output_csv), [dataset], {dataset: _public_graph(candidate)})
    reloaded = validate_graph(parse_csv(output_csv, dataset, shape), shape,
                              candidate=True, label="candidate-reload")
    if set(reloaded["edges"]) != set(candidate["edges"]):
        raise Exp229Error("serialized edges changed")
    if reloaded["nodes"] != reference["nodes"]:
        raise Exp229Error("%s: reloaded candidate nodes != reference nodes" % dataset)
    return {
        "dataset": dataset,
        "arm": ARM,
        "mode": MODE,
        "fold": fold,
        "shape": list(shape),
        "input_csv": str(reference_csv),
        "input_sha256": row["reference_sha256"],
        "receipt_path": str(receipt_path),
        "receipt_sha256": row["receipt_sha256"],
        "output_csv": str(output_csv),
        "output_sha256": sha256_file(output_csv),
        "node_lock": str(candidate_lock),
        "reference_counts": reference["counts"],
        "candidate_counts": reloaded["counts"],
        "code_version": CODE_VERSION,
    }

def write_json(path, payload):
    path = Path(path)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)

# --- top-level run ---
def run(config_path, config_sha256):
    config_path = Path(config_path)
    config = parse_config(config_path, config_sha256)
    rows = validate_config(config)
    base_dir = config_path.resolve().parent
    helper_path = resolve_path(base_dir, config["helper_path"])
    classical_path = resolve_path(base_dir, config["classical_path"])
    output_dir = resolve_path(base_dir, config["output_dir"])
    if output_dir.exists():
        raise Exp229Error("output_dir already exists; no resume/overwrite: %s" % output_dir)
    helper = load_helper(helper_path, config["helper_sha256"])
    classical = load_classical_module(helper, classical_path, config["classical_sha256"])
    check_classical_pins(classical)
    for row in rows:  # every input verified before any directory is created
        prefix = row["dataset"][:4]
        verify_sha256(resolve_path(base_dir, row["reference_csv"]), row["reference_sha256"])
        verify_sha256(resolve_path(base_dir, row["receipt_path"]), row["receipt_sha256"])
        verify_receipt(resolve_path(base_dir, row["receipt_path"]), row["dataset"],
                       FOLDS[prefix], row["reference_sha256"])
    os.makedirs(output_dir)
    receipts_dir = output_dir / "receipts"
    os.makedirs(receipts_dir)
    provenance = {
        "experiment": EXPERIMENT,
        "code_version": CODE_VERSION,
        "code_path": str(Path(__file__).resolve()),
        "code_sha256": sha256_file(Path(__file__).resolve()),
        "config_path": str(config_path.resolve()),
        "config_sha256": config_sha256.strip().lower(),
        "helper_path": str(helper_path),
        "helper_sha256": config["helper_sha256"].strip().lower(),
        "classical_path": str(classical_path),
        "classical_sha256": config["classical_sha256"].strip().lower(),
        "scale_zyx_um": list(SCALE_ZYX_UM),
        "max_link_um": MAX_LINK_UM,
        "allow_divisions": ALLOW_DIVISIONS,
        "arm": ARM,
        "mode": MODE,
        "n_movies": N_MOVIES,
        "labels_used": False,
        "checkpoints_used": False,
        "image_arrays_used": False,
        "helper_main_called": False,
        "classical_main_called": False,
    }
    records = []
    try:
        for index, row in enumerate(rows, start=1):
            record = process_movie(row, base_dir, output_dir, helper, classical)
            records.append(record)
            write_json(receipts_dir / ("%s.json" % row["dataset"]), record)
            write_json(output_dir / "progress.json", {
                "status": "RUNNING", "done": index, "total": N_MOVIES,
                "last_dataset": row["dataset"], "complete_status": COMPLETE_STATUS})
            print("EXP229 [%3d/%d] %s nodes=%d edges=%d isolated=%d sha=%s" % (
                index, N_MOVIES, row["dataset"], record["candidate_counts"]["nodes"],
                record["candidate_counts"]["edges"], record["candidate_counts"]["isolated"],
                record["output_sha256"][:12]), flush=True)
    except Exception as error:
        try:
            write_json(output_dir / "progress.json", {
                "status": "FAILED", "error": repr(error),
                "done": len(records), "total": N_MOVIES})
        except Exception:
            pass
        raise
    if len(records) != N_MOVIES:
        raise Exp229Error("expected %d records, got %d" % (N_MOVIES, len(records)))
    write_json(output_dir / "complete.json", {
        "experiment": EXPERIMENT,
        "status": COMPLETE_STATUS,
        "completed": len(records),
        "provenance": provenance,
        "records": records,
    })
    write_json(output_dir / "progress.json", {
        "status": "COMPLETE", "done": len(records), "total": N_MOVIES,
        "complete_status": COMPLETE_STATUS})
    print("EXP229 COMPLETE %s (%d/%d)" % (COMPLETE_STATUS, len(records), N_MOVIES), flush=True)
    return 0

def main(argv=None):
    parser = argparse.ArgumentParser(description="EXP229 fixed-node physical-link adapter")
    parser.add_argument("--config", required=True, help="EXP229 config path")
    parser.add_argument("--config-sha256", required=True, help="sha256 of the config file")
    arguments = parser.parse_args(argv)
    return run(arguments.config, arguments.config_sha256)

if __name__ == "__main__":
    sys.exit(main())
