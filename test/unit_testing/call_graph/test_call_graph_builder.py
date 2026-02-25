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