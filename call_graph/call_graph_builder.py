import json
import os
from typing import Any, Dict, List, Optional


class CallGraphBuilder:
    """
    Merges per-file call graph fragments into a project-level JSON artifact.
    """

    _DELIM = "::"

    def build(self, fragments: List[Dict[str, Any]], project_root: Optional[str] = None) -> Dict[str, Any]:
        nodes: Dict[str, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []

        # First pass: normalize nodes
        for frag in fragments:
            file_path = frag.get("file", "")
            file_rel = self._relativize(file_path, project_root)

            for n in frag.get("nodes", []):
                qualname = self._extract_qualname(n.get("id", ""))
                node_id = f"{file_rel}:{qualname}"

                nodes[node_id] = {
                    "id": node_id,
                    "label": n.get("label", qualname),
                    "file": file_rel,
                    "line": n.get("line", -1),
                    "type": n.get("type", "function"),
                }

        # Index by short name to resolve unresolved plain calls
        short_index: Dict[str, List[str]] = {}
        for nid, n in nodes.items():
            label = n.get("label", "")
            short = label.split(".")[-1] if label else ""
            if short:
                short_index.setdefault(short, []).append(nid)

        # Second pass: normalize edges
        for frag in fragments:
            file_path = frag.get("file", "")
            file_rel = self._relativize(file_path, project_root)

            for e in frag.get("edges", []):
                src_qn = self._extract_qualname(e.get("source", ""))
                source = f"{file_rel}:{src_qn}"

                tgt_raw = e.get("target", "unresolved:<unknown>")
                target = self._normalize_target(tgt_raw, nodes, short_index, file_rel)

                edges.append(
                    {
                        "source": source,
                        "target": target,
                        "call": e.get("call", "direct"),
                        "line": e.get("line", -1),
                    }
                )

        return {
            "version": "1.0",
            "project_root": os.path.abspath(project_root) if project_root else None,
            "nodes": list(nodes.values()),
            "edges": edges,
        }

    def save(self, callgraph: Dict[str, Any], output_path: str) -> None:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(callgraph, f, indent=2, ensure_ascii=False)

    def _relativize(self, file_path: str, project_root: Optional[str]) -> str:
        try:
            abs_file = os.path.abspath(file_path)
            if project_root:
                rel = os.path.relpath(abs_file, os.path.abspath(project_root))
                return rel.replace("\\", "/")
            return abs_file.replace("\\", "/")
        except Exception:
            return file_path.replace("\\", "/")

    def _extract_qualname(self, node_id: str) -> str:
        if node_id.startswith("unresolved:"):
            return node_id

        # The fragment ID format is: "<file><DELIM><qualname>"
        if self._DELIM in node_id:
            return node_id.rsplit(self._DELIM, 1)[1]

        # Fallback: if already "file:qualname", split on last ':'
        if ":" in node_id:
            return node_id.rsplit(":", 1)[1]

        return node_id

    def _normalize_target(
        self,
        target: str,
        nodes: Dict[str, Dict[str, Any]],
        short_index: Dict[str, List[str]],
        current_file_rel: str,
    ) -> str:
        if target in nodes:
            return target

        # If the extractor emitted a local target as "<file>::<qualname>", normalize it
        if self._DELIM in target and not target.startswith("unresolved:"):
            qn = self._extract_qualname(target)
            cand = f"{current_file_rel}:{qn}"
            if cand in nodes:
                return cand
            return cand

        # Resolve unresolved plain name to a unique node by short label
        if target.startswith("unresolved:"):
            name = target[len("unresolved:") :].strip()
            if name and "." not in name:
                cands = short_index.get(name, [])
                if len(cands) == 1:
                    return cands[0]
            return target

        return target
