from mcp_traceguard.connection import is_loopback_url


def test_loopback_url_detection_is_narrow() -> None:
    assert is_loopback_url("http://127.0.0.1:8000/mcp")
    assert is_loopback_url("http://localhost:8000/mcp")
    assert is_loopback_url("http://[::1]:8000/mcp")
    assert not is_loopback_url("https://example.com/mcp")
    assert not is_loopback_url("https://127.0.0.1.example.com/mcp")
