from .base import Tool
from .edit_file import EditFileTool
from .git_diff import GitDiffTool
from .list_files import ListFilesTool
from .read_file import ReadFileTool
from .run_command import RunCommandTool
from .search_code import SearchCodeTool


def default_tools() -> dict[str, Tool]:
    tools = [ListFilesTool(), ReadFileTool(), SearchCodeTool(), EditFileTool(), RunCommandTool(), GitDiffTool()]
    return {tool.name: tool for tool in tools}
