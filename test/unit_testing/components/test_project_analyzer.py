import os
import shutil
import pytest
import pandas as pd
from unittest.mock import ANY, MagicMock, patch
from components.project_analyzer import ProjectAnalyzer


@pytest.fixture
def mock_output_path(tmp_path):
    """
    Pytest fixture to create a temporary output directory.
    """
    return str(tmp_path)


@pytest.fixture
def project_analyzer(mock_output_path):
    """
    Fixture to create an instance of ProjectAnalyzer.
    """
    return ProjectAnalyzer(output_path=mock_output_path)


@pytest.fixture
def mock_file_related_methods(monkeypatch):
    """
    Fixture to mock the file-related methods.
    This fixture reduces repetition
    for mocking methods like os.path, FileUtils, etc.
    """
    monkeypatch.setattr("os.path.isdir", lambda path: True)
    monkeypatch.setattr("os.listdir", lambda path: ["project1", "project2"])
    monkeypatch.setattr(
        "utils.file_utils.FileUtils.get_python_files",
        lambda path: ["file1.py"],
    )
    monkeypatch.setattr(
        "utils.file_utils.FileUtils.initialize_log", lambda path: None
    )
    monkeypatch.setattr(
        "utils.file_utils.FileUtils.synchronized_append_to_log",
        lambda path, project, lock: None,
    )


def test_analyze_project(
    monkeypatch, project_analyzer, mock_file_related_methods, tmp_path
):
    """
    Test the `analyze_project` method.
    """

    output_dir = tmp_path / "output"

    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    monkeypatch.setattr(
        "components.project_analyzer.ProjectAnalyzer._save_results",
        lambda self, df, path, report_format="csv": df.to_csv(
            output_dir / "overview.csv", index=False
        ),
    )

    # Mock inspection results for two files
    df1 = pd.DataFrame(
        {
            "filename": ["file1.py"],
            "function_name": ["func1"],
            "smell_name": ["smell1"],
            "line": [10],
            "description": ["desc1"],
            "additional_info": ["info1"],
        }
    )
    df2 = pd.DataFrame(
        {
            "filename": ["file2.py"],
            "function_name": ["func2"],
            "smell_name": ["smell2"],
            "line": [20],
            "description": ["desc2"],
            "additional_info": ["info2"],
        }
    )

    mock_inspection_results = [
        (df1, {"file": "file1.py", "nodes": [], "edges": []}),
        (df2, {"file": "file2.py", "nodes": [], "edges": []}),
    ]

    # Mock inspect method to return the inspection results
    project_analyzer.inspector.inspect = MagicMock(
        side_effect=mock_inspection_results
    )

    # Mock the get_python_files method to return both files
    monkeypatch.setattr(
        "utils.file_utils.FileUtils.get_python_files",
        lambda _: ["file1.py", "file2.py"],
    )

    # Run the method
    total_smells = project_analyzer.analyze_project(
        "test/unit_testing/components/mock_project_path",
        enable_callgraph=True,
    )

    # Assertions
    assert total_smells == 2  # Expecting 2 smells (from file1.py and file2.py)
    project_analyzer.inspector.inspect.assert_any_call(
        "file1.py", include_callgraph=True
    )
    project_analyzer.inspector.inspect.assert_any_call(
        "file2.py", include_callgraph=True
    )

    mock_project_path = "test/unit_testing/components/mock_project_path"
    if os.path.exists(mock_project_path):
        shutil.rmtree(mock_project_path)


