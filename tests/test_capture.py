import asyncio
import socket
import threading
import time

from mcp import Client
from mcp.server import MCPServer
from uvicorn import Config, Server

from mcp_traceguard.snapshot import capture_from_client, capture_snapshot


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


def test_capture_legacy_handshake_server() -> None:
    server = MCPServer("legacy-capture-test")

    @server.tool()
    def echo(text: str) -> str:
        """Echo text without changing it."""

        return text

    async def capture_legacy():
        async with Client(server, mode="legacy") as client:
            return await capture_from_client(client)

    captured = asyncio.run(capture_legacy())
    assert captured.server.protocol_version != "2026-07-28"
    assert captured.tools[0].name == "echo"


def test_capture_streamable_http_server() -> None:
    mcp_server = MCPServer("http-capture-test")

    @mcp_server.tool()
    def echo(text: str) -> str:
        """Echo text without changing it."""

        return text

    app = mcp_server.streamable_http_app(stateless_http=True)
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    listener.listen()
    port = listener.getsockname()[1]
    http_server = Server(Config(app, log_level="error", lifespan="on"))
    thread = threading.Thread(
        target=http_server.run,
        kwargs={"sockets": [listener]},
        daemon=True,
    )
    thread.start()
    for _ in range(100):
        if http_server.started:
            break
        time.sleep(0.01)
    try:
        captured = asyncio.run(capture_snapshot(f"http://127.0.0.1:{port}/mcp"))
    finally:
        http_server.should_exit = True
        thread.join(timeout=5)
        listener.close()

    assert not thread.is_alive()
    assert captured.server.protocol_version == "2026-07-28"
    assert captured.tools[0].name == "echo"
