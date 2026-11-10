"""Parser for Alpine Linux apk package repository and test repositories."""

import io
import os
import tarfile
import urllib.request


HTTP_TIMEOUT = 15
INDEX_ARCHIVE = "APKINDEX.tar.gz"
INDEX_FILE = "APKINDEX"
HTTP_PREFIX = "http://"
HTTPS_PREFIX = "https://"
PREFIX_PKG = "P:"
PREFIX_VER = "V:"
PREFIX_DEP = "D:"
EMPTY_LEN = 0


class ApkParseError(Exception):
    """Base exception for package parsing errors."""


class PackageNotFoundError(ApkParseError):
    """Raised when the specified package or version is not found."""


def clean_dep_name(raw_dep: str) -> str:
    """Strip version constraints and return the clean package name."""
    cleaned = raw_dep.strip()
    for operator in (">=", "<=", "~=", "=", ">", "<"):
        if operator in cleaned:
            cleaned = cleaned.split(operator)[0].strip()
            break
    return cleaned


def _parse_apkindex_block(
    block: str,
) -> tuple[str, str, list[str]]:
    """Extract package name, version, and dependencies from index block."""
    lines = block.strip().splitlines()
    pkg_name = ""
    version = ""
    deps: list[str] = []

    for line in lines:
        if line.startswith(PREFIX_PKG):
            pkg_name = line[len(PREFIX_PKG):].strip()
        elif line.startswith(PREFIX_VER):
            version = line[len(PREFIX_VER):].strip()
        elif line.startswith(PREFIX_DEP):
            raw_deps = line[len(PREFIX_DEP):].strip().split()
            deps = [d for d in raw_deps if len(d) > EMPTY_LEN]

    return pkg_name, version, deps


def parse_apkindex_content(
    text: str,
) -> dict[str, dict[str, list[str]]]:
    """Parse raw APKINDEX text into a nested package dictionary."""
    catalog: dict[str, dict[str, list[str]]] = {}
    for block in text.split("\n\n"):
        pkg_name, version, deps = _parse_apkindex_block(block)
        if pkg_name and version:
            if pkg_name not in catalog:
                catalog[pkg_name] = {}
            catalog[pkg_name][version] = deps

    return catalog


def parse_test_repo_content(
    text: str,
) -> dict[str, dict[str, list[str]]]:
    """Parse simplified test repository format (e.g. A: B C)."""
    if PREFIX_PKG in text:
        return parse_apkindex_content(text)

    catalog: dict[str, dict[str, list[str]]] = {}
    for line in text.splitlines():
        line = line.strip()
        if len(line) == EMPTY_LEN or line.startswith("#"):
            continue
        if ":" in line:
            parts = line.split(":", 1)
            pkg = parts[0].strip()
            raw_deps = parts[1].replace(",", " ").split()
            deps = [d for d in raw_deps if len(d) > EMPTY_LEN]
            catalog[pkg] = {"*": deps}
    return catalog


def _download_index_data(url: str) -> bytes:
    """Download index archive bytes from remote URL."""
    target_url = url
    if not target_url.endswith(INDEX_ARCHIVE):
        target_url = target_url.rstrip("/") + "/" + INDEX_ARCHIVE
    req = urllib.request.Request(
        target_url,
        headers={"User-Agent": "apk-dependency-visualizer/1.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as response:
            return response.read()
    except Exception as exc:
        msg = f"Failed to download repository index from {target_url}: {exc}"
        raise ApkParseError(msg) from exc


def _read_tar_archive(raw_bytes: bytes) -> str:
    """Extract and decode APKINDEX text from tar.gz bytes."""
    try:
        buffer = io.BytesIO(raw_bytes)
        with tarfile.open(fileobj=buffer, mode="r:gz") as archive:
            member = archive.extractfile(INDEX_FILE)
            if member is None:
                raise ApkParseError(f"'{INDEX_FILE}' not found in archive.")
            return member.read().decode("utf-8", errors="replace")
    except Exception as exc:
        msg = f"Failed to unpack APKINDEX archive: {exc}"
        raise ApkParseError(msg) from exc


def _load_local_apkindex(path: str) -> dict[str, dict[str, list[str]]]:
    """Load package index from a local file or tar.gz archive."""
    if not os.path.exists(path):
        raise ApkParseError(f"Repository file not found: {path}")

    if path.endswith((".tar.gz", ".apkindex.tar.gz")):
        with open(path, "rb") as file_handle:
            data = _read_tar_archive(file_handle.read())
            return parse_apkindex_content(data)

    with open(path, "r", encoding="utf-8") as file_handle:
        return parse_apkindex_content(file_handle.read())


def load_repository_index(
    url_or_path: str, is_test: bool
) -> dict[str, dict[str, list[str]]]:
    """Load package index from URL, local archive, or test file."""
    if is_test:
        if not os.path.exists(url_or_path):
            raise ApkParseError(f"Test file not found: {url_or_path}")
        with open(url_or_path, "r", encoding="utf-8") as file_handle:
            return parse_test_repo_content(file_handle.read())

    is_remote = (
        url_or_path.startswith(HTTP_PREFIX)
        or url_or_path.startswith(HTTPS_PREFIX)
    )
    if is_remote:
        archive_data = _download_index_data(url_or_path)
        return parse_apkindex_content(_read_tar_archive(archive_data))

    return _load_local_apkindex(url_or_path)


def get_direct_dependencies(
    catalog: dict[str, dict[str, list[str]]],
    package_name: str,
    package_version: str,
    is_test: bool,
) -> list[str]:
    """Retrieve direct dependencies for a given package and version."""
    if package_name not in catalog:
        msg = f"Package '{package_name}' not found in repository."
        raise PackageNotFoundError(msg)

    versions = catalog[package_name]
    if is_test and "*" in versions:
        return list(versions["*"])

    if package_version in versions:
        return list(versions[package_version])

    available = ", ".join(versions.keys())
    msg = (
        f"Version '{package_version}' for package '{package_name}' not found. "
        f"Available versions: [{available}]."
    )
    raise PackageNotFoundError(msg)