def test_analyze_projects_sequential(
    monkeypatch, project_analyzer, mock_file_related_methods, tmp_path
):
    """
    Test the `analyze_projects_sequential` method.
    """

    output_dir = tmp_path / "output"
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    monkeypatch.setattr(
        "components.project_analyzer.ProjectAnalyzer._save_results",
        lambda self, df, path, report_format="csv": df.to_csv(
            output_dir / "overview.csv", index=False
        ),
    )

    # Mock the inspector's inspect method
    mock_inspection_results = pd.DataFrame(
        {
            "filename": ["file1.py"],
            "function_name": ["func1"],
            "smell_name": ["smell1"],
            "line": [10],
        }
    )
    project_analyzer.inspector.inspect = MagicMock(
        return_value=(
            mock_inspection_results,
            {"file": "file1.py", "nodes": [], "edges": []},
        )
    )

    # Call the method
    project_analyzer.analyze_projects_sequential(
        "test/unit_testing/components/mock_project_path",
        resume=False,
        enable_callgraph=True,
    )

    # Ensure inspect was called
    project_analyzer.inspector.inspect.assert_called_with(
        "file1.py", include_callgraph=True
    )

    mock_project_path = "test/unit_testing/components/mock_project_path"
    if os.path.exists(mock_project_path):
        shutil.rmtree(mock_project_path)


def test_clean_output_directory(monkeypatch, project_analyzer):
    """
    Test the `clean_output_directory` method.
    """
    mock_clean_directory = MagicMock()
    monkeypatch.setattr(
        "utils.file_utils.FileUtils.clean_directory", mock_clean_directory
    )

    # Run the method
    project_analyzer.clean_output_directory()

    # Assertions
    mock_clean_directory.assert_called_once_with(
        project_analyzer.base_output_path, "output"
    )


def test_merge_all_results(monkeypatch, project_analyzer):
    """
    Test the `merge_all_results` method.
    """
    mock_merge_results = MagicMock()
    monkeypatch.setattr(
        "utils.file_utils.FileUtils.merge_results", mock_merge_results
    )

    # Run the method
    project_analyzer.merge_all_results()

    # Assertions
    mock_merge_results.assert_called_once_with(
        input_dir=os.path.join(project_analyzer.output_path, "project_details"),
        output_dir=project_analyzer.output_path,
        report_format="csv",
    )


def test_analyze_projects_parallel(
    monkeypatch, project_analyzer, mock_file_related_methods, tmp_path
):
    """
    Test the `analyze_projects_parallel` method.
    """

    mock_inspection_results = pd.DataFrame(
        {
            "filename": ["file1.py"],
            "function_name": ["func1"],
            "smell_name": ["smell1"],
            "line": [10],
            "description": ["desc1"],
            "additional_info": ["info1"],
        }
    )

    # Mock dependencies
    monkeypatch.setattr("os.path.exists", lambda path: True)
    monkeypatch.setattr("os.path.isdir", lambda path: True)

    # Mock the inspector's inspect method
    project_analyzer.inspector.inspect = MagicMock(
        return_value=(
            mock_inspection_results,
            {"file": "file1.py", "nodes": [], "edges": []},
        )
    )

    # Mock save results method
    monkeypatch.setattr(
        "components.project_analyzer.ProjectAnalyzer._save_results",
        lambda self, df, path, report_format="csv": None,
    )

    # Mock ThreadPoolExecutor to avoid threading and run tasks synchronously
    with patch("concurrent.futures.ThreadPoolExecutor") as MockExecutor:
        mock_executor = MagicMock()
        MockExecutor.return_value = mock_executor
        mock_executor.__enter__.return_value = mock_executor
        mock_executor.submit.side_effect = lambda func, *args, **kwargs: func(
            *args, **kwargs
        )

        # Run the method
        with patch("builtins.print") as mock_print:
            project_analyzer.analyze_projects_parallel(
                "test/unit_testing/components/mock_base_path", max_workers=1
            )

        # Ensure the inspector's inspect method was called the expected number of times
        assert project_analyzer.inspector.inspect.call_count == 2
        assert mock_print.call_count > 0


