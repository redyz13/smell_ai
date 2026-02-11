import ast
from call_graph.call_graph_extractor import CallGraphExtractor


def test_extractor_resolves_intra_file_function_call():
    code = """
def bar():
    pass

def foo():
    bar()
"""
    tree = ast.parse(code)
    ex = CallGraphExtractor()
    frag = ex.extract(tree, "a.py")

    node_ids = {n["id"] for n in frag["nodes"]}
    assert "a.py::foo" in node_ids
    assert "a.py::bar" in node_ids

    edges = {(e["source"], e["target"]) for e in frag["edges"]}
    assert ("a.py::foo", "a.py::bar") in edges


def test_extractor_resolves_self_method_call():
    code = """
class C:
    def n(self):
        pass

    def m(self):
        self.n()
"""
    tree = ast.parse(code)
    ex = CallGraphExtractor()
    frag = ex.extract(tree, "a.py")

    node_ids = {n["id"] for n in frag["nodes"]}
    assert "a.py::C.m" in node_ids
    assert "a.py::C.n" in node_ids

    edges = {(e["source"], e["target"]) for e in frag["edges"]}
    assert ("a.py::C.m", "a.py::C.n") in edges


def test_extractor_marks_builtins_as_unresolved():
    code = """
def foo():
    print("x")
"""
    tree = ast.parse(code)
    ex = CallGraphExtractor()
    frag = ex.extract(tree, "a.py")

    edges = frag["edges"]
    assert any(e["source"] == "a.py::foo" and e["target"] == "unresolved:print" for e in edges)
