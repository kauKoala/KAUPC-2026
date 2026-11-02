import argparse
import zipfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def add_file(package: zipfile.ZipFile, source: Path, relative: Path) -> None:
    """Add a package file, retaining the executable bit for custom validators."""
    name = relative.as_posix()
    if len(relative.parts) >= 3 and relative.parts[0] == "output_validators" and source.name == "run":
        info = zipfile.ZipInfo(name)
        info.create_system = 3
        info.external_attr = 0o100755 << 16
        package.writestr(info, source.read_bytes(), compress_type=zipfile.ZIP_DEFLATED)
        return
    package.write(source, name)


def build(contest_id: str, label: str) -> Path:
    source = REPO_ROOT / "problems" / "contests" / contest_id / label
    destination = source / "build" / "problem.zip"
    if not (source / "problem.yaml").is_file():
        raise FileNotFoundError(f"Problem package not found: {source}")

    destination.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as package:
        for relative in (
            "problem.yaml",
            "domjudge-problem.ini",
            "problem_statement",
            "submissions",
            "data",
            "output_validators",
        ):
            path = source / relative
            if path.is_file():
                add_file(package, path, path.relative_to(source))
            else:
                for file in sorted(path.rglob("*")):
                    if file.is_file() and "__pycache__" not in file.parts:
                        add_file(package, file, file.relative_to(source))
    return destination


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("contest_id")
    parser.add_argument("label")
    args = parser.parse_args()
    print(build(args.contest_id, args.label))


if __name__ == "__main__":
    main()
