"""Deliberately drifted server that demonstrates TraceGuard findings."""

from mcp.server import MCPServer

mcp = MCPServer("TraceGuard Demo")


@mcp.tool()
def read_note(note_id: str) -> str:
    """Read every note visible to the current process."""

    return f"demo note {note_id}"


@mcp.tool()
def write_note(note_id: str, content: str) -> dict[str, str]:
    """Store text under a stable note identifier."""

    return {"note_id": note_id, "content": content}


@mcp.tool()
def shell_exec(command: str) -> str:
    """Demonstrate an unapproved high-risk capability without executing it."""

    return f"blocked demo command: {command}"


if __name__ == "__main__":
    mcp.run()
