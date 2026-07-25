from __future__ import annotations

from dataclasses import asdict, dataclass
from fnmatch import fnmatch
from pathlib import Path, PurePosixPath
from typing import Iterable
import argparse
import json
import zipfile


SOURCE_EXTENSIONS = {
    ".py", ".pyw", ".cs", ".fs", ".vb", ".java", ".kt", ".kts",
    ".cpp", ".cc", ".c", ".h", ".hpp", ".js", ".mjs", ".cjs",
    ".ts", ".tsx", ".jsx", ".html", ".htm", ".css", ".scss",
    ".xml", ".xaml", ".resx", ".properties", ".sql",
}
PROJECT_NAMES = {
    "requirements.txt", "pyproject.toml", "poetry.lock", "pipfile",
    "package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
    "pom.xml", "build.gradle", "settings.gradle", "dockerfile",
    "docker-compose.yml", "docker-compose.yaml",
}
BUILD_HINT_NAMES = PROJECT_NAMES | {
    "readme", "readme.md", "readme.txt", "build.md", "build.txt",
    "run.md", "run.txt", "install.md", "install.txt",
}
STORAGE_EXTENSIONS = {".db", ".sqlite", ".sqlite3", ".mdb", ".accdb"}
SECRET_PATTERNS = (
    ".env", "*.pem", "*.key", "*.pfx", "*.p12", "*.keystore",
    "*secret*", "*credential*", "*password*", "*token*", "id_rsa*",
)


@dataclass(frozen=True)
class IntakeReport:
    status: str
    source_file_count: int
    result_file_count: int
    storage_candidate_count: int
    build_instruction_count: int
    framework_candidates: tuple[str, ...]
    source_files: tuple[str, ...]
    result_files: tuple[str, ...]
    storage_candidates: tuple[str, ...]
    build_instructions: tuple[str, ...]
    rejected_paths: tuple[str, ...]
    sensitive_name_warnings: tuple[str, ...]
    missing_requirements: tuple[str, ...]

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)


def _is_sensitive_name(name: str) -> bool:
    return any(fnmatch(name.lower(), pattern.lower()) for pattern in SECRET_PATTERNS)


def _is_safe_member(name: str) -> bool:
    normalized = name.replace("\\", "/")
    path = PurePosixPath(normalized)
    return (
        bool(normalized)
        and not normalized.startswith("/")
        and not path.is_absolute()
        and ".." not in path.parts
        and not (path.parts and ":" in path.parts[0])
    )


def _iter_directory(root: Path) -> Iterable[tuple[str, bytes]]:
    for path in root.rglob("*"):
        if path.is_file():
            yield path.relative_to(root).as_posix(), path.read_bytes()


def _iter_zip(path: Path) -> Iterable[tuple[str, bytes]]:
    with zipfile.ZipFile(path) as archive:
        for info in archive.infolist():
            if not info.is_dir():
                yield info.filename, archive.read(info)


