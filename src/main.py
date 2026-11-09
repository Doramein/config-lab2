"""Main entrypoint for the dependency graph visualizer CLI application."""

import argparse
import sys
from src.config import AppConfig, ConfigError, parse_config


EXIT_SUCCESS = 0
EXIT_FAILURE = 1
DEFAULT_CONFIG = "config.xml"


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


def build_arg_parser() -> argparse.ArgumentParser:
    """Build CLI arguments parser."""
    parser = argparse.ArgumentParser(
        description="Alpine apk package dependency graph visualizer."
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
        default=1,
        help="Target lab stage to execute (1-5).",
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

    if args.stage == 1:
        return run_stage1(cfg)

    sys.stderr.write(f"Stage {args.stage} is not yet implemented.\n")
    return EXIT_FAILURE


if __name__ == "__main__":
    sys.exit(main())
