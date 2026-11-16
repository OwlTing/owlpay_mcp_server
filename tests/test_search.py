import pytest
import requests
from mcp.shared.exceptions import McpError
from mcp.types import INTERNAL_ERROR

from conftest import API_ATTR, UPSTREAM_BODY

GENERIC_MESSAGE = "Failed to search documentation. Please try again later."


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
