"""Unit tests for Alpine apk repository parser and data collection."""

import os
import tempfile
import unittest
from src.apk_parser import (
    ApkParseError,
    PackageNotFoundError,
    clean_dep_name,
    get_direct_dependencies,
    load_repository_index,
    parse_apkindex_content,
    parse_test_repo_content,
)


SAMPLE_APKINDEX = """C:Q1example=
P:sample-pkg
V:1.2.3-r0
D:dep-a dep-b=2.0 so:libtest.so.1

C:Q1example2=
P:sample-pkg
V:1.2.4-r0
D:dep-c

C:Q1example3=
P:dep-a
V:0.9.0-r1
D:
"""


class TestApkParser(unittest.TestCase):
    """Test suite for parsing APKINDEX and test repository data."""

    def test_clean_dep_name(self):
        """Test stripping version constraints from dependency names."""
        self.assertEqual(clean_dep_name("curl-libs=8.14.1-r2"), "curl-libs")
        self.assertEqual(clean_dep_name("openssl>=3.0.0"), "openssl")
        self.assertEqual(clean_dep_name("zlib<2.0"), "zlib")
        self.assertEqual(clean_dep_name("simple-pkg"), "simple-pkg")

    def test_parse_apkindex_content(self):
        """Test parsing APKINDEX text blocks into dictionary."""
        catalog = parse_apkindex_content(SAMPLE_APKINDEX)
        self.assertIn("sample-pkg", catalog)
        self.assertIn("1.2.3-r0", catalog["sample-pkg"])
        self.assertEqual(
            catalog["sample-pkg"]["1.2.3-r0"],
            ["dep-a", "dep-b=2.0", "so:libtest.so.1"],
        )
        self.assertEqual(catalog["sample-pkg"]["1.2.4-r0"], ["dep-c"])
        self.assertEqual(catalog["dep-a"]["0.9.0-r1"], [])

    def test_parse_test_repo_content(self):
        """Test parsing simplified letter-based test repository."""
        text = "A: B, C\nB: D\nC:\n"
        catalog = parse_test_repo_content(text)
        self.assertIn("A", catalog)
        self.assertEqual(catalog["A"]["*"], ["B", "C"])
        self.assertEqual(catalog["B"]["*"], ["D"])
        self.assertEqual(catalog["C"]["*"], [])

    def test_get_direct_dependencies_success(self):
        """Test retrieving dependencies when package and version match."""
        catalog = parse_apkindex_content(SAMPLE_APKINDEX)
        deps = get_direct_dependencies(
            catalog, "sample-pkg", "1.2.3-r0", is_test=False
        )
        self.assertEqual(deps, ["dep-a", "dep-b=2.0", "so:libtest.so.1"])

    def test_get_direct_dependencies_test_mode(self):
        """Test retrieving dependencies in test mode with wildcard version."""
        catalog = parse_test_repo_content("A: B C\nB:\n")
        deps = get_direct_dependencies(catalog, "A", "1.0", is_test=True)
        self.assertEqual(deps, ["B", "C"])

    def test_package_not_found(self):
        """Test error when requested package does not exist."""
        catalog = parse_apkindex_content(SAMPLE_APKINDEX)
        with self.assertRaises(PackageNotFoundError):
            get_direct_dependencies(catalog, "ghost", "1.0", is_test=False)

    def test_version_not_found(self):
        """Test error when requested version does not exist."""
        catalog = parse_apkindex_content(SAMPLE_APKINDEX)
        with self.assertRaises(PackageNotFoundError) as ctx:
            get_direct_dependencies(
                catalog, "sample-pkg", "9.9.9", is_test=False
            )
        self.assertIn("Available versions", str(ctx.exception))

    def test_load_test_repository_file(self):
        """Test loading repository index from a local test file."""
        catalog = load_repository_index("data/sample_graph.txt", is_test=True)
        self.assertIn("A", catalog)
        self.assertEqual(catalog["A"]["*"], ["B", "C"])

    def test_load_missing_file_error(self):
        """Test error when repository index file does not exist."""
        with self.assertRaises(ApkParseError):
            load_repository_index("non_existent_repo.txt", is_test=True)


if __name__ == "__main__":
    unittest.main()
