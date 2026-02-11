import argparse
import sys
from components.project_analyzer import ProjectAnalyzer


class CodeSmileCLI:
    """
    Manages the overall analysis workflow.
    """

    def __init__(self, args):
        """
        Initializes the CLI with parsed arguments.

        Parameters:
        - args: Parsed CLI arguments.
        """
        self.args = args
        self.analyzer = ProjectAnalyzer(args.output)

    def validate_args(self):
        """
        Validates the command-line arguments
        before proceeding with the analysis.
        """
        if self.args.input is None:
            print("Error: Please specify both input and output folders.")
            exit(1)

        if self.args.parallel and self.args.max_walkers <= 0:
            raise ValueError("max_walkers must be greater than 0.")

        if self.args.callgraph_output and not self.args.enable_callgraph:
            raise ValueError(
                "--callgraph-output requires --enable-callgraph."
            )

    def execute(self):
        """
        Executes the analysis workflow based on CLI arguments.
        """
        self.validate_args()

        print("Starting analysis with the following configuration:")
        print(f"Input folder: {self.args.input}")
        print(f"Output folder: {self.args.output}")
        print(f"Parallel execution: {self.args.parallel}")
        print(f"Resume execution: {self.args.resume}")
        print(f"Max Walkers: {self.args.max_walkers}")
        print(f"Analyze multiple projects: {self.args.multiple}")
        print(f"Enable call graph: {self.args.enable_callgraph}")
        print(f"Call graph output: {self.args.callgraph_output}")
        print(f"Exclude paths: {self.args.exclude_paths}")
        print(f"Report format: {self.args.format}")

        if not self.args.resume:
            self.analyzer.clean_output_directory()

        analysis_kwargs = {
            "enable_callgraph": self.args.enable_callgraph,
            "callgraph_output": self.args.callgraph_output,
            "exclude_paths": self.args.exclude_paths,
            "report_format": self.args.format,
        }

        if self.args.multiple:
            if self.args.parallel:
                self.analyzer.analyze_projects_parallel(
                    self.args.input,
                    self.args.max_walkers,
                    **analysis_kwargs,
                )
            else:
                self.analyzer.analyze_projects_sequential(
                    self.args.input,
                    resume=self.args.resume,
                    **analysis_kwargs,
                )
        else:
            total_smells = self.analyzer.analyze_project(
                self.args.input, **analysis_kwargs
            )
            print(
                f"Analysis completed. Total code smells found: {total_smells}"
            )

        if self.args.multiple:
            self.analyzer.merge_all_results(report_format=self.args.format)

        print("Analysis results saved successfully.")


def main():
    parser = argparse.ArgumentParser(
        description="Code Smile: AI-specific "
        "code smells detector for Python projects."
    )
    parser.add_argument(
        "--input", type=str, help="Path to the input folder", required=True
    )
    parser.add_argument(
        "--output", type=str, help="Path to the output folder", required=True
    )
    parser.add_argument(
        "--max_walkers",
        type=int,
        default=5,
        help="Number of workers for parallel execution (default: 5)",
    )
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Enable parallel execution (default: False)",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume previous execution (default: False)",
    )
    parser.add_argument(
        "--multiple",
        action="store_true",
        help="Analyze multiple projects (default: False)",
    )

    parser.add_argument(
        "--enable-callgraph",
        action="store_true",
        help="Enable Call Graph generation (default: False)",
    )
    parser.add_argument(
        "--callgraph-output",
        type=str,
        default=None,
        help="Output path for the generated Call Graph file",
    )
    parser.add_argument(
        "--exclude-paths",
        nargs="*",
        default=[],
        help="Paths to exclude from analysis",
    )
    parser.add_argument(
        "--format",
        choices=["csv", "json"],
        default="csv",
        help="Output format for smells report (default: csv)",
    )

    try:
        args = parser.parse_args()
    except SystemExit:
        print("Error: Missing required arguments or invalid input.\n")
        parser.print_help()
        sys.exit(1)

    print("Starting Code Smile analysis...")
    manager = CodeSmileCLI(args)
    manager.execute()


if __name__ == "__main__":
    main()
