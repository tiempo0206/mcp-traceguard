"""Small local MCP server used by the quick start and end-to-end tests."""

from mcp.server import MCPServer

mcp = MCPServer("TraceGuard Demo")


@mcp.tool()
def read_note(note_id: str) -> str:
    """Read one note by its stable identifier."""

    return f"demo note {note_id}"


@mcp.tool()
def write_note(note_id: str, content: str) -> dict[str, str]:
    """Store text under a stable note identifier."""

    return {"note_id": note_id, "content": content}


if __name__ == "__main__":
    mcp.run()
