from pathlib import Path
from autodev.tools.base import ToolContext
from autodev.tools.list_files import ListFilesTool
from autodev.tools.read_file import ReadFileTool
from autodev.tools.search_code import SearchCodeTool
from autodev.tools.edit_file import EditFileTool


def context(tmp_path: Path) -> ToolContext:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.cpp").write_text("calculate_average();\n", encoding="utf-8")
    return ToolContext(repository_root=tmp_path)


def test_read_file_and_root_safety(tmp_path):
    ctx = context(tmp_path)
    assert ReadFileTool().run(ctx, path="src/main.cpp").ok
    assert not ReadFileTool().run(ctx, path="../secret.txt").ok


def test_list_files(tmp_path):
    result = ListFilesTool().run(context(tmp_path))
    assert "src/main.cpp" in result.output


def test_search_code(tmp_path):
    result = SearchCodeTool().run(context(tmp_path), query="calculate_average")
    assert result.output[0]["path"] == "src/main.cpp"


def test_edit_file_is_root_safe(tmp_path):
    ctx = context(tmp_path)
    assert EditFileTool().run(ctx, path="src/new.cpp", content="int main(){}\n").ok
    assert (tmp_path / "src" / "new.cpp").exists()
    assert not EditFileTool().run(ctx, path="../escape.cpp", content="bad").ok
