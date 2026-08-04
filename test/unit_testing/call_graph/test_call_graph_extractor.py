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
    assert "a.py::<module>" in node_ids
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
    assert "a.py::<module>" in node_ids
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

    node_ids = {n["id"] for n in frag["nodes"]}
    assert "a.py::<module>" in node_ids

    edges = frag["edges"]
    assert any(
        e["source"] == "a.py::foo" and e["target"] == "unresolved:print"
        for e in edges
    )


def test_extractor_does_not_assign_nested_calls_to_module():
    code = """
print("top")

def foo():
    print("in foo")
    bar()

def bar():
    print("in bar")
"""
    tree = ast.parse(code)
    ex = CallGraphExtractor()
    frag = ex.extract(tree, "a.py")

    edges = {(e["source"], e["target"]) for e in frag["edges"]}

    assert ("a.py::<module>", "unresolved:print") in edges
    assert ("a.py::foo", "unresolved:print") in edges
    assert ("a.py::foo", "a.py::bar") in edges
    assert ("a.py::bar", "unresolved:print") in edges

    assert ("a.py::<module>", "a.py::bar") not in edges


def test_extractor_classifies_attribute_and_unknown_calls():
    code = """
async def background():
    print("not module code")

callback = lambda: print("not module code either")

class Worker:
    def run(self):
        self.missing()
        client.send()
        package.api.fetch()
        factory().build()

def invoke_lambda():
    (lambda: None)()
"""

    fragment = CallGraphExtractor().extract(ast.parse(code), "worker.py")
    targets = {
        (edge["source"], edge["target"], edge["call"])
        for edge in fragment["edges"]
    }

    assert (
        "worker.py::Worker.run",
        "unresolved:self.missing",
        "attribute",
    ) in targets
    assert (
        "worker.py::Worker.run",
        "unresolved:client.send",
        "attribute",
    ) in targets
    assert (
        "worker.py::Worker.run",
        "unresolved:package.api.fetch",
        "attribute",
    ) in targets
    assert (
        "worker.py::Worker.run",
        "unresolved:<expr>.build",
        "attribute",
    ) in targets
    assert (
        "worker.py::invoke_lambda",
        "unresolved:<unknown>",
        "unknown",
    ) in targets
    assert not any(
        edge["source"] == "worker.py::<module>"
        and edge["target"] == "unresolved:print"
        for edge in fragment["edges"]
    )
