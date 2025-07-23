# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
"""
This utility script updates author information in documentation files.
You can either trial the script in 'dry-run' mode by using the --print flag or apply in-place changes.
This script updates the following files:
- CITATION.cff
- conf.py
- index.rst

Usage:
     python update_authors.py authors.txt [--help] [--debug] [--year YEAR] [--version VERSION] [--doi DOI] [--print]

The expected format for the authors.txt file is:
    Firstname Lastname <ORCID>,
    Firstname Lastname <ORCID>,
    Firstname Lastname, ...

Where ORCID is optional. The '<>' brackets are required to denote the ORCID identifier.
The script will parse this file and update the documentation files where applicable.

note: This script requires the ruamel.yaml package for YAML handling. yaml was considered,
but ruamel.yaml is more suitable for preserving formatting in YAML files.
"""
from __future__ import annotations

import sys
import argparse
import re
import io
import logging

from dataclasses import dataclass
from pathlib import Path
from ruamel.yaml import YAML

yaml = YAML()
yaml.preserve_quotes = True
yaml.indent(sequence=4, offset=2)
yaml.width = 1000  # Prevent autowrapping of long strings


@dataclass
class ProjectPaths:
    """Centralise Path Configuration"""
    project_root: Path
    authors_file: Path
    index_rst: Path
    citation_cff: Path
    conf_py: Path

    @classmethod
    def from_script_location(cls, auithors_file: str) -> ProjectPaths:
        """Create paths relative to script location"""
        script_path = Path(__file__).resolve()
        project_root = script_path.parent.parent

        return cls(project_root=project_root,
                   authors_file=Path(auithors_file).resolve(),
                   index_rst=project_root / "docs" / "index.rst",
                   citation_cff=project_root / "CITATION.cff",
                   conf_py=project_root / "docs" / "conf.py")

    def validate_target_files(self) -> list[Path]:
        """Returns list of missing files"""
        target_files = [self.index_rst, self.citation_cff, self.conf_py]
        return [file for file in target_files if not file.exists()]


@dataclass
class Author:
    """Represents an author with a first name, last name, and optional ORCID identifier."""
    firstname: str
    lastname: str
    orcid: str | None = None

    def __str__(self) -> str:
        if self.orcid:
            return f"{self.firstname} {self.lastname} {self.orcid}"
        return f"{self.firstname} {self.lastname}"


class AuthorList:
    """Represents a list of authors, providing methods to format them for different documentation styles."""

    def __init__(self, authors: list[Author]) -> None:
        self.authors = authors

    @classmethod
    def from_file(cls, filepath: Path) -> AuthorList:
        return cls(read_authors_from_file(filepath))

    def sorted(self) -> AuthorList:
        """Return a new AuthorList sorted by lastname, firstname."""
        sorted_authors = sorted(self.authors, key=lambda author: (author.lastname.lower(), author.firstname.lower()))
        return AuthorList(sorted_authors)

    def to_conf_py_tuple(self, line_length: int = 120) -> str:
        """
        Format authors for conf.py as a tuple.
        Names are 'lastname, firstname' (no ORCID).
        """
        names = [format_author_name(author, style="full") for author in self.authors]
        lines = _wrap_names(names, line_length)
        return format_conf_py_author_block(lines)

    def to_cff_format(self) -> str:
        """
        Format authors for CITATION.cff as a YAML string
        Each author is represented as a dictionary with 'family-names', 'given-names', and optional 'orcid' fields.
        """
        author_dicts = []
        for author in self.authors:
            entry = {"family-names": author.lastname, "given-names": author.firstname}
            if author.orcid:
                entry["orcid"] = author.orcid
            author_dicts.append(entry)
        return yaml_to_string({"authors": author_dicts})

    def to_index_rst_format(self, year: int, version: str, doi: str = "10.5281/zenodo.4728059") -> str:
        """Format authors for index.rst citation."""
        author_str = "; ".join([format_author_name(author, style="index") for author in self.authors])
        return f"{author_str}. ({year}). Mantid Imaging ({version}), Zenodo https://doi.org/{doi}"

    def print(self) -> None:
        for author in self.authors:
            print(str(author))


def read_authors_from_file(filepath: Path) -> list[Author]:
    """
    Reads a list of authors from a file, parsing names and optional ORCID identifiers.

    The file should contain author entries separated by commas. Each entry should be in the format:
    "Firstname Lastname" or "Firstname Lastname <ORCID>". Entries with less than two name parts are skipped.

    :param filepath: Path to the file containing author entries.
    :return: List[Author]: A list of Author objects parsed from the file.
    :raises ValueError: If an entry does not contain at least a first and last name.
    """
    entries = _split_entries(_read_file_content(filepath))
    authors = []

    for entry in entries:
        try:
            authors.append(_parse_author_entry(entry))
        except ValueError as unexpected_value_error:
            logging.warning(f"Skipping invalid author entry: {entry} ({unexpected_value_error})")
    return authors


