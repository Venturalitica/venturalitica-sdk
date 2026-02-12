"""
Tests for venturalitica.assurance.graph.parser (ASTCodeScanner).

Covers: scan_file (file not found, syntax error, successful parse),
        scan_directory (nonexistent dir, real dir with .py files).
"""

import pytest

from venturalitica.assurance.graph.parser import ASTCodeScanner


@pytest.fixture
def scanner():
    return ASTCodeScanner()


class TestScanFile:
    def test_file_not_found(self, scanner):
        """Line 15: returns error dict when file doesn't exist."""
        result = scanner.scan_file("/nonexistent/path/fake.py")
        assert result == {"error": "File not found"}

    def test_syntax_error(self, scanner, tmp_path):
        """Lines 22-23: returns error dict for invalid Python syntax."""
        bad_file = tmp_path / "bad.py"
        bad_file.write_text("def broken(:\n    pass\n")
        result = scanner.scan_file(str(bad_file))
        assert result == {"error": "Syntax Error"}

    def test_successful_parse(self, scanner, tmp_path):
        """Lines 25-76: parses valid Python file, extracts context."""
        good_file = tmp_path / "sample.py"
        good_file.write_text(
            '"""Module docstring."""\n'
            "import os\n"
            "from pathlib import Path\n"
            "\n"
            "def my_func():\n"
            '    """A function."""\n'
            "    pass\n"
            "\n"
            "df = pd.read_csv('data.csv')\n"
            "model.fit(X)\n"
        )
        result = scanner.scan_file(str(good_file))
        assert "error" not in result
        assert result["docstring"] == "Module docstring."
        assert "os" in result["imports"]
        assert any(f["name"] == "my_func" for f in result["functions"])
        # read_csv and fit are interesting calls
        method_names = [c["method"] for c in result["calls"]]
        assert "read_csv" in method_names
        assert "fit" in method_names

    def test_data_loading_type(self, scanner, tmp_path):
        """Verifies data_loading vs training_logic type classification."""
        src = tmp_path / "typed.py"
        src.write_text("loader.load_data()\nmodel.train()\n")
        result = scanner.scan_file(str(src))
        calls = result["calls"]
        load_call = next(c for c in calls if c["method"] == "load_data")
        train_call = next(c for c in calls if c["method"] == "train")
        assert load_call["type"] == "data_loading"
        assert train_call["type"] == "training_logic"


class TestScanDirectory:
    def test_nonexistent_directory(self, scanner):
        """Line 84: returns empty dict for nonexistent directory."""
        result = scanner.scan_directory("/nonexistent/dir")
        assert result == {}

    def test_scans_py_files(self, scanner, tmp_path):
        """Lines 87-89: iterates .py files, skips dotfiles."""
        (tmp_path / "module_a.py").write_text("x = 1\n")
        (tmp_path / "module_b.py").write_text("y = 2\n")
        (tmp_path / ".hidden.py").write_text("z = 3\n")
        (tmp_path / "data.csv").write_text("a,b\n1,2\n")

        result = scanner.scan_directory(str(tmp_path))
        assert "module_a.py" in result
        assert "module_b.py" in result
        assert ".hidden.py" not in result
        assert "data.csv" not in result
        # Each entry should be a valid context dict
        assert "docstring" in result["module_a.py"]
