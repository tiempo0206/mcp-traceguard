"""Safe runtime fixture: it exposes sensitive-shaped data but performs no I/O."""

from mcp.server import MCPServer

mcp = MCPServer("TraceGuard Runtime Fixture")


@mcp.tool()
def read_profile(user_id: str) -> dict[str, str]:
    """Read a deterministic test profile containing a fake credential."""

    return {
        "user_id": user_id,
        "display_name": "Demo User",
        "api_token": "fake-test-token-never-use",
    }


@mcp.tool()
def publish_message(channel: str, message: str) -> dict[str, str]:
    """Simulate publishing a message without contacting an external service."""

    return {"channel": channel, "message": message, "status": "simulated"}


@mcp.tool()
def shell_exec(command: str) -> str:
    """Return a blocked command as text without executing it."""

    return f"not executed: {command}"


@mcp.tool()
def echo_unclassified(text: str) -> str:
    """Echo text for exercising the default runtime decision."""

    return text


@mcp.tool()
def fetch_url(url: str) -> dict[str, str]:
    """Simulate a URL fetch without making a network request."""

    return {"url": url, "status": "simulated"}


if __name__ == "__main__":
    mcp.run()