def test_exception_handling_in_inspect(
    monkeypatch, project_analyzer, mock_file_related_methods, tmp_path
):
    """
    Test that the `inspect` method handles exceptions gracefully.
    """

    # Simulate an exception in the inspect method
    project_analyzer.inspector.inspect = MagicMock(
        side_effect=FileNotFoundError
    )

    with patch("builtins.print") as mock_print:
        project_analyzer.analyze_projects_parallel(
            "test/unit_testing/components/mock_project_path", max_workers=1
        )

    # Assertions
    assert (
        "Total code smells found in all projects: 0\n"
        in mock_print.call_args[0][0]
    )

    mock_project_path = "test/unit_testing/components/mock_project_path"
    if os.path.exists(mock_project_path):
        shutil.rmtree(mock_project_path)


def test_analyze_project_with_errors(
    monkeypatch, project_analyzer, mock_file_related_methods, tmp_path
):
    """
    Test `analyze_project` with error
    handling (FileNotFoundError, SyntaxError).
    """
    output_dir = tmp_path / "output"

    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    monkeypatch.setattr(
        "components.project_analyzer.ProjectAnalyzer._save_results",
        lambda self, df, path, report_format="csv": df.to_csv(
            output_dir / "overview.csv", index=False
        ),
    )

    # Mocking a SyntaxError for a specific file
    project_analyzer.inspector.inspect = MagicMock(side_effect=SyntaxError)

    # Run the method (simulate failure for file1.py)
    project_analyzer.analyze_project(
        "test/unit_testing/components/mock_project_path"
    )

    # Check if the error is logged to the error.txt file
    error_file = output_dir / "error.txt"
    with open(error_file, "r") as f:
        error_content = f.read()

    assert "Error in file file1.py: " in error_content

    mock_project_path = "test/unit_testing/components/mock_project_path"
    if os.path.exists(mock_project_path):
        shutil.rmtree(mock_project_path)


def test_analyze_projects_sequential_save_results(
    monkeypatch, project_analyzer, mock_file_related_methods, tmp_path
):
    """
    Test saving results in `project_details` for sequential analysis.
    """
    output_dir = tmp_path / "output"

    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    monkeypatch.setattr(
        "components.project_analyzer.ProjectAnalyzer._save_results",
        lambda self, df, path, report_format="csv": df.to_csv(
            output_dir / "overview.csv", index=False
        ),
    )

    # Mock the inspector's inspect method
    mock_inspection_results = pd.DataFrame(
        {
            "filename": ["file1.py"],
            "function_name": ["func1"],
            "smell_name": ["smell1"],
            "line": [10],
        }
    )
    project_analyzer.inspector.inspect = MagicMock(
        return_value=(
            mock_inspection_results,
            {"file": "file1.py", "nodes": [], "edges": []},
        )
    )

    # Call the method
    project_analyzer.analyze_projects_sequential(
        "test/unit_testing/components/mock_project_path",
        resume=False,
        enable_callgraph=True,
    )

    # Check if project_details directory and the result file were created
    details_path = output_dir / "project_details"
    assert details_path.exists()

    detailed_file_path = details_path / "project1_results.csv"
    assert detailed_file_path.exists()

    # Check if the CSV file contains the expected data
    df = pd.read_csv(detailed_file_path)
    assert not df.empty
    assert "filename" in df.columns
    assert df["filename"].iloc[0] == "file1.py"

    mock_project_path = "test/unit_testing/components/mock_project_path"
    if os.path.exists(mock_project_path):
        shutil.rmtree(mock_project_path)


