from pathlib import Path
import tempfile
import unittest
import zipfile

from defans_mania_reference.source_intake import inspect_source_package


def write_zip(path: Path, files: dict[str, str]) -> None:
    with zipfile.ZipFile(path, "w") as archive:
        for name, content in files.items():
            archive.writestr(name, content)


class SourceIntakeTests(unittest.TestCase):
    def test_ready_python_tkinter_package(self):
        with tempfile.TemporaryDirectory() as tmp:
            package = Path(tmp) / "source.zip"
            write_zip(
                package,
                {
                    "app/main.py": "import tkinter\n",
                    "README.md": "python app/main.py\n",
                    "quiz_result_2.txt": "Score: 300\n",
                    "saved_test_schema.sql": "create table attempts(id text);\n",
                    "requirements.txt": "",
                },
            )
            report = inspect_source_package(package)
            self.assertEqual(report.status, "ready")
            self.assertIn("python-tkinter", report.framework_candidates)
            self.assertEqual(report.result_file_count, 1)
            self.assertEqual(report.storage_candidate_count, 1)

    def test_blocks_missing_required_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            package = Path(tmp) / "source.zip"
            write_zip(package, {"app/main.py": "print('x')\n"})
            report = inspect_source_package(package)
            self.assertEqual(report.status, "blocked")
            self.assertIn(
                "at least one complete quiz_result_*.txt",
                report.missing_requirements,
            )
            self.assertIn(
                "saved-test storage sample or schema",
                report.missing_requirements,
            )
            self.assertIn(
                "build/run instructions or project manifest",
                report.missing_requirements,
            )

    def test_rejects_path_traversal(self):
        with tempfile.TemporaryDirectory() as tmp:
            package = Path(tmp) / "source.zip"
            write_zip(
                package,
                {
                    "../escape.py": "print('bad')",
                    "README.md": "run",
                    "quiz_result_1.txt": "Score: 1",
                    "saved_test.db": "",
                },
            )
            report = inspect_source_package(package)
            self.assertIn("../escape.py", report.rejected_paths)
            self.assertIn(
                "archive must not contain unsafe paths",
                report.missing_requirements,
            )

    def test_warns_and_excludes_sensitive_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            package = Path(tmp) / "source.zip"
            write_zip(
                package,
                {
                    "app/main.py": "print('x')",
                    ".env": "TOKEN=secret",
                    "README.md": "run",
                    "quiz_result_1.txt": "Score: 1",
                    "saved_test.db": "",
                },
            )
            report = inspect_source_package(package)
            self.assertIn(".env", report.sensitive_name_warnings)
            self.assertIn(
                "remove sensitive-looking files before upload",
                report.missing_requirements,
            )
            self.assertNotIn(".env", report.source_files)

    def test_detects_dotnet_wpf(self):
        with tempfile.TemporaryDirectory() as tmp:
            package = Path(tmp) / "source.zip"
            write_zip(
                package,
                {
                    "DefansMania.csproj": (
                        "<Project><PropertyGroup><UseWPF>true</UseWPF>"
                        "</PropertyGroup></Project>"
                    ),
                    "MainWindow.xaml": "<Window />",
                    "README.md": "dotnet run",
                    "quiz_result_1.txt": "Score: 1",
                    "saved_test_schema.sql": "create table attempts(id text);",
                },
            )
            report = inspect_source_package(package)
            self.assertEqual(report.status, "ready")
            self.assertIn("dotnet-wpf", report.framework_candidates)

    def test_directory_input_is_supported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "main.py").write_text("print('x')", encoding="utf-8")
            (root / "README.md").write_text("run", encoding="utf-8")
            (root / "quiz_result_1.txt").write_text("Score: 1", encoding="utf-8")
            (root / "saved_test_schema.sql").write_text(
                "create table x(y text)", encoding="utf-8"
            )
            report = inspect_source_package(root)
            self.assertEqual(report.status, "ready")


if __name__ == "__main__":
    unittest.main()