def _detect_framework(contents: dict[str, bytes]) -> tuple[str, ...]:
    lowered_paths = [path.lower() for path in contents]
    frameworks: set[str] = set()

    if any(path.endswith(".csproj") for path in lowered_paths):
        project_text = "\n".join(
            contents[path].decode("utf-8", "ignore").lower()
            for path in contents
            if path.lower().endswith(".csproj")
        )
        if "usewpf" in project_text or any(path.endswith(".xaml") for path in lowered_paths):
            frameworks.add("dotnet-wpf")
        if "usewindowsforms" in project_text or "system.windows.forms" in project_text:
            frameworks.add("dotnet-winforms")
        if not frameworks:
            frameworks.add("dotnet")

    python_text = "\n".join(
        contents[path].decode("utf-8", "ignore").lower()
        for path in contents
        if path.lower().endswith((".py", ".pyw"))
    )
    if python_text:
        if "tkinter" in python_text or "customtkinter" in python_text:
            frameworks.add("python-tkinter")
        if "pyqt" in python_text or "pyside" in python_text:
            frameworks.add("python-qt")
        if not any(item.startswith("python-") for item in frameworks):
            frameworks.add("python")

    for path in [item for item in contents if item.lower().endswith("package.json")]:
        try:
            payload = json.loads(contents[path].decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
        dependencies = {
            **(payload.get("dependencies") or {}),
            **(payload.get("devDependencies") or {}),
        }
        if "electron" in dependencies:
            frameworks.add("electron")
        elif any(name in dependencies for name in ("react", "vue", "@angular/core")):
            frameworks.add("web-desktop-unknown")

    if any(path.endswith((".java", ".kt", ".kts")) for path in lowered_paths):
        frameworks.add("jvm")

    return tuple(sorted(frameworks))


def inspect_source_package(path: str | Path) -> IntakeReport:
    package = Path(path)
    if not package.exists():
        raise FileNotFoundError(package)

    iterator = _iter_directory(package) if package.is_dir() else _iter_zip(package)
    contents: dict[str, bytes] = {}
    rejected_paths: list[str] = []
    sensitive_names: list[str] = []

    for raw_path, data in iterator:
        normalized = raw_path.replace("\\", "/")
        if not _is_safe_member(normalized):
            rejected_paths.append(raw_path)
            continue
        if _is_sensitive_name(PurePosixPath(normalized).name):
            sensitive_names.append(normalized)
            continue
        contents[normalized] = data

    source_files: list[str] = []
    result_files: list[str] = []
    storage_candidates: list[str] = []
    build_instructions: list[str] = []

    for item in sorted(contents):
        name = PurePosixPath(item).name.lower()
        suffix = PurePosixPath(item).suffix.lower()
        if (
            suffix in SOURCE_EXTENSIONS
            or name in PROJECT_NAMES
            or suffix in {".sln", ".csproj", ".fsproj", ".vbproj", ".vcxproj", ".props", ".targets"}
        ):
            source_files.append(item)
        if name.startswith("quiz_result_") and suffix == ".txt":
            result_files.append(item)
        if suffix in STORAGE_EXTENSIONS or "saved_test" in name or "test_history" in name:
            storage_candidates.append(item)
        if name in BUILD_HINT_NAMES:
            build_instructions.append(item)

    missing_requirements: list[str] = []
    if not source_files:
        missing_requirements.append("desktop source or project files")
    if not result_files:
        missing_requirements.append("at least one complete quiz_result_*.txt")
    if not storage_candidates:
        missing_requirements.append("saved-test storage sample or schema")
    if not build_instructions:
        missing_requirements.append("build/run instructions or project manifest")
    if rejected_paths:
        missing_requirements.append("archive must not contain unsafe paths")
    if sensitive_names:
        missing_requirements.append("remove sensitive-looking files before upload")

    return IntakeReport(
        status="ready" if not missing_requirements else "blocked",
        source_file_count=len(source_files),
        result_file_count=len(result_files),
        storage_candidate_count=len(storage_candidates),
        build_instruction_count=len(build_instructions),
        framework_candidates=_detect_framework(contents),
        source_files=tuple(source_files),
        result_files=tuple(result_files),
        storage_candidates=tuple(storage_candidates),
        build_instructions=tuple(build_instructions),
        rejected_paths=tuple(sorted(rejected_paths)),
        sensitive_name_warnings=tuple(sorted(sensitive_names)),
        missing_requirements=tuple(missing_requirements),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate a Defans Mania source directory or ZIP before integration."
    )
    parser.add_argument("package", help="Source directory or ZIP path")
    parser.add_argument("--output", help="Optional JSON report path")
    args = parser.parse_args(argv)

    report = inspect_source_package(args.package)
    rendered = report.to_json()
    if args.output:
        Path(args.output).write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if report.status == "ready" else 2


if __name__ == "__main__":
    raise SystemExit(main())