def test_analyze_projects_parallel_thread_safety(
    monkeypatch, project_analyzer, mock_file_related_methods, tmp_path
):
    """
    Test thread-safety in the `analyze_projects_parallel` method.
    """

    mock_inspection_results = pd.DataFrame(
        {
            "filename": ["file1.py"],
            "function_name": ["func1"],
            "smell_name": ["smell1"],
            "line": [10],
            "description": ["desc1"],
            "additional_info": ["info1"],
        }
    )

    # Mock the inspector's inspect method
    project_analyzer.inspector.inspect = MagicMock(
        return_value=(
            mock_inspection_results,
            {"file": "file1.py", "nodes": [], "edges": []},
        )
    )

    # Mock the synchronized_append_to_log method to check for thread-safety
    mock_synchronized_append = MagicMock()
    monkeypatch.setattr(
        "utils.file_utils.FileUtils.synchronized_append_to_log",
        mock_synchronized_append,
    )

    # Run the method with parallel execution
    project_analyzer.analyze_projects_parallel(
        "test/unit_testing/components/mock_base_path", max_workers=2
    )

    expected_path = os.path.join(
        "test/unit_testing/components/mock_base_path", "execution_log.txt"
    )

    mock_synchronized_append.assert_any_call(expected_path, "project1", ANY)
    mock_synchronized_append.assert_any_call(expected_path, "project2", ANY)

    mock_project_path = "test/unit_testing/components/mock_base_path"
    if os.path.exists(mock_project_path):
        shutil.rmtree(mock_project_path)


def test_analyze_project_empty_directory(
    monkeypatch, project_analyzer, mock_file_related_methods, tmp_path
):
    """
    Test `analyze_project` when no Python files exist in the directory.
    """
    output_dir = tmp_path / "output"

    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    monkeypatch.setattr(
        "components.project_analyzer.ProjectAnalyzer._save_results",
        lambda self, df, path, report_format="csv": df.to_csv(
            output_dir / "overview.csv", index=False
        ),
    )

    # Mock get_python_files to return an empty list
    monkeypatch.setattr(
        "utils.file_utils.FileUtils.get_python_files", lambda _: []
    )

    project_path = "test/unit_testing/components/mock_project_path"

    with pytest.raises(ValueError) as excinfo:
        project_analyzer.analyze_project(project_path)

    assert f"The project '{project_path}' contains no Python files." == str(
        excinfo.value
    )


@pytest.mark.parametrize(
    ("report_format", "extension"),
    [("csv", ".csv"), ("json", ".json")],
)
def test_save_results_supports_cr2_report_formats(
    project_analyzer, report_format, extension
):
    results = pd.DataFrame(
        [
            {
                "filename": "module.py",
                "function_name": "work",
                "smell_name": "example",
            }
        ]
    )

    project_analyzer._save_results(
        results, "overview.csv", report_format=report_format
    )

    output_file = os.path.join(
        project_analyzer.output_path, f"overview{extension}"
    )
    assert os.path.exists(output_file)
    if report_format == "json":
        loaded = pd.read_json(output_file)
    else:
        loaded = pd.read_csv(output_file)
    assert loaded.loc[0, "function_name"] == "work"


def test_save_results_skips_empty_reports(project_analyzer, capsys):
    project_analyzer._save_results(
        pd.DataFrame(), "overview.csv", report_format="json"
    )

    assert "No results to save for overview.csv" in capsys.readouterr().out
    assert not os.path.exists(
        os.path.join(project_analyzer.output_path, "overview.json")
    )


def test_build_smells_by_node_id_uses_relative_paths_and_skips_invalid_rows(
    project_analyzer, tmp_path
):
    project_root = tmp_path / "project"
    source = project_root / "src" / "model.py"
    results = pd.DataFrame(
        [
            {
                "filename": str(source),
                "function_name": "Model.fit",
                "smell_name": "first",
                "line": 7,
                "description": "description",
                "additional_info": "details",
            },
            {
                "filename": str(source),
                "function_name": "Model.fit",
                "smell_name": "second",
                "line": None,
                "description": "description",
                "additional_info": "details",
            },
            {
                "filename": "",
                "function_name": "ignored",
                "smell_name": "ignored",
                "line": 1,
            },
            {
                "filename": str(source),
                "function_name": "",
                "smell_name": "ignored",
                "line": 1,
            },
        ]
    )

    smells = project_analyzer._build_smells_by_node_id(
        results, str(project_root)
    )

    assert project_analyzer._build_smells_by_node_id(None, str(project_root)) == {}
    assert project_analyzer._build_smells_by_node_id(
        pd.DataFrame(), str(project_root)
    ) == {}
    assert list(smells) == ["src/model.py:Model.fit"]
    assert [smell["line"] for smell in smells["src/model.py:Model.fit"]] == [
        7,
        -1,
    ]