def _read_file_content(path: Path) -> str:
    with path.open("r", encoding="utf-8") as file:
        return file.read()


def write_lines_to_file(path: Path, lines: list[str]) -> None:
    """Write a list of lines to a file, overwriting its contents"""
    with path.open("w", encoding="utf-8") as f:
        f.writelines(lines)
    logging.info(f"Successfully wrote {len(lines)} lines to {path}")


def write_yaml_to_file(path: Path, data) -> None:
    """Write a YAML object to a file, preserving formatting"""
    with path.open("w", encoding="utf-8") as f:
        yaml.dump(data, f)


def yaml_to_string(data) -> str:
    """Convert a Python object to a YAML string"""
    stream = io.StringIO()
    yaml.dump(data, stream)
    return stream.getvalue()


def _split_entries(content: str) -> list[str]:
    return [entry.strip() for entry in content.split(",") if entry.strip()]


def _validate_orcid(orcid: str) -> bool:
    """Validate ORCID format: https://orcid.org/0000-0000-0000-000X"""
    pattern = r'^https://orcid\.org/\d{4}-\d{4}-\d{4}-\d{3}[\dX]$'
    return re.match(pattern, orcid) is not None


def _parse_author_entry(entry: str) -> Author:
    """
    Parse a single author entry string into an Author object.
    If the name consists of more than 2 parts, everything but the last part is considered the first name.
    Expected formats:
      - "Firstname Lastname"
      - "Firstname Lastname <ORCID>"
    Returns an Author object.
    """
    entry = entry.strip()

    # Extract orcid if present
    match = re.match(r"^(.*?)\s*<([^>]+)>$", entry)
    if match:
        name_section = match.group(1).strip()
        orcid = match.group(2).strip()
        if orcid and not _validate_orcid(orcid):
            logging.warning(f"Invalid ORCID format: {orcid} in entry: {entry}")
    else:
        name_section, orcid = entry, None

    # Split name and validate name
    name_parts = name_section.split()
    if len(name_parts) < 2:
        raise ValueError(f"Invalid author entry: '{entry}'")
    firstname = " ".join(name_parts[:-1])
    lastname = name_parts[-1]
    return Author(firstname=firstname, lastname=lastname, orcid=orcid)


def format_author_name(author: Author, style: str = "full") -> str:
    """
    Format an Author object as a string.
    style: 'full' -> 'Firstname Lastname'
              'index' -> 'Lastname, Firstname'
    """
    if style == "index":
        return f"{author.lastname}, {author.firstname}"
    return f"{author.firstname} {author.lastname}"


def _wrap_names(names: list[str], line_length: int) -> list[str]:
    """Wrap names into quoted lines not exceeding a line_length."""
    lines = []
    current_line = ""

    for _, name in enumerate(names):
        addition = (", " if current_line else "") + name
        if len(current_line) + len(addition) > line_length and current_line:
            lines.append(current_line + ", ")
            current_line = name
        else:
            current_line += addition
    if current_line:
        lines.append(current_line)

    quoted_lines = [f'    "{line}"' for line in lines]  # Ensure each line is quoted and indented
    return quoted_lines


def format_conf_py_author_block(lines: list[str]) -> str:
    """ Format the author lines into a conf.py author block as a string."""
    return "author = (\n" + "\n".join(lines) + "\n)\n"


def find_index(lines: list[str], is_match, error_msg="No matching line found.") -> int:
    """Return the index of the first line matching the condition, or raise ValueError."""
    index = next((index for index, line in enumerate(lines) if is_match(line)), None)
    if index is None:
        raise ValueError(error_msg)
    return index


class AuthorUpdater:
    """A class to handle the updating of author information in documentation files."""

    def __init__(self, authors: AuthorList, year: int, version: str, doi: str) -> None:
        self.authors = authors
        self.year = year
        self.version = version
        self.doi = doi

    def update_all(self, paths: ProjectPaths, dry_run: bool = False) -> None:
        """
        Update all documentation files with the new author information.
        If dry_run is True, print the changes instead of applying them in-place.
        """
        citation_format = self.authors.to_cff_format()
        conf_format = self.authors.to_conf_py_tuple()
        index_format = self.authors.to_index_rst_format(self.year, self.version, self.doi)

        if dry_run:
            print("CITATION.cff authors:\n", citation_format)
            print("\nconf.py authors:\n", conf_format)
            print("\nindex.rst authors:\n", index_format)
        else:
            doc_updater = DocUpdater(paths)
            doc_updater.replace_citation_line(index_format)
            doc_updater.replace_authors_block(citation_format)
            doc_updater.replace_author_tuple(conf_format)


