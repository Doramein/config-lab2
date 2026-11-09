"""Unit tests for configuration loading and validation (Stage 1)."""

import os
import tempfile
import unittest
from src.config import ConfigError, parse_config


class TestConfig(unittest.TestCase):
    """Tests XML configuration parsing and comprehensive error handling."""

    def _create_temp_xml(self, content: str) -> str:
        """Helper to create a temporary XML file with given content."""
        temp_file = tempfile.NamedTemporaryFile(
            delete=False, suffix=".xml", mode="w", encoding="utf-8"
        )
        temp_file.write(content)
        temp_file.close()
        return temp_file.name

    def test_valid_config_parsing(self):
        """Test parsing valid XML configuration file."""
        cfg = parse_config("config.xml")
        self.assertEqual(cfg.package_name, "curl")
        self.assertFalse(cfg.test_mode)
        self.assertEqual(cfg.package_version, "8.11.1-r0")
        self.assertEqual(cfg.max_depth, 3)
        self.assertEqual(cfg.output_file, "graph.svg")
        self.assertEqual(cfg.filter_substring, "so:")

    def test_valid_test_mode_config(self):
        """Test parsing valid test-mode XML configuration."""
        cfg = parse_config("data/test_config.xml")
        self.assertEqual(cfg.package_name, "A")
        self.assertTrue(cfg.test_mode)
        self.assertEqual(cfg.repo_url, "data/sample_graph.txt")

    def test_file_not_found(self):
        """Test error when config file does not exist."""
        with self.assertRaises(ConfigError) as ctx:
            parse_config("non_existent_config.xml")
        self.assertIn("not found", str(ctx.exception).lower())

    def test_malformed_xml(self):
        """Test error when XML is syntactically invalid."""
        path = self._create_temp_xml("<config><unclosed>")
        try:
            with self.assertRaises(ConfigError) as ctx:
                parse_config(path)
            self.assertIn("parse error", str(ctx.exception).lower())
        finally:
            os.remove(path)

    def test_missing_required_tag(self):
        """Test error when a required tag is missing."""
        content = (
            "<config>"
            "<repo_url>http://example.com</repo_url>"
            "<test_mode>false</test_mode>"
            "<package_version>1.0</package_version>"
            "<output_file>g.svg</output_file>"
            "<max_depth>2</max_depth>"
            "<filter_substring></filter_substring>"
            "</config>"
        )
        path = self._create_temp_xml(content)
        try:
            with self.assertRaises(ConfigError) as ctx:
                parse_config(path)
            self.assertIn("package_name", str(ctx.exception))
        finally:
            os.remove(path)

    def test_empty_package_name(self):
        """Test error when package_name is empty."""
        content = (
            "<config>"
            "<package_name>   </package_name>"
            "<repo_url>http://example.com</repo_url>"
            "<test_mode>false</test_mode>"
            "<package_version>1.0</package_version>"
            "<output_file>g.svg</output_file>"
            "<max_depth>2</max_depth>"
            "<filter_substring></filter_substring>"
            "</config>"
        )
        path = self._create_temp_xml(content)
        try:
            with self.assertRaises(ConfigError) as ctx:
                parse_config(path)
            self.assertIn("cannot be empty", str(ctx.exception))
        finally:
            os.remove(path)

    def test_invalid_test_mode(self):
        """Test error when test_mode is neither true nor false."""
        content = (
            "<config>"
            "<package_name>curl</package_name>"
            "<repo_url>http://example.com</repo_url>"
            "<test_mode>not_a_bool</test_mode>"
            "<package_version>1.0</package_version>"
            "<output_file>g.svg</output_file>"
            "<max_depth>2</max_depth>"
            "<filter_substring></filter_substring>"
            "</config>"
        )
        path = self._create_temp_xml(content)
        try:
            with self.assertRaises(ConfigError) as ctx:
                parse_config(path)
            self.assertIn("test_mode", str(ctx.exception))
        finally:
            os.remove(path)

    def test_invalid_max_depth(self):
        """Test error when max_depth is non-integer or zero/negative."""
        content = (
            "<config>"
            "<package_name>curl</package_name>"
            "<repo_url>http://example.com</repo_url>"
            "<test_mode>false</test_mode>"
            "<package_version>1.0</package_version>"
            "<output_file>g.svg</output_file>"
            "<max_depth>0</max_depth>"
            "<filter_substring></filter_substring>"
            "</config>"
        )
        path = self._create_temp_xml(content)
        try:
            with self.assertRaises(ConfigError) as ctx:
                parse_config(path)
            self.assertIn("max_depth", str(ctx.exception))
        finally:
            os.remove(path)

    def test_invalid_output_file_extension(self):
        """Test error when output_file does not end with .svg."""
        content = (
            "<config>"
            "<package_name>curl</package_name>"
            "<repo_url>http://example.com</repo_url>"
            "<test_mode>false</test_mode>"
            "<package_version>1.0</package_version>"
            "<output_file>graph.png</output_file>"
            "<max_depth>2</max_depth>"
            "<filter_substring></filter_substring>"
            "</config>"
        )
        path = self._create_temp_xml(content)
        try:
            with self.assertRaises(ConfigError) as ctx:
                parse_config(path)
            self.assertIn(".svg", str(ctx.exception))
        finally:
            os.remove(path)


if __name__ == "__main__":
    unittest.main()