def test_exclude_paths_support_relative_directories_and_absolute_files(
    project_analyzer, tmp_path
):
    project_root = tmp_path / "project"
    kept = project_root / "src" / "keep.py"
    excluded_child = project_root / "generated" / "child.py"
    excluded_exact = project_root / "skip.py"
    filenames = [str(kept), str(excluded_child), str(excluded_exact)]

    filtered = project_analyzer._filter_excluded_files(
        filenames,
        ["generated", "", str(excluded_exact)],
        str(project_root),
    )

    assert filtered == [str(kept)]
    assert project_analyzer._filter_excluded_files(
        [], ["generated"], str(project_root)
    ) == []
    assert project_analyzer._filter_excluded_files(
        filenames, [], str(project_root)
    ) == filenames


def test_callgraph_output_paths_cover_single_and_multiple_projects(
    project_analyzer, tmp_path
):
    project = tmp_path / "project"

    default_single = project_analyzer._resolve_callgraph_output_path(
        project_path=str(project),
        project_name="project",
        callgraph_output=None,
        multiple=False,
    )
    default_multiple = project_analyzer._resolve_callgraph_output_path(
        project_path=str(project),
        project_name="project",
        callgraph_output=None,
        multiple=True,
    )
    explicit_single = project_analyzer._resolve_callgraph_output_path(
        project_path=str(project),
        project_name="project",
        callgraph_output=str(tmp_path / "custom" / "graph.json"),
        multiple=False,
    )
    intended_directory = project_analyzer._resolve_callgraph_output_path(
        project_path=str(project),
        project_name="project",
        callgraph_output=str(tmp_path / "graphs"),
        multiple=True,
    )
    existing_directory = tmp_path / "graphs.bundle"
    existing_directory.mkdir()
    inside_existing_directory = project_analyzer._resolve_callgraph_output_path(
        project_path=str(project),
        project_name="project",
        callgraph_output=str(existing_directory),
        multiple=True,
    )
    suffixed_file = project_analyzer._resolve_callgraph_output_path(
        project_path=str(project),
        project_name="project",
        callgraph_output=str(tmp_path / "combined.json"),
        multiple=True,
    )

    assert default_single.endswith(os.path.join("output", "callgraph.json"))
    assert default_multiple.endswith(
        os.path.join("output", "project_details", "project_callgraph.json")
    )
    assert explicit_single == str(tmp_path / "custom" / "graph.json")
    assert intended_directory == str(tmp_path / "graphs" / "project_callgraph.json")
    assert inside_existing_directory == str(
        existing_directory / "project_callgraph.json"
    )
    assert suffixed_file == str(tmp_path / "combined_project.json")


def test_single_project_cr2_options_filter_files_and_write_json_callgraph(
    monkeypatch, project_analyzer, tmp_path
):
    project = tmp_path / "project"
    included = project / "src" / "main.py"
    excluded = project / "generated" / "generated.py"
    callgraph_output = tmp_path / "graphs" / "single.json"
    results = pd.DataFrame(
        [
            {
                "filename": str(included),
                "function_name": "main",
                "smell_name": "example",
                "line": 1,
                "description": "description",
                "additional_info": "details",
            }
        ]
    )
    fragment = {
        "file": str(included),
        "nodes": [
            {"id": f"{included}::main", "label": "main", "line": 1}
        ],
        "edges": [],
    }
    monkeypatch.setattr(
        "utils.file_utils.FileUtils.get_python_files",
        lambda _: [str(included), str(excluded)],
    )
    project_analyzer.inspector.inspect = MagicMock(
        return_value=(results, fragment)
    )

    total_smells = project_analyzer.analyze_project(
        str(project),
        enable_callgraph=True,
        callgraph_output=str(callgraph_output),
        exclude_paths=["generated"],
        report_format="json",
    )

    assert total_smells == 1
    project_analyzer.inspector.inspect.assert_called_once_with(
        str(included), include_callgraph=True
    )
    assert os.path.exists(
        os.path.join(project_analyzer.output_path, "overview.json")
    )
    assert callgraph_output.exists()