class DocUpdater:
    """A class to handle the updating of documentation files containing find and replace operations."""

    def __init__(self, paths: ProjectPaths) -> None:
        self.paths = paths

    def replace_citation_line(self, new_citation: str) -> None:
        """Replace the citation line in index.rst after 'Please cite as:' with new_citation"""
        contents = _read_file_content(self.paths.index_rst)
        lines = contents.splitlines(keepends=True)
        cite_idx = find_index(lines, lambda line: "Please cite as:" in line, "'Please cite as:' not found in file.")
        for index, line_content in enumerate(lines[cite_idx + 1:], start=cite_idx + 1):
            if line_content.strip() and self.is_citation_line(line_content):
                lines[index] = new_citation + "\n"
                break
        else:
            raise ValueError("Citation line not found after 'Please cite as:'.")
        write_lines_to_file(self.paths.index_rst, lines)

    def is_citation_line(self, line: str) -> bool:
        """
        Checks if a line matches the citation pattern:
        lastname, firstname; ... . (YEAR). Mantid Imaging (VERSION), Zenodo https://doi.org/...
        :returns: True if the line matches the pattern, False otherwise.
        """
        name_part = r"[A-Za-zÀ-ÿ\-']+"
        author = fr"{name_part}, {name_part}"
        author_list = fr"({author}(; )?)+"
        year = r"\(\d{4}\)"
        version = r"\([^)]+\)"
        doi = r"https://doi\.org/[^\s]+"
        pattern = fr"^{author_list}\. {year}\. Mantid Imaging {version}, Zenodo {doi}"
        citation_regex = re.compile(pattern)
        return citation_regex.match(line.strip()) is not None

    def replace_authors_block(self, citation_format: str) -> None:
        """Replace the authors block in CITATION.cff with the new citation"""
        content = _read_file_content(self.paths.citation_cff)
        cff_data = yaml.load(content)
        new_authors_block = yaml.load(citation_format)
        cff_data['authors'] = new_authors_block['authors']
        write_yaml_to_file(self.paths.citation_cff, cff_data)

    def replace_author_tuple(self, conf_format: str) -> None:
        """Replace the author tuple in conf.py with the new citation"""
        content = _read_file_content(self.paths.conf_py)
        lines = content.splitlines(keepends=True)
        start_idx, end_idx = self.find_author_tuple_line(lines)
        conf_format_lines = [line if line.endswith('\n') else line + '\n' for line in conf_format.splitlines()]
        lines[start_idx:end_idx + 1] = conf_format_lines
        write_lines_to_file(self.paths.conf_py, lines)

    def find_author_tuple_line(self, lines: list[str]) -> tuple[int, int]:
        """
        Find the start and end line indices of the author tuple in conf.py.
        :returns: (start_idx, end_idx).
        """
        try:
            start_idx = find_index(lines, lambda line: re.match(r"^\s*author\s*=\s*\(", line),
                                   "author = ( ... ) tuple not found in file.")
            end_idx = find_index(lines[start_idx + 1:], lambda line: ")" in line,
                                 "End of author tuple not found in file.") + start_idx + 1
            return start_idx, end_idx
        except ValueError as value_error:
            raise ValueError("Error finding author tuple in conf.py. "
                             f"Possibly due to invalid structure: {value_error}") from value_error


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Update author lists in documentation files.",
                                     epilog=("Examples:\n"
                                             "  python update_authors.py authors.txt\n"
                                             "  python update_authors.py authors.txt --print\n"
                                             "  python update_authors.py authors.txt --year 2024 --version 2.9.0\n"),
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("authors_file", help="Path to authors.txt")
    parser.add_argument("-p", "--print", action="store_true", help="Print output instead of modifying files in-place")
    parser.add_argument("-y", "--year", type=int, default=2025, help="Publication year (default: 2025)")
    parser.add_argument("-v", "--version", default="3.0.0", help="Version string (default: 3.0.0)")
    parser.add_argument("--doi", default="10.5281/zenodo.4728059", help="DOI (default: 10.5281/zenodo.4728059)")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    logging.basicConfig(level=logging.INFO,
                        format='%(levelname)s: %(message)s',
                        handlers=[logging.StreamHandler(sys.stderr)])

    logging.debug(f"Starting with args: {args}")

    try:
        paths = ProjectPaths.from_script_location(args.authors_file)
        logging.debug(f"Project paths: {paths}")

        if not args.print:
            missing_files = paths.validate_target_files()
            if missing_files:
                raise FileNotFoundError(
                    f"The following required files are missing: {', '.join(str(file) for file in missing_files)}")

        authors = AuthorList.from_file(Path(args.authors_file)).sorted()
        updater = AuthorUpdater(authors, year=args.year, version=args.version, doi=args.doi)
        updater.update_all(paths, dry_run=args.print)

        if not args.print:
            logging.info("Successfully updated all documentation files!")

    except FileNotFoundError as file_not_found_error:
        logging.error(f"Error: File not found - {file_not_found_error}")
    except PermissionError as permission_error:
        logging.error(f"Error: Permission denied - {permission_error}")
    except ValueError as value_error:
        logging.error(f"Error: Invalid data - {value_error}")
    except Exception as general_error:
        logging.error(f"Unexpected error: {general_error}")
    else:
        return

    sys.exit(1)


if __name__ == "__main__":
    main()
