import ast
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple


@dataclass(frozen=True)
class _DefNode:
    qualname: str
    node_type: str  # "function" | "method" | "module"
    line: int


class CallGraphExtractor:
    """
    Builds a per-file call graph fragment from an AST.

    - A fake "<module>" node is added to represent code executed
      at import time or inside the main block.
    - '::' is used as delimiter inside fragment IDs.
    - When scanning the module body, nested defs/classes are skipped
      so their calls are not assigned to <module>.
    """

    _DELIM = "::"
    _MODULE_QN = "<module>"

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

        # Fake node for top-level execution
        defined[self._MODULE_QN] = _DefNode(
            qualname=self._MODULE_QN,
            node_type="module",
            line=1,
        )

        # Top-level functions
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

    def _build_edges(
        self,
        filename: str,
        tree: ast.AST,
        defined: Dict[str, _DefNode],
    ) -> List[Dict[str, Any]]:
        edges: List[Dict[str, Any]] = []

        class_methods: Dict[str, Set[str]] = {}
        for qn in defined.keys():
            if "." in qn:
                cls, m = qn.split(".", 1)
                class_methods.setdefault(cls, set()).add(m)

        # Calls written directly in the module (no nested defs)
        edges.extend(
            self._edges_in_scope(
                filename=filename,
                caller_qualname=self._MODULE_QN,
                body=tree,
                defined=defined,
                current_class=None,
                class_methods=class_methods,
                skip_nested_defs=True,
            )
        )

        # Calls inside top-level functions
        for node in getattr(tree, "body", []):
            if isinstance(node, ast.FunctionDef):
                edges.extend(
                    self._edges_in_scope(
                        filename=filename,
                        caller_qualname=node.name,
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
                        edges.extend(
                            self._edges_in_scope(
                                filename=filename,
                                caller_qualname=f"{cls}.{item.name}",
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
        skip_nested_defs: bool = False,
    ) -> List[Dict[str, Any]]:
        edges: List[Dict[str, Any]] = []
        caller_id = f"{filename}{self._DELIM}{caller_qualname}"

        if skip_nested_defs:
            calls: List[ast.Call] = []

            class _Collector(ast.NodeVisitor):
                def visit_Call(self, node: ast.Call) -> None:
                    calls.append(node)
                    self.generic_visit(node)

                # Do not enter nested scopes
                def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
                    return

                def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
                    return

                def visit_ClassDef(self, node: ast.ClassDef) -> None:
                    return

                def visit_Lambda(self, node: ast.Lambda) -> None:
                    return

            _Collector().visit(body)

            for n in calls:
                target_id, call_kind = self._resolve_call(
                    filename,
                    n,
                    defined,
                    current_class,
                    class_methods,
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

        # Normal walk for function/method bodies
        for n in ast.walk(body):
            if isinstance(n, ast.Call):
                target_id, call_kind = self._resolve_call(
                    filename,
                    n,
                    defined,
                    current_class,
                    class_methods,
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

        # Simple call: foo(...)
        if isinstance(func, ast.Name):
            name = func.id
            if name in defined:
                return f"{filename}{self._DELIM}{name}", "direct"
            return f"unresolved:{name}", "direct"

        # Attribute call: obj.foo(...)
        if isinstance(func, ast.Attribute):
            base = func.value
            attr = func.attr

            # self.method() inside classes
            if (
                isinstance(base, ast.Name)
                and base.id == "self"
                and current_class is not None
            ):
                if attr in class_methods.get(current_class, set()):
                    qn = f"{current_class}.{attr}"
                    return f"{filename}{self._DELIM}{qn}", "attribute"
                return f"unresolved:self.{attr}", "attribute"

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