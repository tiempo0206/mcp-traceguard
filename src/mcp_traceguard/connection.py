"""Construct MCP clients with safe, predictable loopback HTTP behavior."""

from __future__ import annotations

import ipaddress
from contextlib import asynccontextmanager
from typing import Any
from urllib.parse import urlparse

import httpx2
from mcp import Client
from mcp.client.streamable_http import streamable_http_client


def is_loopback_url(target: str) -> bool:
    parsed = urlparse(target)
    if parsed.scheme not in {"http", "https"} or parsed.hostname is None:
        return False
    if parsed.hostname.lower() == "localhost":
        return True
    try:
        return ipaddress.ip_address(parsed.hostname).is_loopback
    except ValueError:
        return False


@asynccontextmanager
async def _loopback_transport(url: str):
    # System proxy settings frequently intercept localhost unless NO_PROXY is
    # configured. Only literal loopback targets bypass them; remote URLs retain
    # the official SDK's default proxy behavior.
    async with (
        httpx2.AsyncClient(trust_env=False) as http_client,
        streamable_http_client(url, http_client=http_client) as streams,
    ):
        yield streams


def client_for_target(target: Any) -> Client:
    if isinstance(target, str) and is_loopback_url(target):
        return Client(_loopback_transport(target))
    return Client(target)
