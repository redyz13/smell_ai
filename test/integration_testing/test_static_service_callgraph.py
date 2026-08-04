from webapp.services.staticanalysis.app.utils.static_analysis import (
    detect_static,
)


def test_static_service_maps_method_smells_and_callers_to_graph_nodes():
    code = """
import pandas as pd

class Model:
    def fit(self, data):
        return pd.DataFrame(data)

    def run(self, data):
        return self.fit(data)
"""

    result = detect_static([{"filename": "pkg/model.py", "content": code}])

    assert result["success"] is True
    by_id = {
        node["id"]: node for node in result["graph_data"]["nodes"]
    }
    assert by_id["pkg/model.py:Model.fit"]["is_smelly"] is True
    assert by_id["pkg/model.py:Model.fit"]["smells"][0][
        "function_name"
    ] == "Model.fit"
    assert by_id["pkg/model.py:Model.run"]["calls_smelly"] is True


def test_static_service_preserves_same_named_files_in_relative_directories():
    files = [
        {
            "filename": "pkg1/utils.py",
            "content": "def first():\n    pass\n",
        },
        {
            "filename": "pkg2/utils.py",
            "content": "def second():\n    pass\n",
        },
    ]

    result = detect_static(files)

    assert result["success"] is True
    node_ids = {node["id"] for node in result["graph_data"]["nodes"]}
    assert "pkg1/utils.py:first" in node_ids
    assert "pkg2/utils.py:second" in node_ids