def test_multiple_project_callgraphs_and_json_reports_sequentially(
    monkeypatch, project_analyzer, tmp_path
):
    base_path = tmp_path / "projects"
    project = base_path / "project1"
    project.mkdir(parents=True)
    source = project / "main.py"
    graphs_dir = tmp_path / "graphs"
    results = pd.DataFrame(
        [
            {
                "filename": str(source),
                "function_name": "main",
                "smell_name": "example",
                "line": 1,
                "description": "description",
                "additional_info": "details",
            }
        ]
    )
    fragment = {
        "file": str(source),
        "nodes": [
            {"id": f"{source}::main", "label": "main", "line": 1}
        ],
        "edges": [],
    }
    monkeypatch.setattr(
        "utils.file_utils.FileUtils.get_python_files", lambda _: [str(source)]
    )
    monkeypatch.setattr(
        "utils.file_utils.FileUtils.initialize_log", lambda _: None
    )
    append_to_log = MagicMock()
    monkeypatch.setattr(
        "utils.file_utils.FileUtils.append_to_log", append_to_log
    )
    project_analyzer.inspector.inspect = MagicMock(
        return_value=(results, fragment)
    )

    project_analyzer.analyze_projects_sequential(
        str(base_path),
        enable_callgraph=True,
        callgraph_output=str(graphs_dir),
        report_format="json",
    )

    assert os.path.exists(
        os.path.join(
            project_analyzer.output_path,
            "project_details",
            "project1_results.json",
        )
    )
    assert (graphs_dir / "project1_callgraph.json").exists()
    append_to_log.assert_called_once_with(
        os.path.join(str(base_path), "execution_log.txt"), "project1"
    )


def test_multiple_project_callgraphs_and_json_reports_in_parallel(
    monkeypatch, project_analyzer, tmp_path
):
    base_path = tmp_path / "projects"
    project = base_path / "project1"
    project.mkdir(parents=True)
    source = project / "main.py"
    combined_graph = tmp_path / "combined.json"
    results = pd.DataFrame(
        [
            {
                "filename": str(source),
                "function_name": "main",
                "smell_name": "example",
                "line": 1,
                "description": "description",
                "additional_info": "details",
            }
        ]
    )
    fragment = {
        "file": str(source),
        "nodes": [
            {"id": f"{source}::main", "label": "main", "line": 1}
        ],
        "edges": [],
    }
    monkeypatch.setattr(
        "utils.file_utils.FileUtils.get_python_files", lambda _: [str(source)]
    )
    monkeypatch.setattr(
        "utils.file_utils.FileUtils.initialize_log", lambda _: None
    )
    synchronized_log = MagicMock()
    monkeypatch.setattr(
        "utils.file_utils.FileUtils.synchronized_append_to_log",
        synchronized_log,
    )
    project_analyzer.inspector.inspect = MagicMock(
        return_value=(results, fragment)
    )

    project_analyzer.analyze_projects_parallel(
        str(base_path),
        max_workers=1,
        enable_callgraph=True,
        callgraph_output=str(combined_graph),
        report_format="json",
    )

    assert os.path.exists(
        os.path.join(
            project_analyzer.output_path,
            "project_details",
            "project1_results.json",
        )
    )
    assert (tmp_path / "combined_project1.json").exists()
    synchronized_log.assert_called_once()
