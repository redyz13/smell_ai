import json
from components.project_analyzer import ProjectAnalyzer


def test_pipeline_generates_callgraph_json(tmp_path):
    project_dir = tmp_path / "project"
    out_dir = tmp_path / "out"
    project_dir.mkdir()
    out_dir.mkdir()

    (project_dir / "b.py").write_text(
        "def bar():\n"
        "    print('x')\n",
        encoding="utf-8",
    )

    (project_dir / "a.py").write_text(
        "from b import bar\n\n"
        "def foo():\n"
        "    bar()\n",
        encoding="utf-8",
    )

    analyzer = ProjectAnalyzer(str(out_dir))
    analyzer.analyze_project(str(project_dir), enable_callgraph=True)

    cg_path = out_dir / "output" / "callgraph.json"
    assert cg_path.exists()

    cg = json.loads(cg_path.read_text(encoding="utf-8"))

    node_ids = {n["id"] for n in cg["nodes"]}
    assert "a.py:foo" in node_ids
    assert "b.py:bar" in node_ids

    edges = {(e["source"], e["target"]) for e in cg["edges"]}
    assert ("a.py:foo", "b.py:bar") in edges

    by_id = {n["id"]: n for n in cg["nodes"]}

    for n in cg["nodes"]:
        assert "smells" in n
        assert "is_smelly" in n
        assert "calls_smelly" in n
        assert isinstance(n["smells"], list)
        assert isinstance(n["is_smelly"], bool)
        assert isinstance(n["calls_smelly"], bool)

    assert by_id["a.py:foo"]["calls_smelly"] is False
    assert by_id["b.py:bar"]["calls_smelly"] is False