import ast
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple


@dataclass(frozen=True)
class _DefNode:
    qualname: str
    node_type: str  # "function" | "method"
    line: int


class CallGraphExtractor:
    """
    Extracts a per-file call graph fragment from an AST.
    IDs in the fragment use the delimiter '::' to be OS-safe.
    """

    _DELIM = "::"

    def extract(self, tree: ast.AST, filename: str) -> Dict[str, Any]:
        defined = self._collect_definitions(tree)
        nodes = self._build_nodes(filename, defined)
        edges = self._build_edges(filename, tree, defined)

        return {
            "file": filename,
            "nodes": nodes,
            "edges": edges,
        }

    def _collect_definitions(self, tree: ast.AST) -> Dict[str, _DefNode]:
        defined: Dict[str, _DefNode] = {}

        # Top-level functions only
        for node in getattr(tree, "body", []):
            if isinstance(node, ast.FunctionDef):
                qn = node.name
                defined[qn] = _DefNode(
                    qualname=qn,
                    node_type="function",
                    line=getattr(node, "lineno", -1),
                )

        # Methods inside classes
        for node in getattr(tree, "body", []):
            if isinstance(node, ast.ClassDef):
                cls = node.name
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        qn = f"{cls}.{item.name}"
                        defined[qn] = _DefNode(
                            qualname=qn,
                            node_type="method",
                            line=getattr(item, "lineno", -1),
                        )

        return defined

    def _build_nodes(self, filename: str, defined: Dict[str, _DefNode]) -> List[Dict[str, Any]]:
        nodes: List[Dict[str, Any]] = []
        for qn, dn in defined.items():
            nodes.append(
                {
                    "id": f"{filename}{self._DELIM}{qn}",
                    "label": qn,
                    "file": filename,
                    "line": dn.line,
                    "type": dn.node_type,
                }
            )
        return nodes

    def _build_edges(self, filename: str, tree: ast.AST, defined: Dict[str, _DefNode]) -> List[Dict[str, Any]]:
        edges: List[Dict[str, Any]] = []

        class_methods: Dict[str, Set[str]] = {}
        for qn in defined.keys():
            if "." in qn:
                cls, m = qn.split(".", 1)
                class_methods.setdefault(cls, set()).add(m)

        # Calls inside top-level functions only
        for node in getattr(tree, "body", []):
            if isinstance(node, ast.FunctionDef):
                caller_qn = node.name
                edges.extend(
                    self._edges_in_scope(
                        filename=filename,
                        caller_qualname=caller_qn,
                        body=node,
                        defined=defined,
                        current_class=None,
                        class_methods=class_methods,
                    )
                )

        # Calls inside class methods
        for node in getattr(tree, "body", []):
            if isinstance(node, ast.ClassDef):
                cls = node.name
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        caller_qn = f"{cls}.{item.name}"
                        edges.extend(
                            self._edges_in_scope(
                                filename=filename,
                                caller_qualname=caller_qn,
                                body=item,
                                defined=defined,
                                current_class=cls,
                                class_methods=class_methods,
                            )
                        )

        return edges

    def _edges_in_scope(
        self,
        filename: str,
        caller_qualname: str,
        body: ast.AST,
        defined: Dict[str, _DefNode],
        current_class: Optional[str],
        class_methods: Dict[str, Set[str]],
    ) -> List[Dict[str, Any]]:
        edges: List[Dict[str, Any]] = []
        caller_id = f"{filename}{self._DELIM}{caller_qualname}"

        for n in ast.walk(body):
            if isinstance(n, ast.Call):
                target_id, call_kind = self._resolve_call(
                    filename=filename,
                    call_node=n,
                    defined=defined,
                    current_class=current_class,
                    class_methods=class_methods,
                )
                edges.append(
                    {
                        "source": caller_id,
                        "target": target_id,
                        "call": call_kind,
                        "line": getattr(n, "lineno", -1),
                    }
                )

        return edges

    def _resolve_call(
        self,
        filename: str,
        call_node: ast.Call,
        defined: Dict[str, _DefNode],
        current_class: Optional[str],
        class_methods: Dict[str, Set[str]],
    ) -> Tuple[str, str]:
        func = call_node.func

        if isinstance(func, ast.Name):
            name = func.id
            if name in defined:
                return f"{filename}{self._DELIM}{name}", "direct"
            return f"unresolved:{name}", "direct"

        if isinstance(func, ast.Attribute):
            base = func.value
            attr = func.attr

            # self.method() resolution inside class scope
            if isinstance(base, ast.Name) and base.id == "self" and current_class is not None:
                if attr in class_methods.get(current_class, set()):
                    qn = f"{current_class}.{attr}"
                    return f"{filename}{self._DELIM}{qn}", "attribute"
                return f"unresolved:self.{attr}", "attribute"

            # module.func() or obj.method() - kept unresolved for CR1
            base_name = self._stringify_base(base)
            return f"unresolved:{base_name}.{attr}", "attribute"

        return "unresolved:<unknown>", "unknown"

    def _stringify_base(self, base: ast.AST) -> str:
        if isinstance(base, ast.Name):
            return base.id
        if isinstance(base, ast.Attribute):
            left = self._stringify_base(base.value)
            return f"{left}.{base.attr}"
        return "<expr>"
