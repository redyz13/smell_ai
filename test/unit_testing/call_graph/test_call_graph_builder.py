import json
from call_graph.call_graph_builder import CallGraphBuilder


def test_builder_normalizes_ids_and_files_to_be_portable(tmp_path):
    project_root = tmp_path / "proj"
    project_root.mkdir()

    a_abs = str(project_root / "a.py")
    b_abs = str(project_root / "b.py")

    fragments = [
        {
            "file": a_abs,
            "nodes": [
                {"id": f"{a_abs}::foo", "label": "foo", "file": a_abs, "line": 1, "type": "function"},
            ],
            "edges": [],
        },
        {
            "file": b_abs,
            "nodes": [
                {"id": f"{b_abs}::bar", "label": "bar", "file": b_abs, "line": 1, "type": "function"},
            ],
            "edges": [],
        },
    ]

    builder = CallGraphBuilder()
    cg = builder.build(fragments, project_root=str(project_root))

    assert cg["version"] == "1.0"
    assert cg["project_root"] == str(project_root)

    node_ids = [n["id"] for n in cg["nodes"]]
    assert "a.py:foo" in node_ids
    assert "b.py:bar" in node_ids

    for n in cg["nodes"]:
        assert "::" not in n["id"]
        assert ":\\" not in n["id"]
        assert n["id"].count(":") >= 1

        assert "smells" in n
        assert "is_smelly" in n
        assert "calls_smelly" in n
        assert n["smells"] == []
        assert n["is_smelly"] is False
        assert n["calls_smelly"] is False

    files = {n["file"] for n in cg["nodes"]}
    assert "a.py" in files
    assert "b.py" in files


def test_builder_saves_valid_json(tmp_path):
    out = tmp_path / "callgraph.json"
    cg = {
        "version": "1.0",
        "project_root": "x",
        "nodes": [
            {
                "id": "a.py:foo",
                "label": "foo",
                "file": "a.py",
                "line": 1,
                "type": "function",
                "smells": [],
                "is_smelly": False,
                "calls_smelly": False,
            }
        ],
        "edges": [],
    }

    builder = CallGraphBuilder()
    builder.save(cg, str(out))

    assert out.exists()
    loaded = json.loads(out.read_text(encoding="utf-8"))
    assert loaded["version"] == "1.0"
    assert loaded["nodes"][0]["id"] == "a.py:foo"
    assert loaded["nodes"][0]["smells"] == []
    assert loaded["nodes"][0]["is_smelly"] is False
    assert loaded["nodes"][0]["calls_smelly"] is False


def test_builder_marks_smelly_method_and_its_caller():
    fragments = [
        {
            "file": "model.py",
            "nodes": [
                {
                    "id": "model.py::Model.fit",
                    "label": "Model.fit",
                    "line": 2,
                    "type": "method",
                },
                {
                    "id": "model.py::Model.run",
                    "label": "Model.run",
                    "line": 5,
                    "type": "method",
                },
            ],
            "edges": [
                {
                    "source": "model.py::Model.run",
                    "target": "model.py::Model.fit",
                    "call": "attribute",
                    "line": 6,
                }
            ],
        }
    ]
    smell = {"smell_name": "example_smell"}

    graph = CallGraphBuilder().build(
        fragments,
        project_root=".",
        smells_by_node_id={"model.py:Model.fit": [smell]},
    )
    by_id = {node["id"]: node for node in graph["nodes"]}

    assert by_id["model.py:Model.fit"]["smells"] == [smell]
    assert by_id["model.py:Model.fit"]["is_smelly"] is True
    assert by_id["model.py:Model.run"]["calls_smelly"] is True


def test_builder_keeps_same_named_files_in_different_directories(tmp_path):
    project_root = tmp_path / "project"
    first = project_root / "pkg1" / "utils.py"
    second = project_root / "pkg2" / "utils.py"
    fragments = [
        {
            "file": str(first),
            "nodes": [
                {
                    "id": f"{first}::work",
                    "label": "work",
                    "line": 1,
                    "type": "function",
                }
            ],
            "edges": [],
        },
        {
            "file": str(second),
            "nodes": [
                {
                    "id": f"{second}::work",
                    "label": "work",
                    "line": 1,
                    "type": "function",
                }
            ],
            "edges": [],
        },
    ]

    graph = CallGraphBuilder().build(fragments, project_root=str(project_root))
    node_ids = {node["id"] for node in graph["nodes"]}

    assert "pkg1/utils.py:work" in node_ids
    assert "pkg2/utils.py:work" in node_ids


def test_builder_resolves_only_unambiguous_cross_file_calls(tmp_path):
    project_root = tmp_path / "project"
    first = project_root / "first.py"
    second = project_root / "second.py"
    third = project_root / "third.py"
    fragments = [
        {
            "file": str(first),
            "nodes": [
                {"id": f"{first}::caller", "label": "caller"},
                {"id": f"{first}::shared", "label": "shared"},
            ],
            "edges": [
                {
                    "source": f"{first}::caller",
                    "target": "unresolved:unique",
                },
                {
                    "source": f"{first}::caller",
                    "target": "unresolved:shared",
                },
                {
                    "source": f"{first}::caller",
                    "target": "unresolved:package.run",
                },
            ],
        },
        {
            "file": str(second),
            "nodes": [
                {"id": f"{second}:unique", "label": "unique"},
                {"id": f"{second}::shared", "label": "shared"},
            ],
            "edges": [],
        },
        {
            "file": str(third),
            "nodes": [
                {"id": "plain", "label": ""},
            ],
            "edges": [],
        },
    ]

    graph = CallGraphBuilder().build(
        fragments,
        project_root=str(project_root),
        smells_by_node_id={"third.py:plain": None},
    )
    targets = [edge["target"] for edge in graph["edges"]]

    assert "second.py:unique" in targets
    assert "unresolved:shared" in targets
    assert "unresolved:package.run" in targets
    blank_label_node = next(
        node for node in graph["nodes"] if node["id"] == "third.py:plain"
    )
    assert blank_label_node["smells"] == []
    assert blank_label_node["line"] == -1
    assert blank_label_node["type"] == "function"


def test_builder_target_normalization_fallbacks():
    builder = CallGraphBuilder()
    nodes = {"a.py:known": {"label": "known"}}
    short_index = {"known": ["a.py:known"]}

    assert (
        builder._normalize_target(
            "a.py:known", nodes, short_index, "a.py"
        )
        == "a.py:known"
    )
    assert (
        builder._normalize_target(
            "a.py::missing", nodes, short_index, "a.py"
        )
        == "a.py:missing"
    )
    assert (
        builder._normalize_target("external", nodes, short_index, "a.py")
        == "external"
    )
    assert builder._extract_qualname("unresolved:name") == "unresolved:name"
    assert builder._extract_qualname("a.py:name") == "name"
    assert builder._extract_qualname("name") == "name"


def test_builder_without_project_root_uses_absolute_file_path(tmp_path):
    source = tmp_path / "module.py"
    graph = CallGraphBuilder().build(
        [
            {
                "file": str(source),
                "nodes": [
                    {"id": f"{source}::work", "label": "work"},
                ],
                "edges": [],
            }
        ]
    )

    assert graph["project_root"] is None
    assert graph["nodes"][0]["file"] == str(source).replace("\\", "/")
