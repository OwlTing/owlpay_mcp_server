import asyncio
import time
from contextlib import asynccontextmanager

import anyio
import pytest
import requests
from mcp import ClientSession
from mcp.shared.exceptions import McpError
from mcp.shared.memory import create_client_server_memory_streams
from mcp.types import INTERNAL_ERROR

from conftest import API_ATTR, TOOL_NAME, UPSTREAM_BODY

GENERIC_MESSAGE = "Failed to search documentation. Please try again later."
# Each upstream call takes SLOW_DELAY; two calls run serially would take >= 2 * SLOW_DELAY.
SLOW_DELAY = 0.5
CONCURRENT_LIMIT = 1.5 * SLOW_DELAY


def _assert_generic_error(excinfo):
    err = excinfo.value
    assert err.error.code == INTERNAL_ERROR
    assert err.error.message == GENERIC_MESSAGE
    for text in (err.error.message, str(err)):
        assert "127.0.0.1" not in text
        assert "http" not in text


def test_retries_transient_503_then_succeeds(fast_retry, upstream, server, search):
    fake = upstream([503, 503, 200])

    result = search("payment")

    assert len(fake.requests) == 3
    assert result.startswith(server.RESULT_PREFIX)
    assert result[len(server.RESULT_PREFIX):] == UPSTREAM_BODY


def test_retry_adapter_mounted_for_http_and_https(fast_retry, upstream, server, search, monkeypatch):
    upstream([200])
    sessions = []

    class RecordingSession(requests.Session):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            sessions.append(self)

    monkeypatch.setattr(server.requests, "Session", RecordingSession)

    search("payment")

    assert len(sessions) == 1
    session = sessions[0]
    https_adapter = session.get_adapter("https://example.com/")
    http_adapter = session.get_adapter("http://example.com/")
    assert https_adapter is http_adapter
    retry = https_adapter.max_retries
    assert retry.total == 3
    assert {502, 503, 504} <= set(retry.status_forcelist)


def test_persistent_503_raises_generic_error(fast_retry, upstream, search):
    upstream([503])

    with pytest.raises(McpError) as excinfo:
        search("payment")

    _assert_generic_error(excinfo)


def test_connection_refused_raises_generic_error(fast_retry, monkeypatch, server, search, closed_port_url):
    monkeypatch.setattr(server, API_ATTR, closed_port_url)

    with pytest.raises(McpError) as excinfo:
        search("payment")

    _assert_generic_error(excinfo)


def test_instructions_and_result_prefix(server):
    assert server.mcp.instructions == server.SERVER_INSTRUCTIONS
    assert server.RESULT_PREFIX.startswith("[External content:")


def test_fastmcp_tool_does_not_block_event_loop(upstream, server):
    upstream([200], delay=SLOW_DELAY)
    ticks = 0

    async def ticker(stop):
        nonlocal ticks
        while not stop.is_set():
            ticks += 1
            await asyncio.sleep(0.01)

    async def run():
        stop = asyncio.Event()
        tick_task = asyncio.create_task(ticker(stop))
        start = time.monotonic()
        results = await asyncio.gather(
            server.mcp.call_tool(TOOL_NAME, {"query": "a"}),
            server.mcp.call_tool(TOOL_NAME, {"query": "b"}),
        )
        elapsed = time.monotonic() - start
        stop.set()
        await tick_task
        return results, elapsed

    results, elapsed = asyncio.run(run())

    assert elapsed < CONCURRENT_LIMIT, elapsed
    # The loop kept running while both calls were in flight.
    assert ticks >= 10, ticks
    for content, _ in results:
        assert content[0].text == server.RESULT_PREFIX + UPSTREAM_BODY


@asynccontextmanager
async def _stdio_session(server, monkeypatch):
    """Run serve_mcp() over in-memory streams instead of real stdio."""
    async with create_client_server_memory_streams() as (client_streams, server_streams):

        @asynccontextmanager
        async def fake_stdio_server():
            yield server_streams

        monkeypatch.setattr(server, "stdio_server", fake_stdio_server)
        async with anyio.create_task_group() as tg:
            tg.start_soon(server.serve_mcp)
            async with ClientSession(*client_streams) as session:
                await session.initialize()
                yield session
            tg.cancel_scope.cancel()


def test_stdio_call_tool_does_not_block_event_loop(upstream, server, monkeypatch):
    upstream([200], delay=SLOW_DELAY)

    async def run():
        async with _stdio_session(server, monkeypatch) as session:
            start = time.monotonic()
            results = await asyncio.gather(
                session.call_tool(TOOL_NAME, {"query": "a"}),
                session.call_tool(TOOL_NAME, {"query": "b"}),
            )
            return results, time.monotonic() - start

    results, elapsed = asyncio.run(run())

    assert elapsed < CONCURRENT_LIMIT, elapsed
    for result in results:
        assert not result.isError
        assert result.content[0].text == server.RESULT_PREFIX + UPSTREAM_BODY


def test_stdio_get_prompt_returns_results(upstream, server, monkeypatch):
    upstream([200])

    async def run():
        async with _stdio_session(server, monkeypatch) as session:
            return await session.get_prompt(TOOL_NAME, {"query": "payment"})

    result = asyncio.run(run())

    assert result.messages[0].content.text == server.RESULT_PREFIX + UPSTREAM_BODY
