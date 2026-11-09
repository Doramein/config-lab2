"""Main entrypoint for the dependency graph visualizer CLI application."""

import argparse
import os
import sys

# Ensure project root is on sys.path when running script directly
_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT_DIR not in sys.path:
    sys.path.insert(0, _ROOT_DIR)

from src.apk_parser import (
    ApkParseError,
    get_direct_dependencies,
    load_repository_index,
)
from src.config import AppConfig, ConfigError, parse_config


EXIT_SUCCESS = 0
EXIT_FAILURE = 1
DEFAULT_CONFIG = "config.xml"
STAGE_1 = 1
STAGE_2 = 2


def format_config_params(cfg: AppConfig) -> str:
    """Format configuration parameters as key-value pairs."""
    return (
        f"package_name: {cfg.package_name}\n"
        f"repo_url: {cfg.repo_url}\n"
        f"test_mode: {str(cfg.test_mode).lower()}\n"
        f"package_version: {cfg.package_version}\n"
        f"output_file: {cfg.output_file}\n"
        f"max_depth: {cfg.max_depth}\n"
        f"filter_substring: {cfg.filter_substring}"
    )


def run_stage1(cfg: AppConfig) -> int:
    """Execute Stage 1: display configuration in key-value format."""
    print(format_config_params(cfg))
    return EXIT_SUCCESS


def run_stage2(cfg: AppConfig) -> int:
    """Execute Stage 2: display direct dependencies of the package."""
    try:
        catalog = load_repository_index(cfg.repo_url, cfg.test_mode)
        deps = get_direct_dependencies(
            catalog, cfg.package_name, cfg.package_version, cfg.test_mode
        )
    except ApkParseError as err:
        sys.stderr.write(f"Package index error: {err}\n")
        return EXIT_FAILURE

    print(f"Direct dependencies for {cfg.package_name} "
          f"({cfg.package_version}):")
    if not deps:
        print("  (no dependencies)")
    else:
        for dep in deps:
            print(f"- {dep}")
    return EXIT_SUCCESS


def build_arg_parser() -> argparse.ArgumentParser:
    """Build CLI arguments parser."""
    parser = argparse.ArgumentParser(
        description="Alpine apk package dependency analyzer."
    )
    parser.add_argument(
        "--config",
        "-c",
        default=DEFAULT_CONFIG,
        help="Path to XML configuration file.",
    )
    parser.add_argument(
        "--stage",
        "-s",
        type=int,
        choices=[STAGE_1, STAGE_2],
        default=STAGE_2,
        help="Stage to execute (1 or 2).",
    )
    return parser


def main(argv=None) -> int:
    """Run CLI application dispatching selected stage."""
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    try:
        cfg = parse_config(args.config)
    except ConfigError as err:
        sys.stderr.write(f"Configuration error: {err}\n")
        return EXIT_FAILURE

    if args.stage == STAGE_1:
        return run_stage1(cfg)
    return run_stage2(cfg)


if __name__ == "__main__":
    sys.exit(main())
