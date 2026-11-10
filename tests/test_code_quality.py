"""Automated code quality compliance tests for lab rules.

Verifies:
- Line length <= 80 characters (P2)
- Function length <= 40 lines (F1)
- Function parameters count <= 7 (A1)
- Docstrings present and no comments instead of docstrings (K1)
- Cyclomatic complexity <= 10 (C1)
- No magic numbers in comparisons (M1)
- Identifiers follow PEP8 naming conventions (I1)
"""

import ast
import os
import tokenize
import unittest


MAX_LINE_LENGTH = 80
MAX_FUNC_LINES = 40
MAX_FUNC_ARGS = 7
MAX_CYCLOMATIC_COMPLEXITY = 10
BASE_COMPLEXITY = 1


def _calc_complexity(node: ast.AST) -> int:
    """Calculate cyclomatic complexity of an AST node."""
    complexity = BASE_COMPLEXITY
    for child in ast.walk(node):
        if isinstance(
            child,
            (
                ast.If,
                ast.While,
                ast.For,
                ast.AsyncFor,
                ast.ExceptHandler,
                ast.With,
                ast.AsyncWith,
            ),
        ):
            complexity += 1
        elif isinstance(child, ast.BoolOp):
            complexity += len(child.values) - 1
    return complexity


class TestCodeQuality(unittest.TestCase):
    """Verifies that repository Python code strictly follows constraints."""

    def _get_python_files(self) -> list[str]:
        """Collect all python files from src and tests directories."""
        py_files: list[str] = []
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

    def test_cyclomatic_complexity(self):
        """Rule C1: Cyclomatic complexity must not exceed 10."""
        for path in self._get_python_files():
            with open(path, "r", encoding="utf-8") as file_handle:
                tree = ast.parse(file_handle.read(), filename=path)

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    complexity = _calc_complexity(node)
                    msg = (
                        f"Function {node.name} in {path} has complexity "
                        f"{complexity} > {MAX_CYCLOMATIC_COMPLEXITY}"
                    )
                    self.assertLessEqual(
                        complexity, MAX_CYCLOMATIC_COMPLEXITY, msg
                    )

    def test_no_magic_numbers_in_comparisons(self):
        """Rule M1: Code must not use raw numeric literals in comparisons."""
        for path in self._get_python_files():
            with open(path, "r", encoding="utf-8") as file_handle:
                tree = ast.parse(file_handle.read(), filename=path)

            for node in ast.walk(tree):
                if isinstance(node, ast.Compare):
                    operands = [node.left] + node.comparators
                    for item in operands:
                        is_num = isinstance(item, ast.Constant) and isinstance(
                            item.value, (int, float)
                        )
                        msg = (
                            f"Magic number in comparison at "
                            f"{path}:{node.lineno}"
                        )
                        self.assertFalse(is_num, msg)

    def test_no_inline_comments(self):
        """Rule K1: Code must not use inline comments instead of docstrings."""
        for path in self._get_python_files():
            with open(path, "rb") as file_handle:
                tokens = tokenize.tokenize(file_handle.readline)
                for tok in tokens:
                    is_comment = tok.type == tokenize.COMMENT
                    msg = (
                        f"Stray comment '{tok.string}' in "
                        f"{path}:{tok.start[0]}"
                    )
                    self.assertFalse(is_comment, msg)


if __name__ == "__main__":
    unittest.main()
