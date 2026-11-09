"""Configuration module for dependency graph visualizer.

Parses and validates XML configuration files for the tool.
"""

from dataclasses import dataclass
import os
import xml.etree.ElementTree as ET


MIN_ALLOWED_DEPTH = 1
EMPTY_LENGTH = 0
SVG_EXTENSION = ".svg"
TRUE_VALUES = ("true", "1", "yes")
FALSE_VALUES = ("false", "0", "no")
HTTP_PREFIX = "http://"
HTTPS_PREFIX = "https://"


class ConfigError(Exception):
    """Raised when configuration validation or parsing fails."""


@dataclass
class AppConfig:
    """Application configuration parameters container."""

    package_name: str
    repo_url: str
    test_mode: bool
    package_version: str
    output_file: str
    max_depth: int
    filter_substring: str


def validate_test_mode(raw_value: str) -> bool:
    """Validate and convert test mode string to boolean."""
    norm = raw_value.strip().lower()
    if norm in TRUE_VALUES:
        return True
    if norm in FALSE_VALUES:
        return False
    msg = f"Invalid test_mode '{raw_value}'. Expected true or false."
    raise ConfigError(msg)


def validate_package_name(raw_value: str) -> str:
    """Validate package name parameter."""
    norm = raw_value.strip()
    if len(norm) == EMPTY_LENGTH:
        raise ConfigError("package_name cannot be empty.")
    return norm


def validate_package_version(raw_value: str) -> str:
    """Validate package version parameter."""
    norm = raw_value.strip()
    if len(norm) == EMPTY_LENGTH:
        raise ConfigError("package_version cannot be empty.")
    return norm


def validate_max_depth(raw_value: str) -> int:
    """Validate maximum dependency recursion depth."""
    try:
        depth = int(raw_value.strip())
    except ValueError as exc:
        msg = f"Invalid max_depth '{raw_value}'. Must be integer."
        raise ConfigError(msg) from exc
    if depth < MIN_ALLOWED_DEPTH:
        msg = f"max_depth must be at least {MIN_ALLOWED_DEPTH}."
        raise ConfigError(msg)
    return depth


def validate_output_file(raw_value: str) -> str:
    """Validate output SVG file path."""
    norm = raw_value.strip()
    if len(norm) == EMPTY_LENGTH:
        raise ConfigError("output_file cannot be empty.")
    if not norm.lower().endswith(SVG_EXTENSION):
        msg = f"output_file must end with '{SVG_EXTENSION}'."
        raise ConfigError(msg)
    return norm


def validate_repo_url(raw_value: str, test_mode: bool) -> str:
    """Validate repository URL or local file path."""
    norm = raw_value.strip()
    if len(norm) == EMPTY_LENGTH:
        raise ConfigError("repo_url cannot be empty.")
    if test_mode:
        if not os.path.exists(norm):
            msg = f"Test repo file not found: {norm}"
            raise ConfigError(msg)
    else:
        is_web = (
            norm.startswith(HTTP_PREFIX) or norm.startswith(HTTPS_PREFIX)
        )
        if not is_web and not os.path.exists(norm):
            msg = f"repo_url must be web URL or existing file: {norm}"
            raise ConfigError(msg)
    return norm


def _get_element_text(root: ET.Element, tag_name: str) -> str:
    """Extract required tag text from XML element."""
    elem = root.find(tag_name)
    if elem is None:
        raise ConfigError(f"Missing required XML tag: <{tag_name}>.")
    return elem.text or ""


def parse_config(file_path: str) -> AppConfig:
    """Parse and validate XML configuration file."""
    if not os.path.exists(file_path):
        raise ConfigError(f"Configuration file not found: {file_path}")

    try:
        tree = ET.parse(file_path)
    except ET.ParseError as exc:
        raise ConfigError(f"XML parse error in {file_path}: {exc}") from exc

    root = tree.getroot()
    if root.tag != "config":
        raise ConfigError(f"Root tag must be <config>, got <{root.tag}>.")

    pkg_name = validate_package_name(_get_element_text(root, "package_name"))
    mode = validate_test_mode(_get_element_text(root, "test_mode"))
    url = validate_repo_url(_get_element_text(root, "repo_url"), mode)
    version = validate_package_version(
        _get_element_text(root, "package_version")
    )
    output = validate_output_file(_get_element_text(root, "output_file"))
    depth = validate_max_depth(_get_element_text(root, "max_depth"))
    substring = _get_element_text(root, "filter_substring").strip()

    return AppConfig(
        package_name=pkg_name,
        repo_url=url,
        test_mode=mode,
        package_version=version,
        output_file=output,
        max_depth=depth,
        filter_substring=substring,
    )
