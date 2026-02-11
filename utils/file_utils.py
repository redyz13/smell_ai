import os
import shutil
import pandas as pd


class FileUtils:
    """
    Handles file and directory-related operations.
    """

    @staticmethod
    def clean_directory(root_path: str, subfolder_name: str = "output") -> str:
        """
        Cleans or creates a specified subfolder within a root directory.

        Parameters:
        - root_path (str): Root directory where the subfolder will be created.
        - subfolder_name (str): Name of the subfolder to clean or create.

        Returns:
        - str: Path to the cleaned or created subfolder.
        """
        output_path = os.path.join(root_path, subfolder_name)

        if os.path.exists(output_path):
            for filename in os.listdir(output_path):
                file_path = os.path.join(output_path, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print(f"Failed to delete {file_path}. Reason: {e}")
        else:
            os.makedirs(output_path)

        return output_path

    @staticmethod
    def _normalize_exclude_paths(exclude_paths, base_path: str) -> list[str]:
        if not exclude_paths:
            return []

        normalized = []
        for p in exclude_paths:
            if not p:
                continue
            abs_p = (
                os.path.abspath(os.path.join(base_path, p))
                if not os.path.isabs(p)
                else os.path.abspath(p)
            )
            normalized.append(os.path.normpath(abs_p))
        return normalized

    @staticmethod
    def _is_excluded(file_path: str, excluded_paths: list[str]) -> bool:
        if not excluded_paths:
            return False
        f = os.path.normpath(os.path.abspath(file_path))
        for ex in excluded_paths:
            if f == ex or f.startswith(ex + os.sep):
                return True
        return False

    @staticmethod
    def get_python_files(path: str, exclude_paths=None) -> list[str]:
        """
        Retrieves all Python files from the specified path.

        Parameters:
        - path (str): Path to search for Python files.
        - exclude_paths: Optional list of paths (absolute or relative to `path`)
          to exclude from discovery.

        Returns:
        - list[str]: List of Python file paths.
        """
        result = []
        base_path = path if os.path.isdir(path) else os.path.dirname(path)
        excluded = FileUtils._normalize_exclude_paths(exclude_paths, base_path)

        if os.path.isfile(path) and path.endswith(".py"):
            if FileUtils._is_excluded(path, excluded):
                return []
            return [path]

        for root, dirs, files in os.walk(path):
            if "venv" in dirs:
                dirs.remove("venv")
            if "lib" in dirs:
                dirs.remove("lib")

            # prune excluded directories
            dirs[:] = [
                d
                for d in dirs
                if not FileUtils._is_excluded(os.path.join(root, d), excluded)
            ]

            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.abspath(os.path.join(root, file))
                    if FileUtils._is_excluded(file_path, excluded):
                        continue
                    result.append(file_path)

        return result

    @staticmethod
    def merge_results(input_dir: str, output_dir: str, report_format: str = "csv"):
        """
        Merges analysis results from multiple projects into a single report.

        Parameters:
        - input_dir (str): Directory containing analysis results.
        - output_dir (str): Directory where the merged results will be saved.
        - report_format (str): "csv" (default) or "json".
        """
        dataframes = []

        if report_format == "json":
            print(f"Looking for JSON files in directory: {input_dir}")
        else:
            print(f"Looking for CSV files in directory: {input_dir}")

        for subdir, _, files in os.walk(input_dir):
            for file in files:
                if report_format == "json" and file.endswith(".json"):
                    file_path = os.path.join(subdir, file)
                    try:
                        df = pd.read_json(file_path)
                        if not df.empty:
                            dataframes.append(df)
                        else:
                            print(f"Skipping empty JSON: {file_path}")
                    except Exception as e:
                        print(f"Failed to read {file_path}: {e}")

                if report_format != "json" and file.endswith(".csv"):
                    file_path = os.path.join(subdir, file)
                    try:
                        df = pd.read_csv(file_path)
                        if not df.empty:
                            dataframes.append(df)
                        else:
                            print(f"Skipping empty CSV: {file_path}")
                    except Exception as e:
                        print(f"Failed to read {file_path}: {e}")

        if dataframes:
            combined_df = pd.concat(dataframes, ignore_index=True)
            os.makedirs(output_dir, exist_ok=True)

            if report_format == "json":
                out_path = os.path.join(output_dir, "overview.json")
                combined_df.to_json(out_path, orient="records", indent=2)
                print(f"Merged results saved to {out_path}")
            else:
                out_path = os.path.join(output_dir, "overview.csv")
                combined_df.to_csv(out_path, index=False)
                print(f"Merged results saved to {out_path}")
        else:
            if report_format == "json":
                print("No valid JSON files found to merge.")
            else:
                print("No valid CSV files found to merge.")

    @staticmethod
    def initialize_log(log_path: str):
        """
        Initializes an execution log file by overwriting its contents.

        Parameters:
        - log_path (str): Path to the log file to initialize.
        """
        with open(log_path, "w") as log_file:
            log_file.write("")
        print(f"Execution log initialized: {log_path}")

    @staticmethod
    def append_to_log(log_path: str, project_name: str):
        """
        Appends a project name to the execution log.

        Parameters:
        - log_path (str): Path to the log file.
        - project_name (str): Name of the project to append to the log.
        """
        with open(log_path, "a") as log_file:
            log_file.write(project_name + "\n")
        print(f"Appended to log: {project_name}")

    @staticmethod
    def get_last_logged_project(log_path: str) -> str:
        """
        Retrieves the last project name logged in the execution log.

        Parameters:
        - log_path (str): Path to the log file.

        Returns:
        - str: Name of the last logged project,
          or an empty string if the log is empty.
        """
        try:
            with open(log_path, "r") as log_file:
                lines = log_file.readlines()
                return lines[-1].strip() if lines else ""
        except FileNotFoundError:
            return ""

    @staticmethod
    def synchronized_append_to_log(log_path: str, project_name: str, lock):
        """
        Thread-safe method to append a project name to the execution log.

        Parameters:
        - log_path (str): Path to the log file.
        - project_name (str): Name of the project to append to the log.
        - lock: Threading lock to ensure synchronized writes.
        """
        with lock:
            with open(log_path, "a") as log_file:
                log_file.write(project_name + "\n")
            print(f"Thread-safe appended to log: {project_name}")
