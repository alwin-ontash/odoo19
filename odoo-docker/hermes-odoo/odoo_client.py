"""
odoo_client.py — MCP Streamable HTTP client for Odoo's /mcp endpoint.

Initializes an MCP session once (caches the session ID), then calls
tools/call for every query. Authentication via Bearer token.
Loads credentials from .env. Never logs or exposes keys.
"""

import json
import logging
import os

import requests
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

_MCP_URL: str = os.getenv("MCP_URL", "").rstrip("/") + "/mcp"
_MCP_KEY: str = os.getenv("MCP_KEY", "")

_REQUEST_TIMEOUT: int = 15  # seconds

logger = logging.getLogger(__name__)

# Persistent session — reused across all MCP calls
_session = requests.Session()
_mcp_session_id: str | None = None


def _check_config() -> None:
    missing = [
        name
        for name, value in [("MCP_URL", _MCP_URL), ("MCP_KEY", _MCP_KEY)]
        if not value or value == "/mcp"
    ]
    if missing:
        raise RuntimeError(
            f"Missing required environment variables: {', '.join(missing)}. "
            "Copy .env.example to .env and fill in your values."
        )


def _get_session_id() -> str:
    global _mcp_session_id
    if _mcp_session_id:
        return _mcp_session_id

    _check_config()
    headers = {
        "Authorization": f"Bearer {_MCP_KEY}",
        "Content-Type": "application/json",
    }

    # Step 1: initialize — server returns Mcp-Session-Id header
    init_payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "clientInfo": {"name": "hermes-odoo", "version": "2.0"},
            "capabilities": {},
        },
    }
    try:
        resp = _session.post(
            _MCP_URL, headers=headers, json=init_payload, timeout=_REQUEST_TIMEOUT
        )
        resp.raise_for_status()
    except requests.exceptions.Timeout:
        raise RuntimeError("Odoo MCP did not respond in time. Please try again later.")
    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            "Could not reach Odoo. Check MCP_URL and that Odoo is running."
        )
    except requests.exceptions.HTTPError as exc:
        raise RuntimeError(f"Odoo MCP returned HTTP {exc.response.status_code} during init.")

    sid = resp.headers.get("Mcp-Session-Id")
    if not sid:
        raise RuntimeError(
            "MCP server did not return a session ID. "
            "Check MCP_URL points to your Odoo instance and MCP_KEY is valid."
        )

    # Step 2: notify server that client is initialized
    headers["Mcp-Session-Id"] = sid
    _session.post(
        _MCP_URL,
        headers=headers,
        json={"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
        timeout=_REQUEST_TIMEOUT,
    )

    _mcp_session_id = sid
    logger.info("MCP session established [sid=%s]", sid)
    return sid


def call_mcp_tool(tool_name: str, arguments: dict) -> list:
    """
    Call an MCP tool on the Odoo /mcp endpoint and return the records list.

    Args:
        tool_name:  MCP tool name, e.g. "search_read".
        arguments:  Dict of arguments for the tool.

    Returns:
        A list of records (dicts) from the tool response.

    Raises:
        RuntimeError: On config errors, connection failures, or MCP errors.
    """
    sid = _get_session_id()
    headers = {
        "Authorization": f"Bearer {_MCP_KEY}",
        "Content-Type": "application/json",
        "Mcp-Session-Id": sid,
    }
    payload = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": arguments},
    }

    try:
        resp = _session.post(
            _MCP_URL, headers=headers, json=payload, timeout=_REQUEST_TIMEOUT
        )
        resp.raise_for_status()
    except requests.exceptions.Timeout:
        logger.error("MCP request timed out [tool=%s]", tool_name)
        raise RuntimeError("Odoo MCP did not respond in time. Please try again later.")
    except requests.exceptions.ConnectionError:
        logger.error("Could not connect to Odoo MCP [url=%s]", _MCP_URL)
        raise RuntimeError(
            "Could not reach Odoo. Check MCP_URL and that Odoo is running."
        )
    except requests.exceptions.HTTPError as exc:
        status = exc.response.status_code
        logger.error("MCP HTTP error [status=%s tool=%s]", status, tool_name)
        raise RuntimeError(f"Odoo MCP returned HTTP {status}.")

    body = resp.json()

    if "error" in body:
        safe_message = body["error"].get("message", "An MCP error occurred.")
        logger.error("MCP error [tool=%s message=%s]", tool_name, safe_message)
        raise RuntimeError(f"MCP error: {safe_message}")

    content = body.get("result", {}).get("content", [])
    if not content:
        return []

    text = content[0].get("text", "[]")
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            if "records" in parsed:
                return parsed["records"]
            return parsed  # write tool result — return dict as-is
        return parsed if isinstance(parsed, list) else []
    except (json.JSONDecodeError, TypeError):
        return []
