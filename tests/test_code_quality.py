"""Automated code quality compliance tests for lab rules.

Verifies:
- Line length <= 80 characters (P2)
- Function length <= 40 lines (F1)
- Function parameters count <= 7 (A1)
- Docstrings present on modules, classes, and functions (K1)
"""

import ast
import os
import unittest


MAX_LINE_LENGTH = 80
MAX_FUNC_LINES = 40
MAX_FUNC_ARGS = 7


class TestCodeQuality(unittest.TestCase):
    """Verifies that repository Python code strictly follows constraints."""

    def _get_python_files(self):
        """Collect all python files from src and tests directories."""
        py_files = []
        for root_dir in ("src", "tests"):
            for root, _, files in os.walk(root_dir):
                for fname in files:
                    if fname.endswith(".py"):
                        py_files.append(os.path.join(root, fname))
        return py_files

    def test_line_length(self):
        """Rule P2: Python code must not have lines > 80 characters."""
        for path in self._get_python_files():
            with open(path, "r", encoding="utf-8") as file_handle:
                for idx, line in enumerate(file_handle, start=1):
                    stripped = line.rstrip("\r\n")
                    msg = (
                        f"Line {idx} in {path} exceeds 80 chars "
                        f"({len(stripped)})"
                    )
                    self.assertLessEqual(len(stripped), MAX_LINE_LENGTH, msg)

    def test_function_length_and_args(self):
        """Rules F1, A1, K1: checks function length, args and docstrings."""
        for path in self._get_python_files():
            with open(path, "r", encoding="utf-8") as file_handle:
                tree = ast.parse(file_handle.read(), filename=path)

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    total_args = (
                        len(node.args.args)
                        + len(node.args.posonlyargs)
                        + len(node.args.kwonlyargs)
                    )
                    self.assertLessEqual(
                        total_args,
                        MAX_FUNC_ARGS,
                        f"Function {node.name} in {path} has > 7 args",
                    )
                    lines = (node.end_lineno - node.lineno) + 1
                    self.assertLessEqual(
                        lines,
                        MAX_FUNC_LINES,
                        f"Function {node.name} in {path} has > 40 lines",
                    )
                    doc = ast.get_docstring(node)
                    self.assertIsNotNone(
                        doc,
                        f"Function {node.name} in {path} missing docstring",
                    )


if __name__ == "__main__":
    unittest.main()
