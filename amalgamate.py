from typing import Callable
import sys
import os
import re
import pathlib
import graphlib

def git_root(start_path: str | pathlib.Path | None = None) -> pathlib.Path | None:
    current: pathlib.Path = pathlib.Path(start_path or pathlib.Path.cwd()).resolve()
    for parent in [current, *current.parents]:
        if (parent / ".git").exists():
            return parent
    return None

def unwrap[T](option: T | None) -> T:
    if option is None:
        sys.exit(1)
    return option

def try_unwrap[T](func: Callable[[], T]) -> T:
    try:
        return func()
    except Exception as ex:
        print(f"error {ex}", file=sys.stderr)
        sys.exit(1)

def wildcard(path: pathlib.Path | str, pattern: str) -> list[pathlib.Path]:
    p = pathlib.Path(path)
    if not p.is_dir():
        raise NotADirectoryError(f"'{p}' is not a valid directory")

    return [
        entry for entry
        in p.rglob(pattern)
        if entry.is_file()
    ]

ROOT: pathlib.Path = unwrap(git_root())

SOURCE_FILES: list[pathlib.Path] = try_unwrap(lambda: wildcard(ROOT / "src", "*.c"))
HEADER_FILES: list[pathlib.Path] = try_unwrap(lambda: wildcard(ROOT / "src", "*.h"))
ALL_FILES = SOURCE_FILES + HEADER_FILES

# ^ start of line
# \s* zero or more whitespace
# #include literal match
# \s+ one or more whitespace
# " literal match
# ([^"]+) make a capture group (used later) that finds one or more of any character that arent a "
# " literal match
LOCAL_INCLUDE_RE = re.compile(r'^\s*#include\s+"([^"]+)"')

def resolve_dependencies() -> list[pathlib.Path]:
    file_map = {path.name: path for path in ALL_FILES}
    graph: dict[str, set[str]] = {}

    for path in ALL_FILES:
        if path.name not in graph:
            graph[path.name] = set()

        content = path.read_text(encoding="utf-8")
        for line in content.splitlines():
            match = LOCAL_INCLUDE_RE.match(line)
            if match:
                included_file = pathlib.Path(match.group(1)).name
                # only track files in the project
                if included_file in file_map:
                    # if file A includes B, B must come before A
                    graph[path.name].add(included_file)

    try:
        sorter = graphlib.TopologicalSorter(graph)
        sorted_names = list(sorter.static_order())
        return [
            file_map[name]
            for name in sorted_names
            if name in file_map
        ]
    except Exception as ex:
        print(f"error: cyclic dependency detected or sorting failed: {ex}", file=sys.stderr)
        sys.exit(1)

def amalgamate(files: list[pathlib.Path], banner: str, include_header: str | None = None) -> str:
    content: list[str] = [banner]
    if include_header:
        content.append(f'#include "{include_header}"\n\n')

    for src_path in files:
        relative_name = src_path.relative_to(ROOT)
        content.append(f"/* BEGIN FILE: {relative_name}*/\n")

        for line in src_path.read_text(encoding="utf-8").splitlines(keepends=True):
            # remove all local header includes
            if line.strip().startswith('#include "'):
                continue
            content.append(line)
                    
        content.append(f"/* END FILE:   {relative_name}*/\n")

    return "".join(content)
                    
OUTPUT_SOURCE_FILE = ROOT / "librpn_amalgamated.c"
OUTPUT_HEADER_FILE = ROOT / "librpn_amalgamated.h"

if __name__ == "__main__":
    sorted_files = resolve_dependencies()
    sorted_headers = [f for f in sorted_files if f.suffix == ".h"]
    sorted_sources = [f for f in sorted_files if f.suffix == ".c"]

    header_text = amalgamate(
        sorted_headers,
        banner="/* Amalgamated uRPN Public Header */\n\n"
    )
    OUTPUT_HEADER_FILE.write_text(header_text, encoding="utf-8")

    source_text = amalgamate(
        sorted_sources,
        banner="/* Amalgamated uRPN Implementation */\n\n",
        include_header=OUTPUT_HEADER_FILE.name
    )
    OUTPUT_SOURCE_FILE.write_text(source_text, encoding="utf-8")

    print("done!")
