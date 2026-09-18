import asyncio

from mcp.server import MCPServer

from mcp_traceguard.snapshot import capture_snapshot


def test_capture_real_in_memory_mcp_server() -> None:
    server = MCPServer("capture-test")

    @server.tool()
    def echo(text: str) -> str:
        """Echo text without changing it."""

        return text

    captured = asyncio.run(capture_snapshot(server))
    assert captured.server.name == "capture-test"
    assert captured.tools[0].name == "echo"
    assert len(captured.tools[0].fingerprint) == 64
